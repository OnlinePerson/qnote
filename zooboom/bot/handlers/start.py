import random
import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    WebAppInfo,
)

from database.db import get_connection
from database.animals_data import ANIMALS, COLORS, GENDERS, RARITY_COLORS
from bot.config import OWNER_ID, WEBAPP_URL

logger = logging.getLogger(__name__)
router = Router()

COUNTRIES = [
    "ایران 🇮🇷",
    "افغانستان 🇦🇫",
    "تاجیکستان 🇹🇯",
    "آلمان 🇩🇪",
    "آمریکا 🇺🇸",
    "انگلستان 🇬🇧",
    "امارات 🇦🇪",
    "ترکیه 🇹🇷",
    "کانادا 🇨🇦",
    "کشور دیگه 🌍",
]


# ─────────────────────────────────────────────
#  States
# ─────────────────────────────────────────────

class Registration(StatesGroup):
    AskName = State()
    AskAge = State()
    AskCountry = State()
    ChooseAnimal = State()
    ConfirmAnimal = State()


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """کیبورد منوی اصلی"""
    rows = [
        [
            InlineKeyboardButton(
                text="🌿 مزرعه من",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/farm?uid={user_id}"),
            ),
            InlineKeyboardButton(
                text="🏪 پت‌شاپ",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/shop?uid={user_id}"),
            ),
        ],
        [
            InlineKeyboardButton(text="🦁 باغ وحش", callback_data="zoo_menu"),
            InlineKeyboardButton(text="💰 خرید سکه", callback_data="buy_coins"),
        ],
        [
            InlineKeyboardButton(text="📖 راهنما", callback_data="help_menu"),
            InlineKeyboardButton(text="👤 پروفایل", callback_data="profile"),
        ],
    ]
    if user_id == OWNER_ID:
        rows.append(
            [InlineKeyboardButton(text="⚙️ پنل مدیریت", callback_data="admin_panel")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def animals_keyboard() -> InlineKeyboardMarkup:
    """کیبورد انتخاب حیوان"""
    buttons = []
    row = []
    for key, data in ANIMALS.items():
        row.append(
            InlineKeyboardButton(
                text=f"{data['emoji']} {data['name']}",
                callback_data=f"pick_animal:{key}",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def country_keyboard() -> ReplyKeyboardMarkup:
    """کیبورد انتخاب کشور"""
    rows = []
    for i in range(0, len(COUNTRIES), 2):
        row = [KeyboardButton(text=COUNTRIES[i])]
        if i + 1 < len(COUNTRIES):
            row.append(KeyboardButton(text=COUNTRIES[i + 1]))
        rows.append(row)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def roll_animal(species_key: str) -> dict:
    """جعبه حیوان رو باز می‌کنه و یه نمونه تصادفی می‌ده"""
    animal = ANIMALS[species_key]
    breed_key = random.choice(list(animal["breeds"].keys()))
    breed = animal["breeds"][breed_key]
    color = random.choice(COLORS)
    gender = random.choice(GENDERS)
    rarity = breed.get("rarity", "common")
    rarity_icon = RARITY_COLORS.get(rarity, "⚪")
    return {
        "species": species_key,
        "species_name": animal["name"],
        "species_emoji": animal["emoji"],
        "breed_key": breed_key,
        "breed_name": breed["name"],
        "breed_emoji": breed.get("emoji", animal["emoji"]),
        "color": color,
        "gender": gender,
        "rarity": rarity,
        "rarity_icon": rarity_icon,
        "sound": animal["sound"],
    }


def confirm_animal_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تایید و ثبت‌نام", callback_data="confirm_animal"),
                InlineKeyboardButton(text="🎲 باز کردن دوباره (۵۰ سکه)", callback_data="reroll_animal"),
            ]
        ]
    )


def get_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = get_user(message.from_user.id)

    if user:
        # کاربر قبلاً ثبت‌نام کرده
        await message.answer(
            f"🎉 خوش برگشتی، {user['full_name']}!\n\n"
            f"💰 سکه‌هات: {user['coins']:,}\n"
            f"⭐ سطح: {user['level']}\n\n"
            "از منوی زیر یه گزینه انتخاب کن:",
            reply_markup=main_menu_keyboard(message.from_user.id),
        )
    else:
        # شروع ثبت‌نام
        await message.answer(
            "🐾 سلام به ZooBoom خوش اومدی!\n\n"
            "🦁 یه بازی جذاب برای نگهداری از حیوانات خانگیه.\n"
            "بریم ثبت‌نام کنیم! 🚀\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "📝 اول اسمت رو بنویس (۲ تا ۳۰ کاراکتر):",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(Registration.AskName)


# ─────────────────────────────────────────────
#  /cancel
# ─────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer(
            "❌ عملیات لغو شد.\n"
            "هر وقت خواستی /start بزن تا دوباره شروع کنیم!",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer("هیچ عملیاتی در حال اجرا نیست.")


# ─────────────────────────────────────────────
#  Registration FSM
# ─────────────────────────────────────────────

@router.message(Registration.AskName)
async def ask_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip() if message.text else ""
    if len(name) < 2 or len(name) > 30:
        await message.answer(
            "⚠️ اسم باید بین ۲ تا ۳۰ کاراکتر باشه.\n"
            "دوباره امتحان کن:"
        )
        return

    await state.update_data(full_name=name)
    await message.answer(
        f"✅ اسم خوبیه، {name}! 😊\n\n"
        "📅 حالا سنت رو بنویس (۵ تا ۱۰۰ سال):"
    )
    await state.set_state(Registration.AskAge)


@router.message(Registration.AskAge)
async def ask_age(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("⚠️ لطفاً یه عدد وارد کن:")
        return

    age = int(text)
    if age < 5 or age > 100:
        await message.answer(
            "⚠️ سن باید بین ۵ تا ۱۰۰ سال باشه.\n"
            "دوباره امتحان کن:"
        )
        return

    await state.update_data(age=age)
    await message.answer(
        f"✅ {age} سال! عالیه! 🎉\n\n"
        "🌍 کشورت رو از لیست زیر انتخاب کن:",
        reply_markup=country_keyboard(),
    )
    await state.set_state(Registration.AskCountry)


@router.message(Registration.AskCountry)
async def ask_country(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    # قبول کردن هر گزینه‌ای که در لیست کشورهاست یا کشور دیگه
    if text not in COUNTRIES:
        await message.answer(
            "⚠️ لطفاً یکی از گزینه‌های موجود رو انتخاب کن:",
            reply_markup=country_keyboard(),
        )
        return

    await state.update_data(country=text)
    await message.answer(
        f"✅ {text}! خوشحالم که اینجایی! 🗺️\n\n"
        "🐾 حالا نوبت مهم‌ترین قدمه!\n"
        "اولین حیوانت رو انتخاب کن:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "👇 روی حیوان مورد علاقه‌ات کلیک کن:",
        reply_markup=animals_keyboard(),
    )
    await state.set_state(Registration.ChooseAnimal)


@router.callback_query(Registration.ChooseAnimal, F.data.startswith("pick_animal:"))
async def choose_animal(callback: CallbackQuery, state: FSMContext) -> None:
    species_key = callback.data.split(":")[1]
    if species_key not in ANIMALS:
        await callback.answer("حیوان نامعتبر!", show_alert=True)
        return

    rolled = roll_animal(species_key)
    await state.update_data(chosen_species=species_key, rolled=rolled)

    animal_info = (
        f"🎁 جعبه‌ات باز شد!\n\n"
        f"{rolled['breed_emoji']} **{rolled['breed_name']}** ({rolled['species_name']})\n"
        f"{rolled['rarity_icon']} ندرت: **{rolled['rarity'].upper()}**\n"
        f"🎨 رنگ: {rolled['color']}\n"
        f"{'♂️' if rolled['gender'] == 'نر' else '♀️'} جنسیت: {rolled['gender']}\n"
        f"🔊 صدا: {rolled['sound']}\n\n"
        f"ازش خوشت اومد؟ 😍\n"
        f"یا می‌خوای دوباره امتحان کنی؟ (هر بار ۵۰ سکه)"
    )

    await callback.message.edit_text(
        animal_info,
        reply_markup=confirm_animal_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(Registration.ConfirmAnimal)
    await callback.answer()


@router.callback_query(Registration.ConfirmAnimal, F.data == "reroll_animal")
async def reroll_animal(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    species_key = data.get("chosen_species")

    # بررسی سکه (اگه کاربر از قبل ثبت‌نام شده بود، ولی اینجا هنوز ثبت‌نام نشده)
    # در مرحله ثبت‌نام اول رایگانه، بعدی‌ها ۵۰ سکه
    reroll_count = data.get("reroll_count", 0)
    if reroll_count > 0:
        # چک کردن سکه
        user = get_user(callback.from_user.id)
        if user:
            if user["coins"] < 50:
                await callback.answer("💰 سکه کافی نداری! حداقل ۵۰ سکه لازمه.", show_alert=True)
                return
            # کسر ۵۰ سکه
            conn = get_connection()
            conn.execute(
                "UPDATE users SET coins = coins - 50 WHERE user_id = ?",
                (callback.from_user.id,),
            )
            conn.commit()
            conn.close()

    rolled = roll_animal(species_key)
    await state.update_data(rolled=rolled, reroll_count=reroll_count + 1)

    animal_info = (
        f"🎲 دوباره باز کردی!\n\n"
        f"{rolled['breed_emoji']} **{rolled['breed_name']}** ({rolled['species_name']})\n"
        f"{rolled['rarity_icon']} ندرت: **{rolled['rarity'].upper()}**\n"
        f"🎨 رنگ: {rolled['color']}\n"
        f"{'♂️' if rolled['gender'] == 'نر' else '♀️'} جنسیت: {rolled['gender']}\n"
        f"🔊 صدا: {rolled['sound']}\n\n"
        f"ازش خوشت اومد؟ 😍"
    )

    await callback.message.edit_text(
        animal_info,
        reply_markup=confirm_animal_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer("🎲 دوباره باز شد!")


@router.callback_query(Registration.ConfirmAnimal, F.data == "confirm_animal")
async def confirm_animal(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    rolled = data.get("rolled")
    full_name = data.get("full_name")
    age = data.get("age")
    country = data.get("country")

    if not all([rolled, full_name, age, country]):
        await callback.answer("خطا در اطلاعات! دوباره /start بزن.", show_alert=True)
        await state.clear()
        return

    user_id = callback.from_user.id
    username = callback.from_user.username or ""

    try:
        conn = get_connection()
        c = conn.cursor()

        # درج کاربر
        c.execute(
            """INSERT OR IGNORE INTO users
               (user_id, username, full_name, age, country, coins, level)
               VALUES (?, ?, ?, ?, ?, 100, 1)""",
            (user_id, username, full_name, age, country),
        )

        # درج حیوان
        c.execute(
            """INSERT INTO animals
               (owner_id, species, breed, color, gender, nickname,
                level, xp, hunger, happiness, health, cleanliness)
               VALUES (?, ?, ?, ?, ?, ?, 1, 0, 100, 100, 100, 100)""",
            (
                user_id,
                rolled["species"],
                rolled["breed_key"],
                rolled["color"],
                rolled["gender"],
                rolled["breed_name"],
            ),
        )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطا در ثبت‌نام: {e}")
        await callback.answer("خطا در ثبت‌نام! دوباره امتحان کن.", show_alert=True)
        return

    await state.clear()

    await callback.message.edit_text(
        f"🎊 تبریک، {full_name}! ثبت‌نامت کامل شد!\n\n"
        f"{rolled['breed_emoji']} حیوانت:\n"
        f"  نوع: {rolled['species_name']}\n"
        f"  نژاد: {rolled['breed_name']}\n"
        f"  {rolled['rarity_icon']} ندرت: {rolled['rarity'].upper()}\n"
        f"  🎨 رنگ: {rolled['color']}\n"
        f"  {'♂️' if rolled['gender'] == 'نر' else '♀️'} جنسیت: {rolled['gender']}\n\n"
        f"💰 جایزه خوش‌آمدگویی: **۱۰۰ سکه**\n\n"
        f"حالا بریم باهم بازی کنیم! 🚀",
        parse_mode="Markdown",
    )

    await callback.message.answer(
        "🏠 منوی اصلی ZooBoom:",
        reply_markup=main_menu_keyboard(user_id),
    )
    await callback.answer("✅ ثبت‌نام موفق!")


# ─────────────────────────────────────────────
#  Zoo menu callback (basic placeholder)
# ─────────────────────────────────────────────

@router.callback_query(F.data == "zoo_menu")
async def zoo_menu(callback: CallbackQuery) -> None:
    user = get_user(callback.from_user.id)
    if not user:
        await callback.answer("ابتدا ثبت‌نام کن! /start", show_alert=True)
        return

    conn = get_connection()
    zoo = conn.execute(
        "SELECT * FROM zoos WHERE owner_id = ?", (callback.from_user.id,)
    ).fetchone()
    animal_count = conn.execute(
        "SELECT COUNT(*) FROM animals WHERE owner_id = ? AND is_alive = 1",
        (callback.from_user.id,),
    ).fetchone()[0]
    conn.close()

    if not zoo:
        zoo_text = (
            "🦁 **باغ وحش من**\n\n"
            "هنوز باغ وحشی نساختی!\n"
            f"🐾 تعداد حیوانات: {animal_count}\n\n"
            "برای ساخت باغ وحش به پت‌شاپ برو."
        )
    else:
        status = "باز 🟢" if zoo["is_open"] else "بسته 🔴"
        zoo_text = (
            f"🦁 **{zoo['zoo_name']}**\n\n"
            f"⭐ سطح: {zoo['level']}\n"
            f"🏆 شهرت: {zoo['reputation']}\n"
            f"💵 درآمد روزانه: {zoo['daily_income']:,} سکه\n"
            f"🚪 وضعیت: {status}\n"
            f"🐾 تعداد حیوانات: {animal_count}"
        )

    await callback.message.edit_text(
        zoo_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 برگشت", callback_data="back_main")]
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏠 منوی اصلی ZooBoom:",
        reply_markup=main_menu_keyboard(callback.from_user.id),
    )
    await callback.answer()
