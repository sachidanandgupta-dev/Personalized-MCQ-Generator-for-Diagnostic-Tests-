from app.database import get_database

DEFAULT_DIFFICULTY = 5
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 10
CORRECT_STREAK_TO_INCREASE = 3
INCORRECT_STREAK_TO_DECREASE = 2


def _current_streak(history: list[dict]) -> tuple[bool | None, int]:
    if not history:
        return None, 0

    streak_is_correct = history[-1]["is_correct"]
    streak_len = 0
    for entry in reversed(history):
        if entry["is_correct"] == streak_is_correct:
            streak_len += 1
        else:
            break
    return streak_is_correct, streak_len


def _calculate_difficulty_from_history(history: list[dict], difficulty: int) -> int:
    if not history:
        return difficulty

    streak_is_correct, streak_len = _current_streak(history)

    if streak_is_correct and streak_len >= CORRECT_STREAK_TO_INCREASE:
        return min(MAX_DIFFICULTY, difficulty + 1)
    if streak_is_correct is False and streak_len >= INCORRECT_STREAK_TO_DECREASE:
        return max(MIN_DIFFICULTY, difficulty - 1)
    return difficulty


async def ensure_user(user_id: str) -> dict:
    db = get_database()
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "difficulty": DEFAULT_DIFFICULTY,
                "history": [],
            }
        },
        upsert=True,
    )
    user = await db.users.find_one({"user_id": user_id})
    if user is None:
        raise RuntimeError(f"Failed to load user profile for {user_id}")
    return user


async def get_current_difficulty(user_id: str) -> int:
    user = await ensure_user(user_id)
    return user["difficulty"]


async def calculate_next_difficulty(user_id: str) -> int:
    """Adjust and persist the user's target difficulty (1-10) from their answer streak."""
    db = get_database()
    user = await ensure_user(user_id)
    history = user.get("history", [])
    difficulty = _calculate_difficulty_from_history(history, user["difficulty"])

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"difficulty": difficulty}},
    )
    return difficulty


async def record_answer(user_id: str, question_id: str, is_correct: bool) -> int:
    db = get_database()
    user = await ensure_user(user_id)
    history = [*user.get("history", []), {"question_id": question_id, "is_correct": is_correct}]
    difficulty = _calculate_difficulty_from_history(history, user["difficulty"])

    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"difficulty": difficulty, "history": history}},
    )
    return difficulty
