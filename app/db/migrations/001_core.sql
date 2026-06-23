CREATE TABLE IF NOT EXISTS schema_migrations(
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    category TEXT,
    description TEXT,
    amount INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS incomes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    category TEXT,
    description TEXT,
    amount INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS budgets(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    month TEXT,
    limit_amount INTEGER,
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(telegram_id, month)
);

CREATE TABLE IF NOT EXISTS goals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    title TEXT,
    target_amount INTEGER,
    saved_amount INTEGER DEFAULT 0,
    is_completed INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS user_profiles(
    telegram_id INTEGER PRIMARY KEY,
    full_name TEXT,
    currency TEXT DEFAULT 'UZS',
    premium_plan TEXT DEFAULT 'free',
    premium_until TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS receipt_imports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    file_id TEXT,
    raw_text TEXT,
    parsed_json TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_dialogs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS premium_features(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(telegram_id, created_at);
CREATE INDEX IF NOT EXISTS idx_incomes_user_date ON incomes(telegram_id, created_at);