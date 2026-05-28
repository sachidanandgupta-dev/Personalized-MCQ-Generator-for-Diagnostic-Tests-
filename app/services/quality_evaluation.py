import logging

from app.services.nlp_quality_models import get_quality_models
from app.services.question_store import get_question, save_quality_metric

logger = logging.getLogger(__name__)


async def evaluate_question_quality(
    question_id: str,
    user_id: str,
    user_was_correct: bool,
) -> None:
    """
    Background task: score relevance & clarity with local NLP models, then persist.

    Inference runs in a dedicated thread pool (see ``nlp_quality_models``) so the
    asyncio event loop and main API workers stay responsive.
    """
    stored = await get_question(question_id)
    if not stored:
        logger.warning("evaluate_question_quality: unknown question_id=%s", question_id)
        return

    models = get_quality_models()
    if not models.is_ready:
        logger.error("NLP models not loaded; skipping evaluation for %s", question_id)
        return

    educational_text = stored["educational_text"]
    question_text = stored["question"]

    try:
        scores = await models.score_async(
            educational_text,
            question_text,
            user_was_correct,
        )
        await save_quality_metric(
            {
                "question_id": question_id,
                "user_id": user_id,
                "question_text": question_text,
                "user_was_correct": user_was_correct,
                "relevance": scores["relevance"],
                "clarity": scores["clarity"],
                "rationale": scores["rationale"],
                "evaluator": scores.get("evaluator", "nlp"),
                "similarity": scores.get("similarity"),
                "clarity_probability": scores.get("clarity_probability"),
            }
        )
        logger.info(
            "Quality evaluation stored for %s: relevance=%s clarity=%s (nlp)",
            question_id,
            scores["relevance"],
            scores["clarity"],
        )
    except Exception:
        logger.exception(
            "evaluate_question_quality failed for question_id=%s", question_id
        )
