import uuid
import time
import logging
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.schemas import ChatCompletionRequest, ChatCompletionResponse, Usage, Choice, ChatMessage
from app.database import get_model_by_priority, get_api_key, get_daily_usage, create_call_log, get_default_model, get_auto_switch_status
from app.services.llm_service import forward_to_model

logger = logging.getLogger(__name__)
router = APIRouter()

def parse_response(response_data: dict) -> dict:
    return {
        "id": response_data.get("id", f"chatcmpl-{uuid.uuid4().hex[:8]}"),
        "object": response_data.get("object", "chat.completion"),
        "created": response_data.get("created", int(time.time())),
        "model": response_data.get("model", ""),
        "choices": response_data.get("choices", [{
            "index": 0,
            "message": {"role": "assistant", "content": ""},
            "finish_reason": "stop"
        }]),
        "usage": response_data.get("usage", {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        })
    }

@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None)
):
    logger.info(f"收到请求 - 客户端 model 参数：{request.model}（将被忽略）")
    logger.info(f"请求详情：temperature={request.temperature}, top_p={request.top_p}, stream={request.stream}")
    logger.info(f"stream_options={request.stream_options}, response_format={request.response_format}")
    logger.info(f"tools={request.tools}, tool_choice={request.tool_choice}")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    api_key = authorization.replace("Bearer ", "").strip()

    api_key_record = get_api_key(api_key)
    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    request_id = str(uuid.uuid4())

    auto_switch_enabled = get_auto_switch_status()
    logger.info(f"自动切换状态：{auto_switch_enabled}")

    if not auto_switch_enabled:
        default_model = get_default_model()
        logger.info(f"使用默认模型：{default_model['name'] if default_model else 'None'}")

        if not default_model:
            raise HTTPException(status_code=500, detail="No default model configured")

        config_id = default_model['config_id']
        daily_token_limit = default_model.get('daily_token_limit', 100000)
        daily_call_limit = default_model.get('daily_call_limit', 1000)

        usage = get_daily_usage(config_id)

        if usage['total_tokens'] >= daily_token_limit:
            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": default_model['name'],
                "status": "failed",
                "error_message": f"Token limit exceeded: {usage['total_tokens']}/{daily_token_limit}",
                "error_code": "TOKEN_LIMIT"
            })
            raise HTTPException(status_code=429, detail="Token limit exceeded")

        if usage['total_calls'] >= daily_call_limit:
            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": default_model['name'],
                "status": "failed",
                "error_message": f"Call limit exceeded: {usage['total_calls']}/{daily_call_limit}",
                "error_code": "CALL_LIMIT"
            })
            raise HTTPException(status_code=429, detail="Call limit exceeded")

        result = await forward_to_model(default_model, request)

        if result["status"] == "success":
            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": default_model['name'],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "status": "success"
            })

            # 直接使用第三方返回的响应，只替换 model 字段
            response_data = result["response"]
            
            # 确保响应格式正确
            if not response_data.get("id"):
                response_data["id"] = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            if not response_data.get("object"):
                response_data["object"] = "chat.completion"
            if not response_data.get("created"):
                response_data["created"] = int(time.time())
            
            # 替换 model 为我们的模型名称
            response_data["model"] = default_model['name']
            
            # 确保 choices 格式正确
            if not response_data.get("choices") or len(response_data["choices"]) == 0:
                response_data["choices"] = [{
                    "index": 0,
                    "message": {"role": "assistant", "content": ""},
                    "finish_reason": "stop"
                }]
            
            # 确保 usage 格式正确
            response_data["usage"] = {
                "prompt_tokens": result["input_tokens"],
                "completion_tokens": result["output_tokens"],
                "total_tokens": result["input_tokens"] + result["output_tokens"]
            }
            
            # 直接返回第三方响应，保持原始格式
            return response_data
        else:
            create_call_log({
                "request_id": request_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": default_model['name'],
                "status": "failed",
                "error_message": result.get("error_message", ""),
                "error_code": str(result.get("status_code", ""))
            })
            raise HTTPException(status_code=502, detail=f"Model call failed: {result.get('error_message', 'Unknown error')}")

    else:
        models = get_model_by_priority()
        logger.info(f"自动切换模式，尝试 {len(models)} 个模型")
        if not models:
            raise HTTPException(status_code=500, detail="No models configured")

        for model_config in models:
            config_id = model_config['config_id']
            daily_token_limit = model_config.get('daily_token_limit', 100000)
            daily_call_limit = model_config.get('daily_call_limit', 1000)

            usage = get_daily_usage(config_id)

            if usage['total_tokens'] >= daily_token_limit:
                logger.info(f"模型 {model_config['name']} Token 配额已满")
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_config['name'],
                    "status": "failed",
                    "error_message": f"Token limit exceeded: {usage['total_tokens']}/{daily_token_limit}",
                    "error_code": "TOKEN_LIMIT"
                })
                continue

            if usage['total_calls'] >= daily_call_limit:
                logger.info(f"模型 {model_config['name']} 调用次数已达上限")
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_config['name'],
                    "status": "failed",
                    "error_message": f"Call limit exceeded: {usage['total_calls']}/{daily_call_limit}",
                    "error_code": "CALL_LIMIT"
                })
                continue

            logger.info(f"尝试调用模型：{model_config['name']}")
            result = await forward_to_model(model_config, request)

            if result["status"] == "success":
                logger.info(f"模型 {model_config['name']} 调用成功")
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_config['name'],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "status": "success"
                })

                # 直接使用第三方返回的响应，只替换 model 字段
                response_data = result["response"]
                
                # 确保响应格式正确
                if not response_data.get("id"):
                    response_data["id"] = f"chatcmpl-{uuid.uuid4().hex[:8]}"
                if not response_data.get("object"):
                    response_data["object"] = "chat.completion"
                if not response_data.get("created"):
                    response_data["created"] = int(time.time())
                
                # 替换 model 为我们的模型名称
                response_data["model"] = model_config['name']
                
                # 确保 choices 格式正确
                if not response_data.get("choices") or len(response_data["choices"]) == 0:
                    response_data["choices"] = [{
                        "index": 0,
                        "message": {"role": "assistant", "content": ""},
                        "finish_reason": "stop"
                    }]
                
                # 确保 usage 格式正确
                response_data["usage"] = {
                    "prompt_tokens": result["input_tokens"],
                    "completion_tokens": result["output_tokens"],
                    "total_tokens": result["input_tokens"] + result["output_tokens"]
                }
                
                # 直接返回第三方响应，保持原始格式
                return response_data
            else:
                logger.warning(f"模型 {model_config['name']} 调用失败：{result.get('error_message', '')}")
                create_call_log({
                    "request_id": request_id,
                    "api_key_id": api_key_record['key_id'],
                    "api_key_name": api_key_record['name'],
                    "model_config_id": config_id,
                    "model_name": model_config['name'],
                    "status": "failed",
                    "error_message": result.get("error_message", ""),
                    "error_code": str(result.get("status_code", ""))
                })

        raise HTTPException(status_code=502, detail="All models failed")
