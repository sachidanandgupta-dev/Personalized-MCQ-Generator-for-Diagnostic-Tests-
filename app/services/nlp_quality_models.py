"""
Lightweight NLP quality scoring (replaces LLM evaluation).

Loading strategy (FastAPI-friendly):
  1. Call ``initialize()`` once during app lifespan (in a thread so startup stays async).
  2. Keep a single loaded copy of each model in process memory (singleton).
  3. Run all inference in a dedicated ``ThreadPoolExecutor`` via ``run_in_executor`` so
     PyTorch/transformers never block the main asyncio event loop.
  4. Use ``max_workers=1`` on CPU hosts (Render free tier) to avoid memory spikes from
     parallel forward passes.

Models:
  - Relevance: sentence-transformers/all-MiniLM-L6-v2 (cosine similarity vs source text)
  - Clarity: textattack/distilbert-base-uncased-CoLA (grammatical acceptability proxy)
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

SOURCE_MAX_CHARS = 4_000
QUESTION_MAX_CHARS = 512


def _linear_map(value: float, low: float, high: float) -> int:
    """Map a value in [low, high] to an integer score 1–5."""
    if high <= low:
        return 3
    ratio = (max(low, min(high, value)) - low) / (high - low)
    return max(1, min(5, round(1 + ratio * 4)))


def _heuristic_clarity_score(question: str) -> float:
    """Fallback clarity signal in [0, 1] when the classifier is unavailable."""
    text = question.strip()
    words = re.findall(r"\b[\w']+\b", text)
    n = len(words)
    if n < 4:
        return 0.25
    if n > 60:
        return 0.35

    score = 0.55
    if text.endswith("?"):
        score += 0.2
    if 8 <= n <= 35:
        score += 0.15
    avg_len = sum(len(w) for w in words) / n
    if avg_len <= 8:
        score += 0.1
    return min(1.0, score)


class NLPQualityModels:
    """Process-wide singleton for quality-scoring models."""

    _instance: NLPQualityModels | None = None
    _instance_lock = threading.Lock()

    def __init__(self, encoder_model: str, cola_model: str, max_workers: int = 1) -> None:
        self.encoder_model_name = encoder_model
        self.cola_model_name = cola_model
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="nlp-quality",
        )
        self._init_lock = threading.Lock()
        self._ready = False
        self._encoder: SentenceTransformer | None = None
        self._cola_tokenizer: Any = None
        self._cola_model: Any = None
        self._cola_labels: dict[int, str] = {}

    @classmethod
    def get(cls) -> NLPQualityModels:
        with cls._instance_lock:
            if cls._instance is None:
                from app.config import get_settings

                settings = get_settings()
                cls._instance = cls(
                    encoder_model=settings.quality_encoder_model,
                    cola_model=settings.quality_cola_model,
                    max_workers=settings.nlp_inference_workers,
                )
            return cls._instance

    @property
    def is_ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        """Load models once (call from lifespan via ``asyncio.to_thread``)."""
        with self._init_lock:
            if self._ready:
                return

            logger.info("Loading quality encoder: %s", self.encoder_model_name)
            self._encoder = SentenceTransformer(self.encoder_model_name)

            logger.info("Loading clarity classifier: %s", self.cola_model_name)
            self._cola_tokenizer = AutoTokenizer.from_pretrained(self.cola_model_name)
            self._cola_model = AutoModelForSequenceClassification.from_pretrained(
                self.cola_model_name
            )
            self._cola_model.eval()
            id2label = getattr(self._cola_model.config, "id2label", {}) or {}
            self._cola_labels = {int(k): str(v).lower() for k, v in id2label.items()}

            self._ready = True
            logger.info("NLP quality models ready (device=cpu)")

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        self._encoder = None
        self._cola_model = None
        self._cola_tokenizer = None
        self._ready = False
        with self._instance_lock:
            NLPQualityModels._instance = None

    def _acceptable_probability(self, question: str) -> float:
        assert self._cola_model is not None and self._cola_tokenizer is not None

        inputs = self._cola_tokenizer(
            question,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True,
        )
        with torch.inference_mode():
            logits = self._cola_model(**inputs).logits[0]
            probs = torch.softmax(logits, dim=-1)

        acceptable_idx = None
        for idx, label in self._cola_labels.items():
            if "accept" in label or label in {"1", "label_1", "grammatical"}:
                acceptable_idx = idx
                break

        if acceptable_idx is None:
            acceptable_idx = int(probs.argmax().item())

        return float(probs[acceptable_idx].item())

    def score_sync(
        self,
        educational_text: str,
        question_text: str,
        user_was_correct: bool,
    ) -> dict:
        if not self._ready or self._encoder is None:
            raise RuntimeError("NLP quality models are not initialized.")

        source = educational_text.strip()[:SOURCE_MAX_CHARS]
        question = question_text.strip()[:QUESTION_MAX_CHARS]

        embeddings = self._encoder.encode(
            [source, question],
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        similarity = float(
            torch.nn.functional.cosine_similarity(
                embeddings[0].unsqueeze(0),
                embeddings[1].unsqueeze(0),
            ).item()
        )
        relevance = _linear_map(similarity, low=0.25, high=0.75)

        try:
            clarity_prob = self._acceptable_probability(question)
        except Exception:
            logger.warning("CoLA clarity inference failed; using heuristic.", exc_info=True)
            clarity_prob = _heuristic_clarity_score(question)

        clarity = _linear_map(clarity_prob, low=0.35, high=0.92)

        result_word = "correctly" if user_was_correct else "incorrectly"
        rationale = (
            f"NLP evaluation: semantic similarity to source {similarity:.2f} "
            f"(relevance {relevance}/5); clarity acceptability {clarity_prob:.2f} "
            f"(clarity {clarity}/5). Learner answered {result_word}."
        )

        return {
            "relevance": relevance,
            "clarity": clarity,
            "rationale": rationale,
            "similarity": round(similarity, 4),
            "clarity_probability": round(clarity_prob, 4),
            "evaluator": "nlp",
        }

    async def score_async(
        self,
        educational_text: str,
        question_text: str,
        user_was_correct: bool,
    ) -> dict:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.score_sync,
            educational_text,
            question_text,
            user_was_correct,
        )


def get_quality_models() -> NLPQualityModels:
    return NLPQualityModels.get()
