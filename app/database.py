from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo(uri: str, db_name: str) -> None:
    global _client, _db
    _client = AsyncIOMotorClient(uri)
    _db = _client[db_name]

    await _db.accounts.create_index("username", unique=True)
    await _db.accounts.create_index("user_id", unique=True)
    await _db.users.create_index("user_id", unique=True)
    await _db.questions.create_index("question_id", unique=True)
    await _db.analytics.create_index("question_id")
    await _db.analytics.create_index([("user_id", 1), ("created_at", -1)])


async def close_mongo_connection() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB is not connected.")
    return _db
