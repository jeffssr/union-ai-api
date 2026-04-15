# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.11 - All backend API, admin UI, and launcher code

**Secondary:**
- Bash - Shell scripts for service lifecycle management (`start.sh`, `stop.sh`, `restart.sh`, `clean.sh`, `status.sh`)
- YAML - Docker Compose and supervisord configuration
- SQL (SQLite dialect) - Schema definitions and queries in database layers

## Runtime

**Environment:**
- Python 3.11 (Docker base image: `python:3.11-slim`)

**Package Manager:**
- pip (via `requirements.txt`)
- Lockfile: Not present (no `requirements.lock` or `Pipfile.lock`)

## Frameworks

**Core:**
- FastAPI 0.109.2 - Async HTTP API framework for the proxy server
- Uvicorn 0.27.1 (with `[standard]` extras) - ASGI server running FastAPI
- Streamlit 1.31.1 - Admin dashboard web UI framework

**Testing:**
- Not configured in the main branch (no test runner or test files in primary codebase)
- Gradio migration worktree has pytest-based tests (`.worktrees/gradio-migration/tests/`)

**Build/Dev:**
- Docker - Containerized deployment via `Dockerfile.clean` + `docker-compose.clean.yml`
- supervisord - Process manager running both Uvicorn and Streamlit in a single container
- Tkinter - Desktop GUI launcher (`launcher.py`)

## Key Dependencies

**Critical:**
- httpx 0.26.0 - Async HTTP client for proxying requests to upstream LLM providers. Used in `app/router/chat_final.py`, `app/router/responses_api.py`, `app/services/llm_service.py`
- tiktoken 0.5.2 - OpenAI tokenizer for counting tokens. Uses `cl100k_base` encoding. Used in `app/services/llm_service.py`
- pydantic 2.6.1 - Request/response schema validation. Used in `app/schemas.py`

**Infrastructure:**
- sqlite3 (stdlib) - Database for all persistent data. Both `app/database.py` and `streamlit_app/db.py` connect directly
- pandas 2.2.0 - Data display and Excel import/export in Streamlit admin UI
- openpyxl 3.1.2 - Excel file read/write engine for model config import/export
- python-multipart 0.0.9 - Form data parsing for FastAPI

**Note on declared but unused dependencies:**
- sqlalchemy 2.0.25 - Listed in `requirements.txt` but not imported anywhere in the codebase. Raw `sqlite3` is used instead
- aiosqlite 0.19.0 - Listed in `requirements.txt` but not imported anywhere. Synchronous `sqlite3` is used instead

## Configuration

**Environment:**
- No `.env` file detected
- Environment variables set in `docker-compose.clean.yml`:
  - `PYTHONUNBUFFERED=1`
  - `PYTHONPATH=/app`
- Database path is conditional based on OS:
  - Windows: `<project_root>/data/proxy.db`
  - Linux/Docker: `/app/data/proxy.db`

**Build:**
- `Dockerfile.clean` - Production Docker image definition
- `docker-compose.clean.yml` - Service orchestration
- `supervisord.conf` - Dual-process management (uvicorn + streamlit)
- `requirements.txt` - Python dependency manifest

**Ports:**
- 18080 (host) -> 8000 (container) - FastAPI proxy server
- 18501 (host) -> 8501 (container) - Streamlit admin UI

## Platform Requirements

**Development:**
- Python 3.11+
- pip
- (Optional) Docker Desktop for containerized testing
- (Optional) Tkinter for desktop GUI launcher

**Production:**
- Docker (Linux containers)
- Docker Compose (v1 or v2 plugin)

---

*Stack analysis: 2026-04-15*
