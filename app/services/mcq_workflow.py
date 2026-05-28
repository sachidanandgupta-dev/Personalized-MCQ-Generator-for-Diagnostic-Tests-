import asyncio
import uuid

from app.config import Settings
from app.schemas import GenerateMcqResponse, McqItemWithId
from app.services.adaptive_learning import get_current_difficulty
from app.services.gemini_mcq import generate_mcqs
from app.services.question_store import register_question


async def generate_mcqs_for_user(
    user_id: str,
    educational_text: str,
    settings: Settings,
) -> GenerateMcqResponse:
    difficulty = await get_current_difficulty(user_id)
    questions = await asyncio.to_thread(
        generate_mcqs,
        educational_text,
        difficulty,
        settings,
    )

    questions_with_ids: list[McqItemWithId] = []
    for item in questions:
        question_id = str(uuid.uuid4())
        await register_question(
            question_id=question_id,
            user_id=user_id,
            educational_text=educational_text,
            question=item,
        )
        questions_with_ids.append(
            McqItemWithId(question_id=question_id, **item.model_dump())
        )

    return GenerateMcqResponse(
        user_id=user_id,
        difficulty=difficulty,
        questions=questions_with_ids,
    )
