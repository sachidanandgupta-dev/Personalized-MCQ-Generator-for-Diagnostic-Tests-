import json
import re

import google.generativeai as genai
from fastapi import HTTPException

from app.config import Settings
from app.schemas import McqItem

MCQ_COUNT = 5


def _build_prompt(educational_text: str, difficulty: int) -> str:
    return f"""You are an expert educational assessment designer.

ADAPTIVE DIFFICULTY: The learner's personalized target difficulty is {difficulty} on a scale of 1 (easiest) to 10 (hardest). Calibrate question complexity, depth, and distractor plausibility to match this level.

Using ONLY the educational content below, create exactly {MCQ_COUNT} multiple-choice questions at difficulty level {difficulty}/10.

EDUCATIONAL CONTENT:
---
{educational_text}
---

STRICT OUTPUT RULES (you must follow all of these):
1. Return ONLY a valid JSON array. No markdown, no code fences, no commentary before or after.
2. The array must contain exactly {MCQ_COUNT} objects.
3. Each object MUST have exactly these keys:
   - "question" (string): the question stem
   - "options" (array of exactly 4 strings): the four answer choices
   - "correct_answer" (string): must match one of the four options exactly
   - "explanation" (string): brief rationale for the correct answer
4. Questions must test understanding of the provided content, not outside knowledge.
5. All four options must be plausible; only one may be correct.

Example shape (structure only):
[
  {{
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "B",
    "explanation": "..."
  }}
]
"""


def _extract_json_array(text: str) -> list:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    return json.loads(cleaned)


def generate_mcqs(
    educational_text: str,
    difficulty: int,
    settings: Settings,
) -> list[McqItem]:
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    prompt = _build_prompt(educational_text, difficulty)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed: {exc}",
        ) from exc

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response.")

    try:
        parsed = _extract_json_array(raw_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not parse Gemini response as JSON: {exc}",
        ) from exc

    if not isinstance(parsed, list):
        raise HTTPException(
            status_code=502,
            detail="Gemini response must be a JSON array.",
        )

    try:
        items = [McqItem.model_validate(item) for item in parsed]
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini response did not match expected MCQ schema: {exc}",
        ) from exc

    if len(items) != MCQ_COUNT:
        raise HTTPException(
            status_code=502,
            detail=f"Expected {MCQ_COUNT} questions, got {len(items)}.",
        )

    for item in items:
        if item.correct_answer not in item.options:
            raise HTTPException(
                status_code=502,
                detail="Each correct_answer must be one of the four options.",
            )

    return items
