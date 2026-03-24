import sqlite3
from datetime import date

DATABASE_PATH = "/app/data/proxy.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        api_url TEXT NOT NULL,
        api_key TEXT NOT NULL,
        model_id TEXT DEFAULT '',
        daily_token_limit INTEGER DEFAULT 100000,
        daily_call_limit INTEGER DEFAULT 1000,
        is_default_model INTEGER DEFAULT 0,
        priority INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("PRAGMA table_info(models)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if 'model_id' not in existing_cols:
        cursor.execute("ALTER TABLE models ADD COLUMN model_id TEXT DEFAULT ''")
    if 'is_default_model' not in existing_cols:
        cursor.execute("ALTER TABLE models ADD COLUMN is_default_model INTEGER DEFAULT 0")

    cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )""")

    cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_switch', '1')")

    cursor.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT UNIQUE NOT NULL,
        api_key TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS call_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL,
        api_key_id TEXT NOT NULL,
        api_key_name TEXT NOT NULL,
        model_config_id TEXT NOT NULL,
        model_name TEXT NOT NULL,
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        status TEXT DEFAULT 'success',
        error_message TEXT,
        error_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS daily_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_config_id TEXT NOT NULL,
        usage_date DATE NOT NULL,
        total_tokens INTEGER DEFAULT 0,
        total_calls INTEGER DEFAULT 0,
        UNIQUE(model_config_id, usage_date)
    )""")

    cursor.execute("PRAGMA table_info(daily_usage)")
    daily_cols = [row[1] for row in cursor.fetchall()]
    if 'total_calls' not in daily_cols:
        cursor.execute("ALTER TABLE daily_usage ADD COLUMN total_calls INTEGER DEFAULT 0")

    conn.commit()
    conn.close()

init_db()

def get_auto_switch_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = 'auto_switch'")
    row = cursor.fetchone()
    conn.close()
    return row['value'] == '1' if row else True

def set_auto_switch_status(enabled):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_switch', ?)",
                  ('1' if enabled else '0',))
    conn.commit()
    conn.close()

def get_all_models():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models ORDER BY priority DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_model(name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority):
    import uuid
    config_id = str(uuid.uuid4())[:8]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO models (config_id, name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, is_default_model, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (config_id, name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority))
    conn.commit()
    conn.close()
    return config_id

def update_model(config_id, name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, is_default_model, priority):
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_default_model == 1:
        cursor.execute("UPDATE models SET is_default_model = 0")
    cursor.execute("""UPDATE models SET
        name = ?, api_url = ?, api_key = ?, model_id = ?,
        daily_token_limit = ?, daily_call_limit = ?,
        is_default_model = ?,
        priority = ?, updated_at = CURRENT_TIMESTAMP
        WHERE config_id = ?""",
        (name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, is_default_model, priority, config_id))
    conn.commit()
    conn.close()

def delete_model(config_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM models WHERE config_id = ?", (config_id,))
    conn.commit()
    conn.close()

def get_all_api_keys():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def create_api_key(name):
    import secrets
    import uuid
    key_id = str(uuid.uuid4())[:8]
    api_key = f"sk-{secrets.token_urlsafe(32)}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO api_keys (key_id, api_key, name) VALUES (?, ?, ?)",
        (key_id, api_key, name))
    conn.commit()
    conn.close()
    return {'key_id': key_id, 'api_key': api_key, 'name': name}

def delete_api_key(key_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE api_keys SET is_active = 0 WHERE key_id = ?", (key_id,))
    conn.commit()
    conn.close()

def get_call_logs(limit=200):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM call_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_daily_stats():
    today = date.today()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""SELECT m.config_id, m.name, m.model_id, m.api_url, m.daily_token_limit, m.daily_call_limit, m.is_default_model, m.is_active,
            COALESCE(d.total_tokens, 0) as used_tokens,
            COALESCE(d.total_calls, 0) as used_calls
        FROM models m
        LEFT JOIN daily_usage d ON m.config_id = d.model_config_id AND d.usage_date = ?
        ORDER BY m.priority DESC""", (today.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
