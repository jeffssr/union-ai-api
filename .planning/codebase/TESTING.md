# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- **主分支（main）：无测试。** `tests/` 目录不存在，`requirements.txt` 中未包含 `pytest` 或任何测试依赖。
- **Worktree 分支（feature+gradio-migration）：使用 pytest** — 存在完整的测试套件，位于 `.claude/worktrees/feature+gradio-migration/tests/`

**注意：** 以下内容主要基于 worktree 分支的测试代码分析，该分支正在将管理后台从 Streamlit 迁移到 Gradio，并同步添加了测试。这些模式应作为项目测试的未来标准参考。

**测试依赖:**
- `pytest`（未在 `requirements.txt` 中声明，推测通过 `pip install pytest` 手动安装）
- `pandas`（已在 `requirements.txt` 中，用于测试数据处理函数）

**配置文件:** 无 `pytest.ini`、`conftest.py`（主分支）、`pyproject.toml` 等 pytest 配置文件

**Run Commands（worktree 分支）:**
```bash
pytest                           # 运行所有测试
pytest tests/test_db.py          # 运行特定文件
pytest -v                        # 详细输出
pytest -x                        # 遇到第一个失败停止
```

**Coverage:**
- 未配置覆盖率工具（无 `.coveragerc`、`pytest-cov` 依赖）
- `.gitignore` 中包含 `.coverage` 和 `htmlcov/` 条目，说明曾使用或计划使用 coverage

## Test File Organization

**Location:**
- 独立 `tests/` 目录，与源代码分离
- 测试文件放置在项目根目录的 `tests/` 下

**Naming:**
- 文件：`test_` 前缀 + 模块名：`test_db.py`、`test_auth.py`、`test_dashboard.py`、`test_call_logs.py`、`test_model_config.py`
- 类：`Test` 前缀 + 功能名 PascalCase：`TestUserAuth`、`TestModels`、`TestBuildStatsHtml`
- 方法：`test_` 前缀 + 描述：`test_has_users_initially_false`、`test_empty_logs`

**Structure（worktree 分支）:**
```
tests/
├── __init__.py
├── conftest.py           # 共享 fixture
├── test_auth.py          # 认证逻辑测试
├── test_call_logs.py     # 调用记录 UI 数据测试
├── test_dashboard.py     # 仪表盘 UI 数据测试
├── test_db.py            # 数据库操作测试
└── test_model_config.py  # 模型配置导入导出测试
```

## Test Structure

**Suite Organization（类方式组织）：**
```python
class TestUserAuth:
    def test_has_users_initially_false(self, test_db):
        assert test_db.has_users() is False

    def test_create_user_success(self, test_db):
        assert test_db.create_user("admin", "password123") is True

    def test_create_user_duplicate_fails(self, test_db):
        test_db.create_user("admin", "password123")
        assert test_db.create_user("admin", "another") is False
```

**测试组织模式:**
- 使用类分组相关测试（`TestUserAuth`、`TestModels`、`TestApiKeys` 等）
- 每个测试方法测试一个具体行为
- 测试方法名使用描述性命名：`test_<情境>_<预期结果>`

**Fixture 模式:**

`conftest.py` 提供全局 `autouse=True` fixture：
```python
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

**关键 fixture 特点:**
- `autouse=True`：自动应用于所有测试，无需显式声明
- `tmp_path`：使用 pytest 内置临时目录
- `monkeypatch`：替换模块级常量 `DATABASE_PATH`，确保测试隔离
- `yield db_module`：返回整个 db 模块作为测试中操作数据库的接口
- 每个测试用例获得独立的临时数据库

## Mocking

**Framework:** 使用 pytest 的 `monkeypatch`（轻量级 mock）

**Patterns:**
```python
# 通过 monkeypatch 替换模块级变量
monkeypatch.setattr(db_module, "DATABASE_PATH", test_db_path)
```

**What to Mock:**
- 数据库路径（已实现）
- 外部 API 调用（尚未在现有测试中涉及）

**What NOT to Mock:**
- 数据库操作本身 — 使用真实 SQLite 内存/临时文件
- 业务逻辑验证函数

**注意:** 主分支的 API 转发逻辑（`chat_final.py`、`responses_api.py`）完全无测试，需要 mock `httpx.AsyncClient` 来测试。

## Fixtures and Factories

**Test Data — 工厂函数模式:**
```python
# test_dashboard.py 中的样本数据工厂
def sample_stats():
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
        ...
    ]
```

```python
# test_call_logs.py 中的辅助函数
def insert_sample_logs(test_db):
    """插入测试用调用记录"""
    key_result = test_db.create_api_key("test-app")
    config_id = test_db.create_model("GPT-4", "url", "key", "gpt-4", 100000, 1000, 5)
    conn = sqlite3.connect(test_db.DATABASE_PATH)
    # ... 直接插入测试数据
```

**Location:**
- 测试数据定义在测试文件内
- 无独立的 `fixtures/` 目录或 `factories.py` 文件
- 样本数据使用普通函数返回，非 pytest fixture

**辅助函数特点:**
- `test_auth.py` 将业务逻辑抽为独立函数再测试（`auth_fn`、`validate_register`）
- `test_call_logs.py` 使用直接 SQL 插入绕过应用层创建日志记录

## Coverage

**Requirements:** 无强制覆盖率要求

**覆盖范围分析:**

| 模块 | 测试状态 | 测试文件 |
|------|----------|----------|
| `streamlit_app/db.py` 数据库操作 | 已测试（worktree） | `tests/test_db.py` |
| 用户认证逻辑 | 已测试（worktree） | `tests/test_auth.py` |
| Dashboard 数据展示 | 已测试（worktree） | `tests/test_dashboard.py` |
| 调用记录展示 | 已测试（worktree） | `tests/test_call_logs.py` |
| 模型配置导入导出 | 已测试（worktree） | `tests/test_model_config.py` |
| `app/router/chat_final.py` | **未测试** | — |
| `app/router/responses_api.py` | **未测试** | — |
| `app/services/llm_service.py` | **未测试** | — |
| `app/main.py` 应用启动 | **未测试** | — |
| `app/schemas.py` 数据模型 | **未测试** | — |
| `app/database.py` API 数据层 | **未测试** | — |
| `launcher.py` GUI 启动器 | **未测试** | — |

## Test Types

**Unit Tests（已有）:**
- 范围：数据库 CRUD 操作、认证验证、数据转换
- 方式：独立函数/类方法测试，使用临时数据库
- 不涉及 HTTP 请求

**Integration Tests:**
- **未实现。** API 端点转发逻辑完全无测试
- 需要 FastAPI `TestClient`（`httpx.AsyncClient` 配合 `ASGITransport`）来测试完整请求流程
- 需要外部 API mock（`httpx` 的 `respx` 或自定义 mock）

**E2E Tests:**
- 未使用

## Common Patterns

**Assertion 模式:**
```python
# 布尔断言
assert test_db.has_users() is False
assert result is True

# 等值断言
assert len(models) == 1
assert models[0]["name"] == "GPT-4"

# 包含断言（错误消息检查）
ok, msg = validate_register("", "pass", "pass", test_db)
assert ok is False
assert "用户名" in msg

# 内容检查（HTML 输出测试）
html = build_stats_html(sample_stats())
assert "stat-card" in html
assert "250,000" in html

# 空结果断言
assert test_db.get_all_models() == []
assert df.empty
```

**数据验证测试模式:**
```python
def test_correct_columns(self, test_db):
    insert_sample_logs(test_db)
    from gradio_app.pages.call_logs import build_logs_dataframe
    df = build_logs_dataframe(test_db.get_call_logs())
    expected = ["请求 ID", "API 名称", "调用时间", "模型", ...]
    assert list(df.columns) == expected
```

**排序/顺序测试模式:**
```python
def test_models_ordered_by_priority(self, test_db):
    test_db.create_model("Low", "url1", "key1", "", 100, 10, 1)
    test_db.create_model("High", "url2", "key2", "", 100, 10, 10)
    test_db.create_model("Med", "url3", "key3", "", 100, 10, 5)
    models = test_db.get_all_models()
    assert models[0]["name"] == "High"
    assert models[1]["name"] == "Med"
    assert models[2]["name"] == "Low"
```

**条件测试模式:**
```python
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
```

**Excel 导入导出测试模式:**
```python
def _make_excel(self, data_dict):
    df = pd.DataFrame(data_dict)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='模型配置')
    output.seek(0)
    return output.getvalue()
```

## How to Add New Tests

**新数据库函数测试:**
1. 在 `tests/test_db.py` 中添加测试类或方法
2. 使用 `test_db` fixture（自动提供临时数据库）
3. 通过 `test_db.<function_name>()` 调用被测函数

**新 API 端点测试（需要新增模式）:**
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
```

**需要添加到 requirements.txt 的测试依赖:**
```
pytest>=7.0
pytest-asyncio>=0.21
respx>=0.20  # httpx mock（可选）
```

## Test Coverage Gaps

**关键缺失（优先级高）：**

1. **`app/router/chat_final.py`（592 行）** — 核心业务逻辑
   - 流式/非流式转发
   - 模型自动切换
   - 限流检查
   - 需 mock：`httpx.AsyncClient`、`app.database` 函数

2. **`app/router/responses_api.py`（1036 行）** — Responses API 兼容层
   - 请求格式转换（`convert_input_to_messages`、`convert_tools_for_chat_completions`）
   - 响应格式转换（`convert_chat_completion_to_response`、`convert_chat_completion_stream_chunk`）
   - 部分转换函数可做纯单元测试（无外部依赖）

3. **`app/database.py`（334 行）** — API 后端数据层
   - 与 `streamlit_app/db.py` 功能相同但连接管理模式不同（`get_db()` context manager vs 手动 open/close）
   - 所有函数均未测试

4. **`app/schemas.py`（60 行）** — Pydantic 模型
   - 可通过简单实例化测试验证字段默认值和验证规则

---

*Testing analysis: 2026-04-15*
