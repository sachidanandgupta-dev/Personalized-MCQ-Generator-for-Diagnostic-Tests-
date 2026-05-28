from datetime import datetime, timezone

from app.database import get_database
from app.schemas import McqItem


async def register_question(
    question_id: str,
    user_id: str,
    educational_text: str,
    question: McqItem,
) -> None:
    db = get_database()
    await db.questions.insert_one(
        {
            "question_id": question_id,
            "user_id": user_id,
            "educational_text": educational_text,
            "question": question.question,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def get_question(question_id: str) -> dict | None:
    db = get_database()
    return await db.questions.find_one({"question_id": question_id}, {"_id": 0})


async def save_quality_metric(metric: dict) -> None:
    db = get_database()
    await db.analytics.insert_one(
        {
            **metric,
            "created_at": datetime.now(timezone.utc),
        }
    )


async def get_insight_analytics(user_id: str | None = None) -> dict:
    db = get_database()
    match_filter = {"user_id": user_id} if user_id else {}

    total = await db.analytics.count_documents(match_filter)
    if total == 0:
        return {
            "total_evaluations": 0,
            "avg_relevance": 0.0,
            "avg_clarity": 0.0,
            "avg_overall": 0.0,
            "recent_evaluations": [],
        }

    pipeline = [
        {"$match": match_filter},
        {
            "$group": {
                "_id": None,
                "avg_relevance": {"$avg": "$relevance"},
                "avg_clarity": {"$avg": "$clarity"},
            }
        },
    ]
    agg = await db.analytics.aggregate(pipeline).to_list(length=1)
    averages = agg[0] if agg else {"avg_relevance": 0.0, "avg_clarity": 0.0}
    avg_relevance = round(averages["avg_relevance"], 2)
    avg_clarity = round(averages["avg_clarity"], 2)

    recent_cursor = db.analytics.find(match_filter).sort("created_at", -1).limit(5)
    recent_docs = await recent_cursor.to_list(length=5)

    return {
        "total_evaluations": total,
        "avg_relevance": avg_relevance,
        "avg_clarity": avg_clarity,
        "avg_overall": round((avg_relevance + avg_clarity) / 2, 2),
        "recent_evaluations": [
            {
                "question_id": doc["question_id"],
                "relevance": doc["relevance"],
                "clarity": doc["clarity"],
                "user_was_correct": doc["user_was_correct"],
                "question_preview": doc["question_text"][:80]
                + ("…" if len(doc["question_text"]) > 80 else ""),
            }
            for doc in recent_docs
        ],
    }
