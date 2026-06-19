import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database.db import get_connection
from database.animals_data import ANIMALS, RARITY_COLORS
from bot.config import OWNER_ID

logger = logging.getLogger(__name__)
router = Router()


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def get_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 برگشت به منو", callback_data="back_main")]
        ]
    )


def health_bar(value: int, max_val: int = 100, length: int = 10) -> str:
    """یه بار پیشرفت ساده"""
    filled = round((value / max_val) * length)
    empty = length - filled
    return "█" * filled + "░" * empty


def animal_status_icon(value: int) -> str:
    if value >= 70:
        return "🟢"
    elif value >= 40:
        return "🟡"
    else:
        return "🔴"


# ─────────────────────────────────────────────
#  Callback: profile
# ─────────────────────────────────────────────

@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("ابتدا ثبت‌نام کن! /start", show_alert=True)
        return

    conn = get_connection()
    animal_count = conn.execute(
        "SELECT COUNT(*) FROM animals WHERE owner_id = ? AND is_alive = 1",
        (callback.from_user.id,),
    ).fetchone()[0]
    conn.close()

    admin_badge = " 👑 ادمین" if callback.from_user.id == OWNER_ID else ""
    text = (
        f"👤 **پروفایل من**{admin_badge}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📛 نام: {user['full_name']}\n"
        f"🌍 کشور: {user['country']}\n"
        f"🎂 سن: {user['age']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⭐ سطح: {user['level']}\n"
        f"🏆 امتیاز کل: {user['total_score']:,}\n"
        f"💰 سکه: {user['coins']:,}\n"
        f"🐾 تعداد حیوانات: {animal_count}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📅 عضو از: {str(user['registered_at'])[:10]}\n"
        f"⏰ آخرین فعالیت: {str(user['last_active'])[:10]}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    await callback.answer()


# ─────────────────────────────────────────────
#  Callback: help_menu
# ─────────────────────────────────────────────

@router.callback_query(F.data == "help_menu")
async def cb_help(callback: CallbackQuery) -> None:
    text = (
        "📖 **راهنمای ZooBoom**\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🐾 **مراقبت از حیوان:**\n"
        "• `/feed <id>` — غذا دادن به حیوان (۳۰ سکه)\n"
        "• `/myanimals` — لیست حیوانات من\n"
        "• `/status` — وضعیت حیوانات\n\n"
        "🏪 **خرید و فروش:**\n"
        "• برای خرید آیتم به پت‌شاپ برو\n"
        "• برای خرید سکه از گزینه 💰 استفاده کن\n\n"
        "🦁 **باغ وحش:**\n"
        "• حیواناتت رو در باغ وحش نمایش بده\n"
        "• با دیگران به رقابت بپرداز\n\n"
        "🌿 **مزرعه:**\n"
        "• مزرعه‌ات رو از طریق دکمه مزرعه مدیریت کن\n\n"
        "🔊 **گروه‌ها:**\n"
        "• صدای حیوانت رو در گروه بنویس\n"
        "  تا ۵ سکه جایزه بگیری! (هر ۶۰ ثانیه)\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 برای لغو هر عملیاتی: /cancel"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_button(),
    )
    await callback.answer()


# ─────────────────────────────────────────────
#  Callback: buy_coins
# ─────────────────────────────────────────────

@router.callback_query(F.data == "buy_coins")
async def cb_buy_coins(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("ابتدا ثبت‌نام کن! /start", show_alert=True)
        return

    text = (
        "💰 **خرید سکه**\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "📦 **بسته‌های موجود:**\n\n"
        "🥉 ۱٬۰۰۰ سکه ← ۵٬۰۰۰ تومان\n"
        "🥈 ۵٬۰۰۰ سکه ← ۲۰٬۰۰۰ تومان\n"
        "🥇 ۱۰٬۰۰۰ سکه ← ۳۵٬۰۰۰ تومان\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "📋 **نحوه خرید:**\n\n"
        "1️⃣ مبلغ رو به کارت زیر واریز کن\n"
        "2️⃣ رسید پرداخت رو عکس بگیر\n"
        "3️⃣ عکس رسید + مقدار خریداری شده رو\n"
        "   برای پشتیبانی ارسال کن\n\n"
        "💳 **شماره کارت:**\n"
        "`6037-XXXX-XXXX-XXXX`\n"
        "به نام: صاحب کارت\n\n"
        "⏰ سکه‌ها ظرف ۳۰ دقیقه اضافه می‌شن\n"
        "━━━━━━━━━━━━━━━━\n"
        f"💰 سکه فعلی تو: {user['coins']:,}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📤 ارسال رسید", callback_data="send_receipt"
                    )
                ],
                [InlineKeyboardButton(text="🔙 برگشت", callback_data="back_main")],
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "send_receipt")
async def cb_send_receipt(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "📤 رسیدت رو اینجا بفرست!\n\n"
        "لطفاً عکس رسید پرداخت رو همراه با توضیح مقدار سکه خریداری شده ارسال کن.\n"
        "مثلاً: رسید ۱۰۰۰ سکه"
    )
    await callback.answer()


# ─────────────────────────────────────────────
#  /myanimals command
# ─────────────────────────────────────────────

@router.message(Command("myanimals"))
async def cmd_my_animals(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ ابتدا ثبت‌نام کن! /start")
        return

    conn = get_connection()
    animals = conn.execute(
        """SELECT * FROM animals
           WHERE owner_id = ? AND is_alive = 1
           ORDER BY level DESC, animal_id""",
        (message.from_user.id,),
    ).fetchall()
    conn.close()

    if not animals:
        await message.answer(
            "🐾 هنوز هیچ حیوانی نداری!\n"
            "با /start ثبت‌نام کن و اولین حیوانت رو بگیر."
        )
        return

    lines = [f"🐾 **حیوانات من** ({len(animals)} عدد)\n━━━━━━━━━━━━━━━━\n"]
    for a in animals:
        species_data = ANIMALS.get(a["species"], {})
        emoji = species_data.get("emoji", "🐾")
        rarity_icon = "⚪"  # default
        breed_data = species_data.get("breeds", {}).get(a["breed"], {})
        if breed_data:
            rarity_icon = RARITY_COLORS.get(breed_data.get("rarity", "common"), "⚪")

        sick_tag = " 🤒 بیمار" if a["is_sick"] else ""
        lines.append(
            f"{emoji} **{a['nickname']}** (ID: {a['animal_id']}){sick_tag}\n"
            f"  {rarity_icon} نژاد: {a['breed']} | سطح: {a['level']}\n"
            f"  🍖 {animal_status_icon(a['hunger'])} گرسنگی: {a['hunger']}/100\n"
            f"  ❤️ {animal_status_icon(a['happiness'])} شادی: {a['happiness']}/100\n"
            f"  💊 {animal_status_icon(a['health'])} سلامت: {a['health']}/100\n"
        )

    text = "\n".join(lines)
    # تقسیم پیام اگه خیلی طولانی بود
    if len(text) > 4000:
        text = text[:4000] + "\n..."

    await message.answer(
        text,
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  /feed <animal_id>
# ─────────────────────────────────────────────

@router.message(Command("feed"))
async def cmd_feed(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ ابتدا ثبت‌نام کن! /start")
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer(
            "⚠️ استفاده صحیح:\n"
            "`/feed <id_حیوان>`\n\n"
            "برای دیدن ID حیواناتت: /myanimals",
            parse_mode="Markdown",
        )
        return

    animal_id = int(args[1])

    conn = get_connection()
    animal = conn.execute(
        "SELECT * FROM animals WHERE animal_id = ? AND owner_id = ? AND is_alive = 1",
        (animal_id, message.from_user.id),
    ).fetchone()

    if not animal:
        conn.close()
        await message.answer(
            "❌ حیوانی با این ID پیدا نشد!\n"
            "از /myanimals لیست حیواناتت رو ببین."
        )
        return

    if user["coins"] < 30:
        conn.close()
        await message.answer(
            f"💰 سکه کافی نداری!\n"
            f"برای غذا دادن ۳۰ سکه لازمه.\n"
            f"سکه فعلیت: {user['coins']:,}"
        )
        return

    old_hunger = animal["hunger"]
    new_hunger = min(100, old_hunger + 40)

    conn.execute(
        "UPDATE animals SET hunger = ?, last_fed = datetime('now') WHERE animal_id = ?",
        (new_hunger, animal_id),
    )
    conn.execute(
        "UPDATE users SET coins = coins - 30, last_active = datetime('now') WHERE user_id = ?",
        (message.from_user.id,),
    )
    conn.commit()
    conn.close()

    species_data = ANIMALS.get(animal["species"], {})
    emoji = species_data.get("emoji", "🐾")

    await message.answer(
        f"{emoji} **{animal['nickname']}** غذا خورد!\n\n"
        f"🍖 گرسنگی: {old_hunger} ← {new_hunger}\n"
        f"{health_bar(new_hunger)}\n\n"
        f"💰 ۳۰ سکه از حسابت کم شد.\n"
        f"باقیمانده: {user['coins'] - 30:,} سکه",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  /status command
# ─────────────────────────────────────────────

@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ ابتدا ثبت‌نام کن! /start")
        return

    conn = get_connection()
    animals = conn.execute(
        """SELECT * FROM animals
           WHERE owner_id = ? AND is_alive = 1
           ORDER BY animal_id
           LIMIT 5""",
        (message.from_user.id,),
    ).fetchall()
    total_count = conn.execute(
        "SELECT COUNT(*) FROM animals WHERE owner_id = ? AND is_alive = 1",
        (message.from_user.id,),
    ).fetchone()[0]
    conn.close()

    if not animals:
        await message.answer(
            "🐾 هنوز هیچ حیوانی نداری!\n"
            "با /start ثبت‌نام کن و اولین حیوانت رو بگیر."
        )
        return

    lines = [f"📊 **وضعیت حیوانات**\n━━━━━━━━━━━━━━━━\n"]
    for a in animals:
        species_data = ANIMALS.get(a["species"], {})
        emoji = species_data.get("emoji", "🐾")
        sick_tag = " 🤒" if a["is_sick"] else ""

        lines.append(
            f"{emoji} **{a['nickname']}**{sick_tag} (سطح {a['level']})\n"
            f"🍖 گرسنگی:  {health_bar(a['hunger'])} {a['hunger']}%\n"
            f"😊 شادی:    {health_bar(a['happiness'])} {a['happiness']}%\n"
            f"💊 سلامت:  {health_bar(a['health'])} {a['health']}%\n"
            f"🛁 تمیزی:  {health_bar(a['cleanliness'])} {a['cleanliness']}%\n"
        )

    if total_count > 5:
        lines.append(f"\n...و {total_count - 5} حیوان دیگه\nبرای دیدن همه: /myanimals")

    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  Admin panel callback
# ─────────────────────────────────────────────

@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: CallbackQuery) -> None:
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⛔ دسترسی ندارید!", show_alert=True)
        return

    conn = get_connection()
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    animal_count = conn.execute(
        "SELECT COUNT(*) FROM animals WHERE is_alive = 1"
    ).fetchone()[0]
    pending_requests = conn.execute(
        "SELECT COUNT(*) FROM coin_requests WHERE status = 'pending'"
    ).fetchone()[0]
    conn.close()

    text = (
        "⚙️ **پنل مدیریت**\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"👥 کاربران: {user_count:,}\n"
        f"🐾 حیوانات زنده: {animal_count:,}\n"
        f"💰 درخواست‌های خرید در انتظار: {pending_requests}\n"
        "━━━━━━━━━━━━━━━━\n"
        "دستورات ادمین:\n"
        "/addcoins <user_id> <amount>\n"
        "/broadcast <message>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 برگشت", callback_data="back_main")]
            ]
        ),
    )
    await callback.answer()
