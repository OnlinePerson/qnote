import sqlite3
import json
import os
from datetime import datetime

DATABASE_PATH = os.getenv("DATABASE_PATH", "zooboom.db")


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # جدول کاربران
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        full_name   TEXT,
        age         INTEGER,
        country     TEXT,
        coins       INTEGER DEFAULT 0,
        total_score INTEGER DEFAULT 0,
        level       INTEGER DEFAULT 1,
        registered_at TEXT DEFAULT (datetime('now')),
        last_active   TEXT DEFAULT (datetime('now'))
    )''')

    # جدول حیوان‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS animals (
        animal_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id     INTEGER,
        species      TEXT,
        breed        TEXT,
        color        TEXT,
        gender       TEXT,
        nickname     TEXT,
        level        INTEGER DEFAULT 1,
        xp           INTEGER DEFAULT 0,
        hunger       INTEGER DEFAULT 100,
        happiness    INTEGER DEFAULT 100,
        health       INTEGER DEFAULT 100,
        cleanliness  INTEGER DEFAULT 100,
        age_days     INTEGER DEFAULT 0,
        is_sick      INTEGER DEFAULT 0,
        is_alive     INTEGER DEFAULT 1,
        habitat      TEXT DEFAULT 'basic',
        accessories  TEXT DEFAULT '[]',
        tricks       TEXT DEFAULT '[]',
        parent1_id   INTEGER DEFAULT NULL,
        parent2_id   INTEGER DEFAULT NULL,
        born_at      TEXT DEFAULT (datetime('now')),
        last_fed     TEXT DEFAULT (datetime('now')),
        last_played  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(owner_id) REFERENCES users(user_id)
    )''')

    # جدول باغ وحش‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS zoos (
        zoo_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id     INTEGER UNIQUE,
        zoo_name     TEXT DEFAULT 'باغ وحش من',
        level        INTEGER DEFAULT 1,
        reputation   INTEGER DEFAULT 0,
        daily_income INTEGER DEFAULT 0,
        sections     TEXT DEFAULT '{}',
        decorations  TEXT DEFAULT '[]',
        is_open      INTEGER DEFAULT 0,
        opened_at    TEXT,
        FOREIGN KEY(owner_id) REFERENCES users(user_id)
    )''')

    # جدول حیوان‌های باغ وحش (کدوم حیوون توی کدوم باغ وحشه)
    c.execute('''CREATE TABLE IF NOT EXISTS zoo_animals (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        zoo_id    INTEGER,
        animal_id INTEGER,
        section   TEXT,
        added_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(zoo_id) REFERENCES zoos(zoo_id),
        FOREIGN KEY(animal_id) REFERENCES animals(animal_id)
    )''')

    # جدول آیتم‌های پت‌شاپ
    c.execute('''CREATE TABLE IF NOT EXISTS shop_items (
        item_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT,
        description TEXT,
        category    TEXT,
        species     TEXT DEFAULT 'all',
        price       INTEGER,
        effect      TEXT DEFAULT '{}',
        icon        TEXT DEFAULT '🎁'
    )''')

    # جدول انبار کاربر
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER,
        item_id  INTEGER,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(item_id) REFERENCES shop_items(item_id)
    )''')

    # جدول دوستی حیوان‌ها
    c.execute('''CREATE TABLE IF NOT EXISTS friendships (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        animal1_id    INTEGER,
        animal2_id    INTEGER,
        friendship_lvl INTEGER DEFAULT 1,
        started_at    TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(animal1_id) REFERENCES animals(animal_id),
        FOREIGN KEY(animal2_id) REFERENCES animals(animal_id)
    )''')

    # جدول درخواست‌های خرید سکه
    c.execute('''CREATE TABLE IF NOT EXISTS coin_requests (
        request_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER,
        amount      INTEGER,
        total_price INTEGER,
        receipt_file_id TEXT,
        status      TEXT DEFAULT 'pending',
        created_at  TEXT DEFAULT (datetime('now')),
        reviewed_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )''')

    # جدول امتیاز گروه
    c.execute('''CREATE TABLE IF NOT EXISTS group_scores (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER,
        group_id   INTEGER,
        score      INTEGER,
        earned_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )''')

    # جدول cooldown گروه
    c.execute('''CREATE TABLE IF NOT EXISTS group_cooldowns (
        user_id   INTEGER,
        group_id  INTEGER,
        last_used TEXT DEFAULT (datetime('now')),
        PRIMARY KEY(user_id, group_id)
    )''')

    # جدول ترفندهای آموخته‌شده
    c.execute('''CREATE TABLE IF NOT EXISTS animal_tricks (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        animal_id  INTEGER,
        command    TEXT,
        response   TEXT,
        reward_item_id INTEGER DEFAULT NULL,
        cost       INTEGER DEFAULT 50,
        FOREIGN KEY(animal_id) REFERENCES animals(animal_id)
    )''')

    # جدول آب و هوا
    c.execute('''CREATE TABLE IF NOT EXISTS weather (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        weather_type TEXT,
        description  TEXT,
        effect       TEXT DEFAULT '{}',
        started_at   TEXT DEFAULT (datetime('now'))
    )''')

    # جدول رویدادهای فصلی
    c.execute('''CREATE TABLE IF NOT EXISTS seasonal_events (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT,
        description TEXT,
        start_date TEXT,
        end_date   TEXT,
        rewards    TEXT DEFAULT '{}'
    )''')

    conn.commit()
    conn.close()
    print("✅ دیتابیس با موفقیت ساخته شد")


def seed_shop():
    """آیتم‌های پیش‌فرض پت‌شاپ"""
    conn = get_connection()
    c = conn.cursor()

    existing = c.execute("SELECT COUNT(*) FROM shop_items").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    items = [
        # غذا - عمومی
        ("غذای خشک", "غذای خشک مناسب برای اکثر حیوانات", "food", "all", 10, '{"hunger":30}', "🍖"),
        ("غذای مرطوب", "غذای مرطوب خوشمزه", "food", "all", 20, '{"hunger":50,"happiness":5}', "🥩"),
        ("تنقلات ویژه", "تنقلات مخصوص که حیوانت عاشقشه", "food", "all", 35, '{"hunger":20,"happiness":20}', "🍬"),

        # غذای مخصوص
        ("علوفه", "برای حیوانات علفخوار", "food", "herbivore", 8, '{"hunger":40}', "🌿"),
        ("ماهی تازه", "برای گربه و حیوانات آبزی", "food", "cat", 15, '{"hunger":35,"happiness":10}', "🐟"),
        ("هویج", "مخصوص خرگوش و خوکچه", "food", "rabbit", 5, '{"hunger":25,"happiness":5}', "🥕"),

        # بهداشت
        ("شامپو", "برای شستشوی حیوان", "hygiene", "all", 25, '{"cleanliness":40}', "🧴"),
        ("مسواک حیوانات", "برای بهداشت دهان", "hygiene", "all", 15, '{"health":5,"cleanliness":10}', "🪥"),
        ("حمام کامل", "سرویس کامل بهداشت", "hygiene", "all", 60, '{"cleanliness":80,"happiness":10}', "🛁"),

        # دارو و درمان
        ("قرص مولتی‌ویتامین", "برای تقویت سلامتی", "medicine", "all", 40, '{"health":20}', "💊"),
        ("آنتی‌بیوتیک", "درمان بیماری‌های عفونی", "medicine", "all", 80, '{"health":40,"is_sick":0}', "💉"),
        ("کرم ضدعفونی", "پیشگیری از بیماری", "medicine", "all", 30, '{"health":10}', "🧪"),

        # اسباب‌بازی
        ("توپ بازی", "برای بازی و سرگرمی", "toy", "all", 20, '{"happiness":25}', "⚽"),
        ("چرخ دویدن", "برای ورزش کردن", "toy", "all", 45, '{"happiness":30,"health":10}', "🎡"),
        ("اسباب‌بازی مخصوص", "اسباب‌بازی مورد علاقه", "toy", "all", 35, '{"happiness":35}', "🧸"),

        # لوازم و اکسسوری
        ("گردنبند طلا", "گردنبند زیبا برای حیوانت", "accessory", "all", 100, '{"happiness":15}', "📿"),
        ("لباس زمستانی", "لباس گرم برای فصل سرد", "accessory", "all", 80, '{"health":5}', "🧥"),
        ("تاج شاهانه", "تاج مخصوص حیوانات VIP", "accessory", "all", 200, '{"happiness":20}', "👑"),

        # محل زندگی
        ("قفس استاندارد", "قفس معمولی", "habitat", "all", 150, '{"happiness":10}', "🏠"),
        ("خانه چوبی", "خانه زیبای چوبی", "habitat", "all", 300, '{"happiness":20,"health":5}', "🏡"),
        ("قصر حیوانات", "بهترین محل زندگی", "habitat", "all", 800, '{"happiness":35,"health":10}', "🏰"),

        # جوایز گروه
        ("جایزه رفاقت", "جایزه برای دادن به دوست", "gift", "all", 50, '{"friendship":10}', "🎁"),
    ]

    c.executemany('''INSERT INTO shop_items 
        (name, description, category, species, price, effect, icon) 
        VALUES (?,?,?,?,?,?,?)''', items)

    conn.commit()
    conn.close()
    print("✅ آیتم‌های پت‌شاپ اضافه شدند")


if __name__ == "__main__":
    init_db()
    seed_shop()
