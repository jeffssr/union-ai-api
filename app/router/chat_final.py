"""
完全绕过 Pydantic 的 chat completions 实现
支持流式和非流式输出
"""
import uuid
import json
import logging
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from app.database import get_model_by_priority, get_api_key, get_daily_usage, create_call_log, get_default_model, get_auto_switch_status, update_daily_usage, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

BEIJING_TZ = timezone(timedelta(hours=8))

# 全局HTTP客户端连接池
_global_client: Optional[httpx.AsyncClient] = None

# 速率限制配置
MODEL_SWITCH_DELAY = 0.5  # 模型切换间隔（秒）
MAX_RETRIES = 3  # 最大重试次数
BASE_RETRY_DELAY = 1.0  # 基础重试延迟（秒）
RATE_LIMIT_STATUS_CODES = {429}  # 速率限制HTTP状态码
RATE_LIMIT_ERROR_CODES = {"limit_burst_rate", "rate_limit", "too_many_requests"}  # 限流错误码


def get_global_client() -> httpx.AsyncClient:
    """获取全局HTTP客户端（连接池复用）"""
    global _global_client
    if _global_client is None or _global_client.is_closed:
        _global_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    return _global_client


async def close_global_client():
    """关闭全局HTTP客户端"""
    global _global_client
    if _global_client and not _global_client.is_closed:
        await _global_client.aclose()
        _global_client = None


def is_rate_limit_error(error_text: str, status_code: int) -> bool:
    """检查是否为速率限制错误"""
    if status_code in RATE_LIMIT_STATUS_CODES:
        return True
    error_lower = error_text.lower()
    for code in RATE_LIMIT_ERROR_CODES:
        if code in error_lower:
            return True
    return False


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
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = await operation()
            # 检查结果是否包含速率限制错误
            if isinstance(result, dict) and result.get("status") == "error":
                error_message = result.get("error_message", "")
                status_code = result.get("status_code", 0)
                if is_rate_limit_error(error_message, status_code) and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # 指数退避: 1, 2, 4秒
                    logger.warning(f"{operation_name} 遇到速率限制，{delay}秒后重试 (第{attempt + 1}/{max_retries}次)")
                    await asyncio.sleep(delay)
                    continue
            return result
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"{operation_name} 失败，{delay}秒后重试 (第{attempt + 1}/{max_retries}次): {e}")
                await asyncio.sleep(delay)
            else:
                break
    
    if last_exception:
        raise last_exception
    return {"status": "error", "error_message": "Max retries exceeded"}

def get_beijing_time():
    return datetime.now(BEIJING_TZ)

def convert_message_content(content) -> str:
    """
    将消息内容转换为字符串
    参考 OpenAI 消息格式规范
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif item.get('type') == 'image_url':
                    url = item.get('image_url', {})
                    if isinstance(url, dict):
                        url_str = url.get('url', '')
                    else:
                        url_str = str(url)
                    parts.append(f"[Image: {url_str}]")
        return '\n'.join(parts) if parts else ''
    else:
        return str(content)

def convert_messages(messages: list) -> list:
    """
    转换消息格式
    将 OpenAI 多模态格式转换为目标 API 支持的格式
    只转换纯文本内容，保留 tool_calls 等所有其他字段
    """
    converted = []
    for msg in messages:
        if isinstance(msg, dict):
            new_msg = {}
            role = msg.get('role', 'user')
            new_msg['role'] = role

            if role == 'tool':
                new_msg['content'] = msg.get('content', '')
                if 'tool_call_id' in msg:
                    new_msg['tool_call_id'] = msg['tool_call_id']
            elif role == 'assistant':
                if 'content' in msg:
                    new_msg['content'] = convert_message_content(msg['content'])
                if 'tool_calls' in msg:
                    new_msg['tool_calls'] = msg['tool_calls']
                if 'reasoning_content' in msg:
                    new_msg['reasoning_content'] = msg['reasoning_content']
            else:
                new_msg['content'] = convert_message_content(msg.get('content', ''))

            for key in msg:
                if key not in ['role', 'content', 'tool_calls', 'tool_call_id', 'reasoning_content']:
                    new_msg[key] = msg[key]

            converted.append(new_msg)
        else:
            converted.append(msg)
    return converted

@router.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    """完全透传的 chat completions 端点 - 支持流式和非流式"""

    request_id = str(uuid.uuid4())

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    api_key = authorization.replace("Bearer ", "").strip()
    api_key_record = get_api_key(api_key)
    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        request_body = await request.json()
    except Exception as e:
        logger.error(f"解析请求失败：{e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logger.info(f"收到请求 - model: {request_body.get('model', 'N/A')}, stream: {request_body.get('stream', False)}")

    auto_switch_enabled = get_auto_switch_status()

    logger.info(f"自动切换状态：{auto_switch_enabled}")

    if not auto_switch_enabled:
        default_model = get_default_model()
        if not default_model:
            logger.error("没有配置默认模型")
            raise HTTPException(status_code=500, detail="No default model configured")

        logger.info(f"使用默认模型：{default_model['name']}")

        if request_body.get('stream', False):
            return await forward_stream(default_model, request_body, request_id, api_key_record)
        else:
            result = await forward_to_model(default_model, request_body, request_id, api_key_record)

            if result["status"] == "success":
                return JSONResponse(content=result["response"])
            else:
                logger.error(f"默认模型请求失败：{result.get('error_message')}")
                return JSONResponse(
                    status_code=result.get("status_code", 502),
                    content={"error": {"message": result.get("error_message", "Unknown error"), "type": "api_error"}}
                )
    else:
        models = get_model_by_priority()
        if not models:
            logger.error("自动切换模式下没有配置模型")
            raise HTTPException(status_code=500, detail="No models configured")

        logger.info(f"自动切换模式，尝试 {len(models)} 个模型")

        last_error = None
        for idx, model_config in enumerate(models):
            logger.info(f"尝试模型 #{idx + 1}: {model_config['name']}")

            if request_body.get('stream', False):
                result = await forward_stream(model_config, request_body, request_id, api_key_record)
                if result["status"] == "success":
                    logger.info(f"模型 {model_config['name']} 成功")
                    return result["response"]
                else:
                    logger.warning(f"模型 {model_config['name']} 失败：{result.get('error_message')}")
                    last_error = result.get('error_message')
                    # 如果不是最后一个模型，添加延迟避免突发请求
                    if idx < len(models) - 1:
                        logger.info(f"等待 {MODEL_SWITCH_DELAY} 秒后尝试下一个模型...")
                        await asyncio.sleep(MODEL_SWITCH_DELAY)
                    continue
            else:
                result = await forward_to_model(model_config, request_body, request_id, api_key_record)
                if result["status"] == "success":
                    logger.info(f"模型 {model_config['name']} 成功")
                    return JSONResponse(content=result["response"])
                else:
                    logger.warning(f"模型 {model_config['name']} 失败：{result.get('error_message')}")
                    last_error = result.get('error_message')
                    # 如果不是最后一个模型，添加延迟避免突发请求
                    if idx < len(models) - 1:
                        logger.info(f"等待 {MODEL_SWITCH_DELAY} 秒后尝试下一个模型...")
                        await asyncio.sleep(MODEL_SWITCH_DELAY)
                    continue

        logger.error(f"所有模型都失败：{last_error}")
        return JSONResponse(
            status_code=502,
            content={"error": {"message": f"All models failed: {last_error}", "type": "api_error"}}
        )

async def forward_stream(model_config: dict, request_body: dict, request_id: str, api_key_record: dict):
    """转发流式请求到第三方 API"""

    config_id = model_config['config_id']
    api_key = model_config['api_key']
    model_name = model_config['name']
    model_id = model_config.get('model_id', '')

    usage = get_daily_usage(config_id)
    daily_token_limit = model_config.get('daily_token_limit', 100000)
    daily_call_limit = model_config.get('daily_call_limit', 1000)

    logger.info(f"检查限制 - model: {model_name}, calls: {usage['total_calls']}/{daily_call_limit}, tokens: {usage['total_tokens']}/{daily_token_limit}")

    # 使用 >= 意味着调用次数达到上限时就不能再调用了
    if usage['total_calls'] >= daily_call_limit:
        logger.warning(f"模型 {model_name} 调用次数已达上限 ({usage['total_calls']}/{daily_call_limit})，跳过")
        return {"status": "error", "status_code": 429, "error_message": "Call limit exceeded"}

    if usage['total_tokens'] >= daily_token_limit:
        logger.warning(f"模型 {model_name} Token 限额已达上限 ({usage['total_tokens']}/{daily_token_limit})，跳过")
        return {"status": "error", "status_code": 429, "error_message": "Token limit exceeded"}

    base_url = model_config['api_url'].rstrip('/')
    if not base_url.endswith('/chat/completions'):
        api_url = f"{base_url}/chat/completions"
    else:
        api_url = base_url

    target_model = model_id if model_id else model_name
    request_body['model'] = target_model

    request_body['messages'] = convert_messages(request_body.get('messages', []))

    logger.info(f"流式转发到：{api_url}, model: {target_model}")

    try:
        client = get_global_client()
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body
        )

        logger.info(f"流式响应状态：{response.status_code}")

        if response.status_code == 200:
                # 用于记录实际的 tokens
                actual_input_tokens = 0
                actual_output_tokens = 0

                async def generate():
                    nonlocal actual_input_tokens, actual_output_tokens
                    logger.info(f"generate() 函数开始")
                    try:
                        async for line in response.aiter_lines():
                            if line:
                                if '"model"' in line:
                                    line = line.replace(f'"{target_model}"', f'"{model_name}"')
                                # 尝试解析每个 chunk 的 usage 信息
                                try:
                                    if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                                        chunk_data = json.loads(line[6:])  # 移除 'data: ' 前缀
                                        # usage 可能在顶层或 choices[0] 中
                                        usage = None
                                        if 'usage' in chunk_data:
                                            usage = chunk_data['usage']
                                        elif 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                            usage = chunk_data['choices'][0].get('usage')
                                        
                                        if usage:
                                            actual_input_tokens = usage.get('prompt_tokens', 0)
                                            actual_output_tokens = usage.get('completion_tokens', 0)
                                            logger.info(f"解析到 tokens: input={actual_input_tokens}, output={actual_output_tokens}")
                                except Exception as e:
                                    # 大部分 chunk 没有 usage，这是正常的
                                    pass
                                yield f"{line}\n\n"
                        yield f"data: [DONE]\n\n"
                        
                        logger.info(f"流式完成，actual_input_tokens={actual_input_tokens}, actual_output_tokens={actual_output_tokens}")
                        
                        # 流式完成后记录实际 tokens 和调用次数
                        if actual_input_tokens > 0 or actual_output_tokens > 0:
                            logger.info(f"更新 usage: tokens={actual_input_tokens + actual_output_tokens}, calls=1")
                            update_daily_usage(config_id, actual_input_tokens + actual_output_tokens, 1)
                            # 更新调用日志
                            with get_db() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE call_logs 
                                    SET input_tokens = ?, output_tokens = ?
                                    WHERE request_id = ?
                                """, (actual_input_tokens, actual_output_tokens, request_id))
                                logger.info(f"调用日志已更新")
                        else:
                            # 没有 tokens 也要增加调用次数
                            logger.info(f"更新调用次数：calls=1")
                            update_daily_usage(config_id, 0, 1)
                    except Exception as e:
                        logger.error(f"流式读取错误：{e}")
                        yield f"data: [DONE]\n\n"

                # 先创建调用日志（tokens 初始为 0）
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_name,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": "success"
                })

                return {
                    "status": "success",
                    "response": StreamingResponse(
                        generate(),
                        media_type="text/event-stream",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "X-Request-ID": request_id,
                        }
                    )
                }
        else:
            error_text = response.text
            logger.error(f"流式 API 错误：{error_text[:500]}")

            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": model_name,
                "status": "failed",
                "error_message": error_text[:1000],
                "error_code": str(response.status_code)
            })

            return {
                "status": "error",
                "status_code": response.status_code,
                "error_message": error_text[:1000]
            }

    except httpx.TimeoutException:
        logger.error("流式请求超时")

        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": "Stream timeout (60s)",
            "error_code": "TIMEOUT"
        })

        return {"status": "error", "status_code": 504, "error_message": "Stream timeout"}
    except Exception as e:
        logger.error(f"流式请求异常：{e}")

        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": str(e)[:1000],
            "error_code": "EXCEPTION"
        })

        return {"status": "error", "status_code": 502, "error_message": str(e)}

async def forward_to_model(model_config: dict, request_body: dict, request_id: str, api_key_record: dict) -> dict:
    """转发请求到第三方 API - 完全透传"""
    
    config_id = model_config['config_id']
    api_key = model_config['api_key']
    model_name = model_config['name']
    model_id = model_config.get('model_id', '')

    usage = get_daily_usage(config_id)
    daily_token_limit = model_config.get('daily_token_limit', 100000)
    daily_call_limit = model_config.get('daily_call_limit', 1000)

    if usage['total_tokens'] >= daily_token_limit:
        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": f"Token limit exceeded ({usage['total_tokens']}/{daily_token_limit})",
            "error_code": "TOKEN_LIMIT"
        })

        return {"status": "error", "status_code": 429, "error_message": "Token limit exceeded"}

    if usage['total_calls'] >= daily_call_limit:
        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": f"Call limit exceeded ({usage['total_calls']}/{daily_call_limit})",
            "error_code": "CALL_LIMIT"
        })

        return {"status": "error", "status_code": 429, "error_message": "Call limit exceeded"}

    base_url = model_config['api_url'].rstrip('/')
    if not base_url.endswith('/chat/completions'):
        api_url = f"{base_url}/chat/completions"
    else:
        api_url = base_url

    target_model = model_id if model_id else model_name
    request_body['model'] = target_model

    request_body['messages'] = convert_messages(request_body.get('messages', []))

    logger.info(f"转发到：{api_url}, model: {target_model}")

    try:
        client = get_global_client()
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=request_body
        )

        logger.info(f"响应状态：{response.status_code}")

        if response.status_code == 200:
            response_data = response.json()

            response_data['model'] = model_name

            if 'usage' in response_data:
                input_tokens = response_data['usage'].get('prompt_tokens', 0)
                output_tokens = response_data['usage'].get('completion_tokens', 0)
                total_tokens = input_tokens + output_tokens

                logger.info(f"更新 usage: tokens={total_tokens}, calls=1")
                update_daily_usage(config_id, total_tokens, 1)

                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "status": "success"
                })
            else:
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_name,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "status": "success"
                })

            return {
                "status": "success",
                "response": response_data
            }
        else:
            error_text = response.text
            logger.error(f"API 错误：{error_text[:500]}")

            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": model_name,
                "status": "failed",
                "error_message": error_text[:1000],
                "error_code": str(response.status_code)
            })

            return {
                "status": "error",
                "status_code": response.status_code,
                "error_message": error_text[:1000]
            }
                
    except httpx.TimeoutException:
        logger.error("请求超时")

        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": "Request timeout (30s)",
            "error_code": "TIMEOUT"
        })

        return {"status": "error", "status_code": 504, "error_message": "Request timeout (30s)"}
    except Exception as e:
        logger.error(f"请求异常：{e}")

        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": str(e)[:1000],
            "error_code": "EXCEPTION"
        })

        return {"status": "error", "status_code": 502, "error_message": str(e)}
