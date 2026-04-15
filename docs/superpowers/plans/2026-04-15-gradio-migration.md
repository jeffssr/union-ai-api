# Gradio 前端迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Streamlit 管理后台前端完整迁移到 Gradio 5.x，保持所有业务逻辑不变。

**Architecture:** 新建 `gradio_app/` 目录，`gr.Blocks` + `gr.Tabs` 单页应用。页面模块化（每个页面一个文件），纯函数（HTML 构建、DataFrame 构建）和 Gradio UI 绑定在同一文件但逻辑分离。TDD 驱动纯函数，UI 绑定手测验证。

**Tech Stack:** Python 3.11, Gradio 5.x (>=5.0,<6.0), SQLite, pandas, openpyxl, pytest

**TDD 策略：**
- 纯函数（HTML 构建、DataFrame 构建、Excel 导入导出）→ pytest 单元测试
- 数据库 CRUD → pytest + 临时 SQLite（monkeypatch DATABASE_PATH）
- Gradio UI 绑定 → 手动验证

**前提：** 在隔离工作区（worktree）中执行，不在 main 分支直接修改。

---

## 文件结构

| 操作 | 文件路径 | 职责 |
|------|----------|------|
| 创建 | `gradio_app/__init__.py` | 包标记 |
| 创建 | `gradio_app/db.py` | 数据库操作（复制自 streamlit_app/db.py） |
| 创建 | `gradio_app/theme.py` | MiniMax 主题 + 自定义 CSS |
| 创建 | `gradio_app/pages/__init__.py` | 包标记 |
| 创建 | `gradio_app/pages/dashboard.py` | 数据概览页 |
| 创建 | `gradio_app/pages/call_logs.py` | 调用记录页 |
| 创建 | `gradio_app/pages/api_keys.py` | API Key 管理页 |
| 创建 | `gradio_app/pages/model_config.py` | 模型配置页 |
| 创建 | `gradio_app/app.py` | 主入口：Blocks + Tabs + 认证 + 启动 |
| 创建 | `tests/__init__.py` | 测试包标记 |
| 创建 | `tests/conftest.py` | pytest 共享 fixtures（临时数据库） |
| 创建 | `tests/test_db.py` | 数据库操作测试 |
| 创建 | `tests/test_auth.py` | 认证逻辑测试 |
| 创建 | `tests/test_dashboard.py` | Dashboard 纯函数测试 |
| 创建 | `tests/test_call_logs.py` | 调用记录纯函数测试 |
| 创建 | `tests/test_model_config.py` | 模型配置纯函数测试（Excel 导入导出） |
| 修改 | `requirements.txt` | streamlit → gradio, 添加 pytest |
| 修改 | `supervisord.conf` | 启动命令改为 gradio |
| 修改 | `Dockerfile.clean` | 复制 gradio_app 目录 |

---

### Task 1: 创建项目骨架

**Files:**
- Create: `gradio_app/__init__.py`
- Create: `gradio_app/pages/__init__.py`
- Create: `tests/__init__.py`
- Create: `gradio_app/db.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p gradio_app/pages tests
touch gradio_app/__init__.py gradio_app/pages/__init__.py tests/__init__.py
```

- [ ] **Step 2: 复制 db.py**

```bash
cp streamlit_app/db.py gradio_app/db.py
```

- [ ] **Step 3: 安装依赖**

```bash
pip install "gradio>=5.0,<6.0" pytest
```

- [ ] **Step 4: 提交**

```bash
git add gradio_app/ tests/__init__.py
git commit -m "feat(gradio): 初始化项目结构和 db.py"
```

---

### Task 2: 测试基础设施 + db.py 验证

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_db.py`

**目标：** 验证复制过来的 db.py 所有函数在测试环境中正常工作。由于 db.py 在模块末尾调用了 `init_db()`（line 276），测试时需要通过 monkeypatch 替换 `DATABASE_PATH`。

- [ ] **Step 1: 创建 conftest.py**

```python
# tests/conftest.py
import pytest
import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def test_db(tmp_path, monkeypatch):
    """为每个测试创建临时数据库，自动替换 db.py 的 DATABASE_PATH"""
    import gradio_app.db as db_module

    test_db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DATABASE_PATH", test_db_path)

    # 确保测试数据目录存在
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)

    # 初始化数据库（创建表）
    db_module.init_db()

    yield db_module
```

- [ ] **Step 2: 创建 test_db.py**

```python
# tests/test_db.py
import pytest
from gradio_app.db import (
    create_user, get_user, verify_password, has_users,
    update_user_password,
    get_auto_switch_status, set_auto_switch_status,
    get_all_models, create_model, update_model, delete_model,
    get_all_api_keys, create_api_key, delete_api_key,
    get_call_logs, get_daily_stats,
    hash_password,
)


class TestUserAuth:
    """用户认证相关测试"""

    def test_has_users_initially_false(self, test_db):
        assert test_db.has_users() is False

    def test_create_user_success(self, test_db):
        assert test_db.create_user("admin", "password123") is True

    def test_create_user_duplicate_fails(self, test_db):
        test_db.create_user("admin", "password123")
        assert test_db.create_user("admin", "another") is False

    def test_has_users_after_creation(self, test_db):
        test_db.create_user("admin", "password123")
        assert test_db.has_users() is True

    def test_get_user_exists(self, test_db):
        test_db.create_user("admin", "password123")
        user = test_db.get_user("admin")
        assert user is not None
        assert user["username"] == "admin"
        assert "password_hash" in user
        assert "salt" in user

    def test_get_user_not_exists(self, test_db):
        assert test_db.get_user("nobody") is None

    def test_verify_password_correct(self, test_db):
        test_db.create_user("admin", "password123")
        user = test_db.get_user("admin")
        assert test_db.verify_password("password123", user["password_hash"], user["salt"]) is True

    def test_verify_password_wrong(self, test_db):
        test_db.create_user("admin", "password123")
        user = test_db.get_user("admin")
        assert test_db.verify_password("wrong", user["password_hash"], user["salt"]) is False

    def test_update_password(self, test_db):
        test_db.create_user("admin", "old_pass")
        test_db.update_user_password("admin", "new_pass")
        user = test_db.get_user("admin")
        assert test_db.verify_password("new_pass", user["password_hash"], user["salt"]) is True
        assert test_db.verify_password("old_pass", user["password_hash"], user["salt"]) is False


class TestModels:
    """模型 CRUD 测试"""

    def test_get_all_models_empty(self, test_db):
        assert test_db.get_all_models() == []

    def test_create_model(self, test_db):
        config_id = test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        assert config_id is not None
        assert len(config_id) == 8

    def test_get_all_models_after_create(self, test_db):
        test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        models = test_db.get_all_models()
        assert len(models) == 1
        assert models[0]["name"] == "GPT-4"
        assert models[0]["model_id"] == "gpt-4"
        assert models[0]["priority"] == 5

    def test_update_model(self, test_db):
        config_id = test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        test_db.update_model(config_id, "GPT-4-Turbo", "https://new.api.com/v1", "sk-new", "gpt-4-turbo", 200000, 2000, 0, 10)
        models = test_db.get_all_models()
        assert models[0]["name"] == "GPT-4-Turbo"
        assert models[0]["priority"] == 10

    def test_delete_model(self, test_db):
        config_id = test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        test_db.delete_model(config_id)
        assert test_db.get_all_models() == []

    def test_models_ordered_by_priority(self, test_db):
        test_db.create_model("Low", "url1", "key1", "", 100, 10, 1)
        test_db.create_model("High", "url2", "key2", "", 100, 10, 10)
        test_db.create_model("Med", "url3", "key3", "", 100, 10, 5)
        models = test_db.get_all_models()
        assert models[0]["name"] == "High"
        assert models[1]["name"] == "Med"
        assert models[2]["name"] == "Low"

    def test_update_default_model_clears_others(self, test_db):
        id1 = test_db.create_model("A", "url1", "key1", "", 100, 10, 1)
        id2 = test_db.create_model("B", "url2", "key2", "", 100, 10, 2)
        test_db.update_model(id1, "A", "url1", "key1", "", 100, 10, 1, 1)
        models = test_db.get_all_models()
        for m in models:
            if m["config_id"] == id1:
                assert m["is_default_model"] == 1
            else:
                assert m["is_default_model"] == 0


class TestApiKeys:
    """API Key CRUD 测试"""

    def test_get_all_api_keys_empty(self, test_db):
        assert test_db.get_all_api_keys() == []

    def test_create_api_key(self, test_db):
        result = test_db.create_api_key("test-app")
        assert result["name"] == "test-app"
        assert result["api_key"].startswith("sk-")
        assert len(result["key_id"]) == 8

    def test_get_all_api_keys(self, test_db):
        test_db.create_api_key("app1")
        test_db.create_api_key("app2")
        keys = test_db.get_all_api_keys()
        assert len(keys) == 2

    def test_delete_api_key(self, test_db):
        result = test_db.create_api_key("test-app")
        test_db.delete_api_key(result["key_id"])
        keys = test_db.get_all_api_keys()
        assert len(keys) == 1  # 软删除，is_active=0


class TestSystemConfig:
    """系统配置测试"""

    def test_auto_switch_default_enabled(self, test_db):
        assert test_db.get_auto_switch_status() is True

    def test_set_auto_switch_disabled(self, test_db):
        test_db.set_auto_switch_status(False)
        assert test_db.get_auto_switch_status() is False

    def test_set_auto_switch_enabled(self, test_db):
        test_db.set_auto_switch_status(False)
        test_db.set_auto_switch_status(True)
        assert test_db.get_auto_switch_status() is True


class TestDailyStats:
    """日统计查询测试"""

    def test_get_daily_stats_empty(self, test_db):
        stats = test_db.get_daily_stats()
        assert stats == []

    def test_get_daily_stats_with_model(self, test_db):
        test_db.create_model("GPT-4", "url", "key", "gpt-4", 100000, 1000, 5)
        stats = test_db.get_daily_stats()
        assert len(stats) == 1
        assert stats[0]["name"] == "GPT-4"
        assert stats[0]["used_tokens"] == 0
        assert stats[0]["used_calls"] == 0

    def test_get_call_logs_empty(self, test_db):
        logs = test_db.get_call_logs()
        assert logs == []
```

- [ ] **Step 3: 运行测试**

```bash
cd D:/Jimmy/Softwares/union-ai-api
python -m pytest tests/test_db.py -v
```

Expected: 全部 PASSED

- [ ] **Step 4: 提交**

```bash
git add tests/conftest.py tests/test_db.py
git commit -m "test(gradio): 添加测试基础设施和 db.py 完整测试"
```

---

### Task 3: 认证逻辑测试

**Files:**
- Create: `tests/test_auth.py`

**目标：** 测试 auth_fn 的 3 种场景和注册验证逻辑。

- [ ] **Step 1: 创建 test_auth.py**

```python
# tests/test_auth.py
import pytest


def auth_fn(username, password, db_module):
    """认证函数（与 app.py 中逻辑一致）"""
    if not db_module.has_users():
        return True
    user = db_module.get_user(username)
    if user and db_module.verify_password(password, user["password_hash"], user["salt"]):
        return True
    return False


def validate_register(username, password, confirm, db_module):
    """注册验证逻辑"""
    if not username or not password:
        return False, "请输入用户名和密码"
    if password != confirm:
        return False, "两次输入的密码不一致"
    if len(password) < 4:
        return False, "密码长度至少为4位"
    if db_module.create_user(username, password):
        return True, "注册成功"
    return False, "用户名已存在"


class TestAuthFn:
    """auth_fn 认证函数测试"""

    def test_no_users_always_passes(self, test_db):
        assert auth_fn("anyone", "anything", test_db) is True

    def test_correct_password_passes(self, test_db):
        test_db.create_user("admin", "password123")
        assert auth_fn("admin", "password123", test_db) is True

    def test_wrong_password_fails(self, test_db):
        test_db.create_user("admin", "password123")
        assert auth_fn("admin", "wrong", test_db) is False

    def test_nonexistent_user_fails(self, test_db):
        test_db.create_user("admin", "password123")
        assert auth_fn("nobody", "password123", test_db) is False

    def test_empty_credentials_fails(self, test_db):
        test_db.create_user("admin", "password123")
        assert auth_fn("", "", test_db) is False


class TestRegisterValidation:
    """注册验证逻辑测试"""

    def test_empty_username_fails(self, test_db):
        ok, msg = validate_register("", "pass1234", "pass1234", test_db)
        assert ok is False
        assert "用户名" in msg

    def test_empty_password_fails(self, test_db):
        ok, msg = validate_register("admin", "", "", test_db)
        assert ok is False

    def test_password_mismatch_fails(self, test_db):
        ok, msg = validate_register("admin", "pass1234", "different", test_db)
        assert ok is False
        assert "不一致" in msg

    def test_short_password_fails(self, test_db):
        ok, msg = validate_register("admin", "ab", "ab", test_db)
        assert ok is False
        assert "4" in msg

    def test_valid_registration_succeeds(self, test_db):
        ok, msg = validate_register("admin", "password123", "password123", test_db)
        assert ok is True
        assert test_db.has_users() is True

    def test_duplicate_username_fails(self, test_db):
        validate_register("admin", "password123", "password123", test_db)
        ok, msg = validate_register("admin", "another123", "another123", test_db)
        assert ok is False
        assert "已存在" in msg
```

- [ ] **Step 2: 运行测试**

```bash
python -m pytest tests/test_auth.py -v
```

Expected: 全部 PASSED

- [ ] **Step 3: 提交**

```bash
git add tests/test_auth.py
git commit -m "test(gradio): 添加认证逻辑测试"
```

---

### Task 4: MiniMax 主题 + CSS

**Files:**
- Create: `gradio_app/theme.py`

无测试（主题是配置 + CSS 字符串）。

- [ ] **Step 1: 创建 theme.py**

```python
# gradio_app/theme.py
import gradio as gr

# 渐变色板
GRADIENT_COLORS = [
    "linear-gradient(135deg, #1456f0, #3b82f6)",
    "linear-gradient(135deg, #ea5ec1, #9333ea)",
    "linear-gradient(135deg, #3daeff, #1456f0)",
    "linear-gradient(135deg, #f97316, #ea5ec1)",
    "linear-gradient(135deg, #10b981, #3b82f6)",
]
UNAVAILABLE_GRADIENT = "linear-gradient(135deg, #8e8e93, #45515e)"


def create_theme():
    """创建 MiniMax 风格的 Gradio 主题"""
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.blue,
        secondary_hue=gr.themes.colors.pink,
        neutral_hue=gr.themes.colors.gray,
        font=gr.themes.GoogleFont("DM Sans"),
    )
    return theme


CUSTOM_CSS = """
/* Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600&display=swap');

/* 全局字体 */
body, .gradio-container {
    font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
}

/* Tab 导航：药丸按钮 */
.tabs {
    border: none !important;
}
.tabs .tab-nav {
    background: white !important;
    border-bottom: 1px solid #f2f3f5 !important;
    padding: 8px 16px !important;
    gap: 4px !important;
}
.tabs .tab-nav button {
    border-radius: 9999px !important;
    border: none !important;
    padding: 8px 20px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #8e8e93 !important;
    background: transparent !important;
}
.tabs .tab-nav button.selected {
    background: rgba(0, 0, 0, 0.05) !important;
    color: #18181b !important;
}

/* 卡片圆角 */
.gr-box, .gr-panel {
    border-radius: 16px !important;
}

/* 表格样式 */
.gr-dataframe table {
    border-collapse: collapse !important;
}
.gr-dataframe thead th {
    background: #f8fafc !important;
    color: #45515e !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}
.gr-dataframe tbody tr {
    border-top: 1px solid #f2f3f5 !important;
    font-size: 13px !important;
}
.gr-dataframe tbody tr:nth-child(even) {
    background: #fafbfc !important;
}

/* 隐藏默认 footer */
footer {
    display: none !important;
}

/* 按钮基础样式调整 */
.primary-btn {
    background: #1456f0 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
"""
```

- [ ] **Step 2: 提交**

```bash
git add gradio_app/theme.py
git commit -m "feat(gradio): 添加 MiniMax 主题和自定义 CSS"
```

---

### Task 5: Dashboard 纯函数 TDD

**Files:**
- Create: `tests/test_dashboard.py`
- Create: `gradio_app/pages/dashboard.py`（先只写纯函数）

**目标：** TDD 实现 `build_stats_html`、`build_model_cards_html`、`build_detail_dataframe`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_dashboard.py
import pytest
import pandas as pd


def sample_stats():
    """测试用统计数据"""
    return [
        {
            "config_id": "abc12345",
            "name": "GPT-4",
            "model_id": "gpt-4",
            "api_url": "https://api.openai.com/v1",
            "daily_token_limit": 100000,
            "daily_call_limit": 1000,
            "is_default_model": 1,
            "is_active": 1,
            "priority": 10,
            "used_tokens": 50000,
            "used_calls": 500,
        },
        {
            "config_id": "def67890",
            "name": "Claude",
            "model_id": "claude-3",
            "api_url": "https://api.anthropic.com/v1",
            "daily_token_limit": 200000,
            "daily_call_limit": 2000,
            "is_default_model": 0,
            "is_active": 1,
            "priority": 5,
            "used_tokens": 200000,
            "used_calls": 100,
        },
    ]


class TestBuildStatsHtml:
    """统计摘要卡片 HTML 构建测试"""

    def test_empty_stats(self):
        from gradio_app.pages.dashboard import build_stats_html
        html = build_stats_html([])
        assert "stat-card" in html
        assert "0" in html

    def test_shows_total_tokens(self):
        from gradio_app.pages.dashboard import build_stats_html
        html = build_stats_html(sample_stats())
        assert "250,000" in html

    def test_shows_total_calls(self):
        from gradio_app.pages.dashboard import build_stats_html
        html = build_stats_html(sample_stats())
        assert "600" in html

    def test_shows_active_models(self):
        from gradio_app.pages.dashboard import build_stats_html
        html = build_stats_html(sample_stats())
        # GPT-4: 可用, Claude: token 满了不可用
        assert ">1<" in html

    def test_contains_three_cards(self):
        from gradio_app.pages.dashboard import build_stats_html
        html = build_stats_html(sample_stats())
        assert html.count("stat-card") == 3


class TestBuildModelCardsHtml:
    """模型状态卡片 HTML 构建测试"""

    def test_empty_stats(self):
        from gradio_app.pages.dashboard import build_model_cards_html
        html = build_model_cards_html([])
        assert "暂无" in html

    def test_shows_model_name(self):
        from gradio_app.pages.dashboard import build_model_cards_html
        html = build_model_cards_html(sample_stats())
        assert "GPT-4" in html
        assert "Claude" in html

    def test_default_badge(self):
        from gradio_app.pages.dashboard import build_model_cards_html
        html = build_model_cards_html(sample_stats())
        assert "默认" in html

    def test_unavailable_model_has_class(self):
        from gradio_app.pages.dashboard import build_model_cards_html
        html = build_model_cards_html(sample_stats())
        assert "unavailable" in html

    def test_shows_token_usage(self):
        from gradio_app.pages.dashboard import build_model_cards_html
        html = build_model_cards_html(sample_stats())
        assert "50,000" in html
        assert "100,000" in html


class TestBuildDetailDataframe:
    """详细数据 DataFrame 构建测试"""

    def test_empty_stats(self):
        from gradio_app.pages.dashboard import build_detail_dataframe
        df = build_detail_dataframe([])
        assert df.empty

    def test_correct_columns(self):
        from gradio_app.pages.dashboard import build_detail_dataframe
        df = build_detail_dataframe(sample_stats())
        expected_cols = [
            "模型名称", "Model ID", "是否可用", "已用调用", "调用限额",
            "剩余调用", "调用使用率", "已用 Token", "Token 限额",
            "剩余 Token", "Token 使用率", "默认模型", "优先级"
        ]
        assert list(df.columns) == expected_cols

    def test_availability(self):
        from gradio_app.pages.dashboard import build_detail_dataframe
        df = build_detail_dataframe(sample_stats())
        assert "可用" in df["是否可用"].values
        assert "不可用" in df["是否可用"].values

    def test_usage_rate(self):
        from gradio_app.pages.dashboard import build_detail_dataframe
        df = build_detail_dataframe(sample_stats())
        assert "%" in df["Token 使用率"].iloc[0]
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_dashboard.py -v
```

Expected: ImportError

- [ ] **Step 3: 实现 Dashboard 纯函数**

```python
# gradio_app/pages/dashboard.py
import pandas as pd
from gradio_app.theme import GRADIENT_COLORS, UNAVAILABLE_GRADIENT


def _is_available(stat):
    """判断模型是否可用"""
    return (stat["used_tokens"] < stat["daily_token_limit"] and
            stat["used_calls"] < stat["daily_call_limit"] and
            stat["is_active"] == 1)


def _format_number(n):
    """格式化数字为带逗号的字符串"""
    return f"{n:,}"


def build_stats_html(stats):
    """构建统计摘要卡片 HTML"""
    total_tokens = sum(s["used_tokens"] for s in stats)
    total_calls = sum(s["used_calls"] for s in stats)
    active_models = sum(1 for s in stats if _is_available(s))

    cards = [
        ("今日 Token 用量", _format_number(total_tokens), GRADIENT_COLORS[0]),
        ("今日调用次数", _format_number(total_calls), GRADIENT_COLORS[1]),
        ("活跃模型数", str(active_models), GRADIENT_COLORS[2]),
    ]

    html_parts = ['<div style="display: flex; gap: 16px; margin-bottom: 24px;">']
    for label, value, gradient in cards:
        html_parts.append(f"""
        <div class="stat-card" style="flex: 1; background: {gradient}; border-radius: 16px;
            padding: 20px; color: white; box-shadow: rgba(44,30,116,0.16) 0px 0px 15px;">
            <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">{label}</div>
            <div style="font-size: 24px; font-weight: 600;">{value}</div>
        </div>""")
    html_parts.append('</div>')
    return "".join(html_parts)


def build_model_cards_html(stats):
    """构建模型状态卡片 HTML"""
    if not stats:
        return '<p style="color: #8e8e93; font-size: 14px;">暂无模型配置</p>'

    html_parts = [
        '<div style="font-size: 16px; font-weight: 500; color: #222222; margin-bottom: 12px;">模型状态</div>',
        '<div style="display: flex; gap: 16px; flex-wrap: wrap;">'
    ]

    for i, stat in enumerate(stats):
        gradient = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
        available = _is_available(stat)
        if not available:
            gradient = UNAVAILABLE_GRADIENT

        opacity = "opacity: 0.6;" if not available else ""
        default_badge = ('<span style="background: rgba(255,255,255,0.25); border-radius: 9999px;'
                         'padding: 2px 10px; font-size: 12px;">默认</span>'
                         if stat["is_default_model"] == 1 else "")
        token_rate = int(stat["used_tokens"] / stat["daily_token_limit"] * 100) if stat["daily_token_limit"] > 0 else 0

        html_parts.append(f"""
        <div style="flex: 1; min-width: 200px; background: {gradient}; border-radius: 16px;
            padding: 16px; color: white; position: relative; {opacity}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 16px; font-weight: 600;">{stat['name']}</span>
                {default_badge}
            </div>
            <div style="font-size: 12px; opacity: 0.85; margin-bottom: 8px;">
                {stat.get('model_id', 'N/A')} · 优先级 {stat['priority']}
            </div>
            <div style="font-size: 12px; opacity: 0.8;">
                Token: {_format_number(stat['used_tokens'])} / {_format_number(stat['daily_token_limit'])} ·
                调用: {_format_number(stat['used_calls'])} / {_format_number(stat['daily_call_limit'])}
            </div>
            <div style="margin-top: 8px; background: rgba(255,255,255,0.2); border-radius: 9999px; height: 4px;">
                <div style="background: white; border-radius: 9999px; height: 4px; width: {token_rate}%;"></div>
            </div>
        </div>""")

    html_parts.append('</div>')
    return "".join(html_parts)


def build_detail_dataframe(stats):
    """构建详细数据 DataFrame"""
    if not stats:
        return pd.DataFrame()

    rows = []
    for s in stats:
        available = _is_available(s)
        remaining_tokens = s["daily_token_limit"] - s["used_tokens"]
        remaining_calls = s["daily_call_limit"] - s["used_calls"]
        token_rate = f"{s['used_tokens'] / s['daily_token_limit'] * 100:.1f}%" if s["daily_token_limit"] > 0 else "0%"
        call_rate = f"{s['used_calls'] / s['daily_call_limit'] * 100:.1f}%" if s["daily_call_limit"] > 0 else "0%"
        rows.append({
            "模型名称": s["name"],
            "Model ID": s["model_id"],
            "是否可用": "可用" if available else "不可用",
            "已用调用": s["used_calls"],
            "调用限额": s["daily_call_limit"],
            "剩余调用": remaining_calls,
            "调用使用率": call_rate,
            "已用 Token": s["used_tokens"],
            "Token 限额": s["daily_token_limit"],
            "剩余 Token": remaining_tokens,
            "Token 使用率": token_rate,
            "默认模型": "是" if s["is_default_model"] == 1 else "",
            "优先级": s["priority"],
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_dashboard.py -v
```

Expected: 全部 PASSED

- [ ] **Step 5: 提交**

```bash
git add tests/test_dashboard.py gradio_app/pages/dashboard.py
git commit -m "feat(gradio): TDD 实现 Dashboard 纯函数"
```

---

### Task 6: 调用记录纯函数 TDD

**Files:**
- Create: `tests/test_call_logs.py`
- Create: `gradio_app/pages/call_logs.py`（先只写纯函数）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_call_logs.py
import pytest
import pandas as pd
import sqlite3


def insert_sample_logs(test_db):
    """插入测试用调用记录"""
    key_result = test_db.create_api_key("test-app")
    config_id = test_db.create_model("GPT-4", "url", "key", "gpt-4", 100000, 1000, 5)

    conn = sqlite3.connect(test_db.DATABASE_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO call_logs (request_id, api_key_id, api_key_name, model_config_id,
                               model_name, input_tokens, output_tokens, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("req-001", key_result["key_id"], "test-app", config_id,
          "GPT-4", 100, 200, "success", "2026-04-15 10:00:00"))
    cursor.execute("""
        INSERT INTO call_logs (request_id, api_key_id, api_key_name, model_config_id,
                               model_name, input_tokens, output_tokens, status,
                               error_message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, ("req-002", key_result["key_id"], "test-app", config_id,
          "GPT-4", 50, 0, "failed", "timeout", "2026-04-15 11:00:00"))
    conn.commit()
    conn.close()


class TestBuildLogsDataframe:
    """调用记录 DataFrame 构建测试"""

    def test_empty_logs(self, test_db):
        from gradio_app.pages.call_logs import build_logs_dataframe
        df = build_logs_dataframe(test_db.get_call_logs())
        assert df.empty

    def test_correct_columns(self, test_db):
        insert_sample_logs(test_db)
        from gradio_app.pages.call_logs import build_logs_dataframe
        df = build_logs_dataframe(test_db.get_call_logs())
        expected = ["请求 ID", "API 名称", "调用时间", "模型", "输入 Token", "输出 Token", "状态", "错误信息"]
        assert list(df.columns) == expected

    def test_logs_count(self, test_db):
        insert_sample_logs(test_db)
        from gradio_app.pages.call_logs import build_logs_dataframe
        df = build_logs_dataframe(test_db.get_call_logs())
        assert len(df) == 2

    def test_logs_sorted_by_time_desc(self, test_db):
        insert_sample_logs(test_db)
        from gradio_app.pages.call_logs import build_logs_dataframe
        df = build_logs_dataframe(test_db.get_call_logs())
        assert df.iloc[0]["请求 ID"] == "req-002"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_call_logs.py -v
```

- [ ] **Step 3: 实现调用记录纯函数**

```python
# gradio_app/pages/call_logs.py
import pandas as pd


def build_logs_dataframe(logs):
    """构建调用记录 DataFrame"""
    if not logs:
        return pd.DataFrame(columns=["请求 ID", "API 名称", "调用时间", "模型", "输入 Token", "输出 Token", "状态", "错误信息"])

    rows = []
    for log in logs:
        rows.append({
            "请求 ID": log.get("request_id", ""),
            "API 名称": log.get("api_key_name", ""),
            "调用时间": log.get("created_at", ""),
            "模型": log.get("model_name", ""),
            "输入 Token": log.get("input_tokens", 0),
            "输出 Token": log.get("output_tokens", 0),
            "状态": log.get("status", ""),
            "错误信息": log.get("error_message") or "-",
        })
    return pd.DataFrame(rows)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_call_logs.py -v
```

- [ ] **Step 5: 提交**

```bash
git add tests/test_call_logs.py gradio_app/pages/call_logs.py
git commit -m "feat(gradio): TDD 实现调用记录纯函数"
```

---

### Task 7: 模型配置纯函数 TDD（Excel 导入导出）

**Files:**
- Create: `tests/test_model_config.py`
- Create: `gradio_app/pages/model_config.py`（先只写纯函数）

- [ ] **Step 1: 写失败测试**

```python
# tests/test_model_config.py
import pytest
import io
import pandas as pd


class TestExportModelsToExcel:
    """Excel 导出测试"""

    def test_export_empty_returns_none(self, test_db):
        from gradio_app.pages.model_config import export_models_to_excel
        assert export_models_to_excel(test_db.get_all_models) is None

    def test_export_returns_bytes(self, test_db):
        test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        from gradio_app.pages.model_config import export_models_to_excel
        data = export_models_to_excel(test_db.get_all_models)
        assert data is not None
        assert isinstance(data, bytes)

    def test_export_contains_model_data(self, test_db):
        test_db.create_model("GPT-4", "https://api.openai.com/v1", "sk-test", "gpt-4", 100000, 1000, 5)
        from gradio_app.pages.model_config import export_models_to_excel
        data = export_models_to_excel(test_db.get_all_models)
        df = pd.read_excel(io.BytesIO(data))
        assert len(df) == 1
        assert df.iloc[0]["模型名称"] == "GPT-4"


class TestImportModelsFromExcel:
    """Excel 导入测试"""

    def _make_excel(self, data_dict):
        df = pd.DataFrame(data_dict)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='模型配置')
        output.seek(0)
        return output.getvalue()

    def test_import_none_file_fails(self, test_db):
        from gradio_app.pages.model_config import import_models_from_excel
        ok, msg = import_models_from_excel(None, test_db.create_model)
        assert ok is False

    def test_import_valid_excel(self, test_db):
        excel_data = self._make_excel({
            "模型名称": ["Claude-3"],
            "API地址": ["https://api.anthropic.com/v1"],
            "API密钥": ["sk-ant-test"],
            "Model ID": ["claude-3-opus"],
            "每日Token上限": [200000],
            "每日调用上限": [2000],
            "优先级": [10],
        })
        from gradio_app.pages.model_config import import_models_from_excel
        ok, msg = import_models_from_excel(excel_data, test_db.create_model)
        assert ok is True
        assert "1" in msg
        models = test_db.get_all_models()
        assert len(models) == 1
        assert models[0]["name"] == "Claude-3"

    def test_import_missing_columns_fails(self, test_db):
        excel_data = self._make_excel({"模型名称": ["Test"]})
        from gradio_app.pages.model_config import import_models_from_excel
        ok, msg = import_models_from_excel(excel_data, test_db.create_model)
        assert ok is False
        assert "缺少" in msg

    def test_import_multiple_models(self, test_db):
        excel_data = self._make_excel({
            "模型名称": ["Model-A", "Model-B"],
            "API地址": ["url-a", "url-b"],
            "API密钥": ["key-a", "key-b"],
        })
        from gradio_app.pages.model_config import import_models_from_excel
        ok, msg = import_models_from_excel(excel_data, test_db.create_model)
        assert ok is True
        assert len(test_db.get_all_models()) == 2
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_model_config.py -v
```

- [ ] **Step 3: 实现模型配置纯函数**

```python
# gradio_app/pages/model_config.py
import pandas as pd
import io
from datetime import date


def build_model_list_html(models, stats_lookup=None):
    """构建模型列表卡片 HTML"""
    if not models:
        return '<p style="color: #8e8e93; font-size: 14px;">暂无模型配置</p>'

    html_parts = []
    for model in models:
        is_default = model.get("is_default_model", 0) == 1
        default_badge = ('<span style="font-size: 12px; color: #16a34a; background: #e8ffea;'
                         'padding: 2px 8px; border-radius: 9999px; margin-left: 8px;">默认模型</span>'
                         if is_default else "")

        token_info = ""
        if stats_lookup and model["config_id"] in stats_lookup:
            s = stats_lookup[model["config_id"]]
            token_info = f'{s["used_tokens"]:,} / {s["daily_token_limit"]:,}'
        else:
            token_info = f'0 / {model["daily_token_limit"]:,}'

        html_parts.append(f"""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 16px;
            padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 16px; font-weight: 600; color: #222222;">{model['name']}</span>
                    <span style="font-size: 12px; color: #8e8e93; background: #f2f3f5;
                        padding: 2px 8px; border-radius: 9999px; margin-left: 8px;">优先级 {model['priority']}</span>
                    {default_badge}
                </div>
                <span style="font-size: 12px; color: #8e8e93;">
                    {model.get('model_id', '')} · Token: {token_info}
                </span>
            </div>
        </div>""")
    return "".join(html_parts)


def export_models_to_excel(get_all_models_fn):
    """导出模型配置到 Excel"""
    models = get_all_models_fn()
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
    return output.getvalue()


def import_models_from_excel(file_data, create_model_fn):
    """从 Excel 导入模型配置"""
    if file_data is None:
        return False, "请选择文件"

    try:
        df = pd.read_excel(io.BytesIO(file_data))
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
                name = str(row[column_mapping['name']])
                api_url = str(row[column_mapping['api_url']])
                api_key = str(row[column_mapping['api_key']])
                if not name or not api_url or not api_key:
                    continue
                model_id = str(row.get(column_mapping.get('model_id', 'model_id'), ''))
                daily_token_limit = int(row.get(column_mapping.get('daily_token_limit', 'daily_token_limit'), 100000))
                daily_call_limit = int(row.get(column_mapping.get('daily_call_limit', 'daily_call_limit'), 1000))
                priority = int(row.get(column_mapping.get('priority', 'priority'), 0))
                create_model_fn(name, api_url, api_key, model_id, daily_token_limit, daily_call_limit, priority)
                success_count += 1
            except Exception:
                continue

        return True, f"成功导入 {success_count} 个模型配置"
    except Exception as e:
        return False, f"导入失败：{str(e)}"
```

- [ ] **Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_model_config.py -v
```

- [ ] **Step 5: 提交**

```bash
git add tests/test_model_config.py gradio_app/pages/model_config.py
git commit -m "feat(gradio): TDD 实现模型配置纯函数（Excel 导入导出）"
```

---

### Task 8: Dashboard Gradio 页面绑定

**Files:**
- Modify: `gradio_app/pages/dashboard.py`（添加 `create_dashboard_tab` 函数）

- [ ] **Step 1: 在 dashboard.py 末尾添加 Gradio Tab 绑定函数**

在 `gradio_app/pages/dashboard.py` 文件末尾追加以下代码：

```python
import gradio as gr
from gradio_app import db


def create_dashboard_tab():
    """创建 Dashboard Tab"""
    with gr.Tab("数据概览"):
        gr.Markdown("# 数据概览", elem_classes=["page-title"])

        stats_html = gr.HTML(value=build_stats_html(db.get_daily_stats()))
        model_cards_html = gr.HTML(value=build_model_cards_html(db.get_daily_stats()))

        gr.Markdown("## 详细数据")
        detail_df = gr.Dataframe(
            value=build_detail_dataframe(db.get_daily_stats()),
            interactive=False,
        )

        refresh_btn = gr.Button("刷新", variant="secondary")

        def refresh_dashboard():
            stats = db.get_daily_stats()
            return (
                build_stats_html(stats),
                build_model_cards_html(stats),
                build_detail_dataframe(stats),
            )

        refresh_btn.click(
            fn=refresh_dashboard,
            outputs=[stats_html, model_cards_html, detail_df],
        )

    return {"stats_html": stats_html, "detail_df": detail_df}
```

- [ ] **Step 2: 运行现有测试确保未破坏**

```bash
python -m pytest tests/test_dashboard.py -v
```

Expected: 全部 PASSED

- [ ] **Step 3: 提交**

```bash
git add gradio_app/pages/dashboard.py
git commit -m "feat(gradio): 添加 Dashboard Gradio 页面绑定"
```

---

### Task 9: 调用记录 Gradio 页面绑定

**Files:**
- Modify: `gradio_app/pages/call_logs.py`

- [ ] **Step 1: 在 call_logs.py 末尾追加 Gradio Tab 绑定函数**

```python
import gradio as gr
from gradio_app import db


def create_call_logs_tab():
    """创建调用记录 Tab"""
    with gr.Tab("调用记录"):
        gr.Markdown("# 调用记录")

        logs_df = gr.Dataframe(
            value=build_logs_dataframe(db.get_call_logs()),
            interactive=False,
        )

        refresh_btn = gr.Button("刷新", variant="secondary")
        gr.Markdown("<p style='font-size: 13px; color: #8e8e93;'>显示最近 200 条记录</p>")

        def refresh_logs():
            return build_logs_dataframe(db.get_call_logs())

        refresh_btn.click(fn=refresh_logs, outputs=[logs_df])

    return {"logs_df": logs_df}
```

- [ ] **Step 2: 运行测试确保未破坏**

```bash
python -m pytest tests/test_call_logs.py -v
```

- [ ] **Step 3: 提交**

```bash
git add gradio_app/pages/call_logs.py
git commit -m "feat(gradio): 添加调用记录 Gradio 页面绑定"
```

---

### Task 10: 模型配置 Gradio 页面绑定

**Files:**
- Modify: `gradio_app/pages/model_config.py`

- [ ] **Step 1: 在 model_config.py 末尾追加 Gradio Tab 绑定函数**

```python
import gradio as gr
from gradio_app import db


def create_model_config_tab():
    """创建模型配置 Tab"""
    with gr.Tab("模型配置"):
        gr.Markdown("# 模型配置")

        # 操作栏
        with gr.Row():
            export_btn = gr.DownloadButton("导出配置", variant="secondary")
            import_file = gr.File(label="导入配置", file_types=[".xlsx", ".xls"])
            import_btn = gr.Button("导入", variant="secondary")

        import_status = gr.Textbox(visible=False)

        # 全局设置
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 全局设置")
                auto_switch = gr.Checkbox(
                    label="自动切换模型",
                    value=db.get_auto_switch_status(),
                )
                gr.Markdown("<p style='font-size: 13px; color: #8e8e93;'>开启后按优先级自动切换不可用的模型</p>")

        # 模型列表
        model_list_html = gr.HTML(value=build_model_list_html(db.get_all_models()))

        # 分隔线
        gr.Markdown("---")

        # 编辑操作区
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 编辑模型")
                model_select = gr.Dropdown(
                    label="选择模型",
                    choices=[(f"{m['name']} ({m['model_id']})", m['config_id']) for m in db.get_all_models()],
                )

                with gr.Row():
                    edit_name = gr.Textbox(label="模型名称")
                    edit_model_id = gr.Textbox(label="Model ID")
                with gr.Row():
                    edit_api_url = gr.Textbox(label="API 地址")
                    edit_api_key = gr.Textbox(label="API Key", type="password")
                with gr.Row():
                    edit_token_limit = gr.Number(label="Token 上限", value=100000)
                    edit_call_limit = gr.Number(label="调用上限", value=1000)
                    edit_priority = gr.Number(label="优先级", value=0)

                with gr.Row():
                    update_btn = gr.Button("更新", variant="primary")
                    delete_btn = gr.Button("删除")
                    copy_btn = gr.Button("复制配置", variant="secondary")

                edit_status = gr.Textbox(visible=False)

        # 分隔线
        gr.Markdown("---")

        # 添加模型
        with gr.Accordion("添加新模型", open=False):
            with gr.Row():
                add_name = gr.Textbox(label="模型名称")
                add_model_id = gr.Textbox(label="Model ID")
            with gr.Row():
                add_api_url = gr.Textbox(label="API 地址")
                add_api_key = gr.Textbox(label="API Key", type="password")
            with gr.Row():
                add_token_limit = gr.Number(label="Token 上限", value=100000)
                add_call_limit = gr.Number(label="调用上限", value=1000)
                add_priority = gr.Number(label="优先级", value=0)
            add_btn = gr.Button("添加模型", variant="primary")
            add_status = gr.Textbox(visible=False)

        # 默认模型设置（仅关闭自动切换时显示）
        default_model_col = gr.Column(visible=not db.get_auto_switch_status())
        with default_model_col:
            gr.Markdown("### 默认模型设置")
            gr.Markdown("<p style='font-size: 13px; color: #8e8e93;'>关闭自动切换时，所有请求将使用默认模型</p>")
            default_select = gr.Dropdown(
                label="选择默认模型",
                choices=[(f"{m['name']}", m['config_id']) for m in db.get_all_models()],
            )
            save_default_btn = gr.Button("保存默认模型", variant="primary")
            default_status = gr.Textbox(visible=False)

        # --- 辅助函数 ---

        def _refresh_model_list():
            models = db.get_all_models()
            html = build_model_list_html(models)
            choices = [(f"{m['name']} ({m['model_id']})", m['config_id']) for m in models]
            default_choices = [(f"{m['name']}", m['config_id']) for m in models]
            return html, gr.Dropdown(choices=choices), gr.Dropdown(choices=default_choices)

        def on_model_select(config_id):
            if not config_id:
                return [gr.Textbox()] * 2 + [gr.Textbox()] * 2 + [gr.Number()] * 3
            models = db.get_all_models()
            m = next((m for m in models if m["config_id"] == config_id), None)
            if not m:
                return [gr.Textbox()] * 2 + [gr.Textbox()] * 2 + [gr.Number()] * 3
            return (
                m["name"], m.get("model_id", ""),
                m["api_url"], m["api_key"],
                m["daily_token_limit"], m["daily_call_limit"], m["priority"],
            )

        def on_update(config_id, name, model_id, api_url, api_key, token_limit, call_limit, priority):
            if not config_id or not name or not api_url:
                return "请填写必填字段", *_refresh_model_list()
            models = db.get_all_models()
            m = next((m for m in models if m["config_id"] == config_id), None)
            is_default = m["is_default_model"] if m else 0
            db.update_model(config_id, name, api_url, api_key, model_id,
                            int(token_limit), int(call_limit), is_default, int(priority))
            return "更新成功", *_refresh_model_list()

        def on_delete(config_id):
            if not config_id:
                return "请选择模型", *_refresh_model_list()
            db.delete_model(config_id)
            return "删除成功", *_refresh_model_list()

        def on_copy(config_id):
            if not config_id:
                return "请选择模型"
            models = db.get_all_models()
            m = next((m for m in models if m["config_id"] == config_id), None)
            if not m:
                return "模型不存在"
            db.create_model(
                m["name"] + " (复制)", m["api_url"], m["api_key"],
                m.get("model_id", ""), m["daily_token_limit"],
                m["daily_call_limit"], m["priority"],
            )
            return "复制成功", *_refresh_model_list()

        def on_add(name, model_id, api_url, api_key, token_limit, call_limit, priority):
            if not name or not api_url or not api_key:
                return "请填写必填字段", *_refresh_model_list()
            db.create_model(name, api_url, api_key, model_id,
                            int(token_limit), int(call_limit), int(priority))
            return "添加成功", *_refresh_model_list()

        def on_auto_switch(enabled):
            db.set_auto_switch_status(enabled)
            return gr.Column(visible=not enabled), *_refresh_model_list()

        def on_save_default(config_id):
            if not config_id:
                return "请选择模型"
            models = db.get_all_models()
            for m in models:
                is_default = 1 if m["config_id"] == config_id else 0
                db.update_model(m["config_id"], m["name"], m["api_url"], m["api_key"],
                                m.get("model_id", ""), m["daily_token_limit"],
                                m["daily_call_limit"], is_default, m["priority"])
            return "保存成功", *_refresh_model_list()

        def on_export():
            data = export_models_to_excel(db.get_all_models)
            if data is None:
                return None
            return data

        def on_import(file_data):
            ok, msg = import_models_from_excel(file_data, db.create_model)
            return msg, *_refresh_model_list()

        # --- 事件绑定 ---

        model_select.change(
            fn=on_model_select,
            inputs=[model_select],
            outputs=[edit_name, edit_model_id, edit_api_url, edit_api_key,
                     edit_token_limit, edit_call_limit, edit_priority],
        )

        update_btn.click(
            fn=on_update,
            inputs=[model_select, edit_name, edit_model_id, edit_api_url, edit_api_key,
                    edit_token_limit, edit_call_limit, edit_priority],
            outputs=[edit_status, model_list_html, model_select, default_select],
        )

        delete_btn.click(
            fn=on_delete,
            inputs=[model_select],
            outputs=[edit_status, model_list_html, model_select, default_select],
        )

        copy_btn.click(
            fn=on_copy,
            inputs=[model_select],
            outputs=[edit_status, model_list_html, model_select, default_select],
        )

        add_btn.click(
            fn=on_add,
            inputs=[add_name, add_model_id, add_api_url, add_api_key,
                    add_token_limit, add_call_limit, add_priority],
            outputs=[add_status, model_list_html, model_select, default_select],
        )

        auto_switch.change(
            fn=on_auto_switch,
            inputs=[auto_switch],
            outputs=[default_model_col, model_list_html, model_select, default_select],
        )

        save_default_btn.click(
            fn=on_save_default,
            inputs=[default_select],
            outputs=[default_status, model_list_html, model_select, default_select],
        )

        export_btn.click(fn=on_export, outputs=[export_btn])

        import_btn.click(
            fn=on_import,
            inputs=[import_file],
            outputs=[import_status, model_list_html, model_select, default_select],
        )

    return {"model_list_html": model_list_html}
```

- [ ] **Step 2: 运行测试确保未破坏**

```bash
python -m pytest tests/test_model_config.py -v
```

- [ ] **Step 3: 提交**

```bash
git add gradio_app/pages/model_config.py
git commit -m "feat(gradio): 添加模型配置 Gradio 页面绑定"
```

---

### Task 11: API Key Gradio 页面

**Files:**
- Create: `gradio_app/pages/api_keys.py`

- [ ] **Step 1: 创建 api_keys.py**

```python
# gradio_app/pages/api_keys.py
import gradio as gr
from gradio_app import db


def build_key_list_html(keys):
    """构建 API Key 列表卡片 HTML"""
    if not keys:
        return '<p style="color: #8e8e93; font-size: 14px;">暂无 API Key</p>'

    html_parts = []
    for key in keys:
        html_parts.append(f"""
        <div style="background: white; border: 1px solid #e5e7eb; border-radius: 13px;
            padding: 16px; box-shadow: rgba(0,0,0,0.08) 0px 4px 6px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 16px; font-weight: 500; color: #222222;">{key['name']}</div>
                    <div style="font-family: monospace; font-size: 13px; color: #45515e; margin-top: 4px;">{key['api_key']}</div>
                </div>
            </div>
        </div>""")
    return "".join(html_parts)


def create_api_keys_tab():
    """创建 API Key 管理 Tab"""
    with gr.Tab("API Key"):
        gr.Markdown("# API Key 管理")

        # 生成新 Key
        with gr.Accordion("生成新 Key", open=False):
            key_name = gr.Textbox(label="Key 名称", placeholder="例如：my-app")
            generate_btn = gr.Button("生成", variant="primary")
            result_key_id = gr.Textbox(label="Key ID", visible=False)
            result_api_key = gr.Textbox(label="API Key", visible=False)
            gr.Markdown("<p style='color: #ef4444; font-size: 13px;'>请立即复制保存，此 Key 仅显示一次</p>")

        # Key 列表
        gr.Markdown("## Key 列表")
        key_list_html = gr.HTML(value=build_key_list_html(db.get_all_api_keys()))

        # 删除
        with gr.Row():
            delete_select = gr.Dropdown(
                label="选择要删除的 Key",
                choices=[(f"{k['name']} ({k['key_id']})", k['key_id']) for k in db.get_all_api_keys()],
            )
            delete_btn = gr.Button("删除")

        delete_status = gr.Textbox(visible=False)

        # --- 辅助函数 ---

        def _refresh_keys():
            keys = db.get_all_api_keys()
            html = build_key_list_html(keys)
            choices = [(f"{k['name']} ({k['key_id']})", k['key_id']) for k in keys]
            return html, gr.Dropdown(choices=choices)

        def on_generate(name):
            if not name:
                return "", "", "请输入名称", *_refresh_keys()
            result = db.create_api_key(name)
            return result["key_id"], result["api_key"], "", *_refresh_keys()

        def on_delete(key_id):
            if not key_id:
                return "请选择 Key", *_refresh_keys()
            db.delete_api_key(key_id)
            return "删除成功", *_refresh_keys()

        # --- 事件绑定 ---

        generate_btn.click(
            fn=on_generate,
            inputs=[key_name],
            outputs=[result_key_id, result_api_key, key_list_html, delete_select],
        )
        # 生成后显示结果
        result_key_id.visible = True
        result_api_key.visible = True

        delete_btn.click(
            fn=on_delete,
            inputs=[delete_select],
            outputs=[delete_status, key_list_html, delete_select],
        )

    return {"key_list_html": key_list_html}
```

- [ ] **Step 2: 提交**

```bash
git add gradio_app/pages/api_keys.py
git commit -m "feat(gradio): 实现 API Key 管理页"
```

---

### Task 12: 主入口 app.py（认证 + Tabs 整合）

**Files:**
- Create: `gradio_app/app.py`

- [ ] **Step 1: 创建 app.py**

```python
# gradio_app/app.py
import gradio as gr
from gradio_app import db
from gradio_app.theme import create_theme, CUSTOM_CSS
from gradio_app.pages.dashboard import create_dashboard_tab
from gradio_app.pages.model_config import create_model_config_tab
from gradio_app.pages.api_keys import create_api_keys_tab
from gradio_app.pages.call_logs import create_call_logs_tab


def auth_fn(username, password):
    """Gradio 认证函数"""
    if not db.has_users():
        return True  # 无用户时放行，允许首次注册
    user = db.get_user(username)
    if user and db.verify_password(password, user["password_hash"], user["salt"]):
        return True
    return False


def validate_register(username, password, confirm):
    """注册验证"""
    if not username or not password:
        return False, "请输入用户名和密码"
    if password != confirm:
        return False, "两次输入的密码不一致"
    if len(password) < 4:
        return False, "密码长度至少为4位"
    if db.create_user(username, password):
        return True, "注册成功"
    return False, "用户名已存在"


def create_app():
    """创建 Gradio 应用"""
    theme = create_theme()

    with gr.Blocks(theme=theme, css=CUSTOM_CSS, auth=auth_fn, title="Union-AI-API") as demo:
        # 注册区域（仅无用户时显示）
        show_register = not db.has_users()
        with gr.Column(visible=show_register) as register_col:
            gr.Markdown("# 首次使用，请创建管理员账号")
            reg_username = gr.Textbox(label="用户名")
            reg_password = gr.Textbox(label="密码", type="password")
            reg_confirm = gr.Textbox(label="确认密码", type="password")
            reg_btn = gr.Button("注册", variant="primary")
            reg_status = gr.Textbox(visible=False)

        # 主界面
        with gr.Column(visible=not show_register) as main_col:
            # Tabs
            create_dashboard_tab()
            create_model_config_tab()
            create_api_keys_tab()
            create_call_logs_tab()

            # 修改密码
            with gr.Accordion("修改密码", open=False):
                old_pwd = gr.Textbox(label="当前密码", type="password")
                new_pwd = gr.Textbox(label="新密码", type="password")
                confirm_pwd = gr.Textbox(label="确认新密码", type="password")
                change_pwd_btn = gr.Button("修改密码")
                pwd_status = gr.Textbox(visible=False)

        # --- 事件绑定 ---

        def on_register(username, password, confirm):
            ok, msg = validate_register(username, password, confirm)
            if ok:
                return msg, gr.Column(visible=False), gr.Column(visible=True)
            return msg, gr.Column(visible=True), gr.Column(visible=False)

        def on_change_password(old, new, confirm):
            import gradio as g
            try:
                user_info = g.context.state.user  # Gradio 认证后的用户信息
                username = user_info
            except Exception:
                return "无法获取当前用户"
            if not old or not new:
                return "请填写所有字段"
            if new != confirm:
                return "两次输入的新密码不一致"
            if len(new) < 4:
                return "新密码长度至少为4位"
            user = db.get_user(username)
            if not user or not db.verify_password(old, user["password_hash"], user["salt"]):
                return "当前密码错误"
            db.update_user_password(username, new)
            return "密码修改成功"

        reg_btn.click(
            fn=on_register,
            inputs=[reg_username, reg_password, reg_confirm],
            outputs=[reg_status, register_col, main_col],
        )

        change_pwd_btn.click(
            fn=on_change_password,
            inputs=[old_pwd, new_pwd, confirm_pwd],
            outputs=[pwd_status],
        )

        # 自动加载
        demo.load(fn=lambda: None)

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(server_port=18501)
```

- [ ] **Step 2: 提交**

```bash
git add gradio_app/app.py
git commit -m "feat(gradio): 创建主入口（认证 + Tabs + 启动）"
```

---

### Task 13: 更新部署配置

**Files:**
- Modify: `requirements.txt`
- Modify: `supervisord.conf`
- Modify: `Dockerfile.clean`

- [ ] **Step 1: 更新 requirements.txt**

将 `streamlit==1.31.1` 替换为 `gradio>=5.0,<6.0`：

```
fastapi==0.109.2
uvicorn[standard]==0.27.1
pydantic==2.6.1
sqlalchemy==2.0.25
aiosqlite==0.19.0
httpx==0.26.0
tiktoken==0.5.2
gradio>=5.0,<6.0
python-multipart==0.0.9
pandas==2.2.0
openpyxl==3.1.2
```

- [ ] **Step 2: 更新 supervisord.conf**

将 `[program:streamlit]` 段替换为：

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
command=python -u gradio_app/app.py
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

- [ ] **Step 3: 更新 Dockerfile.clean**

将 `COPY streamlit_app ./streamlit_app` 替换为 `COPY gradio_app ./gradio_app`：

```dockerfile
# 复制应用代码（不包含数据文件）
COPY app ./app
COPY gradio_app ./gradio_app
```

- [ ] **Step 4: 提交**

```bash
git add requirements.txt supervisord.conf Dockerfile.clean
git commit -m "feat(gradio): 更新部署配置（requirements + supervisord + Dockerfile）"
```

---

### Task 14: 全量测试 + 本地验证

- [ ] **Step 1: 运行全部测试**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 2: 本地启动**

```bash
python gradio_app/app.py
```

Expected: 访问 http://localhost:18501

- [ ] **Step 3: 手动验证清单**

- [ ] 注册/登录流程
- [ ] Dashboard 统计卡片 + 详细表格
- [ ] 模型配置 CRUD + 导入导出
- [ ] API Key 生成/删除
- [ ] 调用记录表格
- [ ] 修改密码
- [ ] MiniMax 主题样式

- [ ] **Step 4: 修复问题并提交**

```bash
git add -u
git commit -m "fix(gradio): 修复本地验证中发现的问题"
```

---

## 自审清单

**1. 规格覆盖：**
- [x] 认证系统 → Task 3 (测试) + Task 12 (app.py)
- [x] Dashboard → Task 5 (TDD) + Task 8 (绑定)
- [x] 模型配置 → Task 7 (TDD) + Task 10 (绑定)
- [x] API Key → Task 11 (完整实现)
- [x] 调用记录 → Task 6 (TDD) + Task 9 (绑定)
- [x] MiniMax 主题 → Task 4
- [x] 部署变更 → Task 13
- [x] UI 组件样式规格 → Task 4 (CSS) + Task 5/6/7 (HTML 构建)

**2. 占位符扫描：** 无 TBD、TODO 或空实现。

**3. 类型一致性：** 所有 db.py 函数调用与原始 streamlit_app/db.py 签名匹配。纯函数参数与测试代码一致。
