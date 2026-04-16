# Requirements: Union AI API - 前端 UI 重构

**Defined:** 2026-04-16
**Core Value:** 管理面板 UI 视觉效果达到 DESIGN.md 定义的设计标准，同时完整保留现有 Streamlit 面板的所有功能

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### 认证与用户管理

- [ ] **AUTH-01**: 管理员可以通过用户名/密码登录管理面板
- [ ] **AUTH-02**: 首次使用（无用户时）自动跳转注册页面
- [ ] **AUTH-03**: 管理员可以修改密码
- [ ] **AUTH-04**: 管理员可以退出登录，清除 session 状态
- [ ] **AUTH-05**: 登录状态通过 HttpOnly Cookie 维持，7天过期

### 模型配置管理

- [ ] **MODEL-01**: 管理员可以查看所有模型配置列表（name, model_id, priority, is_active, daily limits）
- [ ] **MODEL-02**: 管理员可以添加新的模型配置（api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority）
- [ ] **MODEL-03**: 管理员可以编辑已有模型配置
- [ ] **MODEL-04**: 管理员可以删除模型配置（带确认对话框）
- [ ] **MODEL-05**: 管理员可以复制模型配置（预填表单，name 加 "(复制)" 后缀）
- [ ] **MODEL-06**: 管理员可以设置默认模型（全局唯一，自动清除其他默认标记）
- [ ] **MODEL-07**: 管理员可以开关自动切换功能

### API Key 管理

- [ ] **KEY-01**: 管理员可以查看所有 API Key 列表（name, key_id, api_key, is_active, created_at）
- [ ] **KEY-02**: 管理员可以生成新 API Key，生成后一次性展示完整 key 并提供复制按钮
- [ ] **KEY-03**: 管理员可以删除/禁用 API Key

### 用量统计

- [ ] **STAT-01**: 仪表盘概览展示今日各模型使用状态（渐变卡片风格，展示 used_tokens/limit, used_calls/limit, priority, 可用状态）
- [ ] **STAT-02**: 详细数据表格展示模型使用详情（Token 使用率、调用使用率、剩余量等）
- [ ] **STAT-03**: 调用日志列表展示（request_id, api_key_name, model_name, input/output tokens, status, error_message）
- [ ] **STAT-04**: 调用日志支持按模型、API Key、状态、时间范围筛选
- [ ] **STAT-05**: 调用日志支持分页浏览

### 配置导入导出

- [ ] **CONF-01**: 管理员可以导出模型配置为 Excel 文件（中文列名）
- [ ] **CONF-02**: 管理员可以导入 Excel 文件批量创建模型配置（支持中英文列名映射）

### 导航与布局

- [ ] **LAYOUT-01**: 侧边栏导航包含 4 个页面入口（数据概览、模型配置、API Key、调用记录）
- [ ] **LAYOUT-02**: 响应式布局适配 Mobile (<768px 单列)、Tablet (768-1024px 双列)、Desktop (>1024px 完整布局)

### 设计系统（DESIGN.md）

- [ ] **DESIGN-01**: Pill 按钮导航系统（9999px radius，rgba(0,0,0,0.05) 背景色）
- [ ] **DESIGN-02**: 多字体排版系统（DM Sans=正文/按钮, Outfit=标题, Poppins=副标题, Roboto=数据）
- [ ] **DESIGN-03**: 渐变模型状态卡片（20-24px 圆角，品牌紫阴影 glow）
- [ ] **DESIGN-04**: Token 使用进度条（渐变色从绿到红）
- [ ] **DESIGN-05**: 紫色调阴影系统（4 层级：Flat/Subtle/Ambient/Brand Glow/Elevated）
- [ ] **DESIGN-06**: 模型卡片悬停快捷操作按钮
- [ ] **DESIGN-07**: 白底主导布局 + 彩色卡片/渐变装饰

### 后端管理 API

- [ ] **API-01**: 新增 FastAPI 管理路由（`app/router/admin.py`），复用现有 `app/database.py` 数据访问函数
- [ ] **API-02**: 认证端点（login, register, me, change-password, logout）
- [ ] **API-03**: 模型 CRUD 端点（list, create, update, delete, set-default）
- [ ] **API-04**: API Key 管理端点（list, create, delete）
- [ ] **API-05**: 统计端点（daily-stats, call-logs）
- [ ] **API-06**: 配置端点（export-excel, import-excel）
- [ ] **API-07**: 系统配置端点（auto-switch get/set）
- [ ] **API-08**: FastAPI 提供静态文件服务（React 构建产物）

### 部署集成

- [ ] **DEPLOY-01**: React 构建产物由 FastAPI 提供静态文件服务
- [ ] **DEPLOY-02**: Docker 多阶段构建（Node.js 构建 + Python 运行）
- [ ] **DEPLOY-03**: 移除 Streamlit 依赖和进程
- [ ] **DEPLOY-04**: 端口统一到 FastAPI 端口（18080）
- [ ] **DEPLOY-05**: SPA catch-all 路由不与 API 路由冲突

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### 高级功能

- **ADV-01**: 定时自动刷新数据（轮询模式）
- **ADV-02**: WebSocket 实时推送调用日志
- **ADV-03**: 深色模式
- **ADV-04**: 图表可视化（Token 趋势图等）

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| 国际化（i18n） | DESIGN.md 为中文场景设计，管理面板是私有工具 |
| PWA / 离线支持 | 管理面板不需要，标准 SPA 即可 |
| 多用户/角色权限 | 现有系统单用户模型，users 表无 role 字段 |
| 拖拽排序模型优先级 | 现有数字优先级系统简单可靠 |
| API Key 编辑/重命名 | 现有系统只有创建和软删除 |
| 数据库 schema 变更 | 用户明确要求不动数据库 |
| 代理 API 路由修改 | 用户明确要求不动后端业务逻辑 |
| 桌面启动器修改 | 非前端范畴 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| API-01 | Phase 1 | Pending |
| API-02 | Phase 1 | Pending |
| API-03 | Phase 1 | Pending |
| API-04 | Phase 1 | Pending |
| API-05 | Phase 1 | Pending |
| API-06 | Phase 1 | Pending |
| API-07 | Phase 1 | Pending |
| API-08 | Phase 1 | Pending |
| DEPLOY-01 | Phase 1 | Pending |
| DEPLOY-05 | Phase 1 | Pending |
| LAYOUT-01 | Phase 2 | Pending |
| LAYOUT-02 | Phase 2 | Pending |
| DESIGN-01 | Phase 2 | Pending |
| DESIGN-02 | Phase 2 | Pending |
| DESIGN-03 | Phase 2 | Pending |
| DESIGN-04 | Phase 2 | Pending |
| DESIGN-05 | Phase 2 | Pending |
| DESIGN-06 | Phase 2 | Pending |
| DESIGN-07 | Phase 2 | Pending |
| MODEL-01 | Phase 3 | Pending |
| MODEL-02 | Phase 3 | Pending |
| MODEL-03 | Phase 3 | Pending |
| MODEL-04 | Phase 3 | Pending |
| MODEL-05 | Phase 3 | Pending |
| MODEL-06 | Phase 3 | Pending |
| MODEL-07 | Phase 3 | Pending |
| KEY-01 | Phase 3 | Pending |
| KEY-02 | Phase 3 | Pending |
| KEY-03 | Phase 3 | Pending |
| STAT-01 | Phase 3 | Pending |
| STAT-02 | Phase 3 | Pending |
| STAT-03 | Phase 4 | Pending |
| STAT-04 | Phase 4 | Pending |
| STAT-05 | Phase 4 | Pending |
| CONF-01 | Phase 4 | Pending |
| CONF-02 | Phase 4 | Pending |
| DEPLOY-02 | Phase 5 | Pending |
| DEPLOY-03 | Phase 5 | Pending |
| DEPLOY-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 44 total (AUTH:5, MODEL:7, KEY:3, STAT:5, CONF:2, LAYOUT:2, DESIGN:7, API:8, DEPLOY:5)
- Mapped to phases: 44
- Unmapped: 0

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-16 after roadmap creation*
