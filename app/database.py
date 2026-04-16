import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List
from contextlib import contextmanager

# 根据环境选择数据库路径
if os.name == 'nt':  # Windows
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "proxy.db")
else:  # Linux/Mac/Docker
    DATABASE_PATH = "/app/data/proxy.db"

# 确保数据目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

BEIJING_TZ = timezone(timedelta(hours=8))

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
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
            created_at TEXT,
            updated_at TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(models)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if 'model_id' not in existing_cols:
        cursor.execute("ALTER TABLE models ADD COLUMN model_id TEXT DEFAULT ''")
    if 'is_default_model' not in existing_cols:
        cursor.execute("ALTER TABLE models ADD COLUMN is_default_model INTEGER DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES ('auto_switch', '1')")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_logs (
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
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_config_id TEXT NOT NULL,
            usage_date DATE NOT NULL,
            total_tokens INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            UNIQUE(model_config_id, usage_date)
        )
    """)

    cursor.execute("PRAGMA table_info(daily_usage)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    if 'total_calls' not in existing_cols:
        cursor.execute("ALTER TABLE daily_usage ADD COLUMN total_calls INTEGER DEFAULT 0")

    # 用户表（管理员认证）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# ========== 认证函数 ==========

def hash_password(password: str, salt: str = None) -> tuple:
    """对密码进行 pbkdf2_hmac 哈希处理"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return pwdhash.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """验证密码是否匹配"""
    pwdhash, _ = hash_password(password, salt)
    return pwdhash == password_hash

def create_user(username: str, password: str) -> bool:
    """创建新用户，用户名重复时返回 False"""
    password_hash, salt = hash_password(password)
    created_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, salt, created_at, created_at)
            )
            return True
        except sqlite3.IntegrityError:
            return False

def get_user(username: str) -> Optional[dict]:
    """根据用户名查询用户信息"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_password(username: str, new_password: str) -> bool:
    """更新用户密码"""
    password_hash, salt = hash_password(new_password)
    updated_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE username = ?",
            (password_hash, salt, updated_at, username)
        )
        return True

def has_users() -> bool:
    """检查是否已存在用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        row = cursor.fetchone()
        return row['count'] > 0


# ========== 业务函数 ==========

def get_auto_switch_status() -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_config WHERE key = 'auto_switch'")
        row = cursor.fetchone()
        return row['value'] == '1' if row else True

def set_auto_switch_status(enabled: bool):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('auto_switch', ?)",
                      ('1' if enabled else '0',))

def get_default_model() -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE is_default_model = 1 AND is_active = 1 LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None

def get_model_by_priority() -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM models
            WHERE is_active = 1
            ORDER BY priority DESC
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_model_by_config_id(config_id: str) -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE config_id = ?", (config_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_api_key(key: str) -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1", (key,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_daily_usage(config_id: str, usage_date: date = None) -> dict:
    if usage_date is None:
        # 使用北京时间
        usage_date = datetime.now(BEIJING_TZ).date()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT total_tokens, total_calls FROM daily_usage
            WHERE model_config_id = ? AND usage_date = ?
        """, (config_id, usage_date.isoformat()))
        row = cursor.fetchone()
        if row:
            return {'total_tokens': row['total_tokens'], 'total_calls': row['total_calls']}
        return {'total_tokens': 0, 'total_calls': 0}

def update_daily_usage(config_id: str, tokens: int, calls: int = 1):
    # 使用北京时间
    today = datetime.now(BEIJING_TZ).date()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (model_config_id, usage_date, total_tokens, total_calls)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(model_config_id, usage_date)
            DO UPDATE SET
                total_tokens = total_tokens + ?,
                total_calls = total_calls + ?
        """, (config_id, today.isoformat(), tokens, calls, tokens, calls))

def create_call_log(log_data: dict):
    created_at = log_data.get('created_at')
    if created_at is None:
        created_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO call_logs (
                request_id, api_key_id, api_key_name, model_config_id,
                model_name, input_tokens, output_tokens, status,
                error_message, error_code, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_data['request_id'],
            log_data['api_key_id'],
            log_data['api_key_name'],
            log_data['model_config_id'],
            log_data['model_name'],
            log_data.get('input_tokens', 0),
            log_data.get('output_tokens', 0),
            log_data.get('status', 'success'),
            log_data.get('error_message'),
            log_data.get('error_code'),
            created_at
        ))

def get_all_models() -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models ORDER BY priority DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def create_model(model_data: dict) -> str:
    import uuid
    config_id = str(uuid.uuid4())[:8]
    created_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO models (config_id, name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, is_default_model, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config_id,
            model_data['name'],
            model_data['api_url'],
            model_data['api_key'],
            model_data.get('model_id', ''),
            model_data.get('daily_token_limit', 100000),
            model_data.get('daily_call_limit', 1000),
            model_data.get('is_default_model', 0),
            model_data.get('priority', 0),
            created_at,
            created_at
        ))
    return config_id

def update_model(config_id: str, model_data: dict):
    updated_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        cursor = conn.cursor()
        if model_data.get('is_default_model', 0) == 1:
            cursor.execute("UPDATE models SET is_default_model = 0")
        cursor.execute("""
            UPDATE models SET
                name = ?, api_url = ?, api_key = ?, model_id = ?,
                daily_token_limit = ?, daily_call_limit = ?,
                is_default_model = ?,
                priority = ?, updated_at = ?
            WHERE config_id = ?
        """, (
            model_data['name'],
            model_data['api_url'],
            model_data['api_key'],
            model_data.get('model_id', ''),
            model_data.get('daily_token_limit', 100000),
            model_data.get('daily_call_limit', 1000),
            model_data.get('is_default_model', 0),
            model_data.get('priority', 0),
            updated_at,
            config_id
        ))

def delete_model(config_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE config_id = ?", (config_id,))

def get_all_api_keys() -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def create_api_key(name: str) -> dict:
    import secrets
    import uuid
    key_id = str(uuid.uuid4())[:8]
    api_key = f"sk-{secrets.token_urlsafe(32)}"
    created_at = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (key_id, api_key, name, created_at)
            VALUES (?, ?, ?, ?)
        """, (key_id, api_key, name, created_at))
    return {'key_id': key_id, 'api_key': api_key, 'name': name}

def delete_api_key(key_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE key_id = ?", (key_id,))

def get_call_logs(limit: int = 100, offset: int = 0) -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM call_logs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_daily_stats() -> List[dict]:
    today = date.today()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.config_id, m.name, m.model_id, m.api_url, m.daily_token_limit, m.daily_call_limit, m.is_default_model, m.is_active, m.priority,
                   COALESCE(d.total_tokens, 0) as used_tokens,
                   COALESCE(d.total_calls, 0) as used_calls
            FROM models m
            LEFT JOIN daily_usage d ON m.config_id = d.model_config_id AND d.usage_date = ?
            ORDER BY m.priority DESC
        """, (today.isoformat(),))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
