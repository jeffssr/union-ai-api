# Roadmap: Union AI API - 前端 UI 重构

## Overview

将现有 Streamlit 管理面板替换为 React + Tailwind CSS 的独立前端应用，严格遵循 DESIGN.md 定义的 MiniMax 风格设计系统。路线分为 5 个阶段：先建立后端 Admin API 基础设施和认证，再搭建前端设计系统和布局骨架，然后实现核心 CRUD 页面，接着完成数据查看和批量操作，最后做部署集成和旧代码清理。

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Admin API 基础设施** - 后端管理路由、认证、SPA 静态文件服务基础
- [ ] **Phase 2: 前端骨架 + 设计系统** - React 项目初始化、DESIGN.md Token 映射、布局组件、登录/注册页面
- [ ] **Phase 3: 核心 CRUD 页面** - 模型配置、API Key 管理、仪表盘概览
- [ ] **Phase 4: 数据页面 + 批量操作** - 调用日志列表、配置导入导出
- [ ] **Phase 5: 部署集成 + 清理** - Docker 多阶段构建、Streamlit 移除、端口统一

## Phase Details

### Phase 1: Admin API 基础设施
**Goal**: 所有前端功能依赖的后端管理 API 和部署基础设施就绪，可通过 curl 完成完整的管理 CRUD 操作
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, API-01, API-02, API-03, API-04, API-05, API-06, API-07, API-08, DEPLOY-01, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. 管理员可以通过 curl 调用 login/register 端点完成认证，获得 HttpOnly Cookie
  2. 管理员可以通过 curl 完成 models、api-keys、stats、config 的完整 CRUD 操作
  3. FastAPI 能正确提供 React 构建产物的静态文件服务（catch-all 路由不与 /v1/* API 路由冲突）
  4. 未认证请求访问管理端点时返回 401，已认证请求在 Cookie 有效期内保持登录状态
  5. 首次使用（数据库无用户时）register 端点可用，有用户后 register 被禁用
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Admin API 路由骨架 + 认证端点（users 表 + login/register/logout/me/change-password）
- [ ] 01-02-PLAN.md — 模型/Key/统计/配置 CRUD 端点（14 个管理端点）
- [ ] 01-03-PLAN.md — 静态文件服务 + SPA catch-all 路由

### Phase 2: 前端骨架 + 设计系统
**Goal**: 前端项目基础建立，DESIGN.md 所有设计 Token 映射到 Tailwind 配置，布局组件和登录/注册页面可用
**Depends on**: Phase 1
**Requirements**: LAYOUT-01, LAYOUT-02, DESIGN-01, DESIGN-02, DESIGN-03, DESIGN-04, DESIGN-05, DESIGN-06, DESIGN-07
**Success Criteria** (what must be TRUE):
  1. 侧边栏导航包含 4 个页面入口（数据概览、模型配置、API Key、调用记录），点击可切换页面
  2. 布局在 Mobile (<768px)、Tablet (768-1024px)、Desktop (>1024px) 三个断点下正确适配
  3. Pill 按钮（9999px radius）、品牌紫阴影、渐变卡片、进度条等 DESIGN.md 核心组件在 Storybook 或页面中可预览
  4. 管理员可以在 React 登录页面输入用户名密码登录，登录后跳转到仪表盘页面
  5. 首次使用时自动跳转到注册页面，注册后自动登录进入面板
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 02-01: Vite + React + Tailwind 项目初始化 + DESIGN.md Token 映射
- [ ] 02-02: 布局组件（Sidebar + MainLayout）+ 响应式适配
- [ ] 02-03: DESIGN.md 核心 UI 组件库（Pill 按钮、渐变卡片、进度条、阴影系统）
- [ ] 02-04: 登录/注册页面 + 认证流程

### Phase 3: 核心 CRUD 页面
**Goal**: 管理面板的核心业务功能完整可用——模型配置管理、API Key 管理、仪表盘概览
**Depends on**: Phase 2
**Requirements**: MODEL-01, MODEL-02, MODEL-03, MODEL-04, MODEL-05, MODEL-06, MODEL-07, KEY-01, KEY-02, KEY-03, STAT-01, STAT-02
**Success Criteria** (what must be TRUE):
  1. 管理员可以在模型配置页面查看所有模型列表，添加/编辑/删除/复制模型配置，设置默认模型
  2. 管理员可以在 API Key 页面查看所有 Key 列表，生成新 Key（一次性展示完整 key 并可复制），删除 Key
  3. 仪表盘页面展示今日各模型使用状态的渐变卡片（Token 使用率、调用使用率、优先级、可用状态）
  4. 模型状态卡片使用 DESIGN.md 定义的渐变风格和品牌紫阴影，Token 使用进度条从绿到红渐变
  5. 管理员可以开关自动切换功能
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 03-01: 模型配置 CRUD 页面
- [ ] 03-02: API Key 管理页面
- [ ] 03-03: 仪表盘概览页面

### Phase 4: 数据页面 + 批量操作
**Goal**: 调用日志查看和 Excel 配置导入导出功能完整可用
**Depends on**: Phase 3
**Requirements**: STAT-03, STAT-04, STAT-05, CONF-01, CONF-02
**Success Criteria** (what must be TRUE):
  1. 管理员可以在调用记录页面查看调用日志列表（request_id, api_key_name, model_name, input/output tokens, status, error_message）
  2. 调用日志支持按模型、API Key、状态、时间范围筛选，支持分页浏览
  3. 管理员可以导出模型配置为 Excel 文件（中文列名），下载到本地
  4. 管理员可以导入 Excel 文件批量创建模型配置（支持中英文列名映射），导入后列表自动刷新
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 04-01: 调用日志列表页面（分页 + 筛选）
- [ ] 04-02: Excel 导入导出功能

### Phase 5: 部署集成 + 清理
**Goal**: 生产部署就绪——单 Docker 容器、单端口、Streamlit 依赖完全移除
**Depends on**: Phase 4
**Requirements**: DEPLOY-02, DEPLOY-03, DEPLOY-04
**Success Criteria** (what must be TRUE):
  1. Docker 多阶段构建成功（Node.js 构建前端 + Python 运行后端），镜像可正常启动
  2. 应用通过单一端口 18080 提供所有服务（API 代理 + Admin API + React SPA）
  3. Streamlit 依赖和 streamlit_app/ 目录已从项目中移除，supervisord 不再管理 Streamlit 进程
**Plans**: TBD

Plans:
- [ ] 05-01: Docker 多阶段构建 + 端口统一
- [ ] 05-02: Streamlit 依赖移除 + supervisord 简化

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Admin API 基础设施 | 0/3 | Planned | - |
| 2. 前端骨架 + 设计系统 | 0/4 | Not started | - |
| 3. 核心 CRUD 页面 | 0/3 | Not started | - |
| 4. 数据页面 + 批量操作 | 0/2 | Not started | - |
| 5. 部署集成 + 清理 | 0/2 | Not started | - |
