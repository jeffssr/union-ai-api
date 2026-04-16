# Feature Landscape

**Domain:** LLM API Proxy 管理面板（React SPA 替换 Streamlit）
**Researched:** 2026-04-15
**Confidence:** HIGH — 功能范围由现有 Streamlit 代码和 PROJECT.md 明确界定，无推测

## 分析方法

本项目的"Table stakes"和"Differentiators"判断基于：
1. 现有 Streamlit 面板已实现的功能（`streamlit_app/home.py`，690 行）
2. PROJECT.md 中已验证的需求列表
3. DESIGN.md 定义的 UI 组件和布局规范
4. API 管理面板领域的通用期望

---

## Table Stakes

用户期望的功能。缺失 = 产品感觉不完整或不如被替换的 Streamlit 面板。

### 认证与用户管理

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T1 | 登录/注册页面 | 现有 Streamlit 面板核心入口，无认证则无法使用 | Low | 首次使用无用户时自动跳转注册；后续只有登录。Session 逻辑已有（cookie + query param 双通道） |
| T2 | Token 认证（7天过期） | 现有机制，必须兼容 | Low | `generate_auth_token` / `verify_auth_token` 逻辑需在前端适配，但 token 生成/验证应在后端完成 |
| T3 | 修改密码 | 管理面板基本功能 | Low | 现有 `show_change_password()` 实现，需在 React 中提供独立页面或对话框 |
| T4 | 退出登录 | 必须清除 session/cookie | Low | 清除 localStorage/sessionStorage + cookie |

### 模型配置管理

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T5 | 模型列表展示 | 核心管理对象 | Low | 展示 name, model_id, priority, is_active, is_default_model, daily limits |
| T6 | 添加模型 | 管理面板存在理由 | Med | 表单字段：name, api_url, api_key(密码), model_id, daily_token_limit, daily_call_limit, priority。需要表单验证 |
| T7 | 编辑模型 | CRUD 必备 | Med | 复用添加表单，预填现有值 |
| T8 | 删除模型 | CRUD 必备 | Low | 需要确认对话框（Streamlit 无确认，React 应加） |
| T9 | 复制模型配置 | 现有功能，预填表单 | Low | 复制现有模型字段到添加表单，name 加 "(复制)" 后缀 |
| T10 | 设置默认模型 | 核心路由逻辑依赖 | Low | 全局只能有一个默认模型，选中时需清除其他模型的默认标记 |
| T11 | 自动切换开关 | 核心路由逻辑 | Low | checkbox/switch，开启时系统按优先级自动切换模型，关闭时固定使用默认模型 |

### API Key 管理

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T12 | API Key 列表 | 管理面板核心功能 | Low | 展示 name, key_id, api_key, is_active, created_at |
| T13 | 生成新 API Key | 管理面板核心功能 | Med | 生成后需要一次性展示完整 key（后续不可再见）。UI 需要明确提示用户复制 |
| T14 | 删除/禁用 API Key | 现有功能 | Low | 现有实现是软删除（`is_active = 0`）。React 中可增加启用/禁用 toggle |

### 用量统计

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T15 | 仪表盘概览（今日） | 管理面板首页，现有功能 | Med | 模型卡片展示：name, model_id, used_tokens/limit, used_calls/limit, priority, 可用状态。DESIGN.md 要求渐变卡片风格 |
| T16 | 详细数据表格 | 现有功能 | Low | DataFrame 表格展示：模型名称、Model ID、是否可用、Token 使用率、调用使用率、剩余量、默认模型、优先级 |
| T17 | 调用日志列表 | 现有功能 | Med | 展示 request_id, api_key_name, created_at, model_name, input_tokens, output_tokens, status, error_message。支持分页 |

### 配置导入导出

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T18 | 导出模型配置（Excel） | 现有功能 | Med | 生成 .xlsx 文件下载。字段映射到中文列名 |
| T19 | 导入模型配置（Excel） | 现有功能 | Med | 上传 Excel 文件解析，支持中英文列名映射，批量创建模型 |

### 导航与布局

| # | Feature | Why Expected | Complexity | Notes |
|---|---------|--------------|------------|-------|
| T20 | 侧边栏导航 | 管理面板标准模式，现有 Streamlit 侧边栏 | Low | 4 个页面：数据概览、模型配置、API Key、调用记录。DESIGN.md 要求 pill 导航样式 |
| T21 | 响应式布局 | DESIGN.md 明确要求 Mobile/Tablet/Desktop 三个断点 | Med | <768px 单列，768-1024px 双列，>1024px 完整布局 |

---

## Differentiators

让管理面板超越"能用到"的增值功能。不是用户期望的，但会显著提升体验。

| # | Feature | Value Proposition | Complexity | Notes |
|---|---------|-------------------|------------|-------|
| D1 | 渐变模型状态卡片 | DESIGN.md 的核心视觉特征：紫色 glow 阴影 + 20-24px 圆角 + 渐变背景。可用/不可用状态用不同渐变色区分 | Med | 现有 Streamlit 有简陋的渐变卡片（CSS hack），React 中可实现 DESIGN.md 标准的 Product Card 样式 |
| D2 | Pill 按钮导航系统 | DESIGN.md 标志性 UI：9999px radius 的 pill 按钮，用于导航标签和 filter toggle | Low | Tailwind 配置 `rounded-full` 即可，但需要精确的 `rgba(0,0,0,0.05)` 背景色和状态切换 |
| D3 | 多层级排版系统 | DESIGN.md 定义了 4 种字体（DM Sans/Outfit/Poppins/Roboto）的分工，现有 Streamlit 无法实现 | Med | 需要加载 4 个 Google Font，严格按规范分配：Outfit=标题, DM Sans=正文/按钮, Poppins=副标题, Roboto=数据 |
| D4 | API Key 一次性展示 + 复制按钮 | 生成 API Key 后在 modal 中展示，附带点击复制按钮和倒计时提示 | Low | 比现有 Streamlit 的纯文本展示好很多，且是安全最佳实践 |
| D5 | 实时 Token 使用进度条 | 在模型卡片中展示 Token/调用次数使用进度，渐变色从绿到红 | Low | 比纯数字更直观，IMPLEMENTATION 简单但视觉效果突出 |
| D6 | 调用日志筛选器 | 按模型、API Key、状态（成功/失败）、时间范围筛选日志 | Med | 现有 Streamlit 无筛选功能（只有 200 条限制），这是实用增值 |
| D7 | 调用日志分页 | 替代现有 Streamlit 的 200 条硬限制 | Low | 后端 `get_call_logs` 已支持 `limit` 和 `offset` 参数 |
| D8 | 模型卡片快捷操作 | 悬停显示编辑/删除/复制操作按钮 | Low | 比 Streamlit 的 expander 展开方式高效得多 |
| D9 | 紫色调阴影系统 | DESIGN.md 特征：`rgba(44, 30, 116, 0.16)` 品牌 glow | Low | Tailwind boxShadow 配置即可，但需要区分 4 个阴影层级（Flat/Subtle/Ambient/Brand Glow/Elevated） |
| D10 | 确认删除对话框 | 删除模型/Key 前弹出确认 | Low | Streamlit 无此功能，但这是防误操作的基本保护 |

---

## Anti-Features

明确不做的功能。做了反而增加复杂度或偏离项目定位。

| # | Anti-Feature | Why Avoid | What to Do Instead |
|---|--------------|-----------|-------------------|
| A1 | 国际化（i18n） | PROJECT.md 明确排除。DESIGN.md 为中文场景设计 | 所有 UI 文本保持中文 |
| A2 | PWA / 离线支持 | PROJECT.md 明确排除。管理面板不需要 | 标准 SPA，依赖网络 |
| A3 | 多用户/角色权限系统 | 现有系统只有单用户认证（users 表无 role 字段），管理面板是私有工具 | 保持现有单用户模型 |
| A4 | 深色模式 | DESIGN.md 明确定义白底主导布局，所有色彩和阴影系统基于浅色背景 | 仅浅色主题，严格遵循 DESIGN.md |
| A5 | 实时 WebSocket 推送 | 管理面板数据更新频率低（按天统计），轮询足够 | 初始版本用手动刷新，未来可加定时轮询 |
| A6 | 图表库（Chart.js/Recharts） | 现有 Streamlit 只用表格和卡片展示数据，不需要复杂图表。数据维度简单（日维度 Token/调用数） | 用进度条和数字卡片展示使用情况 |
| A7 | 拖拽排序模型优先级 | 现有系统用数字优先级，逻辑简单可靠 | 保持数字输入优先级，配合列表实时排序展示 |
| A8 | API Key 编辑/重命名 | 现有系统只有创建和软删除，无编辑功能 | 保持简单：创建 + 禁用 |
| A9 | 数据库直接迁移/管理工具 | PROJECT.md 明确排除数据库 schema 变更 | 复用现有 `app/database.py` 的所有函数 |
| A10 | 后端业务逻辑修改 | 用户明确要求"后端不做调整" | 新增轻量管理 API 路由层（仅 API 层），复用现有 `app/database.py` 数据访问函数 |

---

## Feature Dependencies

```
T1 登录/注册 ──────────────────────────────────┐
  |                                             |
  v                                             |
T2 Token 认证 ──────────────────────────────────┤
  |                                             |
  +──> T20 侧边栏导航 ─> T21 响应式布局          |  全局布局依赖
  |                                             |
  +──> T15 仪表盘概览 ─> D1 渐变卡片 ─> D5 进度条 |  Dashboard 页
  |                   └─> T16 详细表格            |
  |                                             |
  +──> T5 模型列表 ─> T6 添加 ─> T7 编辑         |  模型配置页
  |                └─> T8 删除 ─> D10 确认对话框  |
  |                └─> T9 复制配置               |
  |                └─> T10 默认模型 ─> T11 自动切换开关
  |                └─> T18 导出 ─> T19 导入       |
  |                                             |
  +──> T12 API Key 列表 ─> T13 生成 ─> D4 复制按钮 |  API Key 页
  |                     └─> T14 删除             |
  |                                             |
  +──> T17 调用日志 ─> D6 筛选器 ─> D7 分页      |  调用记录页
  |                                             |
  +──> T3 修改密码 ─> T4 退出登录                |  用户设置
  |                                             |
  D2 Pill 导航 ──> (全局，与 T20 配合)            |  设计系统
  D3 排版系统 ──> (全局)                          |
  D9 阴影系统 ──> (全局，与 D1 配合)              |
```

**关键依赖路径：**
- 后端管理 API 是所有数据操作的前提（PROJECT.md 已识别此矛盾）
- T20 侧边栏导航是所有页面的骨架，必须最先实现
- D3 排版系统 + D9 阴影系统是 DESIGN.md 的基础 Token，影响所有组件
- T15 仪表盘依赖 T5 模型数据，T17 日志依赖 T12 API Key 数据

---

## MVP 推荐

### 第一优先级（骨架 + 认证）
1. **T1 登录/注册** + **T2 Token 认证** — 无认证则无法使用
2. **T20 侧边栏导航** — 所有页面的容器
3. **D3 排版系统** + **D9 阴影系统** — DESIGN.md 基础 Token

### 第二优先级（核心 CRUD）
4. **T5-T11 模型配置 CRUD** — 管理面板的核心价值
5. **T12-T14 API Key 管理** — 代理认证的核心
6. **T15-T16 仪表盘** — 首页

### 第三优先级（数据 + 配置）
7. **T17 调用日志** — 可观测性
8. **T18-T19 导入导出** — 批量操作

### 第四优先级（视觉提升）
9. **D1 渐变卡片** + **D5 进度条** — 视觉差异化
10. **D6 日志筛选** + **D7 分页** — 体验优化

### 延后考虑
- **D2 Pill 导航**：可在骨架阶段一并实现（复杂度低），不单独排期
- **D8 快捷操作**：hover 菜单是锦上添花
- **D10 确认对话框**：应随 T8/T14 一起实现，不单独排期

---

## 后端 API 需求映射

现有 FastAPI 后端只有代理路由（`/v1/chat/completions`, `/v1/responses`），没有管理 API。以下是需要新增的管理 API 路由，映射到每个功能：

| Feature | 需要的后端 API | 复用现有函数 |
|---------|---------------|-------------|
| T1-T2 认证 | `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me` | `verify_password`, `create_user`, `get_user` |
| T3 修改密码 | `PUT /api/auth/password` | `update_user_password` |
| T5-T11 模型 CRUD | `GET /api/models`, `POST /api/models`, `PUT /api/models/:id`, `DELETE /api/models/:id`, `PUT /api/models/:id/default` | `get_all_models`, `create_model`, `update_model`, `delete_model` |
| T11 自动切换 | `GET /api/system/auto-switch`, `PUT /api/system/auto-switch` | `get_auto_switch_status`, `set_auto_switch_status` |
| T12-T14 API Key | `GET /api/keys`, `POST /api/keys`, `DELETE /api/keys/:id` | `get_all_api_keys`, `create_api_key`, `delete_api_key` |
| T15 仪表盘 | `GET /api/stats/daily` | `get_daily_stats` |
| T17 调用日志 | `GET /api/logs?limit=&offset=` | `get_call_logs` |
| T18 导出 | `GET /api/models/export` | `get_all_models` + Excel 生成 |
| T19 导入 | `POST /api/models/import` | Excel 解析 + `create_model` |

**注意**：这些 API 路由是新增的，不修改现有 `app/router/` 下的代理路由。API 层复用 `app/database.py` 的数据访问函数。

---

## Sources

- 现有 Streamlit 面板代码：`streamlit_app/home.py`（690 行）— 功能细节的权威来源
- 数据库访问层：`app/database.py` — 数据模型和可用操作的权威来源
- 项目定义：`.planning/PROJECT.md` — 需求范围和约束
- 设计规范：`DESIGN.md` — UI 组件样式和布局规则
- 所有 Confidence: HIGH（基于代码分析，非推测）
