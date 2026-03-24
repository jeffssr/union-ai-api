"""
完全最小化的 chat completions 端点
参考 LiteLLM 和 OpenAI-Proxy-Api 的实现
"""
import uuid
import time
import logging
import httpx
from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional
from app.database import get_model_by_priority, get_api_key, get_daily_usage, create_call_log, get_default_model, get_auto_switch_status

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    """完全透传的 chat completions 端点"""
    
    logger.info("收到请求")
    
    # 1. 验证 API Key
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    api_key = authorization.replace("Bearer ", "").strip()
    api_key_record = get_api_key(api_key)
    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 2. 获取原始请求体（不验证，只读取）
    try:
        request_body = await request.json()
    except Exception as e:
        logger.error(f"解析请求失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    logger.info(f"请求 model: {request_body.get('model', 'N/A')}")
    logger.info(f"消息数: {len(request_body.get('messages', []))}")
    
    request_id = str(uuid.uuid4())
    
    # 3. 检查自动切换模式
    auto_switch_enabled = get_auto_switch_status()
    logger.info(f"自动切换: {auto_switch_enabled}")
    
    if not auto_switch_enabled:
        # 使用默认模型
        default_model = get_default_model()
        if not default_model:
            raise HTTPException(status_code=500, detail="No default model configured")
        
        logger.info(f"使用默认模型: {default_model['name']}")
        result = await forward_request(default_model, request_body, request_id, api_key_record)
        
        if result["status"] == "success":
            return result["response"]
        else:
            raise HTTPException(
                status_code=502, 
                detail=f"Model call failed: {result.get('error_message', 'Unknown error')}"
            )
    else:
        # 自动切换模式
        models = get_model_by_priority()
        if not models:
            raise HTTPException(status_code=500, detail="No models configured")
        
        logger.info(f"尝试 {len(models)} 个模型")
        
        for model_config in models:
            logger.info(f"尝试模型: {model_config['name']}")
            result = await forward_request(model_config, request_body, request_id, api_key_record)
            
            if result["status"] == "success":
                return result["response"]
            else:
                logger.warning(f"模型 {model_config['name']} 失败: {result.get('error_message', '')}")
                continue
        
        raise HTTPException(status_code=502, detail="All models failed")

async def forward_request(model_config: dict, request_body: dict, request_id: str, api_key_record: dict) -> dict:
    """转发请求到第三方 API"""
    
    config_id = model_config['config_id']
    api_key = model_config['api_key']
    model_name = model_config['name']
    model_id = model_config.get('model_id', '')
    
    # 检查每日限制
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
            "error_message": f"Token limit exceeded: {usage['total_tokens']}/{daily_token_limit}",
            "error_code": "TOKEN_LIMIT"
        })
        return {"status": "error", "error_message": "Token limit exceeded"}
    
    if usage['total_calls'] >= daily_call_limit:
        create_call_log({
            "request_id": request_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": f"Call limit exceeded: {usage['total_calls']}/{daily_call_limit}",
            "error_code": "CALL_LIMIT"
        })
        return {"status": "error", "error_message": "Call limit exceeded"}
    
    # 构建转发 URL
    base_url = model_config['api_url'].rstrip('/')
    if not base_url.endswith('/chat/completions'):
        api_url = f"{base_url}/chat/completions"
    else:
        api_url = base_url
    
    # 替换 model
    target_model = model_id if model_id else model_name
    request_body['model'] = target_model
    
    logger.info(f"转发到: {api_url}")
    logger.info(f"使用 model: {target_model}")
    
    # 发送请求
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            logger.info(f"响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result_data = response.json()
                
                # 记录使用量
                input_tokens = result_data.get("usage", {}).get("prompt_tokens", 0)
                output_tokens = result_data.get("usage", {}).get("completion_tokens", 0)
                
                from app.database import update_daily_usage
                update_daily_usage(config_id, input_tokens + output_tokens, 1)
                
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
                
                # 替换 model 名称
                result_data['model'] = model_name
                
                return {"status": "success", "response": result_data}
            else:
                error_text = response.text
                logger.error(f"API 错误: {error_text[:500]}")
                
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
        return {"status": "error", "error_message": "Request timeout (30s)"}
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return {"status": "error", "error_message": str(e)}
