import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.database import get_database
from app.services.adaptive_learning import ensure_user


async def register_user(username: str, password: str) -> dict:
    db = get_database()
    normalized = username.strip().lower()

    existing = await db.accounts.find_one({"username": normalized})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user_id = str(uuid.uuid4())
    await db.accounts.insert_one(
        {
            "user_id": user_id,
            "username": normalized,
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc),
        }
    )
    await ensure_user(user_id)

    token = create_access_token(user_id, normalized)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": normalized,
    }


async def login_user(username: str, password: str) -> dict:
    db = get_database()
    normalized = username.strip().lower()

    account = await db.accounts.find_one({"username": normalized})
    if not account or not verify_password(password, account["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = account["user_id"]
    await ensure_user(user_id)

    token = create_access_token(user_id, normalized)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": normalized,
    }
