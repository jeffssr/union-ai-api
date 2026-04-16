# Project Research Summary

**Project:** Union AI API - React 管理面板前端重构
**Domain:** LLM API 反向代理的管理面板 SPA（替换现有 Streamlit 面板）
**Researched:** 2026-04-15
**Confidence:** HIGH

## Executive Summary

本项目是为现有 FastAPI + SQLite LLM API 反向代理构建 React + Tailwind CSS 管理面板，替换功能完整但 UI 简陋的 Streamlit 面板，并严格遵循 DESIGN.md 定义的 MiniMax 风格设计系统。研究结论明确：使用 React 19 + TypeScript + Vite 6 构建纯 SPA，shadcn/ui 提供 headless 组件基础，Tailwind CSS v4 原子化样式实现高度定制化的设计 Token。部署方式为 FastAPI 直接提供 React 静态文件服务，保持单 Docker 容器架构。

核心风险集中在三个方面：第一，项目存在"后端不动"与"前端需要 API"的矛盾，必须新增轻量管理 API 路由层（复用现有 `app/database.py`），这是所有前端功能的前提；第二，DESIGN.md 的定制化程度极高（4 种字体、品牌紫阴影、9999px pill 按钮），必须避免重蹈 Gradio 迁移失败的覆辙——绝不使用有强默认样式的组件库，所有 UI 组件用 Tailwind 从零构建；第三，SPA 路由与 FastAPI API 路由的冲突必须在基础设施阶段解决，catch-all 路由注册顺序错误会导致整个系统不可用。

## Key Findings

### Recommended Stack

前端技术栈选型围绕三个约束：纯 SPA 部署（FastAPI 提供静态文件）、高度定制化 UI（MiniMax 风格）、管理面板 CRUD 场景。核心选择是 React 19 + TypeScript + Vite 6 + Tailwind CSS v4 + shadcn/ui。

**Core technologies:**
- **React 19 + TypeScript 5.x**: UI 框架，函数组件 + Hooks，类型安全减少 CRUD bug
- **Vite 6.x**: 构建工具，HMR 极快，生产构建输出纯静态文件由 FastAPI 服务
- **Tailwind CSS 4.x**: 原子化样式，CSS-first 配置完美映射 DESIGN.md Token 体系
- **shadcn/ui**: 组件基础（复制源码模式），基于 Radix UI 无障碍原语，可完全自定义样式
- **React Router 7.x (Library Mode)**: 客户端路由，纯 BrowserRouter，不用 Framework Mode（与 FastAPI 静态服务冲突）
- **TanStack Query 5.x**: 服务端状态管理，CRUD 操作 + 自动缓存/刷新，替代手写 loading/error 状态
- **Zustand 5.x**: 客户端 UI 状态（侧边栏折叠、主题偏好），极简集中式 store
- **React Hook Form 7.x + Zod 3.x**: 表单管理 + 数据校验，管理面板核心交互模式
- **原生 fetch**: HTTP 客户端，同源部署无 CORS 问题，配合 TanStack Query 足够
- **Recharts 2.x + TanStack Table 8.x**: 数据可视化（用量统计图表）+ 数据表格（日志、Key 列表）

### Expected Features

基于现有 Streamlit 面板代码分析和 DESIGN.md 规范，功能范围明确。

**Must have (table stakes):**
- 登录/注册认证 + Token 认证（7 天过期）— 现有面板入口
- 模型配置 CRUD（添加/编辑/删除/复制/默认模型/自动切换）— 管理面板核心
- API Key 管理（列表/生成/删除）— 代理认证核心
- 仪表盘概览（今日用量、模型状态卡片）— 管理面板首页
- 调用日志列表（分页）— 可观测性
- 配置导入/导出（Excel）— 批量操作
- 侧边栏导航 + 响应式布局 — 页面骨架

**Should have (differentiators):**
- 渐变模型状态卡片（紫色 glow 阴影 + 20-24px 圆角）— DESIGN.md 核心视觉
- Pill 按钮导航系统（9999px radius）— DESIGN.md 标志性 UI
- 多层级排版系统（4 种字体分工）— DESIGN.md 独有特征
- API Key 一次性展示 + 复制按钮 — 安全最佳实践
- 实时 Token 使用进度条 — 直观用量展示
- 调用日志筛选器 — 实用增值

**Defer (v2+):**
- 深色模式、国际化、PWA、拖拽排序、WebSocket 推送 — PROJECT.md 明确排除
- 图表库复杂可视化 — 数据维度简单，进度条和数字卡片足够
- 多用户/角色权限 — 现有系统只有单用户认证

### Architecture Approach

采用 FastAPI 同容器服务 React SPA 的单体架构。React 构建产物（`frontend/dist/`）由 FastAPI 的 `StaticFiles` 中间件 + catch-all route 提供服务。新增 `app/router/admin.py` 管理路由层复用现有 `app/database.py` 数据访问函数，不新建数据访问层。前端通过 TanStack Query 调用 Admin API，无直接数据库访问。

**Major components:**
1. **Proxy Routes (`/v1/*`)** — 现有 LLM API 反向代理，不做任何修改
2. **Admin API (`/admin/api/*`)** — 新增管理 CRUD 接口，复用 `app/database.py`，加 JWT/Cookie 认证
3. **React SPA** — Vite 构建的纯静态前端，Tailwind + shadcn/ui 实现 DESIGN.md 设计系统
4. **SQLite (`data/proxy.db`)** — 共享数据源，需启用 WAL 模式解决并发写入

### Critical Pitfalls

1. **无 Admin API 路由就写前端** — 必须先定义管理 API 契约，再开始前端开发。否则前端是空壳
2. **重蹈 Gradio CSS 覆盖覆辙** — 不用 MUI/Ant Design 等强样式组件库，用 Tailwind + shadcn/ui 从零构建
3. **SPA 路由与 API 路由冲突** — catch-all 必须在所有 API 路由之后注册，且限定在 `/admin/` 前缀范围
4. **SQLite 未启用 WAL 模式** — `app/database.py` 缺少 `PRAGMA journal_mode=WAL`，admin + proxy 并发写入会锁死
5. **认证不兼容现有用户** — 保留现有 PBKDF2 密码验证逻辑，只改 token 生成方式（JWT/Cookie），不修改 `users` 表

## Implications for Roadmap

### Phase 1: 基础设施 + Admin API

**Rationale:** 所有前端功能依赖后端管理 API 和部署基础设施。API 路由、认证、SPA 路由、数据库 WAL 模式必须先到位，否则后续前端开发无法验证。
**Delivers:** 可通过 curl 完成的完整管理 CRUD + 认证 + FastAPI 提供 SPA 的基础设施
**Addresses:** T1-T2（认证）、T20（导航前提）
**Avoids:** Pitfall 1（无 API 就写前端）、Pitfall 3（路由冲突）、Pitfall 4（SQLite 锁定）、Pitfall 5（认证不兼容）

### Phase 2: 前端骨架 + 设计系统

**Rationale:** 在有了可调用的 Admin API 后，搭建前端项目基础和 DESIGN.md 的设计 Token 系统。这一步确立所有组件的样式基础。
**Delivers:** Vite 项目初始化 + Tailwind 配置（映射所有 DESIGN.md Token）+ shadcn/ui 集成 + 布局组件（Sidebar + MainLayout）+ 登录/注册页面
**Addresses:** T1-T4（认证 UI）、T20-T21（导航布局）、D3（排版系统）、D9（阴影系统）
**Avoids:** Pitfall 2（CSS 覆盖陷阱）— 从一开始就用 Tailwind 原子化样式

### Phase 3: 核心 CRUD 页面

**Rationale:** 管理面板的核心价值所在。在设计系统和认证到位后，实现模型配置、API Key、仪表盘三个核心页面。
**Delivers:** 模型配置 CRUD 页面 + API Key 管理页面 + 仪表盘概览页面 + 渐变卡片/进度条等 DESIGN.md 组件
**Addresses:** T5-T16（模型 CRUD + API Key + 仪表盘）、D1-D5（渐变卡片/进度条/Pill 按钮/一次性 Key 展示）
**Uses:** TanStack Query（数据层）、React Hook Form + Zod（表单）、shadcn/ui 组件

### Phase 4: 数据页面 + 批量操作

**Rationale:** 日志查看和 Excel 导入/导出依赖基础 CRUD 页面的组件和模式。分页、筛选等交互模式复用 Phase 3 的经验。
**Delivers:** 调用日志页面（分页 + 筛选）+ Excel 导入/导出功能
**Addresses:** T17-T19（日志 + 导入导出）、D6-D7（日志筛选 + 分页）
**Uses:** TanStack Table（数据表格）、后端 pandas/openpyxl（Excel 操作）

### Phase 5: 部署集成 + 清理

**Rationale:** 所有功能完成后，收尾 Docker 构建、Streamlit 移除、supervisord 简化。
**Delivers:** 多阶段 Dockerfile + 简化的 supervisord.conf + 移除 streamlit_app/ + 端口统一
**Avoids:** Streamlit 残留、Docker 构建失败、生产环境 CORS 问题

### Phase Ordering Rationale

- Phase 1 必须先完成——它解决"前端需要 API 但后端没有管理路由"的核心矛盾，且包含 5 个 Critical Pitfall 的预防
- Phase 2 建立设计系统基础——所有后续页面的样式依赖于此，避免逐页面"发明"样式
- Phase 3 和 Phase 4 是核心业务功能——Phase 3 是高频使用的 CRUD，Phase 4 是低频使用的数据/批量操作
- Phase 5 最后做——删除旧代码必须在所有新功能验证完成后

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Admin API 设计需要详细研究 `app/database.py` 每个函数的签名和返回格式，确保 API 契约正确；认证方案需要确认 Cookie-based vs JWT 的具体实现细节
- **Phase 2:** DESIGN.md 的 Token 系统到 Tailwind v4 CSS-first 配置的映射需要验证，特别是 `@theme` 指令的语法
- **Phase 5:** Docker 多阶段构建（Node.js build + Python runtime）在 Windows 开发环境下的兼容性需要验证

Phases with standard patterns (skip research-phase):
- **Phase 3:** 标准 React CRUD 页面模式，TanStack Query + React Hook Form 有大量成熟范例
- **Phase 4:** 数据表格 + 分页 + 文件上传下载都是标准模式

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 所有技术选型有官方文档和版本验证，shadcn/ui + Tailwind v4 组合在 2025 年 2 月已全面适配 |
| Features | HIGH | 功能范围完全由现有 Streamlit 代码（690 行）和 PROJECT.md 界定，无推测 |
| Architecture | HIGH | FastAPI + React SPA 同容器部署是成熟模式，官方文档和社区教程充分 |
| Pitfalls | HIGH | 多数 Pitfall 基于代码库实际分析（`app/database.py`、`streamlit_app/db.py`），非推测 |

**Overall confidence:** HIGH

### Gaps to Address

- **DESIGN.md Token 到 Tailwind v4 的精确映射**: Tailwind v4 的 CSS-first `@theme` 配置方式与 v3 的 `tailwind.config.js` 差异较大，实际映射时可能需要调试。Phase 2 开始时需验证
- **Cookie-based 认证 vs JWT 的最终选择**: ARCHITECTURE.md 推荐 Cookie-based，PITFALLS.md 建议 JWT Bearer token 避免 CORS 问题。需要在 Phase 1 开始时做最终决策——推荐 JWT Bearer token（管理面板场景，Bearer token 比 Cookie 更简单且无 CSRF 风险）
- **Excel 导入/导出的后端 API 实现**: 现有 Streamlit 中 Excel 操作直接在前端 Python 进程完成，React 前端需要后端新增 `/admin/api/models/import` 和 `/admin/api/models/export` 端点。实现细节需在 Phase 4 规划时确认
- **Vite 构建路径 (`base`) 配置**: 如果 admin 面板部署在 `/admin/` 子路径，需要 Vite `base: '/admin/'` 配置。需在 Phase 5 确认路由前缀策略

## Sources

### Primary (HIGH confidence)
- React 19.2 官方文档 — 版本确认
- shadcn/ui 官方 Vite 安装指南 + Tailwind v4 Changelog — 集成方案
- React Router v7 官方 "Picking a Mode" 文档 — Library Mode 选择依据
- TanStack Query v5 官方文档 — 服务端状态管理
- Tailwind CSS v4.0 发布博客 — CSS-first 配置
- 代码库分析: `app/database.py`, `streamlit_app/home.py`, `streamlit_app/db.py`, `app/main.py` — 功能范围和架构约束

### Secondary (MEDIUM confidence)
- FastAPI + React SPA 同容器部署方案 (Carlo Tasca, Medium) — StaticFiles + catch-all 模式
- FastAPI + React 全栈教程 (TestDriven.io) — 集成参考
- satnaing/shadcn-admin 模板 — Vite + React + shadcn/ui 管理面板范例
- React State Management 2025 (developerway.com) — 状态分层策略
- Evil Martians: Tailwind CSS 防混乱最佳实践 — 样式管理

### Tertiary (LOW confidence)
- Recharts 用于管理面板图表 — 轻量但社区不如 ECharts 活跃，Phase 4 视需求可替换
- Vite 6.x 稳定性 — 虽然比 8.x 更成熟，但实际项目中遇到的边界情况需在开发中验证

---
*Research completed: 2026-04-15*
*Ready for roadmap: yes*
