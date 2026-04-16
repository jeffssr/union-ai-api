# Technology Stack

**Project:** Union AI API - React 管理面板前端
**Researched:** 2026-04-15
**Context:** 为现有 FastAPI + SQLite LLM API 反向代理添加 React + Tailwind CSS 管理面板，替换现有 Streamlit 面板

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React | 19.x | UI 框架 | 2024 年 12 月发布稳定版，成熟可靠。使用函数组件 + Hooks。避免 Next.js 因为项目是 SPA 由 FastAPI 提供静态文件服务，不需要 SSR | HIGH |
| TypeScript | 5.x | 类型系统 | 与 shadcn/ui 深度集成要求一致，TanStack Query/Router 均为 TS-first 设计。管理面板涉及多个 CRUD 操作，类型安全能显著减少 bug | HIGH |
| Vite | 6.x | 构建工具 | 已足够成熟稳定（Vite 7/8 为最新但 6.x 生态更稳定）。shadcn/ui 官方提供 Vite 安装指南。极快的 HMR 开发体验。生产构建产物为纯静态文件，由 FastAPI 的 `StaticFiles` 中间件直接服务 | MEDIUM |

### Styling & UI

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Tailwind CSS | 4.x | 原子化 CSS 框架 | 2025 年初发布 v4，新引擎（Oxide）性能大幅提升。CSS-first 配置（`@theme` 指令替代 `tailwind.config.js`）完美匹配 DESIGN.md 的 Token 体系。自动内容检测，无需配置 `content` 路径。shadcn/ui 已全面支持 v4 | HIGH |
| @tailwindcss/vite | latest | Vite 集成插件 | Tailwind v4 官方 Vite 插件，零配置集成。替代旧版 PostCSS 方案 | HIGH |
| shadcn/ui | latest | UI 组件库 | 2025 年 2 月已全面适配 Tailwind v4 + React 19。不是 npm 包而是 CLI 复制组件到项目，完全可控。基于 Radix UI 无障碍原语。`data-slot` 属性方便自定义样式。与 DESIGN.md 的高定制需求完全契合——可以自由覆盖任何组件样式 | HIGH |

### Routing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React Router | 7.x (Library Mode) | 客户端路由 | v7.14.0 当前最新稳定版。**使用 Library Mode（Declarative 或 Data Mode）**，不用 Framework Mode。原因：Framework Mode 需要 Vite 插件做 SSR/构建集成，与"FastAPI 提供静态文件"的部署模式冲突。Library Mode 简单直接，`BrowserRouter` + 嵌套路由即可满足管理面板需求 | HIGH |

### Data Layer

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| TanStack Query | 5.x | 服务端状态管理 | 管理 panel 的核心需求：CRUD 操作（`useQuery` / `useMutation`），自动缓存和后台刷新，查询失效（`invalidateQueries`）确保数据一致性。替代 Redux/Context 手动管理 loading/error/data 状态。与 React Router Data Mode 可选集成 | HIGH |
| Zustand | 5.x | 客户端 UI 状态 | 仅管理纯客户端状态：侧边栏折叠、主题偏好、当前选中项等。集中式 store 模式天然适合管理面板的全局 UI 状态。极小体积（~1.1KB），API 简洁（`create((set) =>({...}))`）。不需要 Jotai 的原子化粒度 | HIGH |

### Forms & Validation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| React Hook Form | 7.x | 表单状态管理 | 管理面板表单场景为主（模型配置、API Key 创建、用户登录）。成熟稳定，社区最大。使用非受控组件减少重渲染。与 Zod 集成通过 `@hookform/resolvers` 一行配置 | HIGH |
| Zod | 3.x | 数据校验 | TypeScript-first schema 校验库。定义一次 schema，同时获得运行时校验和 TS 类型推导。管理面板的表单校验（API URL 格式、密钥长度等）和 API 响应校验统一使用 Zod | HIGH |
| @hookform/resolvers | latest | RHF + Zod 集成 | React Hook Form 官方 resolver 包，`zodResolver(schema)` 一行集成 | HIGH |

### HTTP Client

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| 原生 fetch | - | HTTP 请求 | 无需额外依赖。管理面板请求量低（CRUD 操作），不需要 Axios 的拦截器或重试机制。与 TanStack Query 的 `queryFn` 天然配合（`queryFn: () => fetch('/api/...').then(r => r.json())`）。同源部署（FastAPI 服务静态文件）无 CORS 问题 | HIGH |

### Data Visualization

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Recharts | 2.x | 图表组件 | 用量统计页面需要折线图（日用量趋势）、柱状图（Token 消耗）。基于 React + D3，声明式 API，与 Tailwind/shadcn 风格一致。轻量，社区成熟 | MEDIUM |
| TanStack Table | 8.x | 数据表格 | API Key 列表、调用日志、模型配置列表需要排序、过滤、分页。Headless 设计完全匹配 shadcn/ui 的样式覆盖需求。框架无关，TypeScript-first | HIGH |

### Dev Dependencies

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| @types/node | latest | Node 类型定义 | shadcn/ui Vite 安装指南要求，用于 `vite.config.ts` 中的 `path` 模块 | HIGH |
| ESLint + Prettier | latest | 代码规范 | TypeScript + React 规则集 | HIGH |
| Vitest | latest | 单元测试 | Vite 原生测试运行器，配置共享 vite.config.ts | MEDIUM |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| 构建工具 | Vite 6.x | Vite 8.x | 8.x 于 2026 年 3 月刚发布稳定版，生态尚未完全跟上。6.x 稳定可靠，满足所有需求。可在后续升级 |
| 构建工具 | Vite 6.x | Next.js | 需要 Node.js 运行时。本项目要求 FastAPI 提供静态文件服务、单 Docker 容器部署，Next.js 不适合 |
| UI 组件库 | shadcn/ui | Ant Design / MUI | DESIGN.md 定义了高度定制化的 MiniMax 风格（pill 按钮、紫色阴影、多字体层级），Ant/MUI 的设计语言太强难以覆盖。shadcn/ui 复制源码到项目中可完全自定义 |
| UI 组件库 | shadcn/ui | Radix UI 直接使用 | shadcn/ui 就是在 Radix UI 上加了 Tailwind 样式，直接使用 Radix 需要手写所有样式，工作量大 |
| 状态管理 | Zustand | Redux Toolkit | 管理面板状态简单，Redux 过重。Zustand 无 boilerplate |
| 状态管理 | Zustand | Jotai | 管理面板是全局互连状态（用户认证、UI 偏好），集中式 store 更自然。Jotai 的原子化模型适合细粒度独立状态 |
| 路由 | React Router Library Mode | TanStack Router | TanStack Router 功能更强但生态较新。React Router v7 Library Mode 成熟稳定，管理面板路由简单（~5-8 个页面），不需要 TanStack Router 的高级特性 |
| 路由 | React Router Library Mode | React Router Framework Mode | Framework Mode 依赖 Vite 插件做 SSR/构建集成，与 FastAPI 静态文件服务模式冲突。Library Mode 纯客户端路由，构建产物是标准 SPA |
| HTTP Client | 原生 fetch | Axios | 同源部署无 CORS 问题，CRUD 操作不需要拦截器/重试/转换。fetch + TanStack Query 已覆盖所有需求。减少一个 13KB 依赖 |
| 表单 | React Hook Form | TanStack Form | RHF 更成熟，社区更大，学习曲线更低。管理面板表单复杂度中等，不需要 TanStack Form 的高级类型推断 |
| 图表 | Recharts | ECharts / Nivo | ECharts 功能过重（~800KB），管理面板只需简单折线/柱状图。Nivo 社区较小。Recharts 平衡了功能和体积 |

## Installation

```bash
# 1. 创建 Vite + React + TypeScript 项目
npm create vite@6 frontend -- --template react-ts

# 2. 安装 Tailwind CSS v4 + Vite 插件
cd frontend
npm install tailwindcss @tailwindcss/vite

# 3. 安装 shadcn/ui（CLI 方式初始化）
npx shadcn@latest init

# 4. 安装路由
npm install react-router

# 5. 安装数据层
npm install @tanstack/react-query zustand

# 6. 安装表单 + 校验
npm install react-hook-form @hookform/resolvers zod

# 7. 安装数据可视化
npm install recharts @tanstack/react-table

# 8. 安装开发依赖
npm install -D @types/node vitest
```

## Project Structure (Recommended)

```
frontend/
  src/
    components/
      ui/              # shadcn/ui 组件（CLI 生成）
      layout/          # 布局组件（Sidebar, Header, MainLayout）
      charts/          # Recharts 封装
    pages/             # 页面组件
      Login.tsx
      Dashboard.tsx
      Models.tsx
      ApiKeys.tsx
      Usage.tsx
      Settings.tsx
    lib/
      api.ts           # fetch 封装 + 基础 URL 配置
      auth.ts          # 认证相关工具函数
    stores/
      ui-store.ts      # Zustand: 侧边栏状态、UI 偏好
    hooks/
      use-models.ts    # TanStack Query: 模型 CRUD
      use-api-keys.ts  # TanStack Query: API Key CRUD
      use-usage.ts     # TanStack Query: 用量统计
    types/
      index.ts         # 共享 TypeScript 类型
    App.tsx            # 根组件 + 路由配置
    index.css          # Tailwind 入口 + DESIGN.md Token
    main.tsx           # 入口
  public/
  index.html
  vite.config.ts
  tsconfig.json
  package.json
```

## Key Design Decisions

### 1. Vite 6.x 而非 8.x

Vite 8.x 于 2026 年 3 月刚发布，虽然功能更新但 6.x 经过更长时间验证。对于管理面板项目，构建工具稳定性优先于新特性。后续可无缝升级。

### 2. React Router Library Mode 而非 Framework Mode

Framework Mode 引入了 SSR/SSG 能力但需要 Vite 插件深度集成。本项目部署方式是 FastAPI 提供 `dist/` 静态文件，Framework Mode 的服务端功能完全用不上。Library Mode（`BrowserRouter`）是纯客户端路由，构建后就是标准 SPA。

选择 Data Mode 子模式（`createBrowserRouter` + `RouterProvider`），可获得 `loader`、`action`、pending UI 等数据特性。但鉴于已选择 TanStack Query 做数据层，Declarative Mode（`BrowserRouter`）也可以。**推荐先用 Declarative Mode，需要时再迁移到 Data Mode——v7 的升级路径是平滑的。**

### 3. 原生 fetch 而非 Axios

关键前提：React 构建产物由 FastAPI 在同源提供服务，无 CORS 问题。管理面板的 HTTP 请求模式简单（标准 REST CRUD），不需要 Axios 的拦截器链、请求/响应转换、自动重试等功能。fetch + TanStack Query 的 `queryFn` 完全够用。

### 4. shadcn/ui 作为组件基础

DESIGN.md 定义了 MiniMax 风格设计系统，包含 pill 按钮（9999px radius）、品牌紫色阴影、多字体层级等高度定制化需求。shadcn/ui 的"复制源码到项目"模式允许完全控制每个组件的样式实现，而 Ant Design/MUI 的封装层级太深，覆盖样式需要大量 `!important` 或 CSS-in-JS hack——这正是之前 Gradio 迁移失败的教训。

### 5. TanStack Query + Zustand 分工

- **TanStack Query**: 服务端状态（模型列表、API Key 列表、用量数据、调用日志）。自动缓存、后台刷新、乐观更新。
- **Zustand**: 客户端 UI 状态（侧边栏折叠、当前页面、主题偏好）。极简 API，无需 Redux 的 action/reducer boilerplate。

不使用 Context 做全局状态管理，因为 TanStack Query 内部已用 Context 提供数据，额外的 Context 层会增加复杂度。

## Sources

- [React 官方版本页](https://react.dev/versions) — React 19.2 稳定版
- [shadcn/ui Vite 安装指南](https://ui.shadcn.com/docs/installation/vite) — 官方 Vite + React + TS 集成
- [shadcn/ui Changelog - Tailwind v4 更新](https://ui.shadcn.com/docs/changelog/2025-02-tailwind-v4) — 2025 年 2 月全面适配 Tailwind v4 + React 19
- [React Router 官方 - Picking a Mode](https://reactrouter.com/start/modes) — v7.14.0, 三种模式选择
- [TanStack Query 官方文档](https://tanstack.com/query/latest/docs/framework/react/overview) — v5 最新
- [Tailwind CSS v4.0 发布](https://tailwindcss.com/blog/tailwindcss-v4) — v4 新引擎
- [Tailwind CSS NPM](https://www.npmjs.com/package/tailwindcss) — 最新版本 4.2.2
- [Vite 官方版本](https://vite.dev/releases) — 版本历史
- [FastAPI 提供 React 静态文件](https://medium.com/@c.tasca.1971/how-to-serve-a-react-frontend-with-fastapi-36a96663b3cb) — 同容器部署模式
- [satnaing/shadcn-admin](https://shadcn.io/template/satnaing-shadcn-admin) — Vite + React + shadcn/ui 管理面板模板参考

---

*Stack research: 2026-04-15*
