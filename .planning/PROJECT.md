# Union AI API - 前端 UI 重构

## What This Is

LLM API 反向代理服务（Union AI API）的管理面板 UI 重构项目。将现有 Streamlit 管理面板替换为基于 React + Tailwind CSS 的独立前端应用，按照 MiniMax 风格设计系统（DESIGN.md）实现高度定制化的 UI。项目只涉及前端层重构，后端 API、业务逻辑和数据库不做任何调整。

## Core Value

管理面板 UI 视觉效果达到 DESIGN.md 定义的设计标准，同时完整保留现有 Streamlit 面板的所有功能。

## Requirements

### Validated

<!-- 从现有 Streamlit 面板推断的已验证功能 -->

- ✓ 用户登录/注册认证 — 现有 Streamlit 面板已实现
- ✓ 模型配置 CRUD（添加/编辑/删除上游 LLM 模型）— 现有功能
- ✓ API Key 管理（创建/删除/启用/禁用客户端密钥）— 现有功能
- ✓ 用量统计查看（日用量、调用日志、Token 消耗）— 现有功能
- ✓ 配置导入/导出（Excel 格式模型配置）— 现有功能
- ✓ 系统配置（自动切换开关等）— 现有功能

### Active

<!-- 本次重构目标 -->

- [ ] 使用 React + Tailwind CSS 构建全新前端应用
- [ ] 实现 DESIGN.md 定义的 MiniMax 风格设计系统
- [ ] 白底主导布局 + 彩色产品卡片/渐变装饰
- [ ] Pill 按钮（9999px radius）用于导航和标签切换
- [ ] 多字体层级（DM Sans/Outfit/Poppins/Roboto）
- [ ] 品牌紫色调阴影系统
- [ ] 响应式布局（Mobile/Tablet/Desktop）
- [ ] 所有页面遵循 DESIGN.md 色彩、圆角、阴影、排版规范
- [x] React 构建产物由 FastAPI 提供静态文件服务 — Validated in Phase 1: Admin API 基础设施
- [ ] 移除 Streamlit 依赖，保持单 Docker 容器部署
- [ ] 现有 FastAPI 后端 API 不做任何修改

### Out of Scope

<!-- 明确排除的范围 -->

- 后端 API 路由或业务逻辑修改 — 用户明确要求不动
- 数据库 schema 变更 — 用户明确要求不动
- API 代理功能（/v1/chat/completions, /v1/responses）— 后端范围
- 桌面启动器（launcher.py）— 非前端范畴
- 国际化/多语言 — DESIGN.md 为中文场景设计
- PWA/离线支持 — 管理面板不需要

## Context

- **现有架构**：FastAPI（端口 18080→8000）+ Streamlit（端口 18501→8501），通过 supervisord 在单 Docker 容器中管理双进程
- **前端现状**：Streamlit 管理面板（`streamlit_app/home.py`），功能完整但 UI 简陋
- **历史教训**：曾尝试 Gradio 5.x 迁移，CSS override 方案效果极差。根本原因是 Streamlit/Gradio 的组件渲染机制限制了自定义样式的表现力
- **设计规范**：`DESIGN.md` 定义了完整的 MiniMax 风格设计系统，包含色彩、排版、组件样式、布局原则、阴影层级等
- **数据库访问**：Streamlit 通过 `streamlit_app/db.py` 直接操作 SQLite。React 前端需要后端提供管理 API（现有 FastAPI 无管理路由，需要新增）
- **关键矛盾**：用户要求"后端不做调整"，但 React 前端需要 API 接口来操作数据。解决方案：新增轻量管理 API 路由（仅 API 层，不涉及业务逻辑变更），复用现有 `app/database.py` 的数据访问函数

## Constraints

- **Tech Stack**: React + Tailwind CSS（前端），复用现有 FastAPI + SQLite（后端）
- **Deployment**: 单 Docker 容器，React 构建产物由 FastAPI 提供静态文件服务，移除 Streamlit 进程
- **Design**: 严格遵循 DESIGN.md 设计规范
- **Compatibility**: 保留现有 API Key 认证机制，用户表结构和 session 逻辑
- **Port**: 统一到原 FastAPI 端口（18080），不再需要独立的 Streamlit 端口

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 独立 React SPA 替换 Streamlit | Streamlit/Gradio 无法实现 DESIGN.md 的高定制 UI，历史教训证明 CSS override 方案失败 | — Pending |
| Tailwind CSS 原子化样式 | DESIGN.md 有完整 Token 体系（色彩、圆角、阴影），Tailwind 配置化方式最适合映射这些 Token | — Pending |
| 同容器部署（FastAPI 提供静态文件） | 保持现有单容器部署架构，降低运维复杂度 | — Pending |
| 新增轻量管理 API 路由 | React 前端需要 REST API 接口，复用现有 `app/database.py` 数据访问函数，不涉及业务逻辑变更 | ✓ Phase 1 完成：19 个 admin 端点 + 认证 + 静态文件服务 |
| 移除 Streamlit 和 Tkinter | 前端重构完成后不再需要 Streamlit 进程和桌面启动器 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-16 after Phase 1 completion*
