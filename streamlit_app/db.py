import sqlite3
import hashlib
import secrets
import os
from datetime import date

# 根据环境选择数据库路径
if os.name == 'nt':  # Windows
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "proxy.db")
else:  # Linux/Mac/Docker
    DATABASE_PATH = "/app/data/proxy.db"

# 确保数据目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

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

    # 用户表
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    """对密码进行哈希处理"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return pwdhash.hex(), salt

def verify_password(password, password_hash, salt):
    """验证密码"""
    pwdhash, _ = hash_password(password, salt)
    return pwdhash == password_hash

def create_user(username, password):
    """创建用户"""
    password_hash, salt = hash_password(password)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    """获取用户信息"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_password(username, new_password):
    """更新用户密码"""
    password_hash, salt = hash_password(new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
        (password_hash, salt, username)
    )
    conn.commit()
    conn.close()
    return True

def has_users():
    """检查是否已有用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    row = cursor.fetchone()
    conn.close()
    return row['count'] > 0

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
    cursor.execute("""SELECT m.config_id, m.name, m.model_id, m.api_url, m.daily_token_limit, m.daily_call_limit, m.is_default_model, m.is_active, m.priority,
            COALESCE(d.total_tokens, 0) as used_tokens,
            COALESCE(d.total_calls, 0) as used_calls
        FROM models m
        LEFT JOIN daily_usage d ON m.config_id = d.model_config_id AND d.usage_date = ?
        ORDER BY m.priority DESC""", (today.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

init_db()
