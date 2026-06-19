import asyncio
import json
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.db import get_connection

router = APIRouter(tags=["shop"])


def _list_shop_items() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT item_id, name, description, category, species, price, effect, icon FROM shop_items ORDER BY category, price"
        ).fetchall()
        items = []
        for row in rows:
            d = dict(row)
            try:
                d["effect"] = json.loads(d["effect"]) if d["effect"] else {}
            except (json.JSONDecodeError, TypeError):
                d["effect"] = {}
            items.append(d)
        return items
    finally:
        conn.close()


def _buy_item(user_id: int, item_id: int) -> dict:
    conn = get_connection()
    try:
        item = conn.execute(
            "SELECT * FROM shop_items WHERE item_id = ?", (item_id,)
        ).fetchone()
        if not item:
            raise LookupError("آیتم مورد نظر یافت نشد.")

        user = conn.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not user:
            raise LookupError("کاربر یافت نشد.")
        if user["coins"] < item["price"]:
            raise ValueError(f"سکه کافی ندارید. قیمت: {item['price']} سکه.")

        conn.execute(
            "UPDATE users SET coins = coins - ? WHERE user_id = ?",
            (item["price"], user_id),
        )

        existing = conn.execute(
            "SELECT id, quantity FROM inventory WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE inventory SET quantity = quantity + 1 WHERE id = ?",
                (existing["id"],),
            )
        else:
            conn.execute(
                "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, 1)",
                (user_id, item_id),
            )

        conn.commit()

        new_coins = conn.execute(
            "SELECT coins FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()["coins"]

        return {
            "item_id": item["item_id"],
            "item_name": item["name"],
            "price_paid": item["price"],
            "remaining_coins": new_coins,
        }
    finally:
        conn.close()


class BuyPayload(BaseModel):
    item_id: int


@router.get("/shop")
async def list_shop():
    return await asyncio.to_thread(_list_shop_items)


@router.post("/shop/buy")
async def buy_item(payload: BuyPayload, request: Request):
    user_id = request.state.user["id"]
    try:
        result = await asyncio.to_thread(_buy_item, user_id, payload.item_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": f"خرید موفق! «{result['item_name']}» به انبارت اضافه شد.", **result}
