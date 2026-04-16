<!-- GSD:project-start source:PROJECT.md -->
## Project

**Union AI API - 前端 UI 重构**

LLM API 反向代理服务（Union AI API）的管理面板 UI 重构项目。将现有 Streamlit 管理面板替换为基于 React + Tailwind CSS 的独立前端应用，按照 MiniMax 风格设计系统（DESIGN.md）实现高度定制化的 UI。项目只涉及前端层重构，后端 API、业务逻辑和数据库不做任何调整。

**Core Value:** 管理面板 UI 视觉效果达到 DESIGN.md 定义的设计标准，同时完整保留现有 Streamlit 面板的所有功能。

### Constraints

- **Tech Stack**: React + Tailwind CSS（前端），复用现有 FastAPI + SQLite（后端）
- **Deployment**: 单 Docker 容器，React 构建产物由 FastAPI 提供静态文件服务，移除 Streamlit 进程
- **Design**: 严格遵循 DESIGN.md 设计规范
- **Compatibility**: 保留现有 API Key 认证机制，用户表结构和 session 逻辑
- **Port**: 统一到原 FastAPI 端口（18080），不再需要独立的 Streamlit 端口
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.11 - All backend API, admin UI, and launcher code
- Bash - Shell scripts for service lifecycle management (`start.sh`, `stop.sh`, `restart.sh`, `clean.sh`, `status.sh`)
- YAML - Docker Compose and supervisord configuration
- SQL (SQLite dialect) - Schema definitions and queries in database layers
## Runtime
- Python 3.11 (Docker base image: `python:3.11-slim`)
- pip (via `requirements.txt`)
- Lockfile: Not present (no `requirements.lock` or `Pipfile.lock`)
## Frameworks
- FastAPI 0.109.2 - Async HTTP API framework for the proxy server
- Uvicorn 0.27.1 (with `[standard]` extras) - ASGI server running FastAPI
- Streamlit 1.31.1 - Admin dashboard web UI framework
- Not configured in the main branch (no test runner or test files in primary codebase)
- Gradio migration worktree has pytest-based tests (`.worktrees/gradio-migration/tests/`)
- Docker - Containerized deployment via `Dockerfile.clean` + `docker-compose.clean.yml`
- supervisord - Process manager running both Uvicorn and Streamlit in a single container
- Tkinter - Desktop GUI launcher (`launcher.py`)
## Key Dependencies
- httpx 0.26.0 - Async HTTP client for proxying requests to upstream LLM providers. Used in `app/router/chat_final.py`, `app/router/responses_api.py`, `app/services/llm_service.py`
- tiktoken 0.5.2 - OpenAI tokenizer for counting tokens. Uses `cl100k_base` encoding. Used in `app/services/llm_service.py`
- pydantic 2.6.1 - Request/response schema validation. Used in `app/schemas.py`
- sqlite3 (stdlib) - Database for all persistent data. Both `app/database.py` and `streamlit_app/db.py` connect directly
- pandas 2.2.0 - Data display and Excel import/export in Streamlit admin UI
- openpyxl 3.1.2 - Excel file read/write engine for model config import/export
- python-multipart 0.0.9 - Form data parsing for FastAPI
- sqlalchemy 2.0.25 - Listed in `requirements.txt` but not imported anywhere in the codebase. Raw `sqlite3` is used instead
- aiosqlite 0.19.0 - Listed in `requirements.txt` but not imported anywhere. Synchronous `sqlite3` is used instead
## Configuration
- No `.env` file detected
- Environment variables set in `docker-compose.clean.yml`:
- Database path is conditional based on OS:
- `Dockerfile.clean` - Production Docker image definition
- `docker-compose.clean.yml` - Service orchestration
- `supervisord.conf` - Dual-process management (uvicorn + streamlit)
- `requirements.txt` - Python dependency manifest
- 18080 (host) -> 8000 (container) - FastAPI proxy server
- 18501 (host) -> 8501 (container) - Streamlit admin UI
## Platform Requirements
- Python 3.11+
- pip
- (Optional) Docker Desktop for containerized testing
- (Optional) Tkinter for desktop GUI launcher
- Docker (Linux containers)
- Docker Compose (v1 or v2 plugin)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language
- **Primary:** Python 3.11（基于 Dockerfile `FROM python:3.11-slim`）
- **注释语言:** 中文注释为主，专有术语保留英文（如 FastAPI、API Key、Token）
- **字符串:** 所有面向用户的文本使用中文
## Naming Patterns
- 模块使用 `snake_case`：`chat_final.py`、`llm_service.py`、`responses_api.py`
- 包使用 `snake_case` 目录：`app/router/`、`app/services/`、`streamlit_app/`
- 测试文件前缀 `test_`：`test_auth.py`、`test_db.py`、`test_call_logs.py`（仅存在于 worktree 分支）
- 使用 `snake_case`：`get_db_connection()`、`forward_to_model()`、`create_call_log()`
- 工具/辅助函数使用动词前缀：`get_*`、`create_*`、`update_*`、`delete_*`、`convert_*`
- 布尔判断函数：`is_rate_limit_error()`、`has_users()`、`verify_password()`
- 类方法：`snake_case`，同函数命名
- 使用 `snake_case`：`api_key`、`config_id`、`model_name`
- 常量使用 `UPPER_SNAKE_CASE` 模块级定义：`BEIJING_TZ`、`MAX_RETRIES`、`MODEL_SWITCH_DELAY`、`RATE_LIMIT_STATUS_CODES`、`DATABASE_PATH`
- 返回值字典键使用 `snake_case`：`{"status": "success", "response": ...}`
- Pydantic Model 使用 `PascalCase`：`Message`、`ChatCompletionRequest`、`Usage`、`Choice`
- 测试类使用 `PascalCase` + `Test` 前缀：`TestUserAuth`、`TestModels`、`TestApiKeys`
- 函数参数使用 `snake_case`
- 类型注解使用标准库 `typing`：`Optional[str]`、`List[dict]`、`Dict[str, Any]`
## Code Style
- 无 formatter 工具配置（无 black、ruff、autopep8 配置文件）
- 缩进：4 空格
- 行宽：无严格限制，部分行超过 120 字符
- 字符串：双引号 `"` 为主，单引号 `'` 在 SQL 和部分 dict 中使用
- 尾部逗号：不定
- 无 linter 配置（无 flake8、pylint、ruff、mypy 配置文件）
- 无 pre-commit hooks 配置
- 函数签名使用类型注解（部分文件）：
- Pydantic models 完整类型注解（`app/schemas.py`）
- 部分函数缺少返回类型注解（如 `forward_stream`、`forward_to_model`）
## Import Organization
- 某些文件在函数内部延迟导入：`import uuid`、`import secrets`（见 `app/database.py` 第 231、293 行）
- 无 `__all__` 导出控制
## Error Handling
## Logging
- `logger.info()`：请求接收、转发目标、响应状态、模型切换
- `logger.warning()`：限额预警、限流重试、不支持的 tools
- `logger.error()`：请求失败、异常、超时
- `logger.debug()`：仅在 `app/services/llm_service.py` 中使用（payload 详情）
- 中文描述 + 变量值：`f"收到请求 - model: {model}, stream: {stream}"`
- 错误截断：`error_text[:500]`、`str(e)[:1000]`
## Comments
- 中文行内注释，以 `#` 开头：`# 根据环境选择数据库路径`
- 模块级 docstring 使用三引号：`"""完全绕过 Pydantic 的 chat completions 实现"""`
- 函数 docstring 使用三引号描述功能，部分包含参数说明
- 中文注释为主
## Function Design
- 函数普遍较长：`chat_completions()` 约 90 行、`forward_stream()` 约 130 行、`responses_api()` 约 180 行
- 存在深层嵌套：`forward_stream()` 内 `generate()` 异步生成器嵌套 4-5 层
- 路由处理函数：`request: Request, authorization: Optional[str] = Header(None)`
- 转发函数：`(model_config: dict, request_body: dict, request_id: str, api_key_record: dict)`
- 数据库函数：使用 `dict` 传参（`model_data: dict`、`log_data: dict`）或展开参数列表
- 路由函数返回 `JSONResponse` 或 `StreamingResponse`
- 转发函数返回 status 字典：`{"status": "success/error", ...}`
- 数据库查询函数返回 `Optional[dict]`、`List[dict]`、`dict`
## Module Design
- 无 `__all__` 定义
- `__init__.py` 文件为空（`app/router/__init__.py`、`app/services/__init__.py`）
- 直接通过模块路径导入：`from app.database import get_model_by_priority, ...`
- `app/router/` — API 路由处理，每个文件一个 `APIRouter()` 实例
- `app/services/` — 业务逻辑（token 计数、API 调用）
- `app/database.py` — 数据访问层，纯函数式（无 ORM）
- `app/schemas.py` — Pydantic 请求/响应模型定义
- `streamlit_app/` — 管理后台 UI（独立应用，直接操作数据库）
## API Design Conventions
- OpenAI 兼容路径：`/v1/chat/completions`、`/v1/responses`
- 兼容路径（无前缀）：`/responses`
- 健康检查：`/health`
- Bearer Token 方式：`authorization: Optional[str] = Header(None)`
- 手动解析：`api_key = authorization.replace("Bearer ", "").strip()`
- 成功：`JSONResponse(content=data)`
- 错误：`{"error": {"message": "...", "type": "api_error"}}`
## Database Conventions
- 使用 `sqlite3.Row` 的 `row_factory` 实现行字典化
- 所有查询使用参数化 `?` 占位符（防止 SQL 注入）
- 返回 `[dict(row) for row in rows]` 统一格式
- Schema 迁移使用 `PRAGMA table_info` + `ALTER TABLE` 增量方式
## Duplicated Patterns
- 全局 HTTP 客户端管理（`_global_client`、`get_global_client()`）
- 速率限制常量和判断函数（`RATE_LIMIT_STATUS_CODES`、`is_rate_limit_error()`）
- 转发函数结构（`forward_stream` / `forward_to_model` / `forward_stream_responses` / `forward_to_model_responses`）
- 限流检查逻辑
- 错误处理和日志记录模式
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- LLM API 反向代理：接收 OpenAI 兼容请求，转发到配置的第三方 LLM 提供商
- 多模型故障切换：按优先级自动切换模型，支持速率限制检测和指数退避重试
- 双协议兼容：同时支持 Chat Completions API (`/v1/chat/completions`) 和 Responses API (`/v1/responses`)
- SQLite 直连：无 ORM，原始 SQL，同步数据库访问（FastAPI 同步调用 SQLite）
- 管理面板独立应用：Streamlit 作为独立进程运行，共享同一 SQLite 数据库
## Layers
- Purpose: 接收 HTTP 请求，鉴权，参数校验，选择路由
- Location: `app/router/`
- Contains: FastAPI 路由处理函数，请求解析，流式/非流式响应生成
- Depends on: `app/database.py`（模型/密钥/用量查询），`httpx`（上游 API 调用）
- Used by: 外部客户端（Codex、OpenAI SDK 等）
- Purpose: SQLite 表的 CRUD 操作，schema 管理
- Location: `app/database.py`（API 端使用），`streamlit_app/db.py`（管理面板使用）
- Contains: 表创建、数据查询/写入函数，全部是同步的纯函数
- Depends on: `sqlite3` 标准库
- Used by: `app/router/` 和 `streamlit_app/home.py`
- Purpose: 将请求转发到第三方 LLM API，处理流式和非流式响应
- Location: `app/router/chat_final.py`（forward_to_model, forward_stream），`app/router/responses_api.py`（forward_to_model_responses, forward_stream_responses）
- Contains: httpx 异步客户端调用，响应格式转换，token 计数，用量记录
- Depends on: `httpx`，`app/database.py`
- Used by: 路由处理函数
- Purpose: 提供 Web UI 进行模型配置、API Key 管理、用量查看
- Location: `streamlit_app/home.py`
- Contains: Streamlit 页面、表单、数据展示，内嵌 CSS 样式
- Depends on: `streamlit_app/db.py`
- Used by: 管理员用户（通过浏览器访问 :18501）
- Purpose: 定义请求/响应数据结构
- Location: `app/schemas.py`
- Contains: ChatCompletionRequest、Message、Usage 等 Pydantic 模型
- Depends on: `pydantic`
- Used by: 未被实际使用（router 直接解析 raw JSON）
## Data Flow
- 全局状态：SQLite 数据库（`data/proxy.db`），通过文件锁协调并发
- 全局 HTTP 客户端连接池：`_global_client` 模块级变量，在 `chat_final.py` 和 `responses_api.py` 中各自独立维护
- Session 状态：Streamlit 使用 `st.session_state` 管理页面导航和登录状态
## Key Abstractions
- Purpose: 描述一个上游 LLM 提供商的连接信息和限额
- Examples: `app/database.py` 中 `models` 表（第 39-55 行）
- Pattern: 字典对象（从 SQLite Row 转换），包含 `config_id`、`api_url`、`api_key`、`model_id`、`daily_token_limit`、`daily_call_limit`、`priority` 等字段
- Purpose: 客户端鉴权凭据，格式 `sk-{random}`，独立于上游 API Key
- Examples: `app/database.py` 中 `api_keys` 表（第 81-88 行）
- Pattern: 字典对象，包含 `key_id`、`api_key`、`name`、`is_active`
- Purpose: 当某个模型不可用（限额耗尽、API 错误）时自动尝试下一个
- Examples: `app/router/chat_final.py` 第 210-253 行
- Pattern: 优先级排序遍历，带延迟的顺序 fallback
- Purpose: 将 OpenAI 新版 Responses API 请求/响应转为旧版 Chat Completions 格式
- Examples: `app/router/responses_api.py` 第 64-435 行（多个 convert_* 函数）
- Pattern: 纯函数转换，无状态
## Entry Points
- Location: `app/main.py`
- Triggers: uvicorn 启动（supervisord 管理）
- Responsibilities: 注册路由、CORS 配置、lifespan 中初始化数据库
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Location: `streamlit_app/home.py`
- Triggers: streamlit 启动（supervisord 管理）
- Responsibilities: 用户认证、模型管理、API Key 管理、用量查看、配置导入导出
- Command: `streamlit run streamlit_app/home.py --server.port 8501 --server.address 0.0.0.0`
- Location: `launcher.py`
- Triggers: 手动运行 `python launcher.py`
- Responsibilities: tkinter GUI，管理 Docker 容器的启停
- Note: 仅用于本地开发/管理，不参与生产容器
- `start.sh`：Docker Compose 启动流程（检查 Docker、创建数据目录、启动容器）
- `stop.sh`：停止容器
- `restart.sh`：重启容器
- `clean.sh`：清理容器和镜像
## Error Handling
- 路由层捕获所有异常，返回 `{"error": {"message": ..., "type": "api_error"}}` 格式的 JSONResponse
- httpx 超时/连接错误被捕获并转化为标准错误返回
- 所有失败的 API 调用记录到 `call_logs` 表（status="failed"）
- 流式响应中错误通过 SSE 事件 `response.failed` 传递给客户端
- Streamlit 面板通过 `st.error()` 显示错误信息
- 指数退避重试机制（`exponential_backoff_retry`）定义在 `chat_final.py` 第 62-98 行，但在当前代码中未被调用
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
