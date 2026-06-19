import asyncio
import json
from fastapi import APIRouter, Request, HTTPException

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.db import get_connection

router = APIRouter(tags=["animals"])

FEED_COST = 10
PLAY_COST = 5
MEDICINE_COST = 50
CLEAN_COST = 15


def _row_to_dict(row) -> dict:
    d = dict(row)
    for field in ("accessories", "tricks"):
        try:
            d[field] = json.loads(d[field]) if d.get(field) else []
        except (json.JSONDecodeError, TypeError):
            d[field] = []
    return d


def _get_animal(animal_id: int, owner_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM animals WHERE animal_id = ? AND owner_id = ? AND is_alive = 1",
            (animal_id, owner_id),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def _list_animals(owner_id: int):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM animals WHERE owner_id = ? AND is_alive = 1 ORDER BY animal_id",
            (owner_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def _apply_action(animal_id: int, owner_id: int, cost: int, updates: dict) -> dict:
    conn = get_connection()
    try:
        user_row = conn.execute(
            "SELECT coins FROM users WHERE user_id = ?", (owner_id,)
        ).fetchone()
        if not user_row:
            raise ValueError("کاربر یافت نشد.")
        if user_row["coins"] < cost:
            raise ValueError("سکه کافی ندارید.")

        animal = conn.execute(
            "SELECT * FROM animals WHERE animal_id = ? AND owner_id = ? AND is_alive = 1",
            (animal_id, owner_id),
        ).fetchone()
        if not animal:
            raise LookupError("حیوان یافت نشد.")

        set_clauses = []
        values = []
        for col, val in updates.items():
            if isinstance(val, str) and val.startswith("+"):
                increment = int(val[1:])
                current = animal[col] if animal[col] is not None else 0
                new_val = min(100, current + increment)
                set_clauses.append(f"{col} = ?")
                values.append(new_val)
            else:
                set_clauses.append(f"{col} = ?")
                values.append(val)

        values += [animal_id, owner_id]
        conn.execute(
            f"UPDATE animals SET {', '.join(set_clauses)} WHERE animal_id = ? AND owner_id = ?",
            values,
        )
        if cost > 0:
            conn.execute(
                "UPDATE users SET coins = coins - ? WHERE user_id = ?",
                (cost, owner_id),
            )
        conn.commit()

        updated = conn.execute(
            "SELECT * FROM animals WHERE animal_id = ?", (animal_id,)
        ).fetchone()
        return _row_to_dict(updated)
    finally:
        conn.close()


@router.get("/animals")
async def list_animals(request: Request):
    user_id = request.state.user["id"]
    return await asyncio.to_thread(_list_animals, user_id)


@router.get("/animals/{animal_id}")
async def get_animal(animal_id: int, request: Request):
    user_id = request.state.user["id"]
    result = await asyncio.to_thread(_get_animal, animal_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="حیوان یافت نشد.")
    return result


@router.post("/animals/{animal_id}/feed")
async def feed_animal(animal_id: int, request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(
            _apply_action,
            animal_id,
            user_id,
            FEED_COST,
            {"hunger": "+30", "last_fed": "datetime('now')"},
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "حیوانت با موفقیت تغذیه شد.", "animal": result}


@router.post("/animals/{animal_id}/play")
async def play_animal(animal_id: int, request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(
            _apply_action,
            animal_id,
            user_id,
            PLAY_COST,
            {"happiness": "+25", "last_played": "datetime('now')"},
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "باهاش بازی کردی! خوشحال شد.", "animal": result}


@router.post("/animals/{animal_id}/medicine")
async def give_medicine(animal_id: int, request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(
            _apply_action,
            animal_id,
            user_id,
            MEDICINE_COST,
            {"health": "+40", "is_sick": 0},
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "دارو داده شد. حیوانت حالش بهتره!", "animal": result}


@router.post("/animals/{animal_id}/clean")
async def clean_animal(animal_id: int, request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(
            _apply_action,
            animal_id,
            user_id,
            CLEAN_COST,
            {"cleanliness": "+50"},
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "حیوانت تمیز شد!", "animal": result}
