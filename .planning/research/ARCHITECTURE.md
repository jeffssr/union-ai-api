# Architecture Research

**Domain:** React Admin Panel + FastAPI Backend Integration
**Researched:** 2026-04-15
**Confidence:** HIGH

## Standard Architecture

### System Overview (目标架构)

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 FastAPI (uvicorn :8000)                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ Proxy Routes │  │ Admin API    │  │ Static Files │  │  │
│  │  │ /v1/*        │  │ /admin/api/* │  │ /assets/*    │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │  │
│  │         │                 │                  │          │  │
│  │         │    ┌────────────┴────────────┐     │          │  │
│  │         │    │  app/database.py        │     │          │  │
│  │         │    │  (共享数据访问层)         │     │          │  │
│  │         │    └────────────┬────────────┘     │          │  │
│  │         │                 │                  │          │  │
│  │  ┌──────┴─────────────────┴──────────────────┴───────┐  │  │
│  │  │              SQLite (data/proxy.db)                │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │  React SPA (静态构建产物)                            │  │  │
│  │  │  /index.html, /assets/*.js, /assets/*.css          │  │  │
│  │  │  Catch-all /{path} → index.html (SPA 路由)          │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  supervisord: 单进程管理（仅 uvicorn，移除 streamlit）         │
└─────────────────────────────────────────────────────────────┘
```

### 组件职责

| 组件 | 职责 | 实现方式 |
|------|------|----------|
| **Proxy Routes** (`/v1/*`) | LLM API 反向代理，鉴权，模型切换 | 现有 `app/router/chat_final.py` + `responses_api.py`，不做修改 |
| **Admin API** (`/admin/api/*`) | 管理面板 CRUD 接口，认证 | 新增 `app/router/admin.py`，复用 `app/database.py` |
| **Auth Middleware** | Admin API 鉴权（Cookie/Session） | 新增 `app/middleware.py` 或 FastAPI `Depends()` |
| **Static Files** (`/assets/*`) | React 构建产物的静态文件服务 | FastAPI `StaticFiles` mount |
| **SPA Catch-all** | 客户端路由兜底，返回 `index.html` | FastAPI catch-all route |
| **React SPA** | 管理面板前端 UI，MiniMax 风格 | Vite + React + Tailwind CSS |
| **SQLite** | 单一数据源，所有组件共享 | 现有 `data/proxy.db` |

### 组件边界关系

```
React SPA ──HTTP (fetch)──→ Admin API Routes ──func call──→ app/database.py ──SQL──→ SQLite
                                                        ↑
Proxy Routes ──func call──→ app/database.py ────────────┘

React SPA ──browser nav──→ FastAPI catch-all ──FileResponse──→ React build files
```

**关键边界规则：**
- React SPA 不直接访问数据库，所有数据通过 Admin API
- Admin API 和 Proxy Routes 共享 `app/database.py` 数据访问层
- Proxy Routes 完全不受 React 迁移影响，不做任何修改
- React SPA 构建产物是静态文件，由 FastAPI 统一服务

## 推荐项目结构

```
union-ai-api/
├── app/                          # FastAPI 后端（现有，不做修改）
│   ├── main.py                   # 入口：注册路由 + mount 静态文件 + catch-all
│   ├── database.py               # 数据访问层（现有，不做修改）
│   ├── schemas.py                # 现有 Pydantic models
│   ├── router/
│   │   ├── chat_final.py         # 代理路由（现有，不动）
│   │   ├── responses_api.py      # 代理路由（现有，不动）
│   │   └── admin.py              # 新增：管理 API 路由
│   └── services/
│       └── llm_service.py        # 现有（未使用）
├── frontend/                     # 新增：React 前端项目
│   ├── dist/                     # 构建输出（.gitignore 排除）
│   ├── public/                   # 静态资源
│   ├── src/
│   │   ├── main.jsx              # React 入口
│   │   ├── App.jsx               # 根组件 + 路由定义
│   │   ├── api/                  # API 客户端层
│   │   │   ├── client.js         # fetch 封装，认证 token 管理
│   │   │   ├── models.js         # 模型 CRUD API 调用
│   │   │   ├── keys.js           # API Key 管理 API 调用
│   │   │   ├── logs.js           # 调用日志 API 调用
│   │   │   └── auth.js           # 登录/注册/认证 API 调用
│   │   ├── components/           # 通用 UI 组件
│   │   │   ├── Layout.jsx        # 页面布局（侧边栏 + 内容区）
│   │   │   ├── Sidebar.jsx       # 侧边导航栏
│   │   │   ├── ModelCard.jsx     # 模型卡片组件
│   │   │   ├── PillButton.jsx    # Pill 按钮组件
│   │   │   └── ...
│   │   ├── pages/                # 页面级组件
│   │   │   ├── Dashboard.jsx     # 数据概览
│   │   │   ├── Models.jsx        # 模型配置
│   │   │   ├── ApiKeys.jsx       # API Key 管理
│   │   │   ├── Logs.jsx          # 调用记录
│   │   │   ├── Login.jsx         # 登录页
│   │   │   └── Register.jsx      # 注册页
│   │   ├── hooks/                # 自定义 Hooks
│   │   │   ├── useAuth.js        # 认证状态管理
│   │   │   └── useApi.js         # 通用数据获取 hook
│   │   └── styles/               # Tailwind 配置和全局样式
│   │       └── globals.css       # Tailwind 导入 + 自定义 CSS 变量
│   ├── index.html                # HTML 模板
│   ├── vite.config.js            # Vite 配置（开发代理 + 构建设置）
│   ├── tailwind.config.js        # Tailwind 配置（DESIGN.md Token 映射）
│   └── package.json              # 前端依赖
├── streamlit_app/                # 旧管理面板（迁移完成后删除）
├── data/                         # SQLite 数据（运行时）
├── supervisord.conf              # 进程管理（简化：移除 streamlit）
├── Dockerfile.clean              # Docker 镜像（新增 Node.js 构建阶段）
└── docker-compose.clean.yml      # Docker Compose（简化端口映射）
```

### 结构说明

- **`frontend/`** 作为独立子项目存在，有自己的 `package.json` 和构建工具链。Vite 构建输出到 `frontend/dist/`，FastAPI 从该目录读取静态文件
- **`app/router/admin.py`** 是唯一需要新增的后端文件，包含所有管理 API 端点。使用 FastAPI `APIRouter` 注册到 `/admin/api` 前缀
- **`streamlit_app/`** 保留到迁移完成后删除，避免迁移期间丢失功能

## 架构模式

### 模式 1: FastAPI 提供 React SPA 静态文件服务

**说明：** FastAPI 使用 `StaticFiles` mount + catch-all route 来服务 React 构建产物，实现单容器部署。

**适用场景：** 小到中型管理面板，不需要独立 CDN 或 Nginx。

**核心实现：**

```python
# app/main.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# 1. API 路由注册在前（优先匹配）
app.include_router(chat_router)
app.include_router(responses_router)
app.include_router(admin_router, prefix="/admin/api")

# 2. 静态资源 mount（JS/CSS/图片等）
# React 构建时 base 为 './'，Vite 默认将资源输出到 assets/ 目录
static_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="static_assets")

# 3. Catch-all SPA 路由（必须在所有 API 路由之后）
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = os.path.join(static_path, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(static_path, "index.html"))
```

**权衡：**
- 优点：单容器部署，零额外基础设施，同源（无 CORS 问题）
- 缺点：Python 服务静态文件效率低于 Nginx。但管理面板流量极低，完全可接受
- 对于此项目（管理面板，仅管理员使用），这是最佳方案

### 模式 2: Admin API 路由复用现有数据访问层

**说明：** 新增的 `app/router/admin.py` 直接调用 `app/database.py` 的函数，不新建数据访问层。

**适用场景：** 后端不需要修改业务逻辑，只需要暴露 HTTP 接口。

```python
# app/router/admin.py
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_all_models, create_model, update_model, delete_model

router = APIRouter()

@router.get("/models")
def list_models():
    return get_all_models()

@router.post("/models")
def add_model(data: dict):
    config_id = create_model(data)
    return {"config_id": config_id}
```

**权衡：**
- 优点：零重复代码，复用已验证的数据库函数
- 缺点：`app/database.py` 的函数签名和返回格式是固定的，如果需要适配前端可能需要少量包装
- 注意：`streamlit_app/db.py` 和 `app/database.py` 存在功能重复。迁移完成后应统一为 `app/database.py`，删除 `streamlit_app/db.py`

### 模式 3: Cookie-Based Session 认证

**说明：** 复用现有 Streamlit 的用户表（`users` 表）和密码验证逻辑，但改用 HttpOnly Cookie 传递认证状态。

**适用场景：** 管理面板是 SPA，浏览器直接访问，Cookie 认证最自然。

```python
# 登录端点返回 Set-Cookie header
@router.post("/auth/login")
def login(credentials: LoginRequest, response: Response):
    user = get_user(credentials.username)
    if not user or not verify_password(credentials.password, user['password_hash'], user['salt']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_auth_token(credentials.username)
    response.set_cookie(
        key="union_ai_auth",
        value=token,
        httponly=True,
        max_age=7 * 24 * 3600,  # 7 天
        samesite="lax"
    )
    return {"username": credentials.username}
```

**权衡：**
- 优点：HttpOnly Cookie 防 XSS 窃取 token，同源自动携带，前端无需手动管理
- 缺点：需要 CSRF 防护（管理面板场景风险低）
- 与现有 Streamlit 认证逻辑（PBKDF2 密码哈希 + `users` 表）完全兼容

### 模式 4: 前端状态分层

**说明：** React 前端将状态分为 Server State（服务端数据）和 Client State（UI 状态）。

- **Server State**：模型列表、API Key 列表、调用日志、统计数据。使用 TanStack Query 管理（自动缓存、刷新、乐观更新）
- **Client State**：当前页面路由、侧边栏展开状态、表单输入值。使用 React 内置 `useState`/`useReducer`
- **Auth State**：登录状态、用户名。使用 React Context + `useAuth` hook

**适用场景：** 标准管理面板 CRUD 应用，服务端数据驱动 UI。

**权衡：**
- 优点：无需引入 Redux/Zustand 等重型状态库，TanStack Query 覆盖 90% 的数据需求
- 缺点：团队需要理解 TanStack Query 的缓存失效和 stale-while-revalidate 概念

## 数据流

### 请求流（完整生命周期）

```
浏览器访问 http://host:18080/
    ↓
Docker 端口映射 (18080 → 8000)
    ↓
FastAPI 接收请求
    ↓
路由匹配：
├── /v1/chat/completions → Proxy Routes → 上游 LLM API
├── /v1/responses        → Proxy Routes → 上游 LLM API
├── /admin/api/auth/*    → Admin API → 鉴权 → users 表
├── /admin/api/models/*  → Admin API → database.py → models 表
├── /admin/api/keys/*    → Admin API → database.py → api_keys 表
├── /admin/api/logs/*    → Admin API → database.py → call_logs 表
├── /admin/api/stats/*   → Admin API → database.py → daily_usage 表
├── /admin/api/config/*  → Admin API → database.py → system_config 表
├── /assets/*            → StaticFiles → React 构建产物
└── /*                   → Catch-all → index.html (SPA)
```

### React 前端数据流

```
[页面组件]
    ↓ useQuery / useMutation
[TanStack Query 缓存层]
    ↓ fetch("/admin/api/...")
[API Client 模块 (src/api/)]
    ↓ HTTP + Cookie 认证
[FastAPI Admin API Routes]
    ↓ 函数调用
[app/database.py]
    ↓ SQL
[SQLite]
```

### 认证数据流

```
1. 用户提交登录表单
   → POST /admin/api/auth/login {username, password}
   → FastAPI 验证密码 (PBKDF2)
   → 生成 token，Set-Cookie: union_ai_auth=xxx; HttpOnly
   → 前端无需存储 token，浏览器自动携带

2. 后续 API 请求
   → 浏览器自动携带 Cookie
   → Admin API 通过 Depends() 提取并验证 Cookie
   → 验证通过 → 执行操作
   → 验证失败 → 401 → 前端跳转登录页

3. 退出登录
   → POST /admin/api/auth/logout
   → 清除 Cookie
   → 前端清除 Auth Context，跳转登录页
```

### 关键数据流说明

1. **模型配置 CRUD：** React 表单 → Admin API → `database.py` → SQLite。`streamlit_app/db.py` 中的 `create_model()` 接受独立参数，而 `app/database.py` 中的接受 `dict`。Admin API 应复用 `app/database.py` 的 dict 接口。

2. **Excel 导入/导出：** 这是 Streamlit 独有的功能（使用 pandas + openpyxl）。迁移方案有两种选择：
   - 后端新增 `/admin/api/models/export` 和 `/admin/api/models/import` 端点（推荐，复用 Python 生态）
   - 前端用 JS 库（SheetJS）实现（不推荐，增加前端复杂度）

3. **用量统计实时性：** 管理面板查看的是"今日用量"，数据由代理路由在每次请求后更新。Admin API 只是读取，不需要额外的缓存失效机制。TanStack Query 的默认 `staleTime: 30s` 即可。

## 开发环境架构

```
开发模式（双服务器）：
┌──────────────────┐     ┌──────────────────┐
│  Vite Dev Server │     │  FastAPI (uvicorn)│
│  localhost:5173   │────→│  localhost:8000   │
│  (React HMR)     │proxy│  (Admin API)      │
└──────────────────┘     └──────────────────┘

vite.config.js:
  server: {
    proxy: {
      "/admin/api": "http://localhost:8000",
      "/v1": "http://localhost:8000"
    }
  }

生产模式（单服务器）：
┌─────────────────────────────┐
│  FastAPI (uvicorn :8000)     │
│  ├── /admin/api/*  → API    │
│  ├── /assets/*     → 静态文件│
│  └── /*            → SPA    │
└─────────────────────────────┘
```

## Docker 构建架构

```
Dockerfile.clean（多阶段构建）：

Stage 1: Node.js 构建 React
  FROM node:20-alpine AS frontend-build
  COPY frontend/ /build/
  WORKDIR /build
  RUN npm ci && npm run build

Stage 2: Python 运行时
  FROM python:3.11-slim
  COPY --from=frontend-build /build/dist /app/frontend/dist
  COPY app/ /app/app/
  COPY requirements.txt /app/
  RUN pip install --no-cache-dir -r requirements.txt
  # supervisord 简化为单进程（仅 uvicorn）
```

**权衡：** 多阶段构建增加 Dockerfile 复杂度，但保证构建环境干净。`frontend/dist/` 不进入 Git，只在 Docker 构建时生成。

## 组件构建顺序（依赖关系）

```
Phase 1: 基础设施（无依赖）
├── Vite + React 项目初始化
├── Tailwind CSS 配置（映射 DESIGN.md Token）
└── FastAPI StaticFiles mount + catch-all route

Phase 2: Admin API 层（依赖 Phase 1 的路由注册机制）
├── app/router/admin.py — 认证端点
├── app/router/admin.py — 模型 CRUD 端点
├── app/router/admin.py — API Key 端点
├── app/router/admin.py — 日志和统计端点
└── app/router/admin.py — 系统配置端点

Phase 3: 前端认证（依赖 Phase 2 的认证 API）
├── API Client 封装（fetch + Cookie 处理）
├── Auth Context + useAuth hook
├── 登录页
└── 注册页

Phase 4: 前端页面（依赖 Phase 2 的 CRUD API + Phase 3 的认证）
├── Layout + Sidebar 组件
├── Dashboard 页面（数据概览）
├── Models 页面（模型配置 CRUD）
├── ApiKeys 页面（API Key 管理）
└── Logs 页面（调用记录）

Phase 5: 部署清理（依赖 Phase 1-4 完成）
├── Dockerfile 多阶段构建
├── supervisord.conf 简化
├── 删除 streamlit_app/
└── 端口映射统一
```

**构建顺序依据：**
- Phase 1 必须先完成，因为它是整个"FastAPI 服务 React 静态文件"的基础设施
- Phase 2 可以与 Phase 1 并行开发（后端 API 独立于前端构建机制）
- Phase 3 依赖 Phase 2 的认证 API 才能工作
- Phase 4 依赖 Phase 2 的全部 API 和 Phase 3 的认证机制
- Phase 5 是收尾，确保所有组件集成后统一清理

## Anti-Patterns（避免）

### 反模式 1: React 直接操作 SQLite

**错误做法：** 前端通过某种方式（如 SQL.js）直接操作数据库文件。
**问题：** 浏览器无法访问服务器文件系统，且会破坏数据一致性。
**正确做法：** 所有数据操作通过 Admin API 中转。

### 反模式 2: 将 React 构建产物提交到 Git

**错误做法：** 将 `frontend/dist/` 目录提交到版本控制。
**问题：** 构建产物是生成的，会污染 Git 历史和 diff。
**正确做法：** `.gitignore` 排除 `frontend/dist/`，Docker 多阶段构建时生成。

### 反模式 3: 在 Admin API 路由中重写数据库逻辑

**错误做法：** 在 `app/router/admin.py` 中重写 SQL 查询和数据操作。
**问题：** 与 `app/database.py` 产生功能重复，增加维护成本。
**正确做法：** 复用 `app/database.py` 的函数。如果函数签名不完全匹配前端需求，在路由层做轻量数据转换，不改底层函数。

### 反模式 4: 全局状态管理库（Redux/MobX）

**错误做法：** 引入 Redux 或其他全局状态库。
**问题：** 管理面板是标准 CRUD 应用，数据来自服务端，不需要复杂的前端状态管理。
**正确做法：** TanStack Query 管理服务端数据，React useState/useContext 管理 UI 状态。

### 反模式 5: 在 catch-all 路由前注册 API 路由失败

**错误做法：** catch-all `/{path:path}` 路由在 Admin API 路由之前注册。
**问题：** 所有请求被 catch-all 拦截，API 路由永远不匹配。
**正确做法：** API 路由注册在前，catch-all 在最后。FastAPI 按注册顺序匹配。

## 扩展性考虑

| 规模 | 架构调整 |
|------|----------|
| 当前（1-5 管理员） | FastAPI 直接服务静态文件，单容器部署，完全够用 |
| 中型（10+ 管理员） | 考虑 Nginx 反代服务静态文件，FastAPI 专注 API |
| 大型（100+ 并发） | SQLite 可能成为瓶颈，考虑 PostgreSQL 迁移 |

**对于此项目：** 永远是 1-5 个管理员的内部工具。SQLite + FastAPI 服务静态文件的方案在可预见的未来不会有性能问题。

## 与现有系统的兼容性

| 现有组件 | 迁移策略 | 影响 |
|----------|----------|------|
| `app/main.py` | 新增 `admin_router` 注册 + 静态文件 mount + catch-all | 最小改动 |
| `app/database.py` | 完全复用，不做修改 | 零改动 |
| `app/router/chat_final.py` | 完全不动 | 零改动 |
| `app/router/responses_api.py` | 完全不动 | 零改动 |
| `streamlit_app/db.py` | 迁移期间保留，迁移完成后删除 | 最终删除 |
| `streamlit_app/home.py` | 迁移期间保留，迁移完成后删除 | 最终删除 |
| `supervisord.conf` | 移除 streamlit 进程段 | 简化 |
| `Dockerfile.clean` | 新增 Node.js 构建阶段 | 改动较大 |
| `docker-compose.clean.yml` | 移除 18501 端口映射 | 简化 |
| `requirements.txt` | 可移除 `streamlit` 依赖 | 简化 |
| `users` 表 | 完全复用，认证逻辑平移 | 零改动 |

## Sources

- [FastAPI Static Files 官方文档](https://fastapi.tiangolo.com/tutorial/static-files/) — StaticFiles mount 机制
- [How to Serve a React Frontend with FastAPI (Carlo Tasca, 2025-12)](https://medium.com/@c.tasca.1971/how-to-serve-a-react-frontend-with-fastapi-36a96663b3cb) — catch-all + StaticFiles 单容器方案
- [FastAPI and React in 2025 (Josh Finnie)](https://www.joshfinnie.com/blog/fastapi-and-react-in-2025/) — Vite + FastAPI 集成开发模式
- [FastAPI catch-all route 问题 (StackOverflow)](https://stackoverflow.com/questions/76527355/fastapi-catch-all-route-put-after-root-route-mount-doesnt-get-hit) — 路由注册顺序的坑
- [React State Management in 2025 (developerway.com)](https://www.developerway.com/posts/react-state-management-2025) — 状态分层策略
- [TanStack Query 官方文档](https://tanstack.com/query) — 服务端状态管理

---
*Architecture research for: React Admin Panel + FastAPI Backend*
*Researched: 2026-04-15*
