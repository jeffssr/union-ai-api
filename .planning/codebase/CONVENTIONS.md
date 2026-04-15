# Coding Conventions

**Analysis Date:** 2026-04-15

## Language

- **Primary:** Python 3.11（基于 Dockerfile `FROM python:3.11-slim`）
- **注释语言:** 中文注释为主，专有术语保留英文（如 FastAPI、API Key、Token）
- **字符串:** 所有面向用户的文本使用中文

## Naming Patterns

**文件:**
- 模块使用 `snake_case`：`chat_final.py`、`llm_service.py`、`responses_api.py`
- 包使用 `snake_case` 目录：`app/router/`、`app/services/`、`streamlit_app/`
- 测试文件前缀 `test_`：`test_auth.py`、`test_db.py`、`test_call_logs.py`（仅存在于 worktree 分支）

**函数:**
- 使用 `snake_case`：`get_db_connection()`、`forward_to_model()`、`create_call_log()`
- 工具/辅助函数使用动词前缀：`get_*`、`create_*`、`update_*`、`delete_*`、`convert_*`
- 布尔判断函数：`is_rate_limit_error()`、`has_users()`、`verify_password()`
- 类方法：`snake_case`，同函数命名

**变量:**
- 使用 `snake_case`：`api_key`、`config_id`、`model_name`
- 常量使用 `UPPER_SNAKE_CASE` 模块级定义：`BEIJING_TZ`、`MAX_RETRIES`、`MODEL_SWITCH_DELAY`、`RATE_LIMIT_STATUS_CODES`、`DATABASE_PATH`
- 返回值字典键使用 `snake_case`：`{"status": "success", "response": ...}`

**类型:**
- Pydantic Model 使用 `PascalCase`：`Message`、`ChatCompletionRequest`、`Usage`、`Choice`
- 测试类使用 `PascalCase` + `Test` 前缀：`TestUserAuth`、`TestModels`、`TestApiKeys`

**参数:**
- 函数参数使用 `snake_case`
- 类型注解使用标准库 `typing`：`Optional[str]`、`List[dict]`、`Dict[str, Any]`

## Code Style

**Formatting:**
- 无 formatter 工具配置（无 black、ruff、autopep8 配置文件）
- 缩进：4 空格
- 行宽：无严格限制，部分行超过 120 字符
- 字符串：双引号 `"` 为主，单引号 `'` 在 SQL 和部分 dict 中使用
- 尾部逗号：不定

**Linting:**
- 无 linter 配置（无 flake8、pylint、ruff、mypy 配置文件）
- 无 pre-commit hooks 配置

**类型注解:**
- 函数签名使用类型注解（部分文件）：
  ```python
  def get_model_by_config_id(config_id: str) -> Optional[dict]:
  def update_daily_usage(config_id: str, tokens: int, calls: int = 1):
  ```
- Pydantic models 完整类型注解（`app/schemas.py`）
- 部分函数缺少返回类型注解（如 `forward_stream`、`forward_to_model`）

## Import Organization

**顺序（实际观察）：**
1. 标准库：`import uuid`、`import json`、`import logging`
2. 第三方库：`import httpx`、`from fastapi import ...`、`from pydantic import ...`
3. 项目内部：`from app.database import ...`、`from streamlit_app.db import ...`

**模式:**
```python
# 标准库
import uuid
import json
import logging

# 第三方
import httpx
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse

# 项目内部
from app.database import get_model_by_priority, get_api_key, ...
```

**注意事项:**
- 某些文件在函数内部延迟导入：`import uuid`、`import secrets`（见 `app/database.py` 第 231、293 行）
- 无 `__all__` 导出控制

## Error Handling

**模式:**

1. **HTTP 错误**（路由层）：使用 `HTTPException` 和 `JSONResponse` 返回错误
   ```python
   raise HTTPException(status_code=401, detail="Missing authorization header")
   raise HTTPException(status_code=400, detail="Invalid JSON body")
   return JSONResponse(status_code=502, content={"error": {"message": ..., "type": "api_error"}})
   ```

2. **转发层结果模式**：使用 status 字典代替异常
   ```python
   # 成功
   return {"status": "success", "response": response_data}
   # 失败
   return {"status": "error", "status_code": 429, "error_message": "Token limit exceeded"}
   ```

3. **异常捕获**：粗粒度 `except Exception` 为主
   ```python
   except httpx.TimeoutException:
       return {"status": "error", "status_code": 504, "error_message": "Request timeout"}
   except Exception as e:
       return {"status": "error", "status_code": 502, "error_message": str(e)}
   ```

4. **数据库操作**：使用 context manager 处理连接
   ```python
   with get_db() as conn:
       cursor = conn.cursor()
       cursor.execute(...)
   # get_db() 自动 commit/rollback/close
   ```

5. **裸 except**：`streamlit_app/home.py` 中存在 `except:` 裸捕获（第 142 行）

## Logging

**框架:** Python 标准 `logging` 模块

**初始化（`app/main.py`）：**
```python
logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("app").setLevel(logging.INFO)
```

**获取 logger：**
```python
logger = logging.getLogger(__name__)
```

**日志级别使用:**
- `logger.info()`：请求接收、转发目标、响应状态、模型切换
- `logger.warning()`：限额预警、限流重试、不支持的 tools
- `logger.error()`：请求失败、异常、超时
- `logger.debug()`：仅在 `app/services/llm_service.py` 中使用（payload 详情）

**日志消息格式:**
- 中文描述 + 变量值：`f"收到请求 - model: {model}, stream: {stream}"`
- 错误截断：`error_text[:500]`、`str(e)[:1000]`

**注意:** `streamlit_app/` 无日志系统，使用 Streamlit 自带的 `st.error()`/`st.success()`/`st.warning()` 代替

## Comments

**风格:**
- 中文行内注释，以 `#` 开头：`# 根据环境选择数据库路径`
- 模块级 docstring 使用三引号：`"""完全绕过 Pydantic 的 chat completions 实现"""`
- 函数 docstring 使用三引号描述功能，部分包含参数说明
- 中文注释为主

**Docstring 示例:**
```python
async def exponential_backoff_retry(
    operation,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_RETRY_DELAY,
    operation_name: str = "operation"
):
    """
    指数退避重试机制
    遇到速率限制错误时，等待一段时间后重试
    """
```

**无 Docstring 的函数:** 部分辅助函数无 docstring（如 `get_beijing_time()`、`convert_message_content()`）

## Function Design

**大小:**
- 函数普遍较长：`chat_completions()` 约 90 行、`forward_stream()` 约 130 行、`responses_api()` 约 180 行
- 存在深层嵌套：`forward_stream()` 内 `generate()` 异步生成器嵌套 4-5 层

**参数:**
- 路由处理函数：`request: Request, authorization: Optional[str] = Header(None)`
- 转发函数：`(model_config: dict, request_body: dict, request_id: str, api_key_record: dict)`
- 数据库函数：使用 `dict` 传参（`model_data: dict`、`log_data: dict`）或展开参数列表

**返回值:**
- 路由函数返回 `JSONResponse` 或 `StreamingResponse`
- 转发函数返回 status 字典：`{"status": "success/error", ...}`
- 数据库查询函数返回 `Optional[dict]`、`List[dict]`、`dict`

## Module Design

**Exports:**
- 无 `__all__` 定义
- `__init__.py` 文件为空（`app/router/__init__.py`、`app/services/__init__.py`）
- 直接通过模块路径导入：`from app.database import get_model_by_priority, ...`

**Barrel Files:** 未使用

**模块职责:**
- `app/router/` — API 路由处理，每个文件一个 `APIRouter()` 实例
- `app/services/` — 业务逻辑（token 计数、API 调用）
- `app/database.py` — 数据访问层，纯函数式（无 ORM）
- `app/schemas.py` — Pydantic 请求/响应模型定义
- `streamlit_app/` — 管理后台 UI（独立应用，直接操作数据库）

## API Design Conventions

**路由注册:**
```python
router = APIRouter()
# 在 app/main.py 中注册
app.include_router(chat_router)
```

**端点路径:**
- OpenAI 兼容路径：`/v1/chat/completions`、`/v1/responses`
- 兼容路径（无前缀）：`/responses`
- 健康检查：`/health`

**认证:**
- Bearer Token 方式：`authorization: Optional[str] = Header(None)`
- 手动解析：`api_key = authorization.replace("Bearer ", "").strip()`

**响应格式:**
- 成功：`JSONResponse(content=data)`
- 错误：`{"error": {"message": "...", "type": "api_error"}}`

## Database Conventions

**连接管理:**
```python
@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**查询模式:**
- 使用 `sqlite3.Row` 的 `row_factory` 实现行字典化
- 所有查询使用参数化 `?` 占位符（防止 SQL 注入）
- 返回 `[dict(row) for row in rows]` 统一格式
- Schema 迁移使用 `PRAGMA table_info` + `ALTER TABLE` 增量方式

## Duplicated Patterns

**注意：** `chat_final.py` 和 `responses_api.py` 存在大量重复代码：
- 全局 HTTP 客户端管理（`_global_client`、`get_global_client()`）
- 速率限制常量和判断函数（`RATE_LIMIT_STATUS_CODES`、`is_rate_limit_error()`）
- 转发函数结构（`forward_stream` / `forward_to_model` / `forward_stream_responses` / `forward_to_model_responses`）
- 限流检查逻辑
- 错误处理和日志记录模式

---

*Convention analysis: 2026-04-15*
