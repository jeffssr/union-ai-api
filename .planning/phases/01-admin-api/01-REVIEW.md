---
phase: 01-admin-api
reviewed: 2026-04-16T13:05:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - app/database.py
  - app/main.py
  - app/router/admin.py
findings:
  critical: 2
  warning: 4
  info: 3
  total: 9
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-16T13:05:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

对 Phase 01 (Admin API) 的三个文件进行了标准深度审查。发现 2 个严重问题、4 个警告、3 个信息项。

最严重的问题是：(1) Session Token 签名密钥硬编码在源码中，且仅使用 SHA-256 截断前 16 位十六进制（64 bit）作为签名，存在伪造风险；(2) `get_daily_stats()` 使用 `date.today()` 本地时间而非北京时间，导致每日统计与业务逻辑时间基准不一致。

## Critical Issues

### CR-01: Session Token 签名密钥硬编码且签名强度不足

**File:** `app/router/admin.py:27`
**Issue:** `SECRET_KEY = "union_ai_secret"` 硬编码在源码中。同时签名仅取 SHA-256 输出的前 16 个十六进制字符（64 bit），这显著降低了签名安全性。攻击者如果获取到源码（开源项目或泄露），可以直接伪造任意用户的 session token。此外，密钥无法在不同部署实例间区分，所有部署共享同一密钥。

**Fix:**
```python
# admin.py 顶部
import os

# 从环境变量读取，提供开发时的 fallback
SECRET_KEY = os.environ.get("ADMIN_SECRET_KEY", None)

# 在应用启动时检查（可选，但推荐）
if not SECRET_KEY:
    if os.environ.get("ENVIRONMENT") == "production":
        raise RuntimeError("ADMIN_SECRET_KEY environment variable is required in production")
    # 仅开发环境使用 fallback
    SECRET_KEY = "dev_only_secret_key"
```

同时在签名中使用完整的 SHA-256 输出（64 位十六进制），而非截断至 16 位：
```python
# 第 36 行和第 54 行，将 [:16] 去掉
token_hash = hashlib.sha256(f"{token_data}:{SECRET_KEY}".encode()).hexdigest()
```

### CR-02: Cookie 缺少 `secure` 标志

**File:** `app/router/admin.py:87-94`
**Issue:** `set_auth_cookie` 设置的 HttpOnly Cookie 没有设置 `secure=True`。在 HTTPS 环境下，缺少 `secure` 标志意味着 Cookie 可能通过明文 HTTP 传输，存在中间人窃取 session 的风险。此外，`samesite="lax"` 虽然合理，但在生产环境建议设置 `secure=True` 以配合 `SameSite` 策略。

**Fix:**
```python
def set_auth_cookie(response: Response, token: str):
    """设置 HttpOnly 认证 Cookie"""
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,  # 生产环境必须启用
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
        path="/"
    )
```

## Warnings

### WR-01: `get_daily_stats()` 使用本地时间而非北京时间

**File:** `app/database.py:398`
**Issue:** `get_daily_stats()` 使用 `date.today()`（服务器本地时区），而所有其他时间相关逻辑（`update_daily_usage` 第 259 行、`create_call_log` 第 274 行等）均使用 `datetime.now(BEIJING_TZ)` 北京时间。当服务器部署在非 UTC+8 时区（如 Docker 容器默认 UTC）时，`get_daily_stats` 查询的日期与 `daily_usage` 记录的日期不一致，导致统计数据显示为零或不完整。

**Fix:**
```python
def get_daily_stats() -> List[dict]:
    today = datetime.now(BEIJING_TZ).date()  # 使用北京时间
    with get_db() as conn:
        # ... 后续不变
```

### WR-02: `update_user_password` 始终返回 True

**File:** `app/database.py:173-183`
**Issue:** `update_user_password` 无论 UPDATE 是否实际更新了行（即用户是否存在），都返回 `True`。调用方 `change_password` 端点依赖 `get_user` 先查到用户（通过 `get_current_user` 依赖注入），所以当前不会出问题，但函数签名暗示了可能失败的语义，未来如果被其他路径调用可能导致静默失败。

**Fix:**
```python
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
        return cursor.rowcount > 0
```

### WR-03: Excel 导入静默吞掉所有异常

**File:** `app/router/admin.py:454`
**Issue:** `import_excel` 中每行导入的 `except Exception: continue` 会静默忽略所有错误，包括数据库连接失败等严重异常。调用方无法知道有多少行因何种原因失败。如果大部分行都失败了但 `success_count > 0`，前端仍显示"导入成功"，误导用户。

**Fix:**
```python
    failed_count = 0
    error_details = []
    for idx, row in df.iterrows():
        try:
            name = str(row.get(col_map['name'], '')).strip()
            # ... 其余逻辑不变
            db_create_model(model_data)
            success_count += 1
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # 只记录前 5 个错误详情
                error_details.append(f"第 {idx + 2} 行: {str(e)[:100]}")

    return {
        "message": "导入完成",
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": error_details
    }
```

### WR-04: Session Token 过期时间验证使用无时区感知的 datetime

**File:** `app/router/admin.py:50`
**Issue:** `datetime.fromtimestamp(int(timestamp))` 创建的是无时区信息的 naive datetime，而 `datetime.now()` 同样返回 naive datetime。虽然两个 naive datetime 相减的比较仍然有效（两者都是本地时间），但这种模式在时区转换或代码重构时容易引入 bug。且 token 过期时间 7 天是硬编码在验证逻辑中的。

**Fix:**
```python
# 使用 UTC 保持一致性
token_time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
if datetime.now(timezone.utc) - token_time > timedelta(days=7):
    return None
```

## Info

### IN-01: `hash_password` 模块级导入了 `secrets` 但在函数内未使用局部导入

**File:** `app/database.py:3` 对比第 367-368 行
**Issue:** 文件顶部第 3 行已导入 `import secrets`，但 `create_api_key` 函数第 368 行又重复 `import secrets`。这是多余的，不影响功能但增加了阅读困惑。

**Fix:** 删除第 368 行的 `import secrets`。

### IN-02: `import_excel` 中 `row.get` 的 fallback 值语义不清

**File:** `app/router/admin.py:448-449`
**Issue:** 当 `col_map` 中缺少某个可选列时，`col_map.get('daily_token_limit', 'daily_token_limit')` 返回字符串 `'daily_token_limit'`，然后传给 `row.get()`。这实际是在用列名作为 DataFrame 行的键来查找，如果 DataFrame 的列名恰好包含该字符串则能匹配，否则返回默认值。虽然结果碰巧正确，但逻辑绕了一圈，阅读性差。

**Fix:**
```python
"daily_token_limit": int(row[col_map['daily_token_limit']]) if 'daily_token_limit' in col_map else 100000,
"daily_call_limit": int(row[col_map['daily_call_limit']]) if 'daily_call_limit' in col_map else 1000,
"priority": int(row[col_map['priority']]) if 'priority' in col_map else 0,
```

### IN-03: `database.py` 中 `create_model` 的 `uuid` 在函数内部导入

**File:** `app/database.py:306`
**Issue:** `import uuid` 在 `create_model` 函数内部延迟导入，而 `create_api_key` 第 369 行同样有 `import uuid`。`uuid` 是标准库，启动开销极小，建议统一在模块顶部导入。

**Fix:** 将 `import uuid` 移至文件顶部与其他标准库导入一起，删除函数内的局部导入。

---

_Reviewed: 2026-04-16T13:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
