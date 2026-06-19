import asyncio
import json
from datetime import date
from fastapi import APIRouter, Request, HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.db import get_connection

router = APIRouter(tags=["farm"])

DAILY_BONUS_COINS = 100


def _get_farm(user_id: int) -> dict:
    conn = get_connection()
    try:
        animals = conn.execute(
            """SELECT animal_id, nickname, species, level, hunger, happiness, health, cleanliness, is_sick
               FROM animals WHERE owner_id = ? AND is_alive = 1""",
            (user_id,),
        ).fetchall()

        weather_row = conn.execute(
            "SELECT weather_type, description, effect FROM weather ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        weather = None
        if weather_row:
            try:
                effect = json.loads(weather_row["effect"]) if weather_row["effect"] else {}
            except (json.JSONDecodeError, TypeError):
                effect = {}
            weather = {
                "type": weather_row["weather_type"],
                "description": weather_row["description"],
                "effect": effect,
            }

        user_row = conn.execute(
            "SELECT last_active FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        today = date.today().isoformat()
        daily_claimed = False
        if user_row and user_row["last_active"]:
            last_date = user_row["last_active"][:10]
            daily_claimed = last_date == today

        return {
            "animals": [dict(a) for a in animals],
            "weather": weather,
            "daily_bonus": {
                "amount": DAILY_BONUS_COINS,
                "claimed": daily_claimed,
            },
        }
    finally:
        conn.close()


def _claim_daily_bonus(user_id: int) -> dict:
    conn = get_connection()
    try:
        user_row = conn.execute(
            "SELECT coins, last_active FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not user_row:
            raise LookupError("کاربر یافت نشد.")

        today = date.today().isoformat()
        last_date = (user_row["last_active"] or "")[:10]
        if last_date == today:
            raise ValueError("جایزه روزانه قبلاً دریافت شده. فردا برگرد!")

        conn.execute(
            "UPDATE users SET coins = coins + ?, last_active = datetime('now') WHERE user_id = ?",
            (DAILY_BONUS_COINS, user_id),
        )
        conn.commit()

        new_coins = conn.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()["coins"]

        return {
            "bonus_coins": DAILY_BONUS_COINS,
            "total_coins": new_coins,
        }
    finally:
        conn.close()


@router.get("/farm")
async def get_farm(request: Request):
    user_id = request.state.user["id"]
    return await asyncio.to_thread(_get_farm, user_id)


@router.post("/farm/daily-bonus")
async def claim_daily_bonus(request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(_claim_daily_bonus, user_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"جایزه روزانه دریافت شد! {result['bonus_coins']} سکه به حسابت اضافه شد.", **result}
