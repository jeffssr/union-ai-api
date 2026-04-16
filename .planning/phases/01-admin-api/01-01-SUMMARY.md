---
phase: 01-admin-api
plan: 01
subsystem: auth
tags: [fastapi, sqlite, cookie-auth, httponly, pbkdf2, session-token]

# Dependency graph
requires: []
provides:
  - "users 表 + 6 个认证函数（hash_password, verify_password, create_user, get_user, update_user_password, has_users）"
  - "Admin API 认证端点（login, register, logout, me, change-password）"
  - "HttpOnly Cookie session 认证机制，7 天有效期"
  - "get_current_user 依赖注入认证守卫"
  - "SQLite WAL 模式支持并发读写"
affects: [01-02, 01-03, react-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HttpOnly Cookie session 认证（非 JWT）"
    - "pbkdf2_hmac sha256 密码哈希，100000 迭代"
    - "base64(username:timestamp:sha256[:16]) session token 格式"
    - "has_users() 首用户注册保护"
    - "get_db() context manager 统一数据库连接管理"

key-files:
  created:
    - app/router/admin.py
  modified:
    - app/database.py
    - app/main.py

key-decisions:
  - "复用 Streamlit 的 SECRET_KEY 和 token 格式，确保迁移期间两个面板可共存"
  - "使用 HttpOnly Cookie 而非 JWT Bearer token，与浏览器前端场景匹配"

patterns-established:
  - "Admin API 路由前缀 /api/admin/*，不与 /v1/* 代理路由冲突"
  - "认证端点使用 Form() 接收参数（非 JSON body），便于浏览器原生表单提交"
  - "get_current_user 依赖注入模式：Cookie 提取 -> token 验证 -> 用户查询 -> 返回脱敏数据"

requirements-completed: [AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, API-01, API-02]

# Metrics
duration: 4min
completed: 2026-04-16
---

# Phase 1 Plan 01: Admin API Auth Summary

**HttpOnly Cookie 认证端点（login/register/logout/me/change-password）+ SQLite users 表 + WAL 模式，复用 Streamlit 现有密码哈希和 token 签名逻辑**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-16T04:42:42Z
- **Completed:** 2026-04-16T04:47:08Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- 在 app/database.py 中新增 users 表和 6 个认证函数，启用 WAL 模式
- 创建 app/router/admin.py 包含 5 个认证端点，使用 HttpOnly Cookie session
- 在 app/main.py 中注册 admin_router，所有 /api/admin/auth/* 端点可访问

## Task Commits

Each task was committed atomically:

1. **Task 1: 在 app/database.py 中添加 users 表 + 认证函数 + WAL 模式** - `7fb5c2e` (feat)
2. **Task 2: 创建 app/router/admin.py 认证端点** - `472a6f6` (feat)
3. **Task 3: 在 app/main.py 中注册 admin 路由** - `1154d90` (feat)

## Files Created/Modified
- `app/database.py` - 新增 users 表创建、6 个认证函数（hash_password, verify_password, create_user, get_user, update_user_password, has_users）、WAL 模式、hashlib/secrets 导入
- `app/router/admin.py` - 新建 Admin API 路由，包含 login/register/logout/me/change-password 端点、session token 生成/验证、get_current_user 依赖注入
- `app/main.py` - 导入并注册 admin_router

## Decisions Made
- 复用 Streamlit 的 `SECRET_KEY="union_ai_secret"` 和 token 格式（base64(username:timestamp:sha256[:16])），确保迁移期间两个面板可共存
- 认证端点使用 `Form()` 接收参数而非 JSON body，与 FastAPI 标准的 OAuth2 密码流一致
- 所有认证函数使用 `get_db()` context manager 而非 streamlit_app/db.py 的手动连接开关模式

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 验证脚本中路由断言使用了相对路径 `/auth/login`，但 FastAPI `APIRouter` 的 routes 属性返回带前缀的完整路径 `/api/admin/auth/login`。修正了验证断言使用 `in` 包含匹配，不影响代码正确性。

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 认证基础已完成，Plan 02 可以在此基础上添加受保护的管理 API 端点（模型 CRUD、API Key 管理、用量统计等）
- get_current_user 依赖注入可直接用于 Plan 02 的所有受保护端点
- session token 与 Streamlit 面板共享同一 SECRET_KEY，两个面板可同时在线

## Self-Check: PASSED

- FOUND: app/database.py
- FOUND: app/router/admin.py
- FOUND: app/main.py
- FOUND: .planning/phases/01-admin-api/01-01-SUMMARY.md
- FOUND: 7fb5c2e (Task 1 commit)
- FOUND: 472a6f6 (Task 2 commit)
- FOUND: 1154d90 (Task 3 commit)

---
*Phase: 01-admin-api*
*Completed: 2026-04-16*
