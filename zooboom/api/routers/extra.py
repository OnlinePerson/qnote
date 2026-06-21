import asyncio
import json
from fastapi import APIRouter, Request

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.db import get_connection

router = APIRouter(tags=["extra"])


def _get_inventory(user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT i.quantity, s.item_id, s.name, s.description,
                      s.category, s.icon, s.effect, s.price
               FROM inventory i
               JOIN shop_items s ON i.item_id = s.item_id
               WHERE i.user_id = ?
               ORDER BY s.category, s.name""",
            (user_id,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["effect"] = json.loads(d["effect"]) if d["effect"] else {}
            except (json.JSONDecodeError, TypeError):
                d["effect"] = {}
            result.append(d)
        return result
    finally:
        conn.close()


def _get_leaderboard() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT u.user_id, u.username, u.full_name, u.total_score, u.level,
                      (SELECT COUNT(*) FROM animals a
                       WHERE a.owner_id = u.user_id AND a.is_alive = 1) AS animal_count
               FROM users u
               ORDER BY u.total_score DESC, u.level DESC
               LIMIT 50""",
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _get_zoo(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM zoos WHERE owner_id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        for field in ("sections", "decorations"):
            try:
                d[field] = json.loads(d[field]) if d.get(field) else ({} if field == "sections" else [])
            except (json.JSONDecodeError, TypeError):
                d[field] = {} if field == "sections" else []
        return d
    finally:
        conn.close()


@router.get("/inventory")
async def get_inventory(request: Request):
    user_id = request.state.user["id"]
    return await asyncio.to_thread(_get_inventory, user_id)


@router.get("/leaderboard")
async def get_leaderboard():
    return await asyncio.to_thread(_get_leaderboard)


@router.get("/zoo")
async def get_zoo(request: Request):
    user_id = request.state.user["id"]
    result = await asyncio.to_thread(_get_zoo, user_id)
    if not result:
        return {"zoo_id": None, "zoo_name": "باغ وحش من", "level": 1,
                "reputation": 0, "daily_income": 0, "is_open": False,
                "sections": {}, "decorations": []}
    return result
