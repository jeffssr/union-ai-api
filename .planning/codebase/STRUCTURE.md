# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
union-ai-api/
├── app/                        # FastAPI API 后端（核心服务）
│   ├── main.py                 # FastAPI 应用入口，路由注册，lifespan
│   ├── database.py             # SQLite 数据访问层（API 端使用）
│   ├── schemas.py              # Pydantic 数据模型（未实际引用）
│   ├── router/                 # API 路由模块
│   │   ├── __init__.py         # 空文件
│   │   ├── chat_final.py       # Chat Completions API 端点（/v1/chat/completions）
│   │   └── responses_api.py    # Responses API 兼容端点（/v1/responses）
│   └── services/               # 服务层
│       ├── __init__.py         # 空文件
│       └── llm_service.py      # LLM 调用服务（token 计数、模型调用）- 未被路由引用
├── streamlit_app/              # Streamlit 管理面板
│   ├── __init__.py             # 空文件
│   ├── home.py                 # 管理面板主页面（单文件应用）
│   └── db.py                   # 管理面板数据库访问层（独立于 app/database.py）
├── data/                       # 运行时数据（.gitignore 排除）
│   └── proxy.db                # SQLite 数据库文件
├── .github/workflows/          # CI/CD
│   └── docker-build.yml        # Docker Hub 构建推送流水线
├── api/                        # 空目录（预留）
├── docs/                       # 文档
├── .claude/                    # Claude 配置和 worktree
├── .worktrees/                 # Git worktree（Gradio 迁移分支）
├── .superpowers/               # Superpowers 插件数据
├── .planning/                  # GSD 规划文档
├── requirements.txt            # Python 依赖
├── Dockerfile.clean            # 生产 Docker 镜像定义
├── docker-compose.clean.yml    # Docker Compose 编排配置
├── supervisord.conf            # 进程管理配置（uvicorn + streamlit）
├── launcher.py                 # tkinter 桌面启动器（本地管理工具）
├── start.sh                    # 服务启动脚本
├── stop.sh                     # 服务停止脚本
├── restart.sh                  # 服务重启脚本
├── clean.sh                    # 清理脚本（删除容器和镜像）
├── status.sh                   # 服务状态查看脚本
├── .gitignore                  # Git 忽略规则
├── README.md                   # 项目说明
├── README_DEPLOYMENT.md        # 部署文档
├── QUICKSTART.md               # 快速开始指南
├── DESIGN.md                   # 设计文档
├── DISCLAIMER.md               # 免责声明
└── LICENSE                     # 开源许可证
```

## Directory Purposes

**app/：**
- Purpose: FastAPI API 后端核心代码
- Contains: 应用入口、数据库访问、路由处理、服务层
- Key files: `app/main.py`（入口），`app/router/chat_final.py`（592 行，核心路由），`app/router/responses_api.py`（1036 行，Responses API 兼容），`app/database.py`（334 行，数据层）

**app/router/：**
- Purpose: API 端点定义
- Contains: FastAPI APIRouter 实例，每个文件对应一组相关端点
- Key files: `chat_final.py`（`/v1/chat/completions`），`responses_api.py`（`/v1/responses`）

**app/services/：**
- Purpose: 业务逻辑服务（设计意图）
- Contains: `llm_service.py`（token 计数和模型调用封装）
- Note: 当前路由代码直接在 router 中实现转发逻辑，`llm_service.py` 的 `forward_to_model` 使用 Pydantic schema（与 router 中直接操作 raw JSON 的方式不一致），未被实际路由引用

**streamlit_app/：**
- Purpose: 管理面板 Web UI
- Contains: 单页面 Streamlit 应用，独立的数据库访问层
- Key files: `home.py`（689 行，所有 UI 页面），`db.py`（275 行，管理面板专用数据访问）

**data/：**
- Purpose: 运行时数据存储
- Contains: `proxy.db`（SQLite 数据库文件）
- Note: 被 `.gitignore` 排除，通过 Docker volume 挂载持久化

## Key File Locations

**Entry Points:**
- `app/main.py`: FastAPI 应用入口，lifespan 管理，路由注册
- `streamlit_app/home.py`: Streamlit 管理面板入口

**Configuration:**
- `requirements.txt`: Python 依赖声明
- `Dockerfile.clean`: 生产环境 Docker 镜像
- `docker-compose.clean.yml`: 容器编排（端口映射 18080:8000, 18501:8501）
- `supervisord.conf`: 双进程管理（uvicorn + streamlit）

**Core Logic:**
- `app/router/chat_final.py`: Chat Completions 代理核心（鉴权、模型选择、流式/非流式转发）
- `app/router/responses_api.py`: Responses API 兼容层（格式转换 + 代理转发）
- `app/database.py`: API 端数据访问（models、api_keys、daily_usage、call_logs）
- `streamlit_app/db.py`: 管理面板数据访问（含 users 表管理）

**Shell Operations:**
- `start.sh`: 一键启动（Docker 检查、数据目录创建、容器启动）
- `stop.sh`: 停止容器
- `restart.sh`: 重启容器
- `status.sh`: 查看服务状态
- `clean.sh`: 清理容器和镜像

**CI/CD:**
- `.github/workflows/docker-build.yml`: GitHub Actions Docker 构建推送到 Docker Hub

**Deployment:**
- `launcher.py`: tkinter 桌面 GUI 启动器（本地开发用）

## Naming Conventions

**Files:**
- Python 模块使用 snake_case：`chat_final.py`、`llm_service.py`、`database.py`
- Docker 相关文件带 `.clean` 后缀：`Dockerfile.clean`、`docker-compose.clean.yml`
- Shell 脚本使用简单命令词：`start.sh`、`stop.sh`、`restart.sh`

**Directories:**
- Python 包使用 snake_case：`app/`、`streamlit_app/`
- 特殊目录使用点前缀：`.claude/`、`.worktrees/`、`.planning/`

## Where to Add New Code

**New API Endpoint:**
- 路由定义：`app/router/` 下新建模块文件，导出 `router = APIRouter()`
- 在 `app/main.py` 中 `app.include_router(new_router)` 注册

**New LLM Provider Support:**
- 消息格式转换：在 `app/router/chat_final.py` 的 `convert_messages()` 函数中添加格式处理
- 工具格式转换：在 `app/router/responses_api.py` 的 `convert_tools_for_chat_completions()` 中添加类型映射

**New Database Table:**
- API 端：在 `app/database.py` 的 `init_database()` 中添加 `CREATE TABLE IF NOT EXISTS`
- 管理面板端：在 `streamlit_app/db.py` 的 `init_db()` 中同步添加（两个文件需要手动保持一致）

**New Admin Page:**
- 在 `streamlit_app/home.py` 的 `pages` 字典中添加新页面名称和标识
- 在同一文件中添加对应的 `elif page == "new_page":` 处理分支

**New Pydantic Schema:**
- 在 `app/schemas.py` 中定义（注意：当前 router 未引用此文件）

**Shared Utility:**
- 放在 `app/services/` 目录下，但目前该目录功能未充分使用

## Special Directories

**data/：**
- Purpose: SQLite 数据库文件存储
- Generated: Yes（运行时由应用创建 `proxy.db`）
- Committed: No（`.gitignore` 排除）
- Docker: 通过 volume 挂载 `./data:/app/data`

**.worktrees/：**
- Purpose: Git worktree，用于并行开发分支
- Generated: Yes（`git worktree add` 命令创建）
- Committed: No（`.gitignore` 排除）
- Current: 包含 `gradio-migration` 分支

**.claude/worktrees/：**
- Purpose: Claude 使用的 worktree 副本
- Contains: Gradio 迁移分支的完整代码副本，含 `gradio_app/` 和 `tests/` 目录

**api/：**
- Purpose: 空目录（预留，用途不明）
- Committed: Yes

**docs/：**
- Purpose: 项目文档
- Contains: superpowers 相关的计划和规格文档

---

*Structure analysis: 2026-04-15*
