import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import ChatTypeFilter
from aiogram.types import Message

from database.db import get_connection
from database.animals_data import ANIMALS

logger = logging.getLogger(__name__)
router = Router()

# فقط در گروه‌ها و سوپرگروه‌ها
router.message.filter(ChatTypeFilter(chat_type=["group", "supergroup"]))

COOLDOWN_SECONDS = 60
SOUND_REWARD_COINS = 5


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def get_user_animal(user_id: int):
    """آخرین حیوان زنده کاربر رو برمی‌گردونه"""
    conn = get_connection()
    animal = conn.execute(
        """SELECT a.*, u.coins FROM animals a
           JOIN users u ON a.owner_id = u.user_id
           WHERE a.owner_id = ? AND a.is_alive = 1
           ORDER BY a.animal_id
           LIMIT 1""",
        (user_id,),
    ).fetchone()
    conn.close()
    return animal


def check_cooldown(user_id: int, group_id: int) -> bool:
    """True اگه می‌تونه صدا بده (cooldown تموم شده)"""
    conn = get_connection()
    row = conn.execute(
        "SELECT last_used FROM group_cooldowns WHERE user_id = ? AND group_id = ?",
        (user_id, group_id),
    ).fetchone()
    conn.close()

    if not row:
        return True

    last_used = datetime.fromisoformat(row["last_used"])
    return datetime.utcnow() - last_used >= timedelta(seconds=COOLDOWN_SECONDS)


def update_cooldown(user_id: int, group_id: int) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO group_cooldowns (user_id, group_id, last_used)
           VALUES (?, ?, datetime('now'))
           ON CONFLICT(user_id, group_id)
           DO UPDATE SET last_used = datetime('now')""",
        (user_id, group_id),
    )
    conn.commit()
    conn.close()


def award_coins_and_score(user_id: int, coins: int, group_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET coins = coins + ?, total_score = total_score + ?, last_active = datetime('now') WHERE user_id = ?",
        (coins, coins, user_id),
    )
    conn.execute(
        """INSERT INTO group_scores (user_id, group_id, score)
           VALUES (?, ?, ?)""",
        (user_id, group_id, coins),
    )
    conn.commit()
    conn.close()


def find_matching_animal_sound(text: str, animal):
    """چک می‌کنه آیا متن شامل صدای حیوانه"""
    species_key = animal["species"]
    species_data = ANIMALS.get(species_key)
    if not species_data:
        return None

    text_lower = text.lower().strip()
    for keyword in species_data.get("sound_keywords", []):
        if keyword in text_lower or keyword in text:
            return species_data
    return None


# ─────────────────────────────────────────────
#  Handler: صدای حیوان در گروه
# ─────────────────────────────────────────────

@router.message(F.text)
async def handle_group_sound(message: Message) -> None:
    if not message.text:
        return

    user_id = message.from_user.id
    group_id = message.chat.id

    # فقط کاربرهای ثبت‌نام‌شده
    animal = get_user_animal(user_id)
    if not animal:
        return

    # چک صدا
    species_data = find_matching_animal_sound(message.text, animal)
    if not species_data:
        return

    # چک cooldown
    if not check_cooldown(user_id, group_id):
        # بدون پیام برای جلوگیری از spam
        return

    # بروزرسانی cooldown
    update_cooldown(user_id, group_id)

    # جایزه سکه
    award_coins_and_score(user_id, SOUND_REWARD_COINS, group_id)

    # پاسخ ربات
    emoji = species_data.get("emoji", "🐾")
    sound = species_data.get("sound", "...")
    nickname = animal["nickname"]

    await message.reply(
        f"{emoji} **{nickname}** گفت:\n"
        f"«{sound}»\n\n"
        f"💰 +{SOUND_REWARD_COINS} سکه برای {message.from_user.first_name}!",
        parse_mode="Markdown",
    )
