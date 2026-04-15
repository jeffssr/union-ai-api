# Codebase Concerns

**Analysis Date:** 2026-04-15

## Tech Debt

### 1. Massive Code Duplication Between Router Files
- Issue: `app/router/chat_final.py` (592 lines) and `app/router/responses_api.py` (1036 lines) share ~80% identical logic. Both contain their own `get_global_client()`, `forward_stream()`, `forward_to_model()`, rate limit checking, call logging, usage tracking, and auto-switch loop. The Responses API version adds format conversion on top.
- Files: `app/router/chat_final.py`, `app/router/responses_api.py`
- Impact: Any bug fix or feature change must be applied twice. Inconsistencies will emerge over time. The two files already diverge in minor ways (e.g., different function signatures, different error message formats).
- Fix approach: Extract shared logic into a service layer -- connection pool management, rate limit checks, call logging, usage updates, and the auto-switch retry loop should live in `app/services/`. Router files should only handle request parsing and response format conversion.

### 2. Duplicate Database Layer (Streamlit vs FastAPI)
- Issue: `streamlit_app/db.py` (275 lines) duplicates almost every function from `app/database.py` (334 lines). Both define their own `init_db()`, `get_db_connection()`, `get_all_models()`, `create_model()`, `update_model()`, `delete_model()`, `create_api_key()`, `delete_api_key()`, `get_call_logs()`, `get_daily_stats()`, and more. They even include identical schema creation DDL.
- Files: `streamlit_app/db.py`, `app/database.py`
- Impact: Schema drift between the two copies. Bug in one does not get fixed in the other. Adding a new column requires editing two files.
- Fix approach: Have the Streamlit app import from `app.database` directly (they share the same SQLite file). Remove `streamlit_app/db.py`. The Streamlit-specific user management functions can move into `app/database.py` or a new `app/services/user_service.py`.

### 3. Dead Code in `app/services/llm_service.py`
- Issue: `app/services/llm_service.py` contains `call_model()` and `forward_to_model()` that use their own per-request `httpx.AsyncClient` (no connection pool reuse). The actual API routers (`chat_final.py`, `responses_api.py`) never import from this file -- they have their own inline forwarding logic. The schemas in `app/schemas.py` are also unused by the routers, which parse request JSON manually.
- Files: `app/services/llm_service.py`, `app/schemas.py`
- Impact: Misleading -- a developer might think `llm_service.py` is the actual service layer. The Pydantic schemas in `schemas.py` are defined but never referenced by the working code.
- Fix approach: Either integrate `llm_service.py` properly as the shared service layer (resolving concern #1), or delete it along with `schemas.py` if the current manual approach is preferred.

### 4. Unused `exponential_backoff_retry` Function
- Issue: `chat_final.py` defines `exponential_backoff_retry()` (lines 62-98) with retry logic, but it is never called. The actual retry/fallback is a manual `for` loop over models in the `chat_completions()` handler.
- Files: `app/router/chat_final.py` lines 62-98
- Impact: Dead code that adds confusion about which retry mechanism is active.
- Fix approach: Remove the unused function, or refactor the auto-switch loop to use it.

### 5. Hardcoded Beijing Timezone Everywhere
- Issue: `BEIJING_TZ` is defined independently in three places: `app/database.py`, `app/router/chat_final.py`, `app/router/responses_api.py`. All time-sensitive operations (daily usage tracking, log timestamps) use `datetime.now(BEIJING_TZ)`.
- Files: `app/database.py` line 16, `app/router/chat_final.py` line 19, `app/router/responses_api.py` line 25
- Impact: If timezone needs to change or be configurable, three files must be edited. Inconsistency risk if one is updated and others are not.
- Fix approach: Define `BEIJING_TZ` once in a shared config or constants module and import it everywhere.

## Known Bugs

### 1. `get_daily_stats()` Uses Server Local Time, Not Beijing Time
- Symptoms: Daily statistics displayed in the Streamlit dashboard may be wrong when the server runs in a non-UTC+8 timezone (e.g., Docker container defaulting to UTC).
- Files: `app/database.py` lines 321-334, `streamlit_app/db.py` lines 261-273
- Trigger: Deploy on a server whose system timezone is not UTC+8. `date.today()` uses local time, while usage tracking uses `BEIJING_TZ`. A request logged at 11pm Beijing time but 3pm UTC could be counted on different dates.
- Workaround: Only run on servers set to UTC+8.

### 2. Global HTTP Client Never Closed on Shutdown
- Symptoms: Resource leak warning on application shutdown. The lifespan handler in `app/main.py` (lines 14-17) calls `init_database()` on startup but never calls `close_global_client()` on shutdown. The `close_global_client()` function exists in `chat_final.py` but is never registered.
- Files: `app/main.py` lines 14-17, `app/router/chat_final.py` lines 43-48
- Trigger: Application shutdown (SIGTERM, Docker stop).
- Workaround: None needed in practice (OS reclaims resources), but it is incorrect.

### 3. Duplicate Global HTTP Client Instances
- Symptoms: Each router module (`chat_final.py` and `responses_api.py`) maintains its own `_global_client` variable. This means two separate connection pools exist, doubling the configured `max_connections=100` to a potential 200 connections.
- Files: `app/router/chat_final.py` line 22, `app/router/responses_api.py` line 28
- Trigger: Both routes are used simultaneously.
- Workaround: None.

### 4. Stream Response Uses `response.aiter_lines()` on Non-Streaming Response
- Symptoms: The `forward_stream()` functions in both routers call `client.post()` which waits for the full response, then attempts `response.aiter_lines()`. This means the proxy buffers the entire upstream response before streaming it to the client, defeating the purpose of streaming.
- Files: `app/router/chat_final.py` lines 291-300, `app/router/responses_api.py` lines 657-666
- Trigger: Any streaming request (`stream: true`).
- Workaround: None. For true streaming, use `client.stream("POST", ...)` context manager instead of `client.post()`.

## Security Considerations

### 1. Hardcoded Auth Secret in Streamlit App
- Risk: The token signing secret `"union_ai_secret"` is hardcoded in `streamlit_app/home.py` (lines 114, 133). Anyone with access to the source code can forge valid auth tokens.
- Files: `streamlit_app/home.py` lines 110-142
- Current mitigation: Source code is not publicly exposed (deployed in Docker).
- Recommendations: Move the secret to an environment variable. Use a proper JWT library instead of a custom HMAC scheme with a truncated hash (only 16 hex chars = 64 bits).

### 2. CORS Allows All Origins
- Risk: `allow_origins=["*"]` in `app/main.py` means any website can make requests to the API proxy. Combined with bearer token auth, this is lower risk but still allows cross-origin attacks if a token is leaked.
- Files: `app/main.py` lines 26-32
- Current mitigation: API requires `Authorization` header with valid API key.
- Recommendations: Restrict `allow_origins` to known frontend origins, or remove CORS entirely if only backend-to-backend communication is expected.

### 3. API Keys Stored in Plain Text in SQLite
- Risk: Third-party LLM provider API keys are stored unencrypted in the `models` table. The SQLite database file at `data/proxy.db` contains all provider API keys in cleartext.
- Files: `app/database.py` lines 39-55 (schema), `streamlit_app/home.py` line 577 (displayed in password field but stored plain)
- Current mitigation: `data/` is in `.gitignore`. Docker volume is local only.
- Recommendations: Encrypt API keys at rest using a master key from an environment variable. At minimum, ensure the Streamlit export-to-Excel feature (`export_models_to_excel()` in `streamlit_app/home.py` line 263) does not leak keys -- currently it exports `api_key` column.

### 4. No Rate Limiting on API Endpoints
- Risk: No rate limiting on `/v1/chat/completions` or `/v1/responses`. An attacker with a valid API key can flood requests, consuming all provider quota instantly.
- Files: `app/router/chat_final.py`, `app/router/responses_api.py`
- Current mitigation: Daily token/call limits per model, but no per-key or per-IP rate limiting.
- Recommendations: Add per-key rate limiting (e.g., slowapi or custom middleware).

### 5. Bare `except:` in Auth Token Verification
- Risk: `streamlit_app/home.py` line 141 uses a bare `except:` that silently swallows all exceptions including `SystemExit` and `KeyboardInterrupt`. This makes debugging auth failures impossible and can mask security issues.
- Files: `streamlit_app/home.py` line 141
- Current mitigation: None.
- Recommendations: Change to `except Exception:` at minimum, and log the error.

## Performance Bottlenecks

### 1. Synchronous SQLite in Async FastAPI
- Problem: All database operations in `app/database.py` use synchronous `sqlite3.connect()` and block the event loop. Each API request performs 2-5 database queries (auth check, usage check, usage update, log creation) that each block the async event loop.
- Files: `app/database.py` (entire file)
- Cause: Using synchronous `sqlite3` module instead of `aiosqlite` (which is listed in `requirements.txt` but never used).
- Improvement path: Use `aiosqlite` or run synchronous DB operations in a thread pool via `asyncio.to_thread()`.

### 2. Stream Proxy Buffers Entire Response Before Streaming
- Problem: `client.post()` downloads the full response body before `response.aiter_lines()` is called. The client experiences the full upstream latency before seeing any streamed output.
- Files: `app/router/chat_final.py` lines 291-300, `app/router/responses_api.py` lines 657-666
- Cause: Using `client.post()` instead of `client.stream()`.
- Improvement path: Use `async with client.stream("POST", ...)` for true streaming passthrough.

### 3. No Database Indexing on High-Query Columns
- Problem: The `call_logs` table has no index on `created_at` despite queries using `ORDER BY created_at DESC LIMIT`. The `daily_usage` table has no index on `usage_date` for range queries.
- Files: `app/database.py` lines 84-99 (call_logs schema), lines 101-109 (daily_usage schema)
- Cause: Schema was created without performance tuning.
- Improvement path: Add `CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON call_logs(created_at)` and similar for `daily_usage(usage_date)`.

## Fragile Areas

### 1. Model Auto-Switch Logic
- Files: `app/router/chat_final.py` lines 210-253, `app/router/responses_api.py` lines 562-614
- Why fragile: The auto-switch loop iterates models with `asyncio.sleep(0.5)` delays between attempts. If all models fail, it returns a generic error. The logic is duplicated in both routers with subtle differences. Any change to the fallback strategy must be kept in sync.
- Safe modification: Extract the auto-switch loop into a shared service function that accepts a callable operation.
- Test coverage: No tests exist on the main branch for the auto-switch behavior.

### 2. Stream Token Parsing
- Files: `app/router/chat_final.py` lines 309-335, `app/router/responses_api.py` lines 717-741
- Why fragile: Token counting for streaming responses relies on parsing JSON from SSE chunks, looking for a `usage` field that may or may not be present depending on the upstream provider. If no `usage` data is received, tokens are recorded as 0 but a call count is still incremented. The parsing uses bare `try/except: pass` which silently ignores malformed chunks.
- Safe modification: Add explicit error handling for chunk parsing failures instead of silently passing.

### 3. Database Migration via Column Detection
- Files: `app/database.py` lines 57-62, 112-115, `streamlit_app/db.py` lines 42-47, 89-92
- Why fragile: Schema migrations use `PRAGMA table_info()` to check for column existence and `ALTER TABLE ADD COLUMN`. This approach does not handle column type changes, constraint changes, or index creation. Two independent migration paths (one per DB module) can diverge.
- Safe modification: Use a proper migration tool (Alembic) or at minimum centralize the migration logic.

## Scaling Limits

### 1. SQLite Concurrency
- Current capacity: Single writer, multiple readers via WAL mode (enabled in Streamlit's `db.py` but NOT in the FastAPI `app/database.py`).
- Limit: Under concurrent write load (multiple API requests updating usage simultaneously), SQLite will encounter `database is locked` errors. The `check_same_thread=False` flag suppresses Python's thread safety check but does not make SQLite thread-safe.
- Scaling path: For single-instance deployment, ensure WAL mode is enabled in `app/database.py` (currently missing). For multi-instance deployment, migrate to PostgreSQL.

### 2. Single-Process Deployment
- Current capacity: One Uvicorn process, one Streamlit process, managed by supervisord.
- Limit: No horizontal scaling. A single Uvicorn process handles all API requests.
- Scaling path: Add Uvicorn `--workers N` for multi-process, or use an external load balancer with multiple containers.

### 3. No Call Log Cleanup
- Current capacity: `call_logs` table grows unbounded. The only query uses `LIMIT ? OFFSET ?` but there is no retention policy or cleanup job.
- Limit: Over months of operation, the table will grow to millions of rows, slowing queries and increasing database file size.
- Scaling path: Add a scheduled cleanup job that purges logs older than N days, or archive to a separate file.

## Dependencies at Risk

### 1. Streamlit as Admin UI
- Risk: Streamlit is designed for data science dashboards, not production admin panels. It adds significant overhead (large dependency tree, WebSocket-based reactivity, slow page loads) for what is essentially a CRUD management interface.
- Impact: Large Docker image size, slow UI response times, limited customization (as documented in the project's own Gradio migration history).
- Migration plan: The project has already explored Gradio migration (see `.claude/worktrees/feature+gradio-migration/`). A lighter alternative would be a simple FastAPI + Jinja2 template or a separate lightweight frontend.

### 2. Pinned but Potentially Outdated Dependencies
- Risk: All dependencies in `requirements.txt` are pinned to specific versions from early 2024 (e.g., `fastapi==0.109.2`, `streamlit==1.31.1`, `httpx==0.26.0`). These are over a year old and may have security patches.
- Impact: Missing security fixes and bug fixes.
- Migration plan: Periodically update dependencies and test. Consider using a range pinning strategy (e.g., `fastapi>=0.109.2,<1.0`).

### 3. `aiosqlite` Listed but Unused
- Risk: `aiosqlite==0.19.0` is in `requirements.txt` but never imported anywhere in the codebase. It adds unnecessary image size.
- Impact: Bloat, developer confusion about whether async DB is used.
- Migration plan: Either use it (see Performance concern #1) or remove it from requirements.

## Missing Critical Features

### 1. No Authentication on Admin API Routes
- Problem: The FastAPI app has no admin routes for model/key management -- all management is done through the Streamlit app which has its own user auth. But the Streamlit app directly accesses the database without any API-level auth. If someone adds admin API routes later, there is no auth middleware to protect them.
- Blocks: Cannot add programmatic management via API.

### 2. No Request Validation
- Problem: Both routers parse the request body as raw JSON (`await request.json()`) without any schema validation. The Pydantic schemas in `app/schemas.py` exist but are unused. Malformed requests will fail at the upstream provider, not at the proxy.
- Blocks: Cannot provide helpful error messages to clients for invalid requests.

### 3. No HTTPS/TLS Configuration
- Problem: No TLS termination configuration anywhere in the codebase. The Docker setup exposes plain HTTP ports.
- Blocks: Production deployment requires a reverse proxy (nginx/caddy) for TLS.

## Test Coverage Gaps

### 1. No Tests on Main Branch
- What's not tested: Everything. There are zero test files on the main branch. Tests exist only in the `.claude/worktrees/feature+gradio-migration/` branch covering `test_db.py`, `test_auth.py`, `test_call_logs.py`, `test_dashboard.py`, `test_model_config.py`.
- Files: All source files in `app/` and `streamlit_app/`
- Risk: Any change can break existing functionality without detection.
- Priority: High -- at minimum, add tests for the core proxy logic (request forwarding, auto-switch, usage tracking).

### 2. No Integration Tests for Streaming
- What's not tested: The streaming response path (SSE parsing, token extraction, format conversion for Responses API). This is the most complex and fragile part of the codebase.
- Files: `app/router/chat_final.py` lines 255-435, `app/router/responses_api.py` lines 617-886
- Risk: Changes to streaming logic can silently break token counting or response format.
- Priority: High.

### 3. No Tests for Responses API Format Conversion
- What's not tested: `convert_input_to_messages()`, `convert_tools_for_chat_completions()`, `convert_chat_completion_to_response()`, `convert_chat_completion_stream_chunk()`. These are complex transformation functions with many edge cases.
- Files: `app/router/responses_api.py` lines 64-435
- Risk: A client relying on specific Responses API fields gets incorrect data.
- Priority: Medium.

---

*Concerns audit: 2026-04-15*
