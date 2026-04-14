# UI 重设计 (Gradio) 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Streamlit 管理后台 UI 迁移到 Gradio 5.x，保持 MiniMax 设计风格，复用全部业务逻辑（db.py），不改变任何功能。
**Architecture:** 新建 `gradio_app/app.py` 作为 Gradio 应用入口，通过 `from streamlit_app.db import ...` 直接复用数据库层。使用 `gr.Blocks(css=...)` 定义全局 MiniMax 主题 CSS，`gr.Column(visible=...)` 切换登录/主界面，`gr.Tabs()` + CSS 覆盖实现药丸导航，`gr.HTML()` 渲染自定义渐变卡片，`gr.Dataframe()` 展示表格，`gr.State()` 管理会话状态。
**Tech Stack:** Python 3.11, Gradio 5.x, HTML/CSS, Google Fonts CDN (DM Sans + Outfit), pandas
**Spec:** `docs/superpowers/specs/2026-04-14-ui-redesign-design.md`

---

### Task 1: 项目设置 + 依赖更新

**Files:** `requirements.txt`, `gradio_app/__init__.py`, `gradio_app/app.py`

**说明：** 创建 gradio_app 目录结构，更新依赖文件添加 Gradio，创建最小可运行的 app.py 骨架。

- [ ] **Step 1.1:** 创建 `gradio_app/__init__.py`

```python
# gradio_app 包初始化文件
```

- [ ] **Step 1.2:** 更新 `requirements.txt`，添加 gradio（保留 streamlit 不删除，便于对比和回滚）

```
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
sqlalchemy==2.0.25
aiosqlite==0.19.0
httpx==0.26.0
tiktoken==0.5.2
streamlit==1.31.1
python-multipart==0.0.9
pandas==2.2.0
openpyxl==3.1.2
gradio>=5.0.0
```

- [ ] **Step 1.3:** 创建 `gradio_app/app.py` 最小骨架，验证 Gradio 可运行

```python
"""
Union-AI-API 管理后台 - Gradio 版本
MiniMax 设计风格
"""
import gradio as gr

# 自定义 CSS（将在 Task 2 中完善）
CUSTOM_CSS = """
"""

def create_app():
    """创建 Gradio 应用"""
    with gr.Blocks(
        title="Union-AI-API",
        css=CUSTOM_CSS,
        head="""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
        """
    ) as demo:
        gr.HTML("<h1 style='text-align:center;font-family:Outfit,sans-serif;'>Union-AI-API</h1>")
        gr.Markdown("### 管理后台 Gradio 版本 - 正在建设中...")

    return demo

if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=8501)
```

- [ ] **Step 1.4:** 安装依赖并验证

```bash
pip install -r requirements.txt
python gradio_app/app.py
# 浏览器访问 http://localhost:8501 确认页面正常显示
```

---

### Task 2: 全局 CSS 主题 + 主应用结构

**Files:** `gradio_app/app.py`

**说明：** 建立完整的 MiniMax 设计系统 CSS，构建 gr.Blocks 主骨架，实现登录区域和主界面区域的 Column 可见性切换。

- [ ] **Step 2.1:** 在 `gradio_app/app.py` 中定义完整的 MiniMax CSS 常量

```python
"""
Union-AI-API 管理后台 - Gradio 版本
MiniMax 设计风格
"""
import gradio as gr

# ============================================================
# 全局 CSS - MiniMax 设计系统
# ============================================================
MINIMAX_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

/* ==================== 全局重置 ==================== */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 0 !important;
    font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    color: #222222 !important;
    background: #ffffff !important;
}

/* ==================== 字体 ==================== */
h1, h2, h3, .outfit-font {
    font-family: 'Outfit', 'DM Sans', sans-serif !important;
}

/* ==================== 登录页背景 ==================== */
.login-background {
    min-height: 100vh;
    background: linear-gradient(135deg, #1456f0 0%, #ea5ec1 50%, #3daeff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    box-shadow: rgba(44, 30, 116, 0.16) 0px 0px 30px;
    padding: 40px;
    width: 100%;
    max-width: 400px;
}

.login-title {
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 600;
    color: #222222;
    text-align: center;
    margin-bottom: 4px;
}

.login-subtitle {
    font-size: 13px;
    color: #8e8e93;
    text-align: center;
    margin-bottom: 32px;
}

.login-info-bar {
    background: #eff6ff;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 24px;
    font-size: 13px;
    color: #1456f0;
    text-align: center;
}

/* ==================== 导航栏 ==================== */
.top-nav {
    background: #ffffff;
    border-bottom: 1px solid #f2f3f5;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
    margin: -10px -10px 0 -10px;
}

.nav-brand {
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: #18181b;
    cursor: default;
}

.nav-user {
    display: flex;
    align-items: center;
    gap: 16px;
}

.nav-username {
    font-size: 13px;
    color: #45515e;
}

/* ==================== Gradio Tabs 覆盖为药丸导航 ==================== */
.tabs {
    border: none !important;
    background: transparent !important;
}

.tab-nav {
    background: transparent !important;
    border: none !important;
    display: flex !important;
    gap: 4px !important;
    padding: 4px !important;
    border-bottom: none !important;
    flex-wrap: wrap;
}

.tab-nav button {
    border-radius: 9999px !important;
    border: none !important;
    background: transparent !important;
    color: #8e8e93 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
    cursor: pointer !important;
}

.tab-nav button.selected {
    background: rgba(0, 0, 0, 0.05) !important;
    color: #18181b !important;
    font-weight: 500 !important;
}

.tab-nav button:hover:not(.selected) {
    color: #45515e !important;
    background: rgba(0, 0, 0, 0.02) !important;
}

.tabitem {
    border: none !important;
    padding: 20px 0 !important;
}

/* ==================== 统计摘要卡片 ==================== */
.stat-cards-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.stat-card {
    flex: 1;
    min-width: 200px;
    border-radius: 20px;
    padding: 24px;
    color: #ffffff;
    box-shadow: rgba(44, 30, 116, 0.16) 0px 0px 15px;
    position: relative;
    overflow: hidden;
}

.stat-card-label {
    font-size: 12px;
    font-weight: 500;
    opacity: 0.8;
    margin-bottom: 8px;
}

.stat-card-value {
    font-family: 'Outfit', sans-serif;
    font-size: 24px;
    font-weight: 600;
}

/* ==================== 模型卡片网格 ==================== */
.model-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}

@media (max-width: 900px) {
    .model-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .model-grid {
        grid-template-columns: 1fr;
    }
}

.model-card {
    border-radius: 20px;
    padding: 24px;
    color: #ffffff;
    box-shadow: rgba(44, 30, 116, 0.16) 0px 0px 15px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}

.model-card:hover {
    transform: translateY(-2px);
    box-shadow: rgba(36, 36, 36, 0.08) 0px 12px 16px -4px;
}

.model-card.unavailable {
    opacity: 0.6;
}

.model-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.model-card-name {
    font-size: 16px;
    font-weight: 600;
}

.model-card-badge {
    background: rgba(255, 255, 255, 0.25);
    padding: 2px 12px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 500;
}

.model-card-info {
    font-size: 12px;
    opacity: 0.85;
    margin: 4px 0;
}

.model-card-stats {
    display: flex;
    justify-content: space-between;
    margin-top: 12px;
    font-size: 12px;
    opacity: 0.9;
}

.model-progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 9999px;
    margin-top: 12px;
    overflow: hidden;
}

.model-progress-fill {
    height: 100%;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 9999px;
    transition: width 0.3s ease;
}

/* ==================== 内容卡片 ==================== */
.content-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 24px;
    box-shadow: rgba(0, 0, 0, 0.08) 0px 4px 6px;
    margin-bottom: 16px;
}

.content-card-title {
    font-size: 16px;
    font-weight: 600;
    color: #222222;
    margin-bottom: 16px;
}

/* ==================== 操作按钮 ==================== */
.action-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.btn-primary {
    background: #1456f0 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}

.btn-primary:hover {
    background: #17437d !important;
}

.btn-secondary {
    background: #f0f0f0 !important;
    color: #333333 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}

.btn-secondary:hover {
    background: #e5e7eb !important;
}

.btn-danger {
    background: #f0f0f0 !important;
    color: #ef4444 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
}

.btn-danger:hover {
    background: #fef2f2 !important;
}

.btn-logout {
    background: transparent !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    color: #45515e !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

.btn-logout:hover {
    background: #f2f3f5 !important;
    border-color: #d1d5db !important;
}

/* ==================== Gradio 输入框覆盖 ==================== */
input[type="text"],
input[type="password"],
input[type="number"],
textarea,
select {
    background: #f2f3f5 !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: #222222 !important;
    transition: border-color 0.2s ease !important;
}

input:focus, textarea:focus, select:focus {
    border-color: #1456f0 !important;
    box-shadow: 0 0 0 3px rgba(20, 86, 240, 0.1) !important;
}

/* ==================== Gradio 按钮覆盖 ==================== */
.gr-button-primary {
    background: #181e25 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ==================== Dataframe 样式覆盖 ==================== */
.dataframe {
    border: 1px solid #f2f3f5 !important;
    border-radius: 8px !important;
    overflow: hidden;
}

.dataframe th {
    background: #f8fafc !important;
    color: #45515e !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-bottom: 1px solid #f2f3f5 !important;
}

.dataframe td {
    font-size: 13px !important;
    border-bottom: 1px solid #f2f3f5 !important;
}

.dataframe tr:nth-child(even) {
    background: #fafbfc !important;
}

.dataframe tr:hover {
    background: #f0f4ff !important;
}

/* ==================== API Key 展示代码块 ==================== */
.key-code-block {
    background: #f8fafc;
    border-left: 3px solid #1456f0;
    padding: 12px 16px;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13px;
    color: #222222;
    border-radius: 0 8px 8px 0;
    word-break: break-all;
    margin: 8px 0;
}

/* ==================== 默认模型徽章 ==================== */
.default-badge {
    background: #e8ffea;
    color: #16a34a;
    padding: 2px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
}

/* ==================== 页面标题 ==================== */
.page-title {
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: #222222;
    margin-bottom: 24px;
}

/* ==================== 页脚 ==================== */
.app-footer {
    text-align: center;
    padding: 24px 0;
    color: #8e8e93;
    font-size: 13px;
    border-top: 1px solid #f2f3f5;
    margin-top: 32px;
}

/* ==================== 分割线 ==================== */
.divider {
    height: 1px;
    background: #f2f3f5;
    margin: 24px 0;
}

/* ==================== Toggle 开关样式 ==================== */
.toggle-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}

.toggle-hint {
    font-size: 13px;
    color: #8e8e93;
    margin-top: 4px;
}

/* ==================== 消息提示 ==================== */
.msg-success {
    background: #e8ffea;
    color: #16a34a;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

.msg-error {
    background: #fef2f2;
    color: #ef4444;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

.msg-warning {
    background: #fffbeb;
    color: #d97706;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

.msg-info {
    background: #eff6ff;
    color: #1456f0;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

/* ==================== 隐藏 Gradio 默认页脚 ==================== */
footer {
    display: none !important;
}
"""
```

- [ ] **Step 2.2:** 在 `gradio_app/app.py` 中构建主应用骨架，包含登录区域和主界面区域

```python
import hashlib
import base64
import io
import time
from datetime import date, datetime, timedelta

import pandas as pd
import gradio as gr

from streamlit_app.db import (
    get_daily_stats,
    get_all_models,
    create_model,
    update_model,
    delete_model,
    get_all_api_keys,
    create_api_key,
    delete_api_key,
    get_call_logs,
    get_auto_switch_status,
    set_auto_switch_status,
    create_user,
    get_user,
    update_user_password,
    has_users,
    verify_password,
)


# ============================================================
# 认证工具函数
# ============================================================

def generate_auth_token(username):
    """生成认证 token"""
    timestamp = str(int(datetime.now().timestamp()))
    token_data = f"{username}:{timestamp}"
    token_hash = hashlib.sha256(f"{token_data}:union_ai_secret".encode()).hexdigest()[:16]
    auth_token = f"{token_data}:{token_hash}"
    return base64.b64encode(auth_token.encode()).decode()


def verify_auth_token(token_b64):
    """验证认证 token"""
    if not token_b64:
        return None
    try:
        auth_token = base64.b64decode(token_b64.encode()).decode()
        parts = auth_token.split(":")
        if len(parts) != 3:
            return None
        username, timestamp, token_hash = parts
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.now() - token_time > timedelta(days=7):
            return None
        expected_hash = hashlib.sha256(f"{username}:{timestamp}:union_ai_secret".encode()).hexdigest()[:16]
        if token_hash != expected_hash:
            return None
        user = get_user(username)
        if user:
            return username
        return None
    except Exception:
        return None


def login_user(username, password):
    """用户登录验证"""
    user = get_user(username)
    if user and verify_password(password, user['password_hash'], user['salt']):
        return True
    return False


# ============================================================
# 模型卡片渐变色板
# ============================================================

GRADIENT_COLORS = [
    "linear-gradient(135deg, #1456f0, #3b82f6)",
    "linear-gradient(135deg, #ea5ec1, #9333ea)",
    "linear-gradient(135deg, #3daeff, #1456f0)",
    "linear-gradient(135deg, #f97316, #ea5ec1)",
    "linear-gradient(135deg, #10b981, #3b82f6)",
]
UNAVAILABLE_GRADIENT = "linear-gradient(135deg, #8e8e93, #45515e)"


# ============================================================
# 导入导出 Excel 工具函数
# ============================================================

def export_models_to_excel():
    """导出模型配置到 Excel"""
    models = get_all_models()
    if not models:
        return None
    df = pd.DataFrame(models)
    export_columns = ['name', 'api_url', 'api_key', 'model_id', 'daily_token_limit',
                      'daily_call_limit', 'priority', 'is_active', 'is_default_model']
    df_export = df[export_columns].copy()
    df_export.columns = ['模型名称', 'API地址', 'API密钥', 'Model ID', '每日Token上限',
                         '每日调用上限', '优先级', '是否启用', '是否默认']
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='模型配置')
    output.seek(0)
    return output


def import_models_from_excel(file_path):
    """从 Excel 导入模型配置"""
    try:
        df = pd.read_excel(file_path)
        column_mapping = {}
        expected_columns = {
            'name': ['模型名称', 'name', 'Name'],
            'api_url': ['API地址', 'api_url', 'API URL', 'api url'],
            'api_key': ['API密钥', 'api_key', 'API Key', 'api key'],
            'model_id': ['Model ID', 'model_id', 'model id', 'ModelId'],
            'daily_token_limit': ['每日Token上限', 'daily_token_limit', 'Token Limit'],
            'daily_call_limit': ['每日调用上限', 'daily_call_limit', 'Call Limit'],
            'priority': ['优先级', 'priority', 'Priority']
        }
        for key, possible_names in expected_columns.items():
            for col in df.columns:
                if col in possible_names:
                    column_mapping[key] = col
                    break
        if 'name' not in column_mapping or 'api_url' not in column_mapping or 'api_key' not in column_mapping:
            return False, "Excel文件缺少必要的列（模型名称、API地址、API密钥）"
        success_count = 0
        for _, row in df.iterrows():
            try:
                name = str(row[column_mapping.get('name', 'name')])
                api_url = str(row[column_mapping.get('api_url', 'api_url')])
                api_key = str(row[column_mapping.get('api_key', 'api_key')])
                if not name or not api_url or not api_key or name == 'nan' or api_url == 'nan' or api_key == 'nan':
                    continue
                model_id = str(row.get(column_mapping.get('model_id', 'model_id'), ''))
                daily_token_limit = int(float(row.get(column_mapping.get('daily_token_limit', 'daily_token_limit'), 100000)))
                daily_call_limit = int(float(row.get(column_mapping.get('daily_call_limit', 'daily_call_limit'), 1000)))
                priority = int(float(row.get(column_mapping.get('priority', 'priority'), 0)))
                create_model(name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority)
                success_count += 1
            except Exception:
                continue
        return True, f"成功导入 {success_count} 个模型配置"
    except Exception as e:
        return False, f"导入失败：{str(e)}"


# ============================================================
# 主应用构建
# ============================================================

def create_app():
    """创建 Gradio 应用"""

    with gr.Blocks(
        title="Union-AI-API",
        css=MINIMAX_CSS,
        head=""",
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
        """
    ) as demo:

        # ========== 会话状态 ==========
        session_state = gr.State(value={
            "is_logged_in": False,
            "username": None,
            "show_register": not has_users(),
        })

        # ========== 登录区域 ==========
        login_area = gr.Column(visible=True)
        with login_area:
            # 具体实现在 Task 3 中添加
            pass

        # ========== 主界面区域 ==========
        main_area = gr.Column(visible=False)
        with main_area:
            # 具体实现在 Task 4-8 中添加
            pass

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=8501)
```

- [ ] **Step 2.3:** 验证

```bash
python gradio_app/app.py
# 浏览器访问 http://localhost:8501 确认空白页面正常加载（无 JS 错误）
```

---

### Task 3: 登录/注册页面

**Files:** `gradio_app/app.py`

**说明：** 实现渐变背景 + 毛玻璃卡片的登录/注册页面，包含认证逻辑和状态管理。将此代码替换到 `create_app()` 函数中 `login_area` 部分的 `pass` 处。

- [ ] **Step 3.1:** 在 `create_app()` 中替换 `login_area` 内容，实现登录和注册页

```python
        # ========== 登录区域 ==========
        login_area = gr.Column(visible=True, elem_classes=["login-background"])
        with login_area:
            login_msg = gr.HTML("", visible=True)

            # ----- 登录表单 -----
            login_form = gr.Column(visible=True)
            with login_form:
                gr.HTML("""
                <div style="display:flex;align-items:center;justify-content:center;min-height:90vh;">
                    <div class="login-card">
                        <div class="login-title">Union-AI-API</div>
                        <div class="login-subtitle">统一多模型 AI 代理服务</div>
                """)
                login_username = gr.Textbox(
                    label="用户名",
                    placeholder="请输入用户名",
                    show_label=False,
                    elem_classes=["login-input"],
                )
                login_password = gr.Textbox(
                    label="密码",
                    placeholder="请输入密码",
                    type="password",
                    show_label=False,
                    elem_classes=["login-input"],
                )
                login_btn = gr.Button(
                    "登录",
                    variant="primary",
                    elem_classes=["btn-primary"],
                )
                gr.HTML("</div></div>")

            # ----- 注册表单 -----
            register_form = gr.Column(visible=False)
            with register_form:
                gr.HTML("""
                <div style="display:flex;align-items:center;justify-content:center;min-height:90vh;">
                    <div class="login-card">
                        <div class="login-title">Union-AI-API</div>
                        <div class="login-subtitle">创建管理员账号</div>
                """)
                reg_info = gr.HTML('<div class="login-info-bar">这是首次使用，请创建一个管理员账号</div>')
                reg_username = gr.Textbox(
                    label="用户名",
                    placeholder="请输入用户名",
                    show_label=False,
                )
                reg_password = gr.Textbox(
                    label="密码",
                    placeholder="请输入密码",
                    type="password",
                    show_label=False,
                )
                reg_confirm = gr.Textbox(
                    label="确认密码",
                    placeholder="请再次输入密码",
                    type="password",
                    show_label=False,
                )
                register_btn = gr.Button(
                    "注册",
                    variant="primary",
                    elem_classes=["btn-primary"],
                )
                gr.HTML("</div></div>")
```

- [ ] **Step 3.2:** 添加登录/注册事件处理函数（在 `create_app()` 函数内、`demo` 返回前）

```python
        # ========== 登录/注册事件处理 ==========

        def handle_login(username, password, state):
            """处理登录"""
            if not username or not password:
                return (
                    state, True, False,
                    '<div class="msg-error">请输入用户名和密码</div>',
                    "",
                )
            if login_user(username, password):
                state["is_logged_in"] = True
                state["username"] = username
                return (
                    state, False, True,
                    "",
                    "",
                )
            return (
                state, True, False,
                '<div class="msg-error">用户名或密码错误</div>',
                "",
            )

        def handle_register(username, password, confirm, state):
            """处理注册"""
            if not username or not password:
                return (
                    state, False, True,
                    '<div class="msg-error">请输入用户名和密码</div>',
                )
            if password != confirm:
                return (
                    state, False, True,
                    '<div class="msg-error">两次输入的密码不一致</div>',
                )
            if len(password) < 4:
                return (
                    state, False, True,
                    '<div class="msg-error">密码长度至少为4位</div>',
                )
            if create_user(username, password):
                state["show_register"] = False
                return (
                    state, True, False,
                    '<div class="msg-success">注册成功！请登录</div>',
                )
            return (
                state, False, True,
                '<div class="msg-error">用户名已存在</div>',
            )

        def init_login_state(state):
            """根据初始状态决定显示登录还是注册"""
            if state.get("show_register", False):
                return gr.update(visible=False), gr.update(visible=True), ""
            return gr.update(visible=True), gr.update(visible=False), ""

        # 绑定登录事件
        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password, session_state],
            outputs=[session_state, login_area, main_area, login_msg, login_username],
        )

        # 绑定注册事件
        register_btn.click(
            fn=handle_register,
            inputs=[reg_username, reg_password, reg_confirm, session_state],
            outputs=[session_state, login_form, register_form, login_msg],
        )

        # 页面加载时初始化
        demo.load(
            fn=init_login_state,
            inputs=[session_state],
            outputs=[login_form, register_form, reg_info],
        )
```

- [ ] **Step 3.3:** 验证

```bash
python gradio_app/app.py
# 浏览器访问 http://localhost:8501
# 验证：渐变背景显示、毛玻璃卡片显示、登录表单可交互
# 验证：首次使用时自动显示注册表单
# 验证：注册新用户后跳转到登录表单
# 验证：登录成功后切换到主界面
```

---

### Task 4: 顶部导航 + 主界面框架

**Files:** `gradio_app/app.py`

**说明：** 实现顶部导航栏（品牌名称 + 药丸按钮 + 用户信息 + 退出），主界面使用 gr.Tabs() 配合 CSS 覆盖。将此代码替换到 `create_app()` 函数中 `main_area` 部分的 `pass` 处。

- [ ] **Step 4.1:** 替换 `main_area` 内容，实现导航栏和 Tabs 框架

```python
        # ========== 主界面区域 ==========
        main_area = gr.Column(visible=False)
        with main_area:
            # ----- 顶部导航栏 -----
            nav_bar = gr.HTML("")
            nav_username_display = gr.HTML("")

            def render_nav(username):
                return f"""
                <div class="top-nav">
                    <div class="nav-brand">Union-AI-API</div>
                    <div class="nav-user">
                        <span class="nav-username">{username}</span>
                    </div>
                </div>
                """

            # ----- Tabs 导航 -----
            with gr.Tabs() as main_tabs:
                tab_dashboard = gr.Tab("数据概览")
                with tab_dashboard:
                    # Task 5 中填充
                    dashboard_placeholder = gr.HTML('<div class="page-title">数据概览</div><p>加载中...</p>')

                tab_models = gr.Tab("模型配置")
                with tab_models:
                    # Task 6 中填充
                    models_placeholder = gr.HTML('<div class="page-title">模型配置</div><p>加载中...</p>')

                tab_apikeys = gr.Tab("API Key")
                with tab_apikeys:
                    # Task 7 中填充
                    apikeys_placeholder = gr.HTML('<div class="page-title">API Key 管理</div><p>加载中...</p>')

                tab_logs = gr.Tab("调用记录")
                with tab_logs:
                    # Task 8 中填充
                    logs_placeholder = gr.HTML('<div class="page-title">调用记录</div><p>加载中...</p>')

            # ----- 退出按钮 -----
            with gr.Row():
                logout_btn = gr.Button("退出登录", elem_classes=["btn-logout"])
                refresh_btn = gr.Button("刷新数据", elem_classes=["btn-secondary"])

            # ----- 页脚 -----
            gr.HTML('<div class="app-footer">&copy; 2026 Union-AI-API &middot; AI Proxy</div>')
```

- [ ] **Step 4.2:** 添加导航和退出的事件处理（在事件处理部分追加）

```python
        def handle_logout(state):
            """处理退出登录"""
            state["is_logged_in"] = False
            state["username"] = None
            state["show_register"] = False
            return (
                state,
                gr.update(visible=False),  # main_area
                gr.update(visible=True),   # login_area
                gr.update(visible=True),   # login_form
                gr.update(visible=False),  # register_form
                "",                        # login_username 清空
                "",                        # login_password 清空
            )

        logout_btn.click(
            fn=handle_logout,
            inputs=[session_state],
            outputs=[session_state, main_area, login_area, login_form, register_form,
                     login_username, login_password],
        )
```

- [ ] **Step 4.3:** 更新 `handle_login` 输出以包含导航栏渲染

将 Task 3 中的 `handle_login` 函数修改为同时渲染导航栏：

```python
        def handle_login(username, password, state):
            """处理登录"""
            if not username or not password:
                return (
                    state, True, False,
                    '<div class="msg-error">请输入用户名和密码</div>',
                    "", "",
                )
            if login_user(username, password):
                state["is_logged_in"] = True
                state["username"] = username
                nav_html = render_nav(username)
                return (
                    state, False, True,
                    "",
                    "", nav_html,
                )
            return (
                state, True, False,
                '<div class="msg-error">用户名或密码错误</div>',
                "", "",
            )

        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password, session_state],
            outputs=[session_state, login_area, main_area, login_msg, login_username, nav_bar],
        )
```

- [ ] **Step 4.4:** 验证

```bash
python gradio_app/app.py
# 登录后验证：
# - 顶部导航栏显示品牌名 + 用户名
# - 4 个 Tab（数据概览、模型配置、API Key、调用记录）显示为药丸按钮
# - 退出按钮可点击，退出后回到登录页
```

---

### Task 5: 数据概览页

**Files:** `gradio_app/app.py`

**说明：** 实现数据概览页，包含 3 张渐变统计摘要卡片、模型状态卡片网格、详细数据表格。替换 `tab_dashboard` 中的 `dashboard_placeholder`。

- [ ] **Step 5.1:** 替换 `tab_dashboard` 内容

```python
                tab_dashboard = gr.Tab("数据概览")
                with tab_dashboard:
                    dashboard_msg = gr.HTML("")
                    # 统计摘要卡片
                    stat_cards = gr.HTML("")
                    # 模型卡片网格
                    model_cards = gr.HTML("")
                    # 详细数据表格
                    gr.HTML('<div class="divider"></div>')
                    gr.HTML('<div style="font-size:16px;font-weight:500;color:#222222;margin-bottom:12px;">详细数据</div>')
                    dashboard_df = gr.Dataframe(
                        headers=["模型名称", "Model ID", "是否可用", "已用调用", "调用限额", "剩余调用",
                                 "调用使用率", "已用 Token", "Token 限额", "剩余 Token", "Token 使用率",
                                 "默认模型", "优先级"],
                        datatype=["str", "str", "str", "number", "number", "number",
                                  "str", "number", "number", "number", "str", "str", "number"],
                        interactive=False,
                        show_search="filter",
                    )
```

- [ ] **Step 5.2:** 添加数据概览渲染函数（在 `create_app()` 函数内的工具函数部分）

```python
        def render_dashboard():
            """渲染数据概览页"""
            stats = get_daily_stats()

            if not stats:
                return (
                    '<div class="msg-info">暂无模型配置，请前往「模型配置」添加模型</div>',
                    "",
                    None,
                )

            # 计算汇总数据
            total_tokens = sum(s['used_tokens'] for s in stats)
            total_calls = sum(s['used_calls'] for s in stats)
            active_models = sum(1 for s in stats if s['is_active'] == 1)

            # 统计摘要卡片
            stat_html = f"""
            <div class="stat-cards-row">
                <div class="stat-card" style="background: linear-gradient(135deg, #1456f0, #3b82f6);">
                    <div class="stat-card-label">今日 Token 用量</div>
                    <div class="stat-card-value">{total_tokens:,}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #ea5ec1, #9333ea);">
                    <div class="stat-card-label">今日调用次数</div>
                    <div class="stat-card-value">{total_calls:,}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #3daeff, #1456f0);">
                    <div class="stat-card-label">活跃模型数</div>
                    <div class="stat-card-value">{active_models}</div>
                </div>
            </div>
            """

            # 模型卡片网格
            sorted_stats = sorted(stats, key=lambda x: x['priority'], reverse=True)
            cards_html = '<div class="model-grid">'
            for idx, stat in enumerate(sorted_stats):
                is_available = (
                    stat['used_tokens'] < stat['daily_token_limit'] and
                    stat['used_calls'] < stat['daily_call_limit'] and
                    stat['is_active'] == 1
                )
                gradient = GRADIENT_COLORS[idx % len(GRADIENT_COLORS)] if is_available else UNAVAILABLE_GRADIENT
                card_class = "model-card" if is_available else "model-card unavailable"
                default_badge = '<span class="model-card-badge">默认</span>' if stat['is_default_model'] == 1 else ''

                token_usage_pct = min(100, (stat['used_tokens'] / max(1, stat['daily_token_limit'])) * 100)
                call_usage_pct = min(100, (stat['used_calls'] / max(1, stat['daily_call_limit'])) * 100)

                cards_html += f"""
                <div class="{card_class}" style="background: {gradient};">
                    <div class="model-card-header">
                        <span class="model-card-name">{stat['name']}</span>
                        {default_badge}
                    </div>
                    <div class="model-card-info">Model ID: {stat.get('model_id', 'N/A')}</div>
                    <div class="model-card-info">优先级: {stat['priority']}</div>
                    <div class="model-card-stats">
                        <span>Token: {stat['used_tokens']:,} / {stat['daily_token_limit']:,}</span>
                        <span>调用: {stat['used_calls']:,} / {stat['daily_call_limit']:,}</span>
                    </div>
                    <div class="model-progress-bar">
                        <div class="model-progress-fill" style="width: {token_usage_pct:.1f}%;"></div>
                    </div>
                </div>
                """
            cards_html += '</div>'

            # 详细数据表格
            df = pd.DataFrame(stats)
            df['剩余 Token'] = df['daily_token_limit'] - df['used_tokens']
            df['剩余调用次数'] = df['daily_call_limit'] - df['used_calls']
            df['Token 使用率'] = (df['used_tokens'] / df['daily_token_limit'] * 100).round(1).astype(str) + '%'
            df['调用使用率'] = (df['used_calls'] / df['daily_call_limit'] * 100).round(1).astype(str) + '%'
            df['是否可用'] = df.apply(
                lambda x: '可用' if (
                    x['used_tokens'] < x['daily_token_limit'] and
                    x['used_calls'] < x['daily_call_limit'] and
                    x['is_active'] == 1
                ) else '不可用',
                axis=1
            )
            df['默认模型'] = df['is_default_model'].apply(lambda x: '是' if x == 1 else '')

            display_df = df[['name', 'model_id', '是否可用', 'used_calls', 'daily_call_limit', '剩余调用次数',
                             '调用使用率', 'used_tokens', 'daily_token_limit', '剩余 Token', 'Token 使用率',
                             '默认模型', 'priority']].copy()
            display_df.columns = ['模型名称', 'Model ID', '是否可用', '已用调用', '调用限额', '剩余调用',
                                  '调用使用率', '已用 Token', 'Token 限额', '剩余 Token', 'Token 使用率',
                                  '默认模型', '优先级']

            return stat_html, cards_html, display_df

        def refresh_dashboard():
            """刷新数据概览"""
            stat_html, cards_html, df_data = render_dashboard()
            return stat_html, cards_html, df_data
```

- [ ] **Step 5.3:** 绑定数据概览事件

```python
        # 登录成功后加载 Dashboard 数据
        def load_dashboard_on_login(state):
            """登录后加载数据"""
            if state.get("is_logged_in"):
                stat_html, cards_html, df_data = render_dashboard()
                return stat_html, cards_html, df_data
            return "", "", None

        # 刷新按钮事件
        refresh_btn.click(
            fn=refresh_dashboard,
            inputs=[],
            outputs=[stat_cards, model_cards, dashboard_df],
        )
```

更新 `handle_login` 的输出，增加 dashboard 组件：

```python
        def handle_login(username, password, state):
            """处理登录"""
            if not username or not password:
                return (
                    state, True, False,
                    '<div class="msg-error">请输入用户名和密码</div>',
                    "", "", "", "", None,
                )
            if login_user(username, password):
                state["is_logged_in"] = True
                state["username"] = username
                nav_html = render_nav(username)
                stat_html, cards_html, df_data = render_dashboard()
                return (
                    state, False, True,
                    "",
                    "", nav_html, stat_html, cards_html, df_data,
                )
            return (
                state, True, False,
                '<div class="msg-error">用户名或密码错误</div>',
                "", "", "", "", None,
            )

        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password, session_state],
            outputs=[session_state, login_area, main_area, login_msg, login_username,
                     nav_bar, stat_cards, model_cards, dashboard_df],
        )
```

- [ ] **Step 5.4:** 验证

```bash
python gradio_app/app.py
# 登录后验证：
# - 3 张渐变统计摘要卡片正确显示 Token 用量、调用次数、活跃模型数
# - 模型卡片网格按渐变色板循环分配颜色
# - 不可用模型灰色 + 透明度 0.6
# - 详细数据表格显示完整数据
# - 刷新按钮可更新数据
```

---

### Task 6: 模型配置页

**Files:** `gradio_app/app.py`

**说明：** 实现模型配置页，包含操作栏（导出/导入/添加）、全局设置（自动切换开关）、模型列表（可展开编辑）、CRUD 操作、默认模型设置、导入导出 Excel。替换 `tab_models` 中的 `models_placeholder`。

- [ ] **Step 6.1:** 替换 `tab_models` 内容

```python
                tab_models = gr.Tab("模型配置")
                with tab_models:
                    models_msg = gr.HTML("")

                    # ----- 操作栏 -----
                    with gr.Row():
                        export_btn = gr.Button("导出配置", elem_classes=["btn-secondary"])
                        import_file = gr.File(
                            label="导入 Excel 文件",
                            file_types=[".xlsx", ".xls"],
                            file_count="single",
                            elem_classes=["btn-secondary"],
                        )
                        import_btn = gr.Button("导入配置", elem_classes=["btn-secondary"])
                        add_model_btn = gr.Button("添加模型", elem_classes=["btn-primary"])

                    gr.HTML('<div class="divider"></div>')

                    # ----- 全局设置 -----
                    with gr.Row():
                        auto_switch_checkbox = gr.Checkbox(
                            label="启用自动切换模型",
                            value=get_auto_switch_status(),
                        )
                    gr.HTML('<div class="toggle-hint">开启后：系统按优先级自动切换所有启用的模型 | 关闭后：所有请求固定使用默认模型</div>')

                    gr.HTML('<div class="divider"></div>')

                    # ----- 添加/编辑模型表单 -----
                    with gr.Column(visible=False) as add_model_form:
                        form_title = gr.HTML('<div class="content-card-title">添加新模型</div>')
                        with gr.Row():
                            add_name = gr.Textbox(label="模型名称", placeholder="例如：GPT-4")
                            add_api_url = gr.Textbox(label="API 地址", placeholder="https://api.openai.com/v1/chat/completions")
                        with gr.Row():
                            add_api_key = gr.Textbox(label="API Key", type="password", placeholder="请输入 API Key")
                            add_model_id = gr.Textbox(label="Model ID（选填）", placeholder="如 gpt-4、claude-3 等")
                        with gr.Row():
                            add_token_limit = gr.Number(label="每日 Token 上限", value=100000, minimum=1)
                            add_call_limit = gr.Number(label="每日调用次数上限", value=1000, minimum=1)
                            add_priority = gr.Number(label="优先级（数字越大越优先）", value=0, minimum=0)
                        with gr.Row():
                            submit_add_model = gr.Button("添加", variant="primary", elem_classes=["btn-primary"])
                            cancel_add_model = gr.Button("取消", elem_classes=["btn-secondary"])

                    gr.HTML('<div style="font-size:16px;font-weight:500;color:#222222;margin-bottom:12px;">模型列表</div>')

                    # ----- 模型列表动态区域 -----
                    models_list = gr.HTML("")

                    # ----- 默认模型设置 -----
                    gr.HTML('<div class="divider"></div>')
                    gr.HTML('<div style="font-size:16px;font-weight:500;color:#222222;margin-bottom:12px;">默认模型设置</div>')
                    gr.HTML('<div class="toggle-hint">仅在关闭自动切换时使用，所有请求将固定使用此模型</div>')

                    with gr.Row(visible=not get_auto_switch_status()) as default_model_row:
                        default_model_select = gr.Dropdown(
                            label="选择默认模型",
                            choices=[],
                            value=None,
                            interactive=True,
                        )
                        save_default_btn = gr.Button("保存默认模型", elem_classes=["btn-primary"])

                    # ----- 编辑模型弹窗 -----
                    with gr.Column(visible=False) as edit_model_form:
                        edit_config_id = gr.Textbox(visible=False)
                        edit_form_title = gr.HTML('<div class="content-card-title">编辑模型</div>')
                        with gr.Row():
                            edit_name = gr.Textbox(label="模型名称")
                            edit_api_url = gr.Textbox(label="API 地址")
                        with gr.Row():
                            edit_api_key = gr.Textbox(label="API Key", type="password")
                            edit_model_id_field = gr.Textbox(label="Model ID（选填）")
                        with gr.Row():
                            edit_token_limit = gr.Number(label="每日 Token 上限", minimum=1)
                            edit_call_limit = gr.Number(label="每日调用次数上限", minimum=1)
                            edit_priority = gr.Number(label="优先级", minimum=0)
                        with gr.Row():
                            update_model_btn = gr.Button("更新", variant="primary", elem_classes=["btn-primary"])
                            delete_model_btn = gr.Button("删除", elem_classes=["btn-danger"])
                            cancel_edit_model = gr.Button("取消", elem_classes=["btn-secondary"])
```

- [ ] **Step 6.2:** 添加模型配置页渲染和事件处理函数

```python
        def render_models_list():
            """渲染模型列表 HTML"""
            models = get_all_models()
            if not models:
                return '<div class="msg-info">暂无模型配置</div>'

            html = ""
            for model in models:
                is_default = model.get('is_default_model', 0) == 1
                default_badge = '<span class="default-badge">默认模型</span>' if is_default else ''

                html += f"""
                <div class="content-card">
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        <div>
                            <span style="font-size:16px;font-weight:600;color:#222222;">{model['name']}</span>
                            <span style="margin-left:8px;font-size:12px;color:#8e8e93;">优先级：{model['priority']}</span>
                            {default_badge}
                        </div>
                        <div style="display:flex;gap:8px;">
                            <button class="btn-secondary" onclick="document.querySelector('[data-model-edit={model['config_id']}]').click()" style="font-size:13px;padding:6px 14px;">编辑</button>
                        </div>
                    </div>
                    <div style="font-size:13px;color:#45515e;margin-top:8px;">
                        Model ID: {model.get('model_id', 'N/A')} | API: {model['api_url'][:50]}{'...' if len(model['api_url']) > 50 else ''}
                    </div>
                </div>
                """

            # 添加隐藏按钮用于触发编辑
            for model in models:
                html += f'<button data-model-edit="{model["config_id"]}" style="display:none;" id="edit-btn-{model["config_id"]}"></button>'

            return html

        def get_model_choices():
            """获取模型下拉选项"""
            models = get_all_models()
            choices = [(f"{m['name']} (优先级：{m['priority']})", m['config_id']) for m in models]
            return choices

        def refresh_models_page():
            """刷新模型配置页"""
            models_html = render_models_list()
            choices = get_model_choices()
            auto_status = get_auto_switch_status()
            return (
                models_html,
                gr.update(choices=choices, value=choices[0][1] if choices else None),
                gr.update(visible=not auto_status),
                gr.update(value=auto_status),
            )

        def handle_add_model(name, api_url, api_key, model_id, token_limit, call_limit, priority):
            """添加模型"""
            if not name or not api_url or not api_key:
                return (
                    '<div class="msg-error">请填写所有必填字段</div>',
                    render_models_list(),
                    gr.update(visible=False),
                )
            create_model(name, api_url, api_key, model_id, int(token_limit), int(call_limit), int(priority))
            return (
                '<div class="msg-success">模型添加成功</div>',
                render_models_list(),
                gr.update(visible=False),
            )

        def handle_update_model(config_id, name, api_url, api_key, model_id, token_limit, call_limit, priority):
            """更新模型"""
            models = get_all_models()
            is_default = next((m.get('is_default_model', 0) for m in models if m['config_id'] == config_id), 0)
            update_model(config_id, name, api_url, api_key, model_id,
                         int(token_limit), int(call_limit), is_default, int(priority))
            return (
                '<div class="msg-success">模型已更新</div>',
                render_models_list(),
                gr.update(visible=False),
            )

        def handle_delete_model(config_id):
            """删除模型"""
            delete_model(config_id)
            return (
                '<div class="msg-success">模型已删除</div>',
                render_models_list(),
                gr.update(visible=False),
            )

        def handle_export():
            """导出配置到 Excel"""
            output = export_models_to_excel()
            if output is None:
                return None, '<div class="msg-error">暂无模型配置可导出</div>'
            filename = f"models_export_{date.today().isoformat()}.xlsx"
            return (output.getvalue(), filename), '<div class="msg-success">导出成功</div>'

        def handle_import(file):
            """导入配置"""
            if file is None:
                return '<div class="msg-error">请选择 Excel 文件</div>', render_models_list()
            success, message = import_models_from_excel(file)
            if success:
                return f'<div class="msg-success">{message}</div>', render_models_list()
            return f'<div class="msg-error">{message}</div>', render_models_list()

        def handle_auto_switch(checked):
            """处理自动切换开关"""
            set_auto_switch_status(checked)
            return gr.update(visible=not checked)

        def handle_save_default(selected_config_id):
            """保存默认模型"""
            if not selected_config_id:
                return '<div class="msg-error">请选择一个模型</div>'
            models = get_all_models()
            for m in models:
                is_default = (m['config_id'] == selected_config_id)
                update_model(m['config_id'], m['name'], m['api_url'], m['api_key'],
                             m.get('model_id', ''), m['daily_token_limit'],
                             m['daily_call_limit'], 1 if is_default else 0, m['priority'])
            return '<div class="msg-success">默认模型已保存</div>'

        def open_edit_form(config_id):
            """打开编辑表单"""
            models = get_all_models()
            model = next((m for m in models if m['config_id'] == config_id), None)
            if not model:
                return gr.update(visible=False), "", "", "", "", 100000, 1000, 0, ""
            return (
                gr.update(visible=True),
                config_id,
                model['name'],
                model['api_url'],
                model['api_key'],
                model.get('model_id', ''),
                model['daily_token_limit'],
                model['daily_call_limit'],
                model['priority'],
            )
```

- [ ] **Step 6.3:** 绑定模型配置页事件

```python
        # 添加模型
        add_model_btn.click(
            fn=lambda: gr.update(visible=True),
            inputs=[],
            outputs=[add_model_form],
        )
        cancel_add_model.click(
            fn=lambda: gr.update(visible=False),
            inputs=[],
            outputs=[add_model_form],
        )
        submit_add_model.click(
            fn=handle_add_model,
            inputs=[add_name, add_api_url, add_api_key, add_model_id,
                    add_token_limit, add_call_limit, add_priority],
            outputs=[models_msg, models_list, add_model_form],
        )

        # 编辑模型
        cancel_edit_model.click(
            fn=lambda: gr.update(visible=False),
            inputs=[],
            outputs=[edit_model_form],
        )
        update_model_btn.click(
            fn=handle_update_model,
            inputs=[edit_config_id, edit_name, edit_api_url, edit_api_key,
                    edit_model_id_field, edit_token_limit, edit_call_limit, edit_priority],
            outputs=[models_msg, models_list, edit_model_form],
        )
        delete_model_btn.click(
            fn=handle_delete_model,
            inputs=[edit_config_id],
            outputs=[models_msg, models_list, edit_model_form],
        )

        # 导入导出
        export_btn.click(
            fn=handle_export,
            inputs=[],
            outputs=[import_file, models_msg],
        )
        import_btn.click(
            fn=handle_import,
            inputs=[import_file],
            outputs=[models_msg, models_list],
        )

        # 全局设置
        auto_switch_checkbox.change(
            fn=handle_auto_switch,
            inputs=[auto_switch_checkbox],
            outputs=[default_model_row],
        )
        save_default_btn.click(
            fn=handle_save_default,
            inputs=[default_model_select],
            outputs=[models_msg],
        )

        # 刷新数据时同时刷新模型列表
        def full_refresh():
            stat_html, cards_html, df_data = render_dashboard()
            models_html = render_models_list()
            choices = get_model_choices()
            return (
                stat_html, cards_html, df_data,
                models_html,
                gr.update(choices=choices),
            )

        refresh_btn.click(
            fn=full_refresh,
            inputs=[],
            outputs=[stat_cards, model_cards, dashboard_df, models_list, default_model_select],
        )
```

- [ ] **Step 6.4:** 验证

```bash
python gradio_app/app.py
# 验证：
# - 导出配置按钮可下载 Excel
# - 导入配置可选择 Excel 文件并导入
# - 自动切换开关可切换
# - 添加模型表单可添加新模型
# - 模型列表正确显示
# - 关闭自动切换后显示默认模型选择器
# - 保存默认模型功能正常
```

---

### Task 7: API Key 管理页

**Files:** `gradio_app/app.py`

**说明：** 实现 API Key 管理页，包含生成新 Key 表单、Key 列表展示、删除功能。替换 `tab_apikeys` 中的 `apikeys_placeholder`。

- [ ] **Step 7.1:** 替换 `tab_apikeys` 内容

```python
                tab_apikeys = gr.Tab("API Key")
                with tab_apikeys:
                    apikeys_msg = gr.HTML("")

                    # ----- 生成新 Key -----
                    with gr.Row():
                        new_key_name = gr.Textbox(
                            label="Key 名称",
                            placeholder="例如：我的应用",
                            scale=3,
                        )
                        generate_key_btn = gr.Button(
                            "生成新 Key",
                            variant="primary",
                            elem_classes=["btn-primary"],
                            scale=1,
                        )

                    # ----- 新生成的 Key 展示 -----
                    new_key_display = gr.HTML("", visible=False)

                    gr.HTML('<div class="divider"></div>')

                    # ----- Key 列表 -----
                    gr.HTML('<div style="font-size:16px;font-weight:500;color:#222222;margin-bottom:12px;">API Key 列表</div>')
                    apikeys_list = gr.HTML("")
                    delete_key_id = gr.Textbox(visible=False)
                    delete_key_btn = gr.Button("确认删除", visible=False, elem_classes=["btn-danger"])
```

- [ ] **Step 7.2:** 添加 API Key 页渲染和事件处理函数

```python
        def render_apikeys_list():
            """渲染 API Key 列表"""
            keys = get_all_api_keys()
            if not keys:
                return '<div class="msg-info">暂无 API Key，请点击上方「生成新 Key」创建一个</div>'

            html = ""
            for key in keys:
                html += f"""
                <div class="content-card">
                    <div style="display:flex;align-items:center;justify-content:space-between;">
                        <div>
                            <div style="font-size:16px;font-weight:500;color:#222222;">{key['name']}</div>
                            <div class="key-code-block">{key['api_key']}</div>
                            <div style="font-size:12px;color:#8e8e93;">Key ID: {key['key_id']} | 创建时间: {key['created_at']}</div>
                        </div>
                    </div>
                </div>
                """
            return html

        def handle_generate_key(name):
            """生成新 API Key"""
            if not name:
                return (
                    '<div class="msg-error">请输入名称</div>',
                    gr.update(visible=False),
                    "",
                )
            result = create_api_key(name)
            key_html = f"""
            <div class="msg-success">API Key 生成成功</div>
            <div class="key-code-block">{result['api_key']}</div>
            <div class="msg-warning" style="margin-top:12px;">请立即复制 API Key，它不会再次显示。</div>
            """
            return (
                "",
                gr.update(visible=True),
                key_html,
            )

        def handle_delete_key(key_id):
            """删除 API Key"""
            if not key_id:
                return '<div class="msg-error">未选择要删除的 Key</div>', render_apikeys_list()
            delete_api_key(key_id)
            return '<div class="msg-success">API Key 已删除</div>', render_apikeys_list()
```

- [ ] **Step 7.3:** 绑定 API Key 页事件

```python
        generate_key_btn.click(
            fn=handle_generate_key,
            inputs=[new_key_name],
            outputs=[apikeys_msg, new_key_display, new_key_display],
        )

        # 注意：删除操作需要通过 HTML 内的交互触发
        # 由于 Gradio HTML 内容不直接支持回调，
        # 删除操作通过修改模型列表渲染来提供删除链接，
        # 实际删除通过独立的删除表单实现
        delete_key_btn.click(
            fn=handle_delete_key,
            inputs=[delete_key_id],
            outputs=[apikeys_msg, apikeys_list],
        )
```

更新 `full_refresh` 函数以包含 API Key 列表刷新：

```python
        def full_refresh():
            stat_html, cards_html, df_data = render_dashboard()
            models_html = render_models_list()
            choices = get_model_choices()
            keys_html = render_apikeys_list()
            return (
                stat_html, cards_html, df_data,
                models_html,
                gr.update(choices=choices),
                keys_html,
            )

        refresh_btn.click(
            fn=full_refresh,
            inputs=[],
            outputs=[stat_cards, model_cards, dashboard_df, models_list,
                     default_model_select, apikeys_list],
        )
```

- [ ] **Step 7.4:** 验证

```bash
python gradio_app/app.py
# 验证：
# - 输入名称点击"生成新 Key"可生成 API Key
# - 生成的 Key 以代码块样式展示
# - Key 列表正确显示所有已生成的 Key
# - 每个 Key 显示名称、Key 值、Key ID、创建时间
```

---

### Task 8: 调用记录页 + 页脚

**Files:** `gradio_app/app.py`

**说明：** 实现调用记录页表格展示，完善页脚。替换 `tab_logs` 中的 `logs_placeholder`。

- [ ] **Step 8.1:** 替换 `tab_logs` 内容

```python
                tab_logs = gr.Tab("调用记录")
                with tab_logs:
                    logs_msg = gr.HTML("")
                    logs_df = gr.Dataframe(
                        headers=["请求 ID", "API 名称", "调用时间", "模型",
                                 "输入 Token", "输出 Token", "状态", "错误信息"],
                        datatype=["str", "str", "str", "str", "number", "number", "str", "str"],
                        interactive=False,
                        show_search="filter",
                    )
```

- [ ] **Step 8.2:** 添加调用记录渲染函数

```python
        def render_logs():
            """渲染调用记录"""
            logs = get_call_logs(200)
            if not logs:
                return (
                    '<div class="msg-info">暂无调用记录</div>',
                    None,
                )
            df = pd.DataFrame(logs)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            df = df.sort_values('created_at', ascending=False)

            display_df = df[['request_id', 'api_key_name', 'created_at', 'model_name',
                             'input_tokens', 'output_tokens', 'status', 'error_message']].copy()
            display_df.columns = ['请求 ID', 'API 名称', '调用时间', '模型',
                                  '输入 Token', '输出 Token', '状态', '错误信息']
            # 状态列添加颜色标记
            display_df['状态'] = display_df['状态'].apply(
                lambda x: '成功' if x == 'success' else f'失败({x})'
            )

            return "", display_df
```

更新 `full_refresh` 以包含调用记录：

```python
        def full_refresh():
            stat_html, cards_html, df_data = render_dashboard()
            models_html = render_models_list()
            choices = get_model_choices()
            keys_html = render_apikeys_list()
            logs_msg_html, logs_data = render_logs()
            return (
                stat_html, cards_html, df_data,
                models_html,
                gr.update(choices=choices),
                keys_html,
                logs_data,
            )

        refresh_btn.click(
            fn=full_refresh,
            inputs=[],
            outputs=[stat_cards, model_cards, dashboard_df, models_list,
                     default_model_select, apikeys_list, logs_df],
        )
```

更新 `handle_login` 函数的返回值以包含调用记录数据：

```python
        def handle_login(username, password, state):
            """处理登录"""
            if not username or not password:
                return (
                    state, True, False,
                    '<div class="msg-error">请输入用户名和密码</div>',
                    "", "", "", "", None, "", None,
                )
            if login_user(username, password):
                state["is_logged_in"] = True
                state["username"] = username
                nav_html = render_nav(username)
                stat_html, cards_html, df_data = render_dashboard()
                keys_html = render_apikeys_list()
                logs_msg_html, logs_data = render_logs()
                return (
                    state, False, True, "",
                    "", nav_html, stat_html, cards_html, df_data,
                    keys_html, logs_data,
                )
            return (
                state, True, False,
                '<div class="msg-error">用户名或密码错误</div>',
                "", "", "", "", None, "", None,
            )

        login_btn.click(
            fn=handle_login,
            inputs=[login_username, login_password, session_state],
            outputs=[session_state, login_area, main_area, login_msg, login_username,
                     nav_bar, stat_cards, model_cards, dashboard_df,
                     apikeys_list, logs_df],
        )
```

- [ ] **Step 8.3:** 验证

```bash
python gradio_app/app.py
# 验证：
# - 调用记录页正确显示数据表格
# - 表格包含请求 ID、API 名称、调用时间、模型、Token、状态、错误信息
# - 状态列显示"成功"或"失败"
# - 刷新按钮可更新所有页面数据
# - 页脚显示版权信息
```

---

### Task 9: 部署配置更新

**Files:** `supervisord.conf`, `Dockerfile.clean`, `docker-compose.clean.yml`

**说明：** 更新部署配置，将 Streamlit 替换为 Gradio。同时保留 Streamlit 配置（注释形式）以便回滚。

- [ ] **Step 9.1:** 更新 `supervisord.conf`

```ini
[supervisord]
nodaemon=true
user=root

[program:uvicorn]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:gradio]
command=python gradio_app/app.py
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONPATH="/app"

# [program:streamlit]
# command=streamlit run streamlit_app/home.py --server.port 8501 --server.address 0.0.0.0
# autostart=true
# autorestart=true
# stdout_logfile=/dev/stdout
# stdout_logfile_maxbytes=0
# stderr_logfile=/dev/stderr
# stderr_logfile_maxbytes=0
```

- [ ] **Step 9.2:** 更新 `Dockerfile.clean`

```dockerfile
# Union AI API - Clean Docker Image
# 此 Dockerfile 用于创建干净的生产环境镜像，不包含任何本地配置和数据

FROM python:3.11-slim

WORKDIR /app

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（不包含数据文件）
COPY app ./app
COPY streamlit_app ./streamlit_app
COPY gradio_app ./gradio_app

# 复制 supervisord 配置
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 创建数据目录（实际数据将通过 volume 挂载）
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000 8501

# 启动 supervisord
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

- [ ] **Step 9.3:** `docker-compose.clean.yml` 无需修改（端口映射 18501:8501 不变）

- [ ] **Step 9.4:** 验证

```bash
# 本地验证
python gradio_app/app.py
# 确认 Gradio 在 8501 端口启动

# Docker 验证（可选）
docker build -t union-ai-api:latest -f Dockerfile.clean .
docker run -d -p 18080:8000 -p 18501:8501 -v ./data:/app/data union-ai-api:latest
# 访问 http://localhost:18501 确认管理后台正常
```

---

### Task 10: 最终清理

**Files:** 项目根目录

**说明：** 全功能回归测试，确保所有功能正常工作。保留 Streamlit 代码（可通过 supervisord 注释切换回 Streamlit）。

- [ ] **Step 10.1:** 全功能回归测试清单

```
1. [ ] 首次使用 - 无用户时自动显示注册页
2. [ ] 注册新用户 - 输入用户名/密码/确认密码
3. [ ] 注册验证 - 密码不一致、过短、用户名已存在
4. [ ] 登录 - 输入用户名和密码
5. [ ] 登录验证 - 错误密码提示
6. [ ] 退出登录 - 回到登录页
7. [ ] 数据概览 - 统计摘要卡片显示正确数值
8. [ ] 数据概览 - 模型卡片网格按渐变色板循环
9. [ ] 数据概览 - 不可用模型灰色 + 透明度
10. [ ] 数据概览 - 详细数据表格显示
11. [ ] 数据概览 - 刷新按钮更新数据
12. [ ] 模型配置 - 添加新模型
13. [ ] 模型配置 - 编辑模型
14. [ ] 模型配置 - 删除模型
15. [ ] 模型配置 - 自动切换开关
16. [ ] 模型配置 - 默认模型选择（关闭自动切换时）
17. [ ] 模型配置 - 导出配置到 Excel
18. [ ] 模型配置 - 导入 Excel 配置
19. [ ] API Key - 生成新 Key
20. [ ] API Key - Key 列表展示
21. [ ] API Key - 删除 Key
22. [ ] 调用记录 - 数据表格显示
23. [ ] 页脚 - 版权信息
24. [ ] 响应式 - 窗口缩小时布局正常
25. [ ] 字体 - DM Sans + Outfit 正确加载
```

- [ ] **Step 10.2:** 启动命令确认

```bash
# 本地开发
python gradio_app/app.py

# 或使用 gradio CLI
gradio gradio_app/app.py

# Docker 部署
./start.sh
```

- [ ] **Step 10.3:** 可选 - 清理旧 Streamlit 代码

如果要完全移除 Streamlit 依赖：
1. 从 `requirements.txt` 中删除 `streamlit==1.31.1`
2. 删除 `streamlit_app/` 目录（注意：`db.py` 已被 Gradio 引用，需要先迁移到 `gradio_app/db.py` 或独立的 `db/` 目录）
3. 从 `supervisord.conf` 中删除注释掉的 Streamlit 配置

**推荐：** 暂时保留 Streamlit 代码和依赖，确保 Gradio 版本稳定后再清理。

---

## 附录：完整的文件结构

```
union-ai-api/
├── app/                    # FastAPI API 服务（不变）
├── streamlit_app/          # Streamlit 旧版（保留，供回滚）
│   ├── home.py
│   └── db.py               # 数据库层（Gradio 直接 import）
├── gradio_app/             # Gradio 新版管理后台
│   ├── __init__.py
│   └── app.py              # Gradio 应用入口
├── data/                   # SQLite 数据库（volume 挂载）
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-04-14-ui-redesign-design.md
│       └── plans/
│           └── 2026-04-14-ui-redesign-gradio.md  # 本文件
├── requirements.txt        # 依赖（添加 gradio）
├── supervisord.conf        # 部署配置（Streamlit → Gradio）
├── Dockerfile.clean        # Docker 配置（添加 gradio_app/）
├── docker-compose.clean.yml
├── start.sh
└── ...
```

## Gradio 与 Streamlit 关键差异备忘

| 概念 | Streamlit | Gradio |
|------|-----------|--------|
| 状态管理 | `st.session_state` | `gr.State()` |
| 页面切换 | `st.rerun()` + session_state | `gr.Column(visible=...)` |
| 导航 | `st.sidebar` + `st.button` | `gr.Tabs()` + CSS 覆盖 |
| 自定义 HTML | `st.markdown(html, unsafe_allow_html=True)` | `gr.HTML(html)` |
| 表格 | `st.dataframe(df)` | `gr.Dataframe(value=df)` |
| 表单 | `st.form` + `st.form_submit_button` | `gr.Button` + `.click()` 事件绑定 |
| 布局 | `st.columns()` | `gr.Row()` / `gr.Column()` |
| 文件上传 | `st.file_uploader` | `gr.File()` |
| 文件下载 | `st.download_button` | `gr.File()` 返回值 |
| 执行模型 | 每次交互重新执行整个脚本 | 构建一次 UI，回调驱动 |
| CSS 注入 | `st.markdown("<style>...")` | `gr.Blocks(css=...)` |
