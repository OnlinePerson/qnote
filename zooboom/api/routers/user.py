import asyncio
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.db import get_connection

router = APIRouter(tags=["user"])


def _get_user(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, username, full_name, coins, total_score, level FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        count = conn.execute(
            "SELECT COUNT(*) FROM animals WHERE owner_id = ? AND is_alive = 1",
            (user_id,),
        ).fetchone()[0]
        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "full_name": row["full_name"],
            "coins": row["coins"],
            "total_score": row["total_score"],
            "level": row["level"],
            "animals_count": count,
        }
    finally:
        conn.close()


def _register_user(user_id: int, username: str, full_name: str) -> dict:
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO users (user_id, username, full_name)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   username = excluded.username,
                   full_name = excluded.full_name,
                   last_active = datetime('now')""",
            (user_id, username, full_name),
        )
        conn.commit()
        return _get_user(user_id)
    finally:
        conn.close()


@router.get("/user")
async def get_user(request: Request):
    telegram_user = request.state.user
    user_id = telegram_user["id"]
    result = await asyncio.to_thread(_get_user, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد. ابتدا ثبت‌نام کنید.")
    return result


class RegisterPayload(BaseModel):
    user_id: int
    username: str = ""
    full_name: str = ""


@router.post("/user/register")
async def register_user(payload: RegisterPayload):
    result = await asyncio.to_thread(
        _register_user, payload.user_id, payload.username, payload.full_name
    )
    return result
