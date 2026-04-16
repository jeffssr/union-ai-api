# Phase 2: 前端骨架 + 设计系统 - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

建立 React 前端项目基础、将 DESIGN.md 所有设计 Token 映射到 Tailwind 配置、构建布局组件（侧边栏+主内容区）和登录/注册页面。前端认证流程对接 Phase 1 已完成的 Admin API Cookie 认证端点。

**范围内：**
- Vite + React + TypeScript + Tailwind CSS v3 项目初始化
- DESIGN.md Token → tailwind.config.js 映射
- 侧边栏导航 + MainLayout 布局组件（Desktop/Tablet/Mobile 三断点）
- 核心 UI 组件（Pill 按钮、渐变卡片、进度条、阴影系统）
- 登录/注册页面 + 认证流程（对接 /api/admin/auth/* 端点）
- 字体本地托管（DM Sans、Outfit、Poppins、Roboto）

**范围外：**
- 具体业务页面（模型配置、API Key、仪表盘）→ Phase 3
- 数据页面和批量操作 → Phase 4
- Docker 部署集成 → Phase 5

</domain>

<decisions>
## Implementation Decisions

### 技术栈选择
- **D-01:** Tailwind CSS v3（JS config），通过 `tailwind.config.js` 的 `theme.extend` 映射 DESIGN.md 所有 Token
- **D-02:** TypeScript，全项目使用，管理面板代码量可控
- **D-03:** React Router v6，处理侧边栏导航切换和认证路由守卫
- **D-04:** Vite 作为构建工具（ROADMAP 已确定）

### 布局与导航
- **D-05:** 移动端侧边栏采用左侧抽屉覆盖模式（hamburger 触发，overlay 遮罩关闭）
- **D-06:** 侧边栏白色背景，导航项 DM Sans 14px，活跃项用 Pill 标记（9999px radius，rgba(0,0,0,0.05) 背景）——与 DESIGN.md Pill Nav 规范对齐
- **D-07:** Desktop 端左侧固定侧边栏 + 右侧内容区，经典管理面板布局

### 组件开发
- **D-08:** 组件在页面内直接验证，不引入 Storybook。减少构建复杂度，Phase 2 专注实际页面
- **D-09:** DESIGN.md 核心组件（Pill 按钮、渐变卡片、进度条、阴影）作为独立 UI 组件实现，在登录页和布局中实际使用验证

### 登录/注册页面
- **D-10:** 居中卡片布局——全屏白色背景，登录卡片居中显示，品牌 Logo 在卡片上方
- **D-11:** 注册页面与登录页面共用布局，切换通过卡片内链接实现

### 字体策略
- **D-12:** 4 种字体（DM Sans、Outfit、Poppins、Roboto）本地托管，离线可用，无外部 CDN 依赖

### Claude's Discretion
- Vite 插件选择（@vitejs/plugin-react 等）
- 状态管理方案（认证状态用 React Context 即可，无需 Redux/Zustand）
- API 请求封装（fetch 或 axios）
- 具体的文件目录结构
- CSS 重置策略（Tailwind Preflight 或自定义）
- 组件 API 设计（props 接口细节）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 设计规范
- `DESIGN.md` — 完整 MiniMax 风格设计系统：色彩、排版、组件、布局、阴影、圆角、响应式规范
- `DESIGN.md` §2 — 色彩体系（品牌蓝 #1456f0、品牌粉 #ea5ec1、文本色阶、表面色）
- `DESIGN.md` §3 — 排版体系（4 字体层级、尺寸/字重/行高规范）
- `DESIGN.md` §4 — 组件样式（Pill 按钮、产品卡片、导航、链接）
- `DESIGN.md` §5 — 布局原则（8px 基准间距、三断点、留白哲学）
- `DESIGN.md` §6 — 深度与阴影系统（5 层级：Flat→Elevated）

### 后端 API 参考
- `app/router/admin.py` — Phase 1 完成的 19 个 Admin API 端点（认证 + CRUD + 静态文件）
- `app/main.py` — 静态文件服务配置（STATIC_DIR = app/static）

### 项目上下文
- `.planning/REQUIREMENTS.md` — 需求清单（LAYOUT-01/02, DESIGN-01~07 为 Phase 2 相关）
- `.planning/ROADMAP.md` — Phase 2 定义和 Success Criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/router/admin.py`: 19 个 Admin API 端点已就绪，认证端点（login/register/logout/me/change-password）可直接对接
- `app/static/` 目录：FastAPI 静态文件服务已配置，React 构建产物放到此目录即可
- `app/database.py`: users 表和认证函数（hash_password, verify_password, create_user, get_user, has_users）已实现

### Established Patterns
- Cookie 认证：`session_token` Cookie，HttpOnly=True, max_age=7天, SameSite=Lax, Path=/
- Admin API 前缀：`/api/admin/*`
- 响应格式：JSON `{"status": "success/error", ...}`

### Integration Points
- 前端构建产物 → `app/static/` 目录
- 前端认证 → POST `/api/admin/auth/login`，Cookie 由后端 Set-Cookie 设置
- 前端路由守卫 → GET `/api/admin/auth/me` 验证登录状态
- 首次使用检测 → GET `/api/admin/auth/register`（无用户时 200，有用户时 403）

</code_context>

<specifics>
## Specific Ideas

- 登录页居中卡片布局：白底全屏，卡片上方放品牌 Logo，下方是表单。简洁不花哨，符合 MiniMax 白底主导风格
- 侧边栏导航活跃项：Pill 标记（9999px radius）与 DESIGN.md Pill Nav 规范一致，`rgba(0,0,0,0.05)` 背景色
- 移动端抽屉覆盖：标准 hamburger 图标触发，左侧滑出，点击遮罩关闭

</specifics>

<deferred>
## Deferred Ideas

None — 讨论未超出 Phase 2 范围

</deferred>

---

*Phase: 02-frontend-skeleton*
*Context gathered: 2026-04-16*
