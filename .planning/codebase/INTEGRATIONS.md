# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**LLM Provider Proxy (Core Function):**
- Arbitrary OpenAI-compatible LLM providers - The system is a multi-model proxy that forwards requests to user-configured API endpoints
  - SDK/Client: httpx 0.26.0 (async HTTP client)
  - Auth: User-configured API keys stored in SQLite `models` table (`api_key` column)
  - Connection pattern: `app/router/chat_final.py` and `app/router/responses_api.py` use a global `httpx.AsyncClient` connection pool (`get_global_client()`) with `max_connections=100`, `max_keepalive_connections=20`, `timeout=60s`
  - Supported endpoints:
    - `POST <provider_url>/chat/completions` - Standard OpenAI Chat Completions API
    - Model replacement: The `model` field in requests is replaced with the configured `model_id` or `name`
  - Referenced providers in comments: ZhiPu (智谱), DeepSeek, OpenAI, Alibaba Cloud Model Studio (Qwen)
  - Explicit compatibility with: Codex CLI v0.80.0+, OpenAI SDK v1.60+, Cursor, Chatbox, LobeChat, Claude Code

**Responses API Compatibility Layer:**
- `app/router/responses_api.py` converts between OpenAI Responses API format and Chat Completions API format
  - Converts `input` (string or message array) to `messages`
  - Converts `tools` (function, web_search_preview, file_search, code_interpreter) to target provider format
  - Converts Chat Completions responses back to Responses API format (including streaming events)
  - Tool conversion targets: ZhiPu `web_search` format, standard `function` calling

## Data Storage

**Databases:**
- SQLite 3 (via Python stdlib `sqlite3`)
  - Connection: Direct file path, no ORM
  - Database file: `data/proxy.db` (Windows: `<project_root>/data/proxy.db`, Docker: `/app/data/proxy.db`)
  - Client: Raw `sqlite3.connect()` with `sqlite3.Row` row factory
  - Connection management: Manual open/close in `streamlit_app/db.py`, context manager pattern in `app/database.py`
  - WAL mode: Enabled in `streamlit_app/db.py` (`PRAGMA journal_mode=WAL`), not explicitly set in `app/database.py`

**Database Tables:**
- `models` - LLM provider configurations (name, api_url, api_key, model_id, limits, priority)
- `system_config` - Key-value system settings (auto_switch toggle)
- `api_keys` - Client API keys for authenticating to this proxy (`sk-` prefixed tokens)
- `call_logs` - Request/response audit log
- `daily_usage` - Per-model daily token and call count aggregation
- `users` - Admin UI user accounts (username, password_hash, salt)

**File Storage:**
- Local filesystem only - SQLite database file in `data/` directory
- Docker volume mount: `./data:/app/data`

**Caching:**
- None - No Redis, memcached, or in-memory caching layer

## Authentication & Identity

**Admin UI Auth:**
- Custom implementation in `streamlit_app/db.py` and `streamlit_app/home.py`
  - Password hashing: `hashlib.pbkdf2_hmac('sha256', ...)` with random salt, 100000 iterations
  - Session management: Streamlit `session_state` + base64-encoded auth tokens in cookies and query params
  - Token format: `base64(username:timestamp:sha256_hash[:16])`
  - Token expiry: 7 days
  - Token secret: Hardcoded string `"union_ai_secret"` in `streamlit_app/home.py` line 114

**Proxy API Auth:**
- Custom API key scheme
  - Key format: `sk-<secrets.token_urlsafe(32)>` (generated in `streamlit_app/db.py` and `app/database.py`)
  - Validation: `Authorization: Bearer <key>` header, looked up in `api_keys` table
  - Key lifecycle: Created via admin UI, soft-deleted by setting `is_active = 0`

## Monitoring & Observability

**Error Tracking:**
- None - No Sentry, Rollbar, or similar service

**Logs:**
- Python stdlib `logging` module
  - Level: INFO (configured in `app/main.py`)
  - Loggers: `uvicorn`, `app` namespace, module-level `__name__` loggers in routers and services
  - Output: stdout/stderr (captured by Docker logs)
  - No structured logging or log aggregation

**Health Check:**
- `GET /health` endpoint returns `{"status": "healthy"}`
- Docker healthcheck: `curl -f http://localhost:8000/health` every 30s

## CI/CD & Deployment

**Hosting:**
- Self-hosted Docker container
- No cloud platform deployment configured

**CI Pipeline:**
- None - No GitHub Actions, Jenkins, or other CI/CD configuration detected

**Deployment Flow:**
- Manual: `./start.sh` builds Docker image and starts container
- Docker Compose manages single service `union-ai-api`
- Image tag: `union-ai-api:latest` (local build only, no registry push configured)
- supervisord manages two processes in container:
  - `uvicorn` on port 8000 (API)
  - `streamlit` on port 8501 (Admin UI)

## Environment Configuration

**Required env vars:**
- `PYTHONUNBUFFERED=1` - Python output buffering (set in docker-compose)
- `PYTHONPATH=/app` - Module resolution (set in docker-compose)
- No secrets in environment variables - all sensitive data stored in SQLite

**Secrets location:**
- SQLite database (`data/proxy.db`): LLM provider API keys, admin user credentials, proxy API keys
- Not encrypted at rest - API keys stored in plaintext in `models.api_key` column

## Webhooks & Callbacks

**Incoming:**
- None - The system only exposes synchronous request/response endpoints

**Outgoing:**
- None - Outbound requests are synchronous proxy calls to LLM providers only

## Rate Limiting & Retry

**Built-in retry mechanism:**
- `app/router/chat_final.py` defines `exponential_backoff_retry()` with:
  - Max retries: 3
  - Base delay: 1.0s (exponential backoff: 1s, 2s, 4s)
  - Rate limit detection: HTTP 429 status, error codes `limit_burst_rate`, `rate_limit`, `too_many_requests`
  - Model switch delay: 0.5s between trying different providers

**Daily usage limits (per model):**
- `daily_token_limit` - Max tokens per day (default: 100,000)
- `daily_call_limit` - Max API calls per day (default: 1,000)
- Enforced before each request in both streaming and non-streaming paths

---

*Integration audit: 2026-04-15*
