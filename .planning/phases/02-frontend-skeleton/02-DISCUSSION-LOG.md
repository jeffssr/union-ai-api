# Phase 2: 前端骨架 + 设计系统 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 02-frontend-skeleton
**Areas discussed:** 技术栈选择, 布局与导航, 组件开发, 登录/注册页面, 字体策略

---

## Tailwind 版本与 Token 映射

| Option | Description | Selected |
|--------|-------------|----------|
| Tailwind v3 (JS config) | JS 配置对象映射 Token，成熟稳定，社区文档丰富 | ✓ |
| Tailwind v4 (CSS-first) | CSS-first @theme 语法，较新，需验证 | |

**User's choice:** Tailwind v3 (JS config)
**Notes:** STATE.md 标注 v4 需验证 Token 映射，用户选择 v3 规避风险

---

## 组件预览与开发方式

| Option | Description | Selected |
|--------|-------------|----------|
| 页面内直接验证 | 轻量无额外依赖，组件在页面内使用验证 | ✓ |
| Storybook 独立预览 | 独立组件文档环境，规范化但增加复杂度 | |

**User's choice:** 页面内直接验证
**Notes:** 减少 Phase 2 构建复杂度，专注实际页面

---

## 侧边栏布局与移动端交互

| Option | Description | Selected |
|--------|-------------|----------|
| 左侧抽屉覆盖 | hamburger 触发，overlay 遮罩关闭 | ✓ |
| 折叠式侧边栏 | 常驻缩为图标列，hover 展开 | |
| 底部导航栏 | 移动端底部显示导航图标 | |

**User's choice:** 左侧抽屉覆盖
**Notes:** 主流管理面板模式

---

## 侧边栏导航视觉风格

| Option | Description | Selected |
|--------|-------------|----------|
| 白底 + Pill 活跃标记 | 9999px radius Pill 与 DESIGN.md 对齐 | ✓ |
| 蓝色强调 + 左侧竖条 | 传统管理面板风格 | |

**User's choice:** 白底 + Pill 活跃标记
**Notes:** 与 DESIGN.md Pill Nav 规范一致

---

## 登录/注册页面视觉方向

| Option | Description | Selected |
|--------|-------------|----------|
| 左右分割布局 | 左侧品牌色区域 + 右侧白色表单 | |
| 居中卡片布局 | 全屏白底，登录卡片居中，Logo 上方 | ✓ |

**User's choice:** 居中卡片布局
**Notes:** 简洁极简，符合 MiniMax 白底主导风格

---

## TypeScript

| Option | Description | Selected |
|--------|-------------|----------|
| TypeScript | 类型安全，IDE 补全好 | ✓ |
| JavaScript | 简单直接，无类型定义开销 | |

**User's choice:** TypeScript

---

## 路由方案

| Option | Description | Selected |
|--------|-------------|----------|
| React Router v6 | 成熟稳定，文档丰富，v6 loader/action 适合管理面板 | ✓ |
| TanStack Router | 更现代，类型安全路由定义，学习曲线稍高 | |

**User's choice:** React Router v6

---

## 字体加载方式

| Option | Description | Selected |
|--------|-------------|----------|
| Google Fonts CDN | 简单可靠，需网络访问 | |
| 本地托管 | 离线可用，无外部依赖，约 200-400KB | ✓ |

**User's choice:** 本地托管
**Notes:** 管理面板 Docker 容器部署，本地托管确保离线可用

---

## Claude's Discretion

- Vite 插件选择
- 状态管理方案（推荐 React Context）
- API 请求封装
- 文件目录结构
- CSS 重置策略
- 组件 API 设计
