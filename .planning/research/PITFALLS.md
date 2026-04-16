# Pitfalls Research

**Domain:** React admin panel bolted onto existing FastAPI + SQLite LLM API proxy
**Researched:** 2026-04-15
**Confidence:** HIGH (codebase-specific pitfalls); MEDIUM (React integration patterns)

## Critical Pitfalls

### Pitfall 1: No Admin API Routes Exist Yet — Building APIs Without Understanding Existing Data Access

**What goes wrong:**
项目 PROJECT.md 说"后端不做调整"，但 React 前端必须有 API 接口才能操作数据。如果团队直接开始写前端页面，到集成阶段才发现没有后端路由，整个前端都是无用的空壳。更糟的是，如果新增的 API 路由没有复用 `app/database.py` 的现有函数，而是另起一套数据访问层，就会产生第三套重复代码（已有 `app/database.py` 和 `streamlit_app/db.py` 两套）。

**Why it happens:**
- 前端开发天然诱惑：先写 UI 组件看起来有进展
- 后端 API 设计看起来"简单"，被推迟到最后
- 现有代码库已存在 `app/database.py`（FastAPI 用）和 `streamlit_app/db.py`（Streamlit 用）两套重复的数据访问层，开发者可能没有意识到应该统一到 `app/database.py`

**How to avoid:**
1. 第一步就定义 admin API 路由（`/admin/models`、`/admin/keys`、`/admin/stats` 等），复用 `app/database.py` 中已有的函数
2. 将 `streamlit_app/db.py` 中的用户管理函数（`create_user`、`get_user`、`verify_password`、`hash_password`、`has_users`）迁移到 `app/database.py`，因为 React 前端需要这些
3. API 路由加认证中间件，不能裸露在公网
4. 用 Pydantic 模型定义请求/响应 schema，复用 `app/database.py` 已有的数据结构

**Warning signs:**
- React 组件用 `useState` 存储硬编码的 mock 数据
- 多人并行开发时前端进展远快于后端
- 发现自己在 `streamlit_app/db.py` 基础上添加第三个数据访问文件

**Phase to address:**
Phase 1（基础设施层）必须先完成 API 路由 + 认证。前端开发必须在 API 契约确定后才开始。

---

### Pitfall 2: Repeating the Gradio Mistake — CSS Override Trap on a Custom Design System

**What goes wrong:**
DESIGN.md 定义了极度定制化的 MiniMax 风格设计系统：4 种字体（DM Sans、Outfit、Poppins、Roboto）、品牌紫色阴影（`rgba(44, 30, 116, 0.16)`）、9999px pill 按钮、渐变产品卡片、5 级阴影系统。如果使用任何组件库（如 MUI、Ant Design、shadcn/ui），都必须大量覆盖其默认样式，重蹈 Gradio 迁移失败的覆辙。

项目历史已经证明：Streamlit/Gradio 的组件渲染机制限制了自定义样式的表现力，CSS override 方案效果极差。同样的教训适用于任何有强默认样式的组件库。

**Why it happens:**
- 组件库提供快速起步，但默认样式与 DESIGN.md 冲突
- 开发者低估了覆盖组件库内部样式的难度（`:where()`、`!important`、CSS specificity war）
- DESIGN.md 的设计 Token 极其具体（如品牌紫阴影的精确 RGBA 值），组件库默认无法匹配

**How to avoid:**
1. **不使用有强默认样式的组件库**。使用 Tailwind CSS 原子化样式直接构建组件
2. 将 DESIGN.md 的所有 Token 映射到 Tailwind 配置（`tailwind.config.ts` 的 `theme.extend`）：
   - `colors`：品牌蓝系列、品牌粉、文本色系、表面色系
   - `borderRadius`：从 4px 到 9999px 的完整圆角尺度
   - `boxShadow`：5 级阴影系统，含品牌紫阴影
   - `fontFamily`：4 种字体族
   - `fontSize` + `lineHeight`：从 10px Micro 到 80px Display Hero
3. 所有 UI 组件从零用 Tailwind 构建，不依赖组件库的 CSS
4. 如果需要无样式组件（headless），使用 Radix UI 或 Headless UI — 只提供行为，不提供样式

**Warning signs:**
- CSS 文件中出现大量 `!important`
- 组件库的 `sx` prop 或 `className` override 超过组件本身代码
- F12 开发者工具中看到样式来源有 3 层以上覆盖
- 设计师/用户说"和 DESIGN.md 不一致"

**Phase to address:**
Phase 1 建立 Tailwind 配置和基础组件库。每个组件必须通过 DESIGN.md 规范的视觉验证。

---

### Pitfall 3: SPA Routing vs FastAPI Route Collision

**What goes wrong:**
React SPA 使用客户端路由（如 `/admin/models`、`/admin/keys`），但 FastAPI 也有自己的路由（`/v1/chat/completions`、`/health`）。当用户在 `/admin/models` 页面刷新浏览器时，请求到达 FastAPI，FastAPI 没有 `/admin/models` 的路由定义，返回 404。

更严重的是：如果 catch-all 路由（`/{full_path:path}`）放在 API 路由之前注册，它会拦截所有 API 请求，导致 `/v1/chat/completions` 返回 `index.html` 而不是处理 API 请求。

**Why it happens:**
- SPA 路由和服务器路由是两个独立系统，容易遗忘它们的交互
- FastAPI 的路由匹配是按注册顺序的，catch-all 必须放在最后
- 现有 `app/main.py` 已经有 `@app.post("/responses")` 这类根级路由，容易与 catch-all 冲突

**How to avoid:**
1. 所有 admin 页面使用统一前缀（如 `/admin/`）
2. 所有 API 路由保持现有前缀（`/v1/`）
3. FastAPI 中 catch-all 路由只在 `/admin/{path:path}` 范围内生效，不要全局 catch-all
4. 具体实现：
```python
# 在所有 API 路由之后注册
@app.get("/admin/{full_path:path}")
async def serve_admin_spa(full_path: str):
    return FileResponse("static/admin/index.html")

# 静态资源单独 mount
app.mount("/admin/assets", StaticFiles(directory="static/admin/assets"), name="admin-assets")
```
5. 确保 catch-all 的注册顺序在 `app.include_router()` 之后

**Warning signs:**
- 浏览器直接访问 admin 路由返回 404 或 JSON 错误
- API 请求返回 HTML 内容
- 页面刷新后显示 FastAPI 默认 404 页面

**Phase to address:**
Phase 1（部署基础设施）就必须解决路由问题，否则开发阶段就无法正常测试。

---

### Pitfall 4: SQLite Concurrent Write Contention When Admin and API Share the Same Database

**What goes wrong:**
管理面板和 API 代理共享同一个 SQLite 数据库文件（`data/proxy.db`）。API 代理每次请求都写入 `call_logs` 和 `daily_usage` 表，管理面板进行 CRUD 操作也写入 `models`、`api_keys` 等表。

当前 `app/database.py` 没有启用 WAL 模式（只有 `streamlit_app/db.py` 启用了），在高并发场景下会出现 `database is locked` 错误。React 前端引入后，admin 操作通过 HTTP API 触发数据库写入，与代理请求的写入并发量增加。

**Why it happens:**
- SQLite 是单写者模型，写操作互斥
- `check_same_thread=False` 只关闭 Python 的线程检查，不提供并发安全
- FastAPI 使用 asyncio，同步的 `sqlite3` 调用在 `get_db()` context manager 中会阻塞事件循环
- `aiosqlite` 在 `requirements.txt` 中列出但从未使用

**How to avoid:**
1. 在 `app/database.py` 的 `get_db_connection()` 中启用 WAL 模式（与 `streamlit_app/db.py` 一致）：
```python
conn.execute("PRAGMA journal_mode=WAL")
```
2. 考虑使用 `aiosqlite` 或 `asyncio.to_thread()` 包装同步 DB 操作，避免阻塞事件循环
3. admin API 操作使用较短的事务，减少锁持有时间
4. 如果未来有并发写入压力，考虑迁移到 PostgreSQL（但 MVP 阶段 SQLite + WAL 足够）

**Warning signs:**
- 日志中出现 `sqlite3.OperationalError: database is locked`
- API 请求延迟突然增加（等待数据库锁）
- admin 操作偶尔失败并回滚

**Phase to address:**
Phase 1 添加 admin API 路由时，同步修复 `app/database.py` 启用 WAL 模式。

---

### Pitfall 5: Authentication Redesign Without Migrating Existing Users

**What goes wrong:**
Streamlit 应用有独立的用户认证系统（`users` 表、`hash_password()`、`verify_password()`、自定义 HMAC token）。如果 React 前端重新设计认证方案（比如使用 JWT + OAuth2），但不兼容现有的 `users` 表和密码哈希，已有用户的账号将无法登录。

现有认证的问题：
- 密码签名密钥 `"union_ai_secret"` 硬编码在源码中
- 使用自定义 HMAC 方案（SHA256 截断到 16 hex 字符 = 64 bit 安全性）
- Token 有效期 7 天，无刷新机制
- `bare except:` 吞掉所有异常

**Why it happens:**
- 现有认证方案有明显的安全缺陷，开发者倾向于重写而非复用
- JWT + OAuth2 是 FastAPI 官方推荐的认证方案，看起来是"正确"的方向
- 没有意识到用户表中已有的 `password_hash` 和 `salt` 必须保持兼容

**How to avoid:**
1. **保留现有密码验证逻辑**：`hash_password()` 和 `verify_password()` 使用 PBKDF2-SHA256 + 随机 salt，这本身没问题
2. 将这些函数迁移到 `app/database.py`（或 `app/services/user_service.py`），从 `streamlit_app/db.py` 的实现中迁移
3. Token 生成改用 JWT（`python-jose` 或 `pyjwt`），但密码验证必须兼容现有 `pbkdf2_hmac('sha256', password, salt, 100000)` 格式
4. 签名密钥从环境变量读取，提供默认值保持向后兼容
5. `users` 表 schema 保持不变，React 前端首次注册/登录走新的 JWT token 流程，但密码验证复用现有逻辑

**Warning signs:**
- 认证代码中没有引用 PBKDF2 或现有 salt 机制
- `users` 表 schema 被修改
- 旧密码无法登录

**Phase to address:**
Phase 1 认证层。这是 admin API 的前提条件。

---

### Pitfall 6: Building Admin API Without CORS Restriction — Exposing Management Endpoints

**What goes wrong:**
当前 `app/main.py` 设置 `allow_origins=["*"]`，任何网站都可以向 API 发请求。API 代理端点有 API key 认证保护，但新增的 admin API 端点如果也暴露在 `allow_origins=["*"]` 下，任何恶意网站都可以尝试调用管理接口。

更危险的是：如果 admin API 使用 cookie-based 认证，`allow_origins=["*"]` + `allow_credentials=True` 的组合在现代浏览器中会被拒绝（浏览器要求指定具体 origin 才能发送 credentials）。

**Why it happens:**
- 开发阶段为了方便设置 `allow_origins=["*"]`
- 新增 admin 路由时没有单独配置 CORS 策略
- API 代理和管理面板在同一个 FastAPI 应用中，共享同一套 CORS 中间件

**How to avoid:**
1. admin API 使用 JWT Bearer token 认证（`Authorization: Bearer <token>`），不依赖 cookie
2. 开发阶段可以保持 `allow_origins=["*"]`（因为是 Bearer token，非 cookie-based）
3. 生产环境中收紧 CORS，至少限制 `allow_origins` 为管理面板的实际域名
4. admin API 路由使用独立的路由前缀（如 `/admin/api/`），便于未来单独配置中间件
5. 考虑为 admin API 添加 IP 白名单或额外的 API key 层

**Warning signs:**
- 浏览器控制台出现 CORS 错误（开发阶段突然无法调用 API）
- `allow_credentials=True` 与 `allow_origins=["*"]` 同时存在
- admin API 可以从任意第三方网站调用

**Phase to address:**
Phase 1 API 路由设计时确定认证方案。CORS 配置在部署阶段收紧。

---

### Pitfall 7: Custom Font Loading Performance — Four Web Fonts Blocking Render

**What goes wrong:**
DESIGN.md 要求 4 种字体：DM Sans（主 UI）、Outfit（展示标题）、Poppins（中间层级）、Roboto（数据/技术场景）。如果同步加载 4 个 web 字体，首次渲染会被阻塞，用户看到白屏或 FOUT（Flash of Unstyled Text）。

每种字体的多个 weight（400、500、600、700）和 size 变体会导致字体文件总体积超过 500KB，严重影响移动端加载速度。

**Why it happens:**
- Google Fonts 默认通过 `<link>` 标签同步加载
- 字体子集化（subsetting）经常被忽略
- Tailwind CSS 的 `@font-face` 配置如果不正确，会导致浏览器下载不必要的字体变体

**How to avoid:**
1. 使用 `font-display: swap` 确保文字立即显示（使用 fallback 字体），字体加载完成后替换
2. 只加载实际使用的 weight：DM Sans（400、500、700），Outfit（500、600），Poppins（500），Roboto（400、500）
3. 使用 `@font-face` 自托管字体文件，避免 Google Fonts 的第三方请求延迟
4. Roboto 可以用系统字体 fallback（Android 和 Chrome OS 自带 Roboto）
5. DM Sans 作为主 UI 字体优先加载，Outfit/Poppins 可延迟加载
6. 使用 `<link rel="preload">` 预加载关键字体

**Warning signs:**
- Lighthouse 报告"消除渲染阻塞资源"
- 首屏白屏时间超过 2 秒
- 文字在加载过程中闪烁或跳变

**Phase to address:**
Phase 2（UI 组件开发）定义字体加载策略。性能验证在部署阶段。

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| 复制 `streamlit_app/db.py` 的函数到新文件 | 快速开始写 admin API | 第三套重复代码，schema 漂移风险极大 | **绝不** — 必须迁移到 `app/database.py` |
| 用 `fetch` + `useState` 管理所有服务端数据 | 不引入额外依赖 | 手动管理 loading/error/cache 状态，代码膨胀，数据陈旧 | 仅原型验证阶段 |
| admin API 不加分页 | 实现简单 | 数据量增长后响应变慢，`get_call_logs` 已经有分页需求 | 仅在确认数据量 <100 条时 |
| 不做请求/响应类型定义 | 写代码快 | 前后端字段不一致，调试困难 | **绝不** — 至少用 TypeScript interface |
| 忽略 DESIGN.md 的精确 Token 值 | 快速出页面 | 视觉不一致，用户不满意（Gradio 迁移失败的根本原因） | **绝不** — 这是项目的核心约束 |
| 同容器用 FastAPI 直接提供静态文件 | 部署简单 | 高并发时 FastAPI 处理静态文件效率低 | MVP 阶段可接受，单用户管理面板不需要 Nginx |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI StaticFiles 提供 React 构建 | `app.mount("/", StaticFiles(...))` 放在 API 路由之前，导致所有 API 返回 HTML | 用带前缀的 catch-all（`/admin/{path}`），放在所有 API 路由之后注册 |
| React 调用 admin API | 请求路径用相对路径 `/admin/api/...`，部署到同域后正确，但开发时需要代理 | Vite 开发时配置 `proxy`，生产时 React 构建产物由 FastAPI 提供，自然同域 |
| JWT Token 管理 | 存在 `localStorage`，XSS 攻击可窃取 | 存在 React 状态（内存），或使用 `httpOnly` cookie + CSRF 保护 |
| snake_case vs camelCase | 后端返回 `api_key`，前端期望 `apiKey`，字段映射错误 | 在 API 层统一：要么 FastAPI 返回 camelCase（Pydantic `alias_generator`），要么前端做转换层 |
| Excel 导入/导出 | 前端无法直接操作 SQLite，但后端有 pandas/openpyxl 依赖 | 保留 Excel 导入/导出为后端 API 端点，前端只负责文件上传/下载 |
| Vite 构建路径 | `base` 配置默认 `/`，但 admin 面板可能部署在 `/admin/` 子路径 | Vite 配置 `base: '/admin/'`，确保资源路径正确 |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `get_daily_stats()` 用 `date.today()` 而非北京时间 | Docker 容器 UTC 时区下统计数据显示错误日期 | 统一使用 `datetime.now(BEIJING_TZ).date()` | 部署到非 UTC+8 时区的服务器时 |
| 同步 SQLite 阻塞 FastAPI 事件循环 | API 请求延迟高，admin 操作卡住 | 使用 `asyncio.to_thread()` 或 `aiosqlite` | 并发请求 >10 时明显 |
| React 组件每次渲染都重新 fetch | 仪表盘页面频繁请求同一数据，服务器压力增大 | 使用 TanStack Query 缓存 + `staleTime` 配置 | 多个组件需要相同数据时 |
| call_logs 表无限增长 | 查询变慢，数据库文件膨胀 | 添加定期清理或归档机制（不在 MVP 范围，但需预留） | 运行数月后，日志行数 >100 万 |
| 4 种 Web 字体阻塞首次渲染 | 白屏时间长，Lighthouse 分数低 | `font-display: swap` + 预加载 + 子集化 | 3G/慢网络环境下明显 |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| admin API 无认证 | 任何人可管理模型配置、创建 API key | 所有 `/admin/api/` 路由必须验证 JWT token |
| JWT 签名密钥硬编码 | 源码泄露 = token 可伪造 | 密钥从环境变量读取 |
| 保留 `allow_origins=["*"]` + `allow_credentials=True` | 浏览器拒绝 credentials 请求，或暴露 CSRF 攻击面 | admin API 用 Bearer token 而非 cookie |
| API key 明文存储在 SQLite | 数据库泄露 = 所有上游 LLM API key 泄露 | 不在 MVP 范围，但需记录为已知风险 |
| Excel 导出包含 `api_key` 列 | 导出文件泄露敏感信息 | 导出 API 需要认证，且默认不包含 `api_key` 字段 |
| React 构建产物中暴露 API 结构 | 源码地图（source maps）泄露前端逻辑 | 生产构建关闭 source maps |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| 登录后刷新丢失 session | 用户被迫重新登录 | JWT token 持久化到 sessionStorage（XSS 风险可控的管理面板） |
| 删除操作无确认 | 误删模型配置或 API key | 所有破坏性操作添加确认对话框 |
| 操作无反馈（loading/error） | 用户不知道操作是否成功 | 每个异步操作显示 loading 状态 + toast 通知 |
| 长表格无分页/虚拟滚动 | 日志页面卡死 | call_logs 使用分页加载，模型列表数据量小可一次加载 |
| 新创建的 API key 只显示一次 | 用户没来得及复制就再也看不到了 | 创建后显示完整 key，提示"此 key 只显示一次" + 复制按钮 |

## "Looks Done But Isn't" Checklist

- [ ] **路由系统:** SPA 路由在直接访问/刷新时工作 — 验证：在 `/admin/models` 按 F5 刷新
- [ ] **认证流程:** 首次使用时显示注册页面（无用户时） — 验证：清空 `users` 表后访问 admin
- [ ] **认证兼容性:** 现有 Streamlit 用户能用相同密码登录 React 面板 — 验证：用现有 `users` 表数据测试登录
- [ ] **API 代理不受影响:** admin 改造完成后 `/v1/chat/completions` 仍然正常工作 — 验证：用 curl 发送 API 请求
- [ ] **Docker 单容器部署:** React 构建产物在 Docker 中由 FastAPI 正确提供 — 验证：`docker build` + `docker run` + 访问管理面板
- [ ] **Streamlit 完全移除:** `supervisord` 配置不再包含 Streamlit 进程 — 验证：检查 `supervisord.conf` 和 Dockerfile
- [ ] **Excel 导入/导出:** 前端能触发后端的 Excel 操作 — 验证：上传 `.xlsx` 文件并检查模型是否创建
- [ ] **响应式布局:** DESIGN.md 定义的 3 个断点（<768px、768-1024px、>1024px）都能正常显示 — 验证：浏览器 DevTools 模拟移动端
- [ ] **设计系统 Token:** 所有颜色、圆角、阴影、字体与 DESIGN.md 一致 — 验证：像素级对比 DESIGN.md 规范

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| 第三套重复数据访问层 | HIGH | 合并到 `app/database.py`，删除重复文件，修改所有 import |
| 组件库 CSS 覆盖失败 | HIGH | 移除组件库，用 Tailwind 重写受影响的组件 |
| 路由冲突导致 API 不可用 | MEDIUM | 调整 catch-all 路由的范围和注册顺序 |
| SQLite WAL 未启用导致锁定 | LOW | 在 `get_db_connection()` 中添加 `PRAGMA journal_mode=WAL` |
| 认证不兼容现有用户 | HIGH | 保留现有密码验证逻辑，只改 token 生成方式 |
| 字体加载阻塞渲染 | LOW | 添加 `font-display: swap` + preload 标签 |
| snake_case/camelCase 混乱 | MEDIUM | 添加全局 Axios 拦截器做 key 转换 |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 无 admin API 路由 | Phase 1: 基础设施 | 所有 CRUD 操作可通过 curl 完成 |
| 组件库 CSS 覆盖 | Phase 1: 设计系统搭建 | F12 中无 `!important` 覆盖链 |
| SPA 路由冲突 | Phase 1: 部署配置 | 刷新任何 admin 页面不出现 404 |
| SQLite 并发写入 | Phase 1: 数据库层 | `PRAGMA journal_mode` 返回 `wal` |
| 认证不兼容 | Phase 1: 认证层 | 现有 `users` 表的用户可正常登录 |
| CORS 安全 | Phase 1: API 设计 | curl 从第三方 origin 调用 admin API 返回 401 |
| 字体加载性能 | Phase 2: UI 组件 | Lighthouse Performance > 80 |
| 设计系统一致性 | Phase 2: UI 组件 | 像素级对比 DESIGN.md |
| 状态管理膨胀 | Phase 3: 数据集成 | 无手写 loading/error 状态管理代码 |
| Streamlit 残留 | Phase 4: 清理 | `requirements.txt` 无 streamlit，Dockerfile 无 streamlit 进程 |
| Excel 导入/导出 | Phase 3: 数据集成 | 上传/下载 `.xlsx` 文件功能完整 |

## Sources

- 代码库分析：`app/main.py`、`app/database.py`、`streamlit_app/db.py`、`streamlit_app/home.py`
- 项目上下文：`.planning/PROJECT.md`、`.planning/codebase/CONCERNS.md`、`DESIGN.md`
- [StackOverflow: FastAPI + React SPA 路由冲突解决方案](https://stackoverflow.com/questions/62928450/how-to-put-backend-and-frontend-together-returning-react-frontend-from-fastapi)
- [Marmelab: JWT 在 React Admin 中的正确管理方式](https://marmelab.com/blog/2020/07/02/manage-your-jwt-react-admin-authentication-in-memory.html)
- [FastAPI 官方文档: OAuth2 Password + Bearer](https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/)
- [Evil Martians: Tailwind CSS 防混乱最佳实践](https://evilmartians.com/chronicles/5-best-practices-for-preventing-chaos-in-tailwind-css)
- [Tailwind CSS 官方: Catalyst 应用 UI Kit](https://tailwindcss.com/blog/introducing-catalyst)
- [TestDriven.io: FastAPI + React 全栈 SPA 教程](https://testdriven.io/blog/fastapi-react/)
- [StackOverflow: JSON 命名约定 snake_case vs camelCase](https://stackoverflow.com/questions/5543490/json-naming-convention-snake-case-camelcase-or-pascalcase)

---
*Pitfalls research for: React admin panel + FastAPI LLM API proxy integration*
*Researched: 2026-04-15*
