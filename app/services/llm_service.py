import httpx
import tiktoken
import logging
from typing import Optional, List
from app.database import get_model_by_priority, get_model_by_config_id, update_daily_usage

logger = logging.getLogger(__name__)

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(enc.encode(text))

def count_messages_tokens(messages: List[dict]) -> int:
    total = 0
    for msg in messages:
        total += count_tokens(msg.get("content", ""))
        total += count_tokens(msg.get("role", ""))
        total += 4
    total += 2
    return total

def count_response_tokens(text: str) -> int:
    return count_tokens(text)

async def call_model(
    api_url: str,
    api_key: str,
    payload: dict,
    timeout: float = 30.0
):
    """
    调用模型 API
    
    Args:
        api_url: 完整的 API 地址（包含 /chat/completions）
        api_key: API Key
        payload: 请求体
        timeout: 超时时间（秒），默认 30 秒
    
    Returns:
        response 对象或 None
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    logger.info(f"调用 API: {api_url}")
    logger.debug(f"请求 payload: {payload}")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(api_url, headers=headers, json=payload)
            logger.info(f"API 响应状态码：{response.status_code}")
            return response
    except httpx.TimeoutException as e:
        logger.error(f"请求超时（{timeout}秒）: {e}")
        return None
    except httpx.ConnectError as e:
        logger.error(f"连接错误：{e}")
        return type('obj', (object,), {
            'status_code': 0,
            'text': f"Connection error: {str(e)}"
        })()
    except Exception as e:
        logger.error(f"未知错误：{e}")
        return type('obj', (object,), {
            'status_code': 0,
            'text': f"Error: {str(e)}"
        })()

async def forward_to_model(model_config: dict, request) -> dict:
    """
    转发请求到配置的模型 API
    
    参考成熟的 openai-proxy 实现：
    - 完全透传所有参数
    - 只替换 model 字段
    - 保持请求的原始结构
    """
    api_key = model_config['api_key']
    model_name = model_config['name']
    config_id = model_config['config_id']
    model_id = model_config.get('model_id', '')
    
    base_url = model_config['api_url'].rstrip('/')
    if not base_url.endswith('/chat/completions'):
        api_url = f"{base_url}/chat/completions"
    else:
        api_url = base_url

    # 使用配置中的 model_id，完全忽略 request.model
    payload_model = model_id if model_id else model_name
    
    logger.info(f"转发请求到 {model_name}，使用 model={payload_model}")

    # 完全透传：使用 model_dump 排除 model 字段，然后替换
    payload = request.model_dump(exclude={'model'}, exclude_none=False)
    payload['model'] = payload_model
    
    # 确保 messages 格式正确
    payload['messages'] = [
        {"role": m.role, "content": m.content} 
        for m in request.messages
    ]

    logger.info(f"完整透传 payload: {payload}")

    input_tokens = count_messages_tokens(payload["messages"])
    logger.info(f"输入 Token 数：{input_tokens}")

    response = await call_model(api_url, api_key, payload, timeout=30.0)

    if response is None:
        logger.error("请求超时")
        return {
            "status": "error",
            "status_code": 0,
            "error_message": "Request timeout (30s)"
        }

    if response.status_code == 200:
        try:
            result = response.json()
            logger.info(f"请求成功，响应：{result}")
            output_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            output_tokens = count_response_tokens(output_content)
            logger.info(f"输出 Token 数：{output_tokens}")

            update_daily_usage(config_id, input_tokens + output_tokens, 1)

            return {
                "status": "success",
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "response": result
            }
        except Exception as e:
            logger.error(f"解析响应失败：{e}")
            return {
                "status": "error",
                "status_code": 0,
                "error_message": f"Response parse error: {str(e)}"
            }
    else:
        error_detail = response.text
        logger.error(f"API 调用失败，状态码：{response.status_code}, 错误：{error_detail}")
        return {
            "status": "error",
            "status_code": response.status_code,
            "error_message": error_detail
        }
