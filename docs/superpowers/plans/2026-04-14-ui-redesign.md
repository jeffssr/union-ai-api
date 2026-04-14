# UI 重设计 - MiniMax 风格管理后台 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Streamlit 管理后台的 UI 完整重设计为 MiniMax 风格（顶部导航、多色渐变卡片、品牌配色），不修改任何业务逻辑。

**Architecture:** 在单个文件 `streamlit_app/home.py` 中替换 CSS 样式块和 HTML 模板。通过 `st.markdown(unsafe_allow_html=True)` 渲染自定义导航栏和卡片组件，通过 CSS 覆盖 Streamlit 默认组件样式。隐藏侧边栏，改用顶部导航。

**Tech Stack:** Python, Streamlit 1.31.1, HTML/CSS, Google Fonts CDN

**Spec:** `docs/superpowers/specs/2026-04-14-ui-redesign-design.md`

**验证方式:** 每个任务完成后运行 `cd /d D:\Jimmy\Softwares\union-ai-api && streamlit run streamlit_app/home.py --server.port 8501` 在浏览器中目视验证。

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `streamlit_app/home.py` | 修改 | 全部 UI 变更（CSS、导航、页面模板） |
| `streamlit_app/db.py` | 不修改 | 数据库操作，完全不动 |

`home.py` 当前结构（行号参考）：
- 1-33: 导入 + `set_page_config`
- 34-94: `<style>` CSS 块
- 96-108: session_state 初始化
- 110-163: 认证函数（token/cookie）
- 165-238: 登录/注册页面
- 240-261: 修改密码
- 263-328: 导入导出函数
- 330-364: `render_model_cards()`
- 366-373: 认证状态检查
- 375-410: 侧边栏（将被替换为顶部导航）
- 414-442: Dashboard 页
- 444-630: 模型配置页
- 632-660: API Key 页
- 662-689: 调用记录页

---

### Task 1: 全局 CSS 基础 + 页面配置

**Files:**
- Modify: `streamlit_app/home.py:1-94`（导入、page_config、CSS 样式块）

**说明:** 替换整个 CSS 样式块为 MiniMax 风格，引入 Google Fonts，隐藏侧边栏，更新页面配置。

- [ ] **Step 1: 更新 `set_page_config` 和 CSS 样式块**

将 `home.py` 第 27-94 行（从 `st.set_page_config` 到 `""", unsafe_allow_html=True)` 结尾）替换为以下内容：

```python
st.set_page_config(
    page_title="Union-AI-API",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式 - MiniMax Design System
st.markdown("""
<style>
    /* ========== 字体引入 ========== */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@500;600&display=swap');

    /* ========== 全局基础 ========== */
    :root {
        --brand-blue: #1456f0;
        --sky-blue: #3daeff;
        --brand-pink: #ea5ec1;
        --deep-blue: #17437d;
        --primary-500: #3b82f6;
        --primary-light: #60a5fa;
        --dark-bg: #181e25;
        --text-primary: #222222;
        --text-secondary: #45515e;
        --text-muted: #8e8e93;
        --border: #e5e7eb;
        --divider: #f2f3f5;
        --input-bg: #f2f3f5;
        --success-bg: #e8ffea;
        --success-text: #16a34a;
        --danger: #ef4444;
        --radius-sm: 8px;
        --radius-md: 13px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --radius-pill: 9999px;
        --shadow-card: rgba(0,0,0,0.08) 0px 4px 6px;
        --shadow-brand: rgba(44,30,116,0.16) 0px 0px 15px;
        --shadow-elevated: rgba(36,36,36,0.08) 0px 12px 16px -4px;
    }

    * {
        font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }

    /* ========== 隐藏侧边栏 ========== */
    div[data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* ========== 隐藏 Streamlit 默认元素 ========== */
    header[data-testid="stHeader"],
    .stDeployButton {
        display: none !important;
    }

    /* ========== 主容器调整 ========== */
    .stMainBlockContainer {
        padding-top: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stMain"] > div:first-child {
        padding-top: 0 !important;
    }

    /* ========== 导航栏 ========== */
    .minimax-nav {
        background: #ffffff;
        border-bottom: 1px solid #f2f3f5;
        padding: 12px 32px;
        display: flex;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 1000;
        margin: -2rem -2rem 1.5rem -2rem;
    }
    .minimax-nav .nav-logo {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 18px;
        font-weight: 600;
        color: #18181b;
        margin-right: 40px;
        white-space: nowrap;
    }
    .minimax-nav .nav-items {
        display: flex;
        gap: 4px;
        flex: 1;
    }
    .minimax-nav .nav-item {
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 14px;
        font-weight: 500;
        color: #8e8e93;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }
    .minimax-nav .nav-item:hover {
        color: #45515e;
        background: rgba(0,0,0,0.03);
    }
    .minimax-nav .nav-item.active {
        background: rgba(0,0,0,0.05);
        color: #18181b;
    }
    .minimax-nav .nav-right {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 13px;
        color: #45515e;
    }
    .minimax-nav .nav-user {
        color: #45515e;
        font-weight: 500;
    }
    .minimax-nav .nav-logout {
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        color: #8e8e93;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e5e7eb;
        background: #fff;
    }
    .minimax-nav .nav-logout:hover {
        color: #ef4444;
        border-color: #ef4444;
    }

    /* ========== 登录页 ========== */
    .login-wrapper {
        min-height: 100vh;
        background: linear-gradient(135deg, #1456f0 0%, #ea5ec1 50%, #3daeff 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: -2rem;
        padding: 2rem;
    }
    .login-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 40px;
        width: 380px;
        box-shadow: rgba(44,30,116,0.16) 0px 0px 30px;
    }
    .login-card .login-title {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 28px;
        font-weight: 600;
        color: #222222;
        text-align: center;
        margin-bottom: 4px;
    }
    .login-card .login-subtitle {
        font-size: 13px;
        color: #8e8e93;
        text-align: center;
        margin-bottom: 28px;
    }
    .login-card .login-info {
        background: #eff6ff;
        color: #1d4ed8;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 13px;
        margin-bottom: 20px;
        text-align: center;
    }

    /* ========== 统计摘要卡片 ========== */
    .stat-cards {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }
    .stat-card {
        flex: 1;
        border-radius: 20px;
        padding: 20px 24px;
        color: #fff;
        box-shadow: rgba(44,30,116,0.16) 0px 0px 15px;
    }
    .stat-card .stat-label {
        font-size: 12px;
        opacity: 0.8;
        margin-bottom: 4px;
    }
    .stat-card .stat-value {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 28px;
        font-weight: 600;
    }

    /* ========== 模型卡片 ========== */
    .model-card-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .model-card {
        border-radius: 20px;
        padding: 24px;
        color: #fff;
        box-shadow: rgba(44,30,116,0.16) 0px 0px 15px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .model-card:hover {
        transform: translateY(-2px);
        box-shadow: rgba(44,30,116,0.2) 0px 0px 20px;
    }
    .model-card.unavailable {
        background: linear-gradient(135deg, #8e8e93, #45515e) !important;
        opacity: 0.6;
    }
    .model-card .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .model-card .card-name {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 18px;
        font-weight: 600;
    }
    .model-card .card-badge {
        background: rgba(255,255,255,0.25);
        padding: 3px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 500;
    }
    .model-card .card-badge.status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        padding: 0;
        background: #4ade80;
        box-shadow: 0 0 8px #4ade80;
    }
    .model-card .card-info {
        font-size: 12px;
        opacity: 0.85;
        margin: 4px 0;
    }
    .model-card .card-usage {
        display: flex;
        gap: 20px;
        font-size: 12px;
        margin-top: 12px;
        opacity: 0.9;
    }
    .model-card .card-progress {
        margin-top: 10px;
        background: rgba(255,255,255,0.2);
        border-radius: 9999px;
        height: 4px;
        overflow: hidden;
    }
    .model-card .card-progress-fill {
        background: #fff;
        border-radius: 9999px;
        height: 4px;
        transition: width 0.3s;
    }

    /* ========== 白色内容卡片 ========== */
    .content-card {
        background: #fff;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: rgba(0,0,0,0.08) 0px 4px 6px;
        padding: 24px;
        margin-bottom: 16px;
    }
    .content-card .card-title {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #222222;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ========== 标签徽章 ========== */
    .badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 500;
    }
    .badge-default {
        background: #e8ffea;
        color: #16a34a;
    }
    .badge-priority {
        background: #eff6ff;
        color: #1456f0;
    }
    .badge-status {
        font-size: 12px;
        color: #8e8e93;
    }

    /* ========== 代码块展示 ========== */
    .key-display {
        background: #f8fafc;
        border-left: 3px solid #1456f0;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #222222;
        word-break: break-all;
        margin: 8px 0;
    }

    /* ========== 按钮覆盖样式 ========== */
    .stButton > button {
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }

    /* ========== 表格样式覆盖 ========== */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #e5e7eb !important;
    }
    .stDataFrame th {
        background-color: #f8fafc !important;
        color: #45515e !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    .stDataFrame td {
        font-size: 13px !important;
        color: #222222 !important;
    }
    .stDataFrame tr:nth-child(even) {
        background-color: #fafbfc !important;
    }

    /* ========== 表单输入框覆盖 ========== */
    .stTextInput > div > div > input,
    .stTextInput input {
        background-color: #f2f3f5 !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextInput input:focus {
        border-color: #1456f0 !important;
        box-shadow: 0 0 0 2px rgba(20, 86, 240, 0.1) !important;
    }

    /* ========== Number Input 覆盖 ========== */
    .stNumberInput input {
        border-radius: 8px !important;
    }

    /* ========== Selectbox 覆盖 ========== */
    .stSelectbox > div > div {
        border-radius: 8px !important;
    }

    /* ========== Expander 覆盖 ========== */
    .streamlit-expanderHeader {
        border-radius: 12px !important;
        font-weight: 500 !important;
    }

    /* ========== 页面标题 ========== */
    .page-title {
        font-family: 'Outfit', 'DM Sans', sans-serif;
        font-size: 22px;
        font-weight: 600;
        color: #222222;
        margin-bottom: 20px;
    }
    .section-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 16px;
        font-weight: 500;
        color: #222222;
        margin-bottom: 12px;
    }

    /* ========== 分隔线 ========== */
    hr {
        border: none !important;
        border-top: 1px solid #f2f3f5 !important;
        margin: 20px 0 !important;
    }

    /* ========== 操作栏 ========== */
    .action-bar {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        align-items: flex-start;
    }
    .action-bar .action-btn {
        padding: 8px 20px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid #e5e7eb;
        background: #fff;
        color: #333;
    }
    .action-bar .action-btn:hover {
        border-color: #ccc;
    }
    .action-bar .action-btn.primary {
        background: #1456f0;
        color: #fff;
        border-color: #1456f0;
    }
    .action-bar .action-btn.primary:hover {
        background: #2563eb;
    }

    /* ========== 提示文字 ========== */
    .hint-text {
        font-size: 13px;
        color: #8e8e93;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)
```

- [ ] **Step 2: 启动 Streamlit 验证基础 CSS 生效**

运行: `streamlit run streamlit_app/home.py --server.port 8501`

验证：
- 侧边栏已隐藏
- Streamlit 默认顶部工具栏已隐藏
- 页面字体变为 DM Sans（需在登录页看到变化）

- [ ] **Step 3: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 替换全局 CSS 为 MiniMax 设计系统风格"
```

---

### Task 2: 顶部导航栏组件

**Files:**
- Modify: `streamlit_app/home.py:375-410`（侧边栏部分替换为导航栏函数 + 导航渲染逻辑）

**说明:** 创建 `render_nav_bar()` 函数替代现有侧边栏，使用 `st.session_state` 管理页面切换。

- [ ] **Step 1: 在 `render_model_cards()` 函数后面添加导航栏渲染函数**

在第 364 行之后（`render_model_cards` 函数结束后）添加新函数：

```python
def render_nav_bar():
    """渲染顶部导航栏"""
    pages = ["数据概览", "模型配置", "API Key", "调用记录"]
    current = st.session_state.current_page

    # 导航项 HTML
    nav_items_html = ""
    for page_name in pages:
        active_class = "active" if page_name == current else ""
        nav_items_html += f'<span class="nav-item {active_class}">{page_name}</span>'

    st.markdown(f"""
    <div class="minimax-nav">
        <div class="nav-logo">Union-AI-API</div>
        <div class="nav-items">
            {nav_items_html}
        </div>
        <div class="nav-right">
            <span class="nav-user">{st.session_state.username}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 导航按钮（用于点击切换页面）
    nav_cols = st.columns([1, 1, 1, 1, 2])
    for i, page_name in enumerate(pages):
        with nav_cols[i]:
            if st.button(
                page_name,
                key=f"nav_{page_name}",
                type="primary" if page_name == current else "secondary"
            ):
                st.session_state.current_page = page_name
                st.rerun()
```

- [ ] **Step 2: 替换主界面的侧边栏和页面路由部分**

将第 381-412 行（从 `else:` 已登录开始的整个侧边栏 + 页面路由块）替换为：

```python
else:
    # 已登录，显示主界面
    pages = {
        "数据概览": "dashboard",
        "模型配置": "models",
        "API Key": "apikeys",
        "调用记录": "logs"
    }

    # 渲染顶部导航栏
    render_nav_bar()

    # 退出登录按钮（放在导航栏下方右侧）
    col_logout1, col_logout2, col_logout3, col_logout4, col_logout5 = st.columns([1, 1, 1, 1, 1])
    with col_logout5:
        if st.button("退出登录", use_container_width=True):
            logout()

    # 修改密码
    with st.expander("修改密码"):
        show_change_password()

    page = pages[st.session_state.current_page]
```

**注意：** 这段代码后面的各页面 `if page == "dashboard":` 等分支逻辑保持不变，只是去掉了 `with st.sidebar:` 的缩进。

- [ ] **Step 3: 更新 session_state 默认值**

将第 98 行的默认页面从 `"📊 数据概览"` 改为 `"数据概览"`：

```python
if "current_page" not in st.session_state:
    st.session_state.current_page = "数据概览"
```

- [ ] **Step 4: 启动验证导航栏**

运行: `streamlit run streamlit_app/home.py --server.port 8501`

验证：
- 顶部显示白色导航栏，左侧 "Union-AI-API" logo
- 药丸按钮导航项，当前页高亮
- 右侧显示用户名
- 点击导航项可切换页面
- 侧边栏已完全隐藏

- [ ] **Step 5: 提交**

```bash
git add streamlit_app/home.py
git commit -m "feat: 用顶部药丸导航栏替换 Streamlit 侧边栏"
```

---

### Task 3: 登录/注册页面重设计

**Files:**
- Modify: `streamlit_app/home.py:165-261`（`show_login_page` 和 `show_register_page` 函数）

**说明:** 用品牌渐变背景 + 毛玻璃白色卡片重新设计登录和注册页面。

- [ ] **Step 1: 替换 `show_login_page()` 函数（第 165-205 行）**

将整个 `show_login_page()` 函数替换为：

```python
def show_login_page():
    """显示登录页面"""
    st.markdown("""
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-title">Union-AI-API</div>
            <div class="login-subtitle">统一多模型 AI 代理服务</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 检查是否已有用户
    if not has_users():
        st.session_state.show_register = True
        st.rerun()

    # 居中表单
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submitted = st.form_submit_button("登录", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                elif login_user(username, password):
                    st.session_state.is_logged_in = True
                    st.session_state.username = username
                    auth_token = generate_auth_token(username)
                    expires_date = (datetime.now() + timedelta(days=7)).strftime("%a, %d %b %Y %H:%M:%S GMT")
                    st.markdown(f"""
                    <script>
                    document.cookie = "union_ai_auth={auth_token}; expires={expires_date}; path=/; SameSite=Lax";
                    sessionStorage.setItem('union_ai_auth', '{auth_token}');
                    </script>
                    """, unsafe_allow_html=True)
                    st.query_params["auth"] = auth_token
                    st.success("登录成功！")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
```

- [ ] **Step 2: 替换 `show_register_page()` 函数（第 207-238 行）**

将整个 `show_register_page()` 函数替换为：

```python
def show_register_page():
    """显示注册页面"""
    st.markdown("""
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-title">Union-AI-API</div>
            <div class="login-subtitle">统一多模型 AI 代理服务</div>
            <div class="login-info">首次使用，请创建管理员账号</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("register_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            submitted = st.form_submit_button("注册", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("请输入用户名和密码")
                elif password != confirm_password:
                    st.error("两次输入的密码不一致")
                elif len(password) < 4:
                    st.error("密码长度至少为4位")
                else:
                    if create_user(username, password):
                        st.success("注册成功！请登录")
                        st.session_state.show_register = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("用户名已存在")
```

- [ ] **Step 3: 启动验证登录/注册页面**

运行: `streamlit run streamlit_app/home.py --server.port 8501`

验证：
- 登录页有品牌渐变背景（蓝→粉→天蓝）
- 居中毛玻璃白色卡片
- 标题 "Union-AI-API" + 副标题
- 输入框和登录按钮在新样式中显示正常
- 如无用户，注册页同样风格，带浅蓝色提示条

- [ ] **Step 4: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 重设计登录/注册页面为渐变背景毛玻璃卡片风格"
```

---

### Task 4: 数据概览页重设计

**Files:**
- Modify: `streamlit_app/home.py:330-442`（`render_model_cards()` 函数 + dashboard 页面块）

**说明:** 添加统计摘要卡片，重新设计模型卡片为多色渐变风格，更新表格标题。

- [ ] **Step 1: 重写 `render_model_cards()` 函数（第 330-364 行）**

替换为：

```python
# 模型卡片渐变色板
GRADIENT_COLORS = [
    "linear-gradient(135deg, #1456f0, #3b82f6)",
    "linear-gradient(135deg, #ea5ec1, #9333ea)",
    "linear-gradient(135deg, #3daeff, #1456f0)",
    "linear-gradient(135deg, #f97316, #ea5ec1)",
    "linear-gradient(135deg, #10b981, #3b82f6)",
]

def render_model_cards(stats):
    """渲染模型卡片列表 - 多色渐变风格"""
    sorted_stats = sorted(stats, key=lambda x: x['priority'], reverse=True)

    cards_html = ""
    for idx, stat in enumerate(sorted_stats):
        is_available = (stat['used_tokens'] < stat['daily_token_limit'] and
                       stat['used_calls'] < stat['daily_call_limit'] and
                       stat['is_active'] == 1)

        token_usage_pct = min(stat['used_tokens'] / stat['daily_token_limit'] * 100, 100) if stat['daily_token_limit'] > 0 else 0

        if is_available:
            gradient = GRADIENT_COLORS[idx % len(GRADIENT_COLORS)]
            if stat['is_default_model'] == 1:
                header_right = '<span class="card-badge">默认</span>'
            else:
                header_right = '<span class="card-badge status-dot"></span>'
            progress_width = f"{token_usage_pct}%"

            cards_html += f"""
            <div class="model-card" style="background:{gradient};">
                <div class="card-header">
                    <span class="card-name">{stat['name']}</span>
                    {header_right}
                </div>
                <div class="card-info">Model ID: {stat.get('model_id', 'N/A')}</div>
                <div class="card-info">优先级: {stat['priority']}</div>
                <div class="card-usage">
                    <span>Token: {stat['used_tokens']:,} / {stat['daily_token_limit']:,}</span>
                    <span>调用: {stat['used_calls']:,} / {stat['daily_call_limit']:,}</span>
                </div>
                <div class="card-progress">
                    <div class="card-progress-fill" style="width:{progress_width};"></div>
                </div>
            </div>"""
        else:
            cards_html += f"""
            <div class="model-card unavailable">
                <div class="card-header">
                    <span class="card-name">{stat['name']}</span>
                    <span class="card-badge status-dot" style="background:#888;box-shadow:none;width:10px;height:10px;padding:0;"></span>
                </div>
                <div class="card-info">Model ID: {stat.get('model_id', 'N/A')}</div>
                <div class="card-info">优先级: {stat['priority']}</div>
                <div class="card-usage">
                    <span>Token: {stat['used_tokens']:,} / {stat['daily_token_limit']:,}</span>
                    <span>调用: {stat['used_calls']:,} / {stat['daily_call_limit']:,}</span>
                </div>
                <div class="card-progress">
                    <div class="card-progress-fill" style="width:100%;"></div>
                </div>
            </div>"""

    st.markdown(f'<div class="model-card-grid">{cards_html}</div>', unsafe_allow_html=True)
```

- [ ] **Step 2: 重写 dashboard 页面块**

将 `if page == "dashboard":` 后面的内容（约第 414-442 行）替换为：

```python
    if page == "dashboard":
        st.markdown('<div class="page-title">数据概览</div>', unsafe_allow_html=True)

        stats = get_daily_stats()

        if not stats:
            st.info("暂无模型配置，请前往「模型配置」添加模型")
        else:
            # 统计摘要卡片
            total_tokens = sum(s['used_tokens'] for s in stats)
            total_calls = sum(s['used_calls'] for s in stats)
            active_models = sum(1 for s in stats if s['is_active'] == 1 and s['used_tokens'] < s['daily_token_limit'] and s['used_calls'] < s['daily_call_limit'])

            st.markdown(f"""
            <div class="stat-cards">
                <div class="stat-card" style="background:linear-gradient(135deg, #1456f0, #3b82f6);">
                    <div class="stat-label">今日 Token 用量</div>
                    <div class="stat-value">{total_tokens:,}</div>
                </div>
                <div class="stat-card" style="background:linear-gradient(135deg, #ea5ec1, #9333ea);">
                    <div class="stat-label">今日调用次数</div>
                    <div class="stat-value">{total_calls:,}</div>
                </div>
                <div class="stat-card" style="background:linear-gradient(135deg, #3daeff, #1456f0);">
                    <div class="stat-label">活跃模型</div>
                    <div class="stat-value">{active_models}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 模型卡片
            render_model_cards(stats)

            # 详细数据表格
            st.markdown('<div class="section-title">详细数据</div>', unsafe_allow_html=True)
            df = pd.DataFrame(stats)
            df['剩余 Token'] = df['daily_token_limit'] - df['used_tokens']
            df['剩余调用次数'] = df['daily_call_limit'] - df['used_calls']
            df['Token 使用率'] = (df['used_tokens'] / df['daily_token_limit'] * 100).round(1).astype(str) + '%'
            df['调用使用率'] = (df['used_calls'] / df['daily_call_limit'] * 100).round(1).astype(str) + '%'
            df['是否可用'] = df.apply(lambda x: '可用' if (x['used_tokens'] < x['daily_token_limit'] and
                                                              x['used_calls'] < x['daily_call_limit'] and
                                                              x['is_active'] == 1) else '不可用', axis=1)
            df['默认模型'] = df['is_default_model'].apply(lambda x: '是' if x == 1 else '')

            display_df = df[['name', 'model_id', '是否可用', 'used_calls', 'daily_call_limit', '剩余调用次数',
                            '调用使用率', 'used_tokens', 'daily_token_limit', '剩余 Token', 'Token 使用率',
                            '默认模型', 'priority']].copy()
            display_df.columns = ['模型名称', 'Model ID', '是否可用', '已用调用', '调用限额', '剩余调用',
                                 '调用使用率', '已用 Token', 'Token 限额', '剩余 Token', 'Token 使用率',
                                 '默认模型', '优先级']
            st.dataframe(display_df, hide_index=True, use_container_width=True)
```

- [ ] **Step 3: 启动验证 Dashboard**

运行: `streamlit run streamlit_app/home.py --server.port 8501`

验证：
- 页面标题 "数据概览"（无 emoji）
- 3 张渐变统计摘要卡片
- 模型卡片使用不同颜色渐变
- 不可用模型灰色 + 半透明
- 卡片有进度条
- 表格有自定义样式

- [ ] **Step 4: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 重设计数据概览页 - 渐变摘要卡片 + 多色模型卡片"
```

---

### Task 5: 模型配置页重设计

**Files:**
- Modify: `streamlit_app/home.py` 中 `elif page == "models":` 块（约第 444-630 行）

**说明:** 更新操作栏、全局设置卡片、模型列表卡片样式。去掉 emoji 前缀，用自定义 HTML 标签替代。

- [ ] **Step 1: 替换模型配置页面块**

将 `elif page == "models":` 后面的整个块替换为：

```python
    elif page == "models":
        st.markdown('<div class="page-title">模型配置</div>', unsafe_allow_html=True)

        models = get_all_models()

        # 操作栏
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        with col1:
            excel_data = export_models_to_excel()
            if excel_data:
                st.download_button(
                    label="导出配置",
                    data=excel_data,
                    file_name=f"models_export_{date.today().isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.button("导出配置", disabled=True, use_container_width=True)

        with col2:
            with st.expander("导入配置"):
                st.markdown("### 导入模型配置")
                uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'], key="import_file")
                if uploaded_file is not None:
                    if st.button("开始导入", key="btn_import"):
                        success, message = import_models_from_excel(uploaded_file)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)

        with col3:
            if st.button("添加模型", use_container_width=True, type="primary"):
                st.session_state.show_add_model = True
                st.rerun()

        st.markdown("---")

        # 全局设置卡片
        st.markdown("""
        <div class="content-card">
            <div class="card-title">全局设置</div>
        </div>
        """, unsafe_allow_html=True)
        auto_switch_global = st.checkbox(
            "启用自动切换模型",
            value=get_auto_switch_status()
        )
        if auto_switch_global != get_auto_switch_status():
            set_auto_switch_status(auto_switch_global)
            st.success("设置已保存")
            time.sleep(0.5)
            st.rerun()
        st.markdown('<div class="hint-text">开启后：系统按优先级自动切换所有启用的模型 | 关闭后：所有请求固定使用默认模型</div>', unsafe_allow_html=True)

        st.markdown("---")

        # 添加新模型
        if st.session_state.show_add_model:
            with st.expander("添加新模型", expanded=True):
                copy_data = st.session_state.copy_model_data

                with st.form("add_model_form", clear_on_submit=True):
                    name = st.text_input("模型名称",
                                        value=copy_data['name'] if copy_data else "",
                                        placeholder="例如：GPT-4")
                    api_url = st.text_input("API 地址",
                                           value=copy_data['api_url'] if copy_data else "",
                                           placeholder="https://api.openai.com/v1/chat/completions")
                    api_key = st.text_input("API Key",
                                           value=copy_data['api_key'] if copy_data else "",
                                           type="password")
                    model_id = st.text_input("Model ID（选填，如 gpt-4、claude-3 等）",
                                            value=copy_data['model_id'] if copy_data else "",
                                            placeholder="如留空则使用请求中的 model 参数")
                    col1, col2 = st.columns(2)
                    with col1:
                        daily_limit = st.number_input("每日 Token 上限",
                                                      value=copy_data['daily_token_limit'] if copy_data else 100000,
                                                      min_value=1)
                    with col2:
                        daily_call_limit = st.number_input("每日调用次数上限",
                                                           value=copy_data['daily_call_limit'] if copy_data else 1000,
                                                           min_value=1)
                    priority = st.number_input("优先级 (数字越大越优先)",
                                              value=copy_data['priority'] if copy_data else 0,
                                              min_value=0)

                    submitted = st.form_submit_button("添加模型")
                    if submitted:
                        if name and api_url and api_key:
                            create_model(name, api_url, api_key, model_id, daily_limit, daily_call_limit, priority)
                            st.success("模型添加成功！")
                            st.session_state.copy_model_data = None
                            st.session_state.show_add_model = False
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("请填写所有必填字段")

        # 模型列表
        st.markdown('<div class="section-title">模型列表</div>', unsafe_allow_html=True)

        if models:
            default_model_id = None
            for m in models:
                if m.get('is_default_model', 0) == 1:
                    default_model_id = m['config_id']
                    break

            for model in models:
                is_default = model.get('is_default_model', 0) == 1

                # 卡片头部标签
                badges = f'<span class="badge badge-priority">优先级 {model["priority"]}</span>'
                if is_default:
                    badges += ' <span class="badge badge-default">默认模型</span>'

                with st.expander(f"**{model['name']}** {badges}"):
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
                    with col_btn1:
                        if st.button("复制配置", key=f"copy_{model['config_id']}"):
                            st.session_state.copy_model_data = {
                                'name': model['name'] + ' (复制)',
                                'api_url': model['api_url'],
                                'api_key': model['api_key'],
                                'model_id': model.get('model_id', ''),
                                'daily_token_limit': model['daily_token_limit'],
                                'daily_call_limit': model['daily_call_limit'],
                                'priority': model['priority']
                            }
                            st.session_state.show_add_model = True
                            st.rerun()

                    with col_btn2:
                        pass

                    with st.form(f"edit_model_{model['config_id']}", clear_on_submit=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_name = st.text_input("模型名称", value=model['name'], key=f"name_{model['config_id']}")
                            new_api_url = st.text_input("API 地址", value=model['api_url'], key=f"url_{model['config_id']}")
                            new_api_key = st.text_input("API Key", value=model['api_key'], type="password", key=f"key_{model['config_id']}")
                            new_model_id = st.text_input("Model ID（选填）", value=model.get('model_id', ''), key=f"model_id_{model['config_id']}")
                        with col2:
                            new_limit = st.number_input("每日 Token 上限", value=model['daily_token_limit'], min_value=1, key=f"limit_{model['config_id']}")
                            new_call_limit = st.number_input("每日调用次数上限", value=model['daily_call_limit'], min_value=1, key=f"call_limit_{model['config_id']}")
                            new_priority = st.number_input("优先级", value=model['priority'], min_value=0, key=f"prio_{model['config_id']}")

                        st.markdown("---")

                        col3, col4 = st.columns(2)
                        with col3:
                            if st.form_submit_button("更新"):
                                update_model(model['config_id'], new_name, new_api_url, new_api_key, new_model_id, new_limit, new_call_limit, 1 if is_default else 0, new_priority)
                                st.success("模型已更新")
                                time.sleep(1)
                                st.rerun()
                        with col4:
                            if st.form_submit_button("删除"):
                                delete_model(model['config_id'])
                                st.success("模型已删除")
                                time.sleep(1)
                                st.rerun()

            st.markdown("---")
            st.markdown('<div class="section-title">默认模型设置</div>', unsafe_allow_html=True)
            st.markdown('<div class="hint-text">仅在关闭自动切换时使用</div>', unsafe_allow_html=True)

            if not auto_switch_global:
                model_options = {}
                for m in models:
                    model_options[f"{m['name']} (优先级：{m['priority']})"] = m['config_id']

                if model_options:
                    current_default = default_model_id if default_model_id else next(iter(model_options.values()))
                    selected = st.selectbox(
                        "选择默认模型",
                        options=list(model_options.values()),
                        format_func=lambda x: next((k for k, v in model_options.items() if v == x), ""),
                        index=list(model_options.values()).index(current_default) if current_default in model_options.values() else 0
                    )

                    if st.button("保存默认模型"):
                        for m in models:
                            is_default = (m['config_id'] == selected)
                            update_model(m['config_id'], m['name'], m['api_url'], m['api_key'], m.get('model_id', ''), m['daily_token_limit'], m['daily_call_limit'], 1 if is_default else 0, m['priority'])
                        st.success("默认模型已保存")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("没有模型可选")
            else:
                st.info("自动切换已开启，无需设置默认模型")
        else:
            st.info("暂无模型配置")
```

- [ ] **Step 2: 启动验证模型配置页**

验证：
- 操作栏按钮水平排列
- 全局设置在白色卡片中
- 模型列表每个模型可展开编辑
- 去掉了 emoji 前缀
- 功能不变（添加/编辑/删除/复制/导入/导出）

- [ ] **Step 3: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 重设计模型配置页 - 卡片式布局，去掉 emoji 前缀"
```

---

### Task 6: API Key 管理页重设计

**Files:**
- Modify: `streamlit_app/home.py` 中 `elif page == "apikeys":` 块

- [ ] **Step 1: 替换 API Key 页面块**

将 `elif page == "apikeys":` 后面的块替换为：

```python
    elif page == "apikeys":
        st.markdown('<div class="page-title">API Key 管理</div>', unsafe_allow_html=True)

        with st.expander("生成新 API Key"):
            with st.form("add_api_key_form", clear_on_submit=True):
                name = st.text_input("Key 名称", placeholder="例如：我的应用", key="key_name")
                submitted = st.form_submit_button("生成")
                if submitted:
                    if name:
                        result = create_api_key(name)
                        st.success("API Key 生成成功！")
                        st.markdown(f"""
                        <div class="key-display">Key ID: {result['key_id']}</div>
                        <div class="key-display">API Key: {result['api_key']}</div>
                        """, unsafe_allow_html=True)
                        st.warning("请立即复制 API Key，它不会被保存，只能生成新的。")
                    else:
                        st.error("请输入名称")

        st.markdown('<div class="section-title">API Key 列表</div>', unsafe_allow_html=True)
        api_keys = get_all_api_keys()

        if api_keys:
            for key in api_keys:
                with st.expander(f"**{key['name']}**"):
                    st.markdown(f'<div class="key-display">{key["api_key"]}</div>', unsafe_allow_html=True)
                    if st.button(f"删除", key=f"del_{key['key_id']}"):
                        delete_api_key(key['key_id'])
                        st.rerun()
        else:
            st.info("暂无 API Key，请点击上方「生成新 API Key」创建一个")
```

- [ ] **Step 2: 启动验证 API Key 页**

验证：
- 标题无 emoji
- Key 展示使用蓝色代码块样式
- 功能不变

- [ ] **Step 3: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 重设计 API Key 管理页 - 品牌色代码块展示"
```

---

### Task 7: 调用记录页重设计 + 页脚

**Files:**
- Modify: `streamlit_app/home.py` 中 `elif page == "logs":` 块

- [ ] **Step 1: 替换调用记录页面块**

将 `elif page == "logs":` 后面的块替换为：

```python
    elif page == "logs":
        st.markdown('<div class="page-title">调用记录</div>', unsafe_allow_html=True)

        logs = get_call_logs(200)

        if logs:
            df = pd.DataFrame(logs)
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.sort_values('created_at', ascending=False)

            st.dataframe(
                df[['request_id', 'api_key_name', 'created_at', 'model_name',
                    'input_tokens', 'output_tokens', 'status', 'error_message']],
                column_config={
                    "request_id": "请求 ID",
                    "api_key_name": "API 名称",
                    "created_at": st.column_config.DatetimeColumn("调用时间"),
                    "model_name": "模型",
                    "input_tokens": st.column_config.NumberColumn("输入 Token"),
                    "output_tokens": st.column_config.NumberColumn("输出 Token"),
                    "status": "状态",
                    "error_message": "错误信息"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("暂无调用记录")

    # 页脚
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#8e8e93; font-size:12px; padding:8px 0;">2026 Union-AI-API</div>',
        unsafe_allow_html=True
    )
```

- [ ] **Step 2: 启动验证调用记录页 + 全局检查**

验证：
- 标题无 emoji
- 表格有自定义样式（表头浅灰背景）
- 所有页面底部有统一页脚

**全局检查清单：**
- [ ] 登录页：渐变背景 + 毛玻璃卡片
- [ ] 导航栏：白色，药丸按钮，页面切换正常
- [ ] Dashboard：统计摘要 + 多色模型卡片 + 表格
- [ ] 模型配置：卡片布局，CRUD 正常
- [ ] API Key：代码块展示，生成/删除正常
- [ ] 调用记录：表格 + 页脚
- [ ] 退出登录正常
- [ ] 修改密码正常

- [ ] **Step 3: 提交**

```bash
git add streamlit_app/home.py
git commit -m "style: 重设计调用记录页 + 添加统一页脚"
```

---

### Task 8: 最终清理与合并准备

**Files:**
- Modify: `streamlit_app/home.py`（清理残留的未使用样式和变量）

- [ ] **Step 1: 删除旧 CSS 中未使用的样式**

检查 `home.py` 中是否还有以下旧样式残留并清理：
- `.model-header` 类
- `.default-badge` 类（旧版）
- 任何不再使用的 HTML class

- [ ] **Step 2: 更新 `show_change_password()` 函数**

将修改密码的 expander 标题去掉 emoji：

```python
def show_change_password():
    """显示修改密码对话框"""
    with st.expander("修改密码"):
        with st.form("change_password_form"):
            old_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_new_password = st.text_input("确认新密码", type="password")
            submitted = st.form_submit_button("修改密码")

            if submitted:
                if not old_password or not new_password:
                    st.error("请填写所有字段")
                elif new_password != confirm_new_password:
                    st.error("两次输入的新密码不一致")
                elif len(new_password) < 4:
                    st.error("新密码长度至少为4位")
                elif not login_user(st.session_state.username, old_password):
                    st.error("当前密码错误")
                else:
                    update_user_password(st.session_state.username, new_password)
                    st.success("密码修改成功！")
                    time.sleep(1)
```

- [ ] **Step 3: 全局功能回归测试**

在浏览器中逐项测试：
- [ ] 注册新用户
- [ ] 登录
- [ ] 添加模型
- [ ] 编辑模型
- [ ] 删除模型
- [ ] 复制配置
- [ ] 导入/导出 Excel
- [ ] 自动切换开关
- [ ] 默认模型设置
- [ ] 生成 API Key
- [ ] 删除 API Key
- [ ] 查看调用记录
- [ ] 修改密码
- [ ] 退出登录

- [ ] **Step 4: 提交**

```bash
git add streamlit_app/home.py
git commit -m "chore: 清理旧样式残留，去掉全局 emoji 前缀"
```

- [ ] **Step 5: 合并到主分支**

确认所有功能正常后，将 worktree 分支合并到 main。
