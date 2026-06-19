-- ZooBoom Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT NOT NULL,
    age INTEGER,
    country TEXT,
    coins INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Animals (species) definition
CREATE TABLE IF NOT EXISTS animal_species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sound TEXT NOT NULL,
    sound_text TEXT NOT NULL,
    emoji TEXT NOT NULL,
    category TEXT NOT NULL, -- mammal, bird, insect, reptile, etc
    description TEXT,
    base_food_type TEXT,
    base_habitat TEXT
);

-- User's animals (pets in farm)
CREATE TABLE IF NOT EXISTS user_animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    nickname TEXT,
    breed TEXT NOT NULL,
    color TEXT NOT NULL,
    gender TEXT NOT NULL, -- male/female
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    age_days INTEGER DEFAULT 0,
    health INTEGER DEFAULT 100,
    happiness INTEGER DEFAULT 100,
    hunger INTEGER DEFAULT 100,
    cleanliness INTEGER DEFAULT 100,
    energy INTEGER DEFAULT 100,
    is_alive INTEGER DEFAULT 1,
    box_opened INTEGER DEFAULT 0,
    slot_number INTEGER DEFAULT 1,
    -- Accessories
    has_collar INTEGER DEFAULT 0,
    has_clothes INTEGER DEFAULT 0,
    has_toy INTEGER DEFAULT 0,
    has_medicine_stock INTEGER DEFAULT 0,
    -- Housing
    habitat_level INTEGER DEFAULT 1,
    -- Breeding
    partner_animal_id INTEGER DEFAULT NULL,
    friendship_level INTEGER DEFAULT 0,
    last_fed DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_played DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_treated DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (species_id) REFERENCES animal_species(id)
);

-- Pet Shop items
CREATE TABLE IF NOT EXISTS shop_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL, -- food, medicine, toy, accessory, habitat
    subcategory TEXT,
    price_coins INTEGER NOT NULL,
    effect_type TEXT, -- health, happiness, hunger, energy, xp
    effect_value INTEGER DEFAULT 0,
    species_specific INTEGER DEFAULT 0, -- 0=all, species_id=specific
    emoji TEXT,
    is_available INTEGER DEFAULT 1
);

-- User inventory
CREATE TABLE IF NOT EXISTS user_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES shop_items(id)
);

-- Zoo
CREATE TABLE IF NOT EXISTS user_zoos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    zoo_name TEXT DEFAULT 'باغ وحش من',
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    is_open INTEGER DEFAULT 0,
    daily_visitors INTEGER DEFAULT 0,
    total_visitors INTEGER DEFAULT 0,
    daily_income INTEGER DEFAULT 0,
    total_income INTEGER DEFAULT 0,
    design_theme TEXT DEFAULT 'classic',
    sections_unlocked INTEGER DEFAULT 1,
    last_income DATETIME DEFAULT CURRENT_TIMESTAMP,
    purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Zoo sections (8 sections)
CREATE TABLE IF NOT EXISTS zoo_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id INTEGER NOT NULL,
    section_number INTEGER NOT NULL,
    section_name TEXT,
    animal_type TEXT,
    capacity INTEGER DEFAULT 3,
    upgrade_level INTEGER DEFAULT 1,
    FOREIGN KEY (zoo_id) REFERENCES user_zoos(id)
);

-- Zoo animals (borrowed from farm)
CREATE TABLE IF NOT EXISTS zoo_animals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zoo_id INTEGER NOT NULL,
    animal_id INTEGER NOT NULL,
    owner_user_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zoo_id) REFERENCES user_zoos(id),
    FOREIGN KEY (animal_id) REFERENCES user_animals(id)
);

-- Coin purchase requests
CREATE TABLE IF NOT EXISTS coin_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_coins INTEGER NOT NULL,
    amount_toman INTEGER NOT NULL,
    receipt_file_id TEXT,
    status TEXT DEFAULT 'pending', -- pending/approved/rejected
    admin_note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Animal friendships
CREATE TABLE IF NOT EXISTS animal_friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal1_id INTEGER NOT NULL,
    animal2_id INTEGER NOT NULL,
    friendship_level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal1_id) REFERENCES user_animals(id),
    FOREIGN KEY (animal2_id) REFERENCES user_animals(id)
);

-- Group game sessions
CREATE TABLE IF NOT EXISTS group_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    game_type TEXT NOT NULL,
    initiator_animal_id INTEGER NOT NULL,
    status TEXT DEFAULT 'waiting', -- waiting/active/finished
    winner_animal_id INTEGER DEFAULT NULL,
    game_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (initiator_animal_id) REFERENCES user_animals(id)
);

-- Group game participants
CREATE TABLE IF NOT EXISTS game_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    animal_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES group_games(id)
);

-- Seasonal events
CREATE TABLE IF NOT EXISTS seasonal_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reward_type TEXT,
    reward_value INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1
);

-- Weather (daily)
CREATE TABLE IF NOT EXISTS daily_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    weather_type TEXT NOT NULL, -- sunny/rainy/cold/hot/storm/windy
    temperature INTEGER,
    effect_description TEXT
);

-- Leaderboard (weekly snapshot)
CREATE TABLE IF NOT EXISTS weekly_leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    zoo_score INTEGER DEFAULT 0,
    rank INTEGER,
    reward_given INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Animal training
CREATE TABLE IF NOT EXISTS animal_training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    animal_id INTEGER NOT NULL,
    command_trigger TEXT NOT NULL,
    response_text TEXT NOT NULL,
    response_image_url TEXT,
    cost_coins INTEGER DEFAULT 50,
    trained_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (animal_id) REFERENCES user_animals(id)
);

-- Transactions log
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL, -- purchase/earn/spend/transfer
    amount INTEGER NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sound cooldowns (group)
CREATE TABLE IF NOT EXISTS sound_cooldowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    last_sound DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, group_id)
);
