# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Reverse Proxy + Admin Dashboard (monolith deployed as single Docker container)

**Key Characteristics:**
- LLM API 反向代理：接收 OpenAI 兼容请求，转发到配置的第三方 LLM 提供商
- 多模型故障切换：按优先级自动切换模型，支持速率限制检测和指数退避重试
- 双协议兼容：同时支持 Chat Completions API (`/v1/chat/completions`) 和 Responses API (`/v1/responses`)
- SQLite 直连：无 ORM，原始 SQL，同步数据库访问（FastAPI 同步调用 SQLite）
- 管理面板独立应用：Streamlit 作为独立进程运行，共享同一 SQLite 数据库

## Layers

**API 层（Router）：**
- Purpose: 接收 HTTP 请求，鉴权，参数校验，选择路由
- Location: `app/router/`
- Contains: FastAPI 路由处理函数，请求解析，流式/非流式响应生成
- Depends on: `app/database.py`（模型/密钥/用量查询），`httpx`（上游 API 调用）
- Used by: 外部客户端（Codex、OpenAI SDK 等）

**数据访问层（Database）：**
- Purpose: SQLite 表的 CRUD 操作，schema 管理
- Location: `app/database.py`（API 端使用），`streamlit_app/db.py`（管理面板使用）
- Contains: 表创建、数据查询/写入函数，全部是同步的纯函数
- Depends on: `sqlite3` 标准库
- Used by: `app/router/` 和 `streamlit_app/home.py`

**LLM 转发层（Forwarding）：**
- Purpose: 将请求转发到第三方 LLM API，处理流式和非流式响应
- Location: `app/router/chat_final.py`（forward_to_model, forward_stream），`app/router/responses_api.py`（forward_to_model_responses, forward_stream_responses）
- Contains: httpx 异步客户端调用，响应格式转换，token 计数，用量记录
- Depends on: `httpx`，`app/database.py`
- Used by: 路由处理函数

**管理面板层（Streamlit UI）：**
- Purpose: 提供 Web UI 进行模型配置、API Key 管理、用量查看
- Location: `streamlit_app/home.py`
- Contains: Streamlit 页面、表单、数据展示，内嵌 CSS 样式
- Depends on: `streamlit_app/db.py`
- Used by: 管理员用户（通过浏览器访问 :18501）

**Schema 层（Pydantic Models）：**
- Purpose: 定义请求/响应数据结构
- Location: `app/schemas.py`
- Contains: ChatCompletionRequest、Message、Usage 等 Pydantic 模型
- Depends on: `pydantic`
- Used by: 未被实际使用（router 直接解析 raw JSON）

## Data Flow

**Chat Completions 请求流：**

1. 客户端发送 POST `/v1/chat/completions`，携带 `Authorization: Bearer sk-xxx`
2. Router 从 Header 提取 API Key，查询 `api_keys` 表验证
3. 查询 `system_config` 获取自动切换状态
4. 若自动切换开启：按优先级遍历 `models` 表中所有活跃模型
5. 对每个模型：检查日用量限额（`daily_usage` 表）-> 构建 payload -> httpx 异步 POST 到上游 API
6. 成功则记录调用日志（`call_logs`）和更新日用量，返回响应
7. 失败则尝试下一个模型（带 0.5s 延迟）
8. 所有模型失败则返回 502

**Responses API 请求流：**

1. 客户端发送 POST `/v1/responses`
2. 鉴权流程同上
3. 将 Responses API 格式转换为 Chat Completions 格式（input -> messages，tools 格式转换等）
4. 转发到上游 API
5. 将 Chat Completions 响应转换回 Responses API 格式返回

**管理面板数据流：**

1. 管理员访问 Streamlit UI（:18501），登录/注册
2. 操作模型配置、API Key、查看统计
3. Streamlit 直接读写同一 SQLite 文件（`data/proxy.db`）

**State Management:**
- 全局状态：SQLite 数据库（`data/proxy.db`），通过文件锁协调并发
- 全局 HTTP 客户端连接池：`_global_client` 模块级变量，在 `chat_final.py` 和 `responses_api.py` 中各自独立维护
- Session 状态：Streamlit 使用 `st.session_state` 管理页面导航和登录状态

## Key Abstractions

**模型配置（Model Config）：**
- Purpose: 描述一个上游 LLM 提供商的连接信息和限额
- Examples: `app/database.py` 中 `models` 表（第 39-55 行）
- Pattern: 字典对象（从 SQLite Row 转换），包含 `config_id`、`api_url`、`api_key`、`model_id`、`daily_token_limit`、`daily_call_limit`、`priority` 等字段

**API Key：**
- Purpose: 客户端鉴权凭据，格式 `sk-{random}`，独立于上游 API Key
- Examples: `app/database.py` 中 `api_keys` 表（第 81-88 行）
- Pattern: 字典对象，包含 `key_id`、`api_key`、`name`、`is_active`

**自动切换策略：**
- Purpose: 当某个模型不可用（限额耗尽、API 错误）时自动尝试下一个
- Examples: `app/router/chat_final.py` 第 210-253 行
- Pattern: 优先级排序遍历，带延迟的顺序 fallback

**格式转换器（Responses API <-> Chat Completions）：**
- Purpose: 将 OpenAI 新版 Responses API 请求/响应转为旧版 Chat Completions 格式
- Examples: `app/router/responses_api.py` 第 64-435 行（多个 convert_* 函数）
- Pattern: 纯函数转换，无状态

## Entry Points

**FastAPI API 服务：**
- Location: `app/main.py`
- Triggers: uvicorn 启动（supervisord 管理）
- Responsibilities: 注册路由、CORS 配置、lifespan 中初始化数据库
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

**Streamlit 管理面板：**
- Location: `streamlit_app/home.py`
- Triggers: streamlit 启动（supervisord 管理）
- Responsibilities: 用户认证、模型管理、API Key 管理、用量查看、配置导入导出
- Command: `streamlit run streamlit_app/home.py --server.port 8501 --server.address 0.0.0.0`

**桌面启动器：**
- Location: `launcher.py`
- Triggers: 手动运行 `python launcher.py`
- Responsibilities: tkinter GUI，管理 Docker 容器的启停
- Note: 仅用于本地开发/管理，不参与生产容器

**Shell 脚本：**
- `start.sh`：Docker Compose 启动流程（检查 Docker、创建数据目录、启动容器）
- `stop.sh`：停止容器
- `restart.sh`：重启容器
- `clean.sh`：清理容器和镜像

## Error Handling

**Strategy:** 逐层错误捕获，最终返回统一 JSON 错误格式

**Patterns:**
- 路由层捕获所有异常，返回 `{"error": {"message": ..., "type": "api_error"}}` 格式的 JSONResponse
- httpx 超时/连接错误被捕获并转化为标准错误返回
- 所有失败的 API 调用记录到 `call_logs` 表（status="failed"）
- 流式响应中错误通过 SSE 事件 `response.failed` 传递给客户端
- Streamlit 面板通过 `st.error()` 显示错误信息
- 指数退避重试机制（`exponential_backoff_retry`）定义在 `chat_final.py` 第 62-98 行，但在当前代码中未被调用

## Cross-Cutting Concerns

**Logging:** Python 标准 `logging` 模块，配置 INFO 级别，按模块命名 `logging.getLogger(__name__)`。无结构化日志或日志聚合。

**Validation:** FastAPI 自带的 HTTPException 用于鉴权和参数错误。请求体通过 `await request.json()` 手动解析（未使用 Pydantic schema 校验）。`app/schemas.py` 定义了 schema 但实际未被引用。

**Authentication:** 自定义 API Key 机制。客户端使用 `sk-{random}` 格式的 key，通过 `Authorization: Bearer` 头传递。管理面板使用独立的用户名/密码认证系统（PBKDF2 哈希，存储在 `users` 表），通过 cookie + query param 维持会话。

**CORS:** 完全开放（`allow_origins=["*"]`），适用于代理场景。

---

*Architecture analysis: 2026-04-15*
