"""
OpenAI Responses API 兼容层
将 Responses API 请求转换为 Chat Completions API 请求，转发到第三方提供商（智谱等）
然后将响应转换回 Responses API 格式

参考文档：
- https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-responses
- https://github.com/openai/completions-responses-migration-pack
- https://platform.openai.com/docs/api-reference/responses
"""
import uuid
import json
import logging
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List, Dict, Any, Union
from app.database import get_model_by_priority, get_api_key, get_daily_usage, create_call_log, get_default_model, get_auto_switch_status, update_daily_usage, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

BEIJING_TZ = timezone(timedelta(hours=8))

# 全局HTTP客户端连接池
_global_client: Optional[httpx.AsyncClient] = None

# 速率限制配置
MODEL_SWITCH_DELAY = 0.5
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0
RATE_LIMIT_STATUS_CODES = {429}
RATE_LIMIT_ERROR_CODES = {"limit_burst_rate", "rate_limit", "too_many_requests"}


def get_global_client() -> httpx.AsyncClient:
    """获取全局HTTP客户端（连接池复用）"""
    global _global_client
    if _global_client is None or _global_client.is_closed:
        _global_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    return _global_client


def is_rate_limit_error(error_text: str, status_code: int) -> bool:
    """检查是否为速率限制错误"""
    if status_code in RATE_LIMIT_STATUS_CODES:
        return True
    error_lower = error_text.lower()
    for code in RATE_LIMIT_ERROR_CODES:
        if code in error_lower:
            return True
    return False


def get_beijing_time():
    return datetime.now(BEIJING_TZ)


def convert_input_to_messages(input_data: Union[str, List[Dict]]) -> List[Dict]:
    """
    将 Responses API 的 input 转换为 Chat Completions API 的 messages
    
    Responses API input 支持格式：
    1. 字符串：直接作为 user 消息
    2. 消息数组：包含 role, content 的对象数组
       - content 可以是字符串或内容部件数组
       - 支持的内容部件类型：input_text, input_image, input_file
    """
    if isinstance(input_data, str):
        return [{"role": "user", "content": input_data}]
    
    elif isinstance(input_data, list):
        messages = []
        for item in input_data:
            if isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", "")
                
                # 处理 content 字段（可能是字符串或数组）
                if isinstance(content, list):
                    # 多模态内容，转换为 OpenAI 格式
                    converted_content = []
                    for part in content:
                        if isinstance(part, dict):
                            part_type = part.get("type", "")
                            if part_type == "input_text":
                                converted_content.append({
                                    "type": "text",
                                    "text": part.get("text", "")
                                })
                            elif part_type == "input_image":
                                # 转换图片格式
                                image_url = part.get("image_url", "")
                                if isinstance(image_url, dict):
                                    image_url = image_url.get("url", "")
                                converted_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": image_url}
                                })
                            elif part_type == "text":
                                converted_content.append({
                                    "type": "text",
                                    "text": part.get("text", "")
                                })
                    content = converted_content if converted_content else ""
                
                msg = {"role": role, "content": content}
                
                # 保留其他字段
                for key in ["tool_calls", "tool_call_id", "name"]:
                    if key in item:
                        msg[key] = item[key]
                
                messages.append(msg)
            else:
                messages.append({"role": "user", "content": str(item)})
        return messages
    
    else:
        return [{"role": "user", "content": str(input_data)}]


def convert_tools_for_chat_completions(tools: List[Dict]) -> List[Dict]:
    """
    将 Responses API / OpenAI 格式的 tools 转换为智谱 API 格式
    
    OpenAI Responses API 支持的工具类型：
    - function: 函数调用
    - web_search_preview: 联网搜索预览
    - file_search: 文件搜索  
    - code_interpreter: 代码解释器
    
    智谱 API 支持的工具类型：
    - function: 函数调用
    - web_search: 联网搜索 (需要特定的格式)
    - retrieval: 知识库检索 (智谱特有)
    """
    converted_tools = []
    
    for tool in tools:
        if not isinstance(tool, dict):
            continue
            
        tool_type = tool.get("type", "")
        
        if tool_type == "function":
            function_data = tool.get("function", {})
            if function_data and isinstance(function_data, dict):
                converted_tools.append({
                    "type": "function",
                    "function": {
                        "name": function_data.get("name", ""),
                        "description": function_data.get("description", ""),
                        "parameters": function_data.get("parameters", {})
                    }
                })
        elif tool_type in ["web_search", "web_search_preview"]:
            # 智谱 web_search 需要特定格式
            converted_tools.append({
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_result": True
                }
            })
            logger.info(f"转换 {tool_type} 工具为智谱格式")
        elif tool_type == "file_search":
            logger.warning("file_search 工具需要配置知识库 ID，暂时跳过")
            continue
        elif tool_type == "code_interpreter":
            logger.warning("code_interpreter 工具不被智谱支持，跳过")
            continue
        else:
            # 未知类型，尝试作为 function 处理
            if "function" in tool:
                function_data = tool.get("function", {})
                if function_data and isinstance(function_data, dict):
                    converted_tools.append({
                        "type": "function",
                        "function": {
                            "name": function_data.get("name", ""),
                            "description": function_data.get("description", ""),
                            "parameters": function_data.get("parameters", {})
                        }
                    })
    
    return converted_tools


def convert_text_format(text_format: Dict) -> Optional[Dict]:
    """
    转换 text.format 为 response_format
    """
    if not text_format or not isinstance(text_format, dict):
        return None
    
    format_type = text_format.get("type", "text")
    
    if format_type == "json_schema":
        schema = text_format.get("json_schema", {})
        return {
            "type": "json_object" if not schema else "json_schema",
            "json_schema": schema if schema else None
        }
    elif format_type == "json_object":
        return {"type": "json_object"}
    else:
        return {"type": "text"}


def convert_chat_completion_to_response(
    chat_response: Dict,
    response_id: str,
    model_name: str,
    created_at: int
) -> Dict:
    """
    将 Chat Completions API 响应转换为 Responses API 响应
    
    完整的 Responses API 响应格式包含：
    - id: 响应唯一标识
    - object: 固定为 "response"
    - created_at: 创建时间戳
    - status: 状态 (completed, in_progress, incomplete, cancelled, failed)
    - model: 模型名称
    - output: 输出内容数组
    - usage: Token 使用统计
    - incomplete_details: 未完成详情
    - error: 错误信息
    """
    choice = chat_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    usage = chat_response.get("usage", {})
    
    # 构建 content 数组
    content_items = []
    
    # 处理普通文本内容
    msg_content = message.get("content", "")
    if msg_content:
        if isinstance(msg_content, str):
            content_items.append({
                "type": "output_text",
                "text": msg_content,
                "annotations": [],
                "logprobs": []
            })
        elif isinstance(msg_content, list):
            for part in msg_content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        content_items.append({
                            "type": "output_text",
                            "text": part.get("text", ""),
                            "annotations": [],
                            "logprobs": []
                        })
    
    # 处理工具调用
    tool_calls = message.get("tool_calls", [])
    for tool_call in tool_calls:
        if isinstance(tool_call, dict):
            function_data = tool_call.get("function", {})
            content_items.append({
                "type": "function_call",
                "id": tool_call.get("id", ""),
                "call_id": tool_call.get("id", ""),
                "name": function_data.get("name", ""),
                "arguments": function_data.get("arguments", "")
            })
    
    # 处理 reasoning_content（某些模型如 DeepSeek 支持）
    reasoning_content = message.get("reasoning_content", "")
    if reasoning_content:
        content_items.insert(0, {
            "type": "output_text",
            "text": f"[Reasoning] {reasoning_content}\n\n",
            "annotations": [],
            "logprobs": []
        })
    
    # 确定状态
    finish_reason = choice.get("finish_reason")
    status = "completed"
    incomplete_details = None
    error = None
    
    if finish_reason == "length":
        status = "incomplete"
        incomplete_details = {"reason": "max_output_tokens"}
    elif finish_reason == "content_filter":
        status = "incomplete"
        incomplete_details = {"reason": "content_filter"}
    elif finish_reason == "tool_calls":
        # tool_calls 是正常流程，保持 completed
        pass
    
    # 构建完整的 Responses API 响应
    response = {
        "id": response_id,
        "object": "response",
        "created_at": created_at,
        "status": status,
        "error": error,
        "incomplete_details": incomplete_details,
        "model": model_name,
        "output": [{
            "type": "message",
            "id": f"msg_{uuid.uuid4().hex[:24]}",
            "status": "completed",
            "role": "assistant",
            "content": content_items
        }],
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "input_tokens_details": {
                "cached_tokens": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)
            },
            "output_tokens": usage.get("completion_tokens", 0),
            "output_tokens_details": {
                "reasoning_tokens": usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
            },
            "total_tokens": usage.get("total_tokens", 0)
        },
        "instructions": None,
        "max_output_tokens": None,
        "parallel_tool_calls": True,
        "previous_response_id": None,
        "reasoning": {
            "effort": None,
            "summary": None
        },
        "store": True,
        "temperature": 1.0,
        "text": {
            "format": {
                "type": "text"
            }
        },
        "tool_choice": "auto",
        "tools": [],
        "top_p": 1.0,
        "truncation": "disabled",
        "user": None,
        "metadata": {}
    }
    
    return response


def convert_chat_completion_stream_chunk(
    chunk: Dict,
    response_id: str,
    model_name: str
) -> Optional[str]:
    """
    将 Chat Completions API 的流式 chunk 转换为 Responses API 格式
    """
    choices = chunk.get("choices", [])
    if not choices:
        return None
    
    choice = choices[0]
    delta = choice.get("delta", {})
    finish_reason = choice.get("finish_reason")
    
    events = []
    
    # 处理文本增量
    delta_text = delta.get("content", "")
    if delta_text:
        event = {
            "type": "response.output_text.delta",
            "item_id": f"msg_{response_id}",
            "output_index": 0,
            "content_index": 0,
            "delta": delta_text
        }
        events.append(f"data: {json.dumps(event, ensure_ascii=False)}\n\n")
    
    # 处理工具调用增量
    tool_calls = delta.get("tool_calls", [])
    if tool_calls:
        for tool_call in tool_calls:
            if isinstance(tool_call, dict):
                event = {
                    "type": "response.function_call_arguments.delta",
                    "item_id": tool_call.get("id", ""),
                    "output_index": 0,
                    "delta": tool_call.get("function", {}).get("arguments", "")
                }
                events.append(f"data: {json.dumps(event, ensure_ascii=False)}\n\n")
    
    # 处理完成
    if finish_reason:
        if finish_reason == "stop":
            event = {
                "type": "response.completed",
                "response": {
                    "id": response_id,
                    "object": "response",
                    "status": "completed",
                    "model": model_name
                }
            }
        elif finish_reason == "length":
            event = {
                "type": "response.incomplete",
                "response": {
                    "id": response_id,
                    "object": "response",
                    "status": "incomplete",
                    "model": model_name,
                    "incomplete_details": {"reason": "max_output_tokens"}
                }
            }
        else:
            event = {
                "type": "response.completed",
                "response": {
                    "id": response_id,
                    "object": "response",
                    "status": "completed",
                    "model": model_name
                }
            }
        events.append(f"data: {json.dumps(event, ensure_ascii=False)}\n\n")
        events.append("data: [DONE]\n\n")
    
    return "".join(events) if events else None


@router.post("/v1/responses")
async def responses_api(request: Request, authorization: Optional[str] = Header(None)):
    """
    OpenAI Responses API 兼容端点
    接收 Responses API 格式请求，转换为 Chat Completions API 格式转发到第三方
    """
    request_id = f"resp_{uuid.uuid4().hex[:24]}"
    created_at = int(get_beijing_time().timestamp())
    
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
    
    # 提取 Responses API 参数（完整的参数列表）
    model = request_body.get("model", "")
    input_data = request_body.get("input", "")
    stream = request_body.get("stream", False)
    previous_response_id = request_body.get("previous_response_id")
    
    # 模型参数
    temperature = request_body.get("temperature")
    max_output_tokens = request_body.get("max_output_tokens")
    top_p = request_body.get("top_p")
    top_logprobs = request_body.get("top_logprobs")
    
    # 工具和函数调用
    tools = request_body.get("tools", [])
    tool_choice = request_body.get("tool_choice")
    parallel_tool_calls = request_body.get("parallel_tool_calls", True)
    
    # 文本格式和输出控制
    text_format = request_body.get("text", {}).get("format") if isinstance(request_body.get("text"), dict) else None
    truncation = request_body.get("truncation", "disabled")
    
    # 其他参数
    user = request_body.get("user")
    metadata = request_body.get("metadata", {})
    store = request_body.get("store", True)
    
    logger.info(f"收到 Responses API 请求 - model: {model}, stream: {stream}, tools_count: {len(tools)}")
    
    # 转换 input 为 messages
    messages = convert_input_to_messages(input_data)
    
    # 构建 Chat Completions 请求体
    chat_request = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    
    # 添加可选参数（只添加非 None 的值）
    if temperature is not None:
        chat_request["temperature"] = temperature
    if max_output_tokens is not None:
        chat_request["max_tokens"] = max_output_tokens
    if top_p is not None:
        chat_request["top_p"] = top_p
    if top_logprobs is not None:
        chat_request["logprobs"] = True
        chat_request["top_logprobs"] = top_logprobs
    
    # 处理 tools
    if tools:
        converted_tools = convert_tools_for_chat_completions(tools)
        if converted_tools:
            chat_request["tools"] = converted_tools
            logger.info(f"转换后 tools 数量: {len(converted_tools)}")
        else:
            logger.warning("所有 tools 都不被支持，已过滤掉")
    
    if tool_choice:
        chat_request["tool_choice"] = tool_choice
    
    # 处理 response_format
    if text_format:
        response_format = convert_text_format(text_format)
        if response_format:
            chat_request["response_format"] = response_format
    
    # 获取自动切换状态
    auto_switch_enabled = get_auto_switch_status()
    
    if not auto_switch_enabled:
        default_model = get_default_model()
        if not default_model:
            logger.error("没有配置默认模型")
            raise HTTPException(status_code=500, detail="No default model configured")
        
        logger.info(f"使用默认模型：{default_model['name']}")
        
        if stream:
            return await forward_stream_responses(
                default_model, chat_request, request_id, api_key_record, created_at, model
            )
        else:
            result = await forward_to_model_responses(
                default_model, chat_request, request_id, api_key_record, created_at, model
            )
            
            if result["status"] == "success":
                return JSONResponse(content=result["response"])
            else:
                logger.error(f"默认模型请求失败：{result.get('error_message')}")
                return JSONResponse(
                    status_code=result.get("status_code", 502),
                    content={
                        "error": {
                            "message": result.get("error_message", "Unknown error"),
                            "type": "api_error",
                            "code": result.get("error_code", "unknown_error")
                        }
                    }
                )
    else:
        # 自动切换模式
        models = get_model_by_priority()
        if not models:
            logger.error("自动切换模式下没有配置模型")
            raise HTTPException(status_code=500, detail="No models configured")
        
        logger.info(f"自动切换模式，尝试 {len(models)} 个模型")
        
        last_error = None
        for idx, model_config in enumerate(models):
            logger.info(f"尝试模型 #{idx + 1}: {model_config['name']}")
            
            if stream:
                result = await forward_stream_responses(
                    model_config, chat_request, request_id, api_key_record, created_at, model
                )
                if result["status"] == "success":
                    logger.info(f"模型 {model_config['name']} 成功")
                    return result["response"]
                else:
                    logger.warning(f"模型 {model_config['name']} 失败：{result.get('error_message')}")
                    last_error = result.get('error_message')
                    if idx < len(models) - 1:
                        logger.info(f"等待 {MODEL_SWITCH_DELAY} 秒后尝试下一个模型...")
                        await asyncio.sleep(MODEL_SWITCH_DELAY)
                    continue
            else:
                result = await forward_to_model_responses(
                    model_config, chat_request, request_id, api_key_record, created_at, model
                )
                if result["status"] == "success":
                    logger.info(f"模型 {model_config['name']} 成功")
                    return JSONResponse(content=result["response"])
                else:
                    logger.warning(f"模型 {model_config['name']} 失败：{result.get('error_message')}")
                    last_error = result.get('error_message')
                    if idx < len(models) - 1:
                        logger.info(f"等待 {MODEL_SWITCH_DELAY} 秒后尝试下一个模型...")
                        await asyncio.sleep(MODEL_SWITCH_DELAY)
                    continue
        
        logger.error(f"所有模型都失败：{last_error}")
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "message": f"All models failed: {last_error}",
                    "type": "api_error",
                    "code": "all_models_failed"
                }
            }
        )


async def forward_stream_responses(
    model_config: dict,
    chat_request: dict,
    response_id: str,
    api_key_record: dict,
    created_at: int,
    original_model: str
):
    """转发流式请求到第三方 API，并将响应转换为 Responses API 格式"""
    
    config_id = model_config['config_id']
    api_key = model_config['api_key']
    model_name = model_config['name']
    model_id = model_config.get('model_id', '')
    
    usage = get_daily_usage(config_id)
    daily_token_limit = model_config.get('daily_token_limit', 100000)
    daily_call_limit = model_config.get('daily_call_limit', 1000)
    
    logger.info(f"检查限制 - model: {model_name}, calls: {usage['total_calls']}/{daily_call_limit}, tokens: {usage['total_tokens']}/{daily_token_limit}")
    
    if usage['total_calls'] >= daily_call_limit:
        logger.warning(f"模型 {model_name} 调用次数已达上限")
        return {"status": "error", "status_code": 429, "error_message": "Call limit exceeded"}
    
    if usage['total_tokens'] >= daily_token_limit:
        logger.warning(f"模型 {model_name} Token 限额已达上限")
        return {"status": "error", "status_code": 429, "error_message": "Token limit exceeded"}
    
    base_url = model_config['api_url'].rstrip('/')
    if not base_url.endswith('/chat/completions'):
        api_url = f"{base_url}/chat/completions"
    else:
        api_url = base_url
    
    target_model = model_id if model_id else model_name
    chat_request['model'] = target_model
    
    logger.info(f"流式转发到：{api_url}, model: {target_model}")
    
    try:
        client = get_global_client()
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=chat_request
        )
        
        logger.info(f"流式响应状态：{response.status_code}")
        
        if response.status_code == 200:
            actual_input_tokens = 0
            actual_output_tokens = 0
            
            async def generate():
                nonlocal actual_input_tokens, actual_output_tokens
                logger.info(f"generate() 函数开始")
                
                # 发送初始事件
                init_event = {
                    "type": "response.created",
                    "response": {
                        "id": response_id,
                        "object": "response",
                        "status": "in_progress",
                        "model": original_model
                    }
                }
                yield f"data: {json.dumps(init_event, ensure_ascii=False)}\n\n"
                
                # 发送 output_item.added 事件
                item_event = {
                    "type": "response.output_item.added",
                    "output_index": 0,
                    "item": {
                        "id": f"msg_{response_id}",
                        "type": "message",
                        "role": "assistant",
                        "content": []
                    }
                }
                yield f"data: {json.dumps(item_event, ensure_ascii=False)}\n\n"
                
                # 发送 content_part.added 事件
                part_event = {
                    "type": "response.content_part.added",
                    "item_id": f"msg_{response_id}",
                    "output_index": 0,
                    "content_index": 0,
                    "part": {
                        "type": "output_text",
                        "text": ""
                    }
                }
                yield f"data: {json.dumps(part_event, ensure_ascii=False)}\n\n"
                
                try:
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith('data: '):
                                if line.startswith('data: [DONE]'):
                                    continue
                                
                                try:
                                    chunk_data = json.loads(line[6:])
                                    
                                    # 提取 usage 信息
                                    usage_data = chunk_data.get('usage')
                                    if usage_data:
                                        actual_input_tokens = usage_data.get('prompt_tokens', 0)
                                        actual_output_tokens = usage_data.get('completion_tokens', 0)
                                    
                                    # 转换 chunk 为 Responses API 格式
                                    converted = convert_chat_completion_stream_chunk(
                                        chunk_data, response_id, original_model
                                    )
                                    if converted:
                                        yield converted
                                    
                                except json.JSONDecodeError:
                                    logger.warning(f"无法解析 JSON: {line}")
                                    continue
                    
                    # 发送 content_part.done 事件
                    part_done_event = {
                        "type": "response.content_part.done",
                        "item_id": f"msg_{response_id}",
                        "output_index": 0,
                        "content_index": 0,
                        "part": {
                            "type": "output_text",
                            "text": ""
                        }
                    }
                    yield f"data: {json.dumps(part_done_event, ensure_ascii=False)}\n\n"
                    
                    # 发送 output_item.done 事件
                    item_done_event = {
                        "type": "response.output_item.done",
                        "output_index": 0,
                        "item": {
                            "id": f"msg_{response_id}",
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": ""}]
                        }
                    }
                    yield f"data: {json.dumps(item_done_event, ensure_ascii=False)}\n\n"
                    
                    # 发送 completed 事件
                    completed_event = {
                        "type": "response.completed",
                        "response": {
                            "id": response_id,
                            "object": "response",
                            "status": "completed",
                            "model": original_model,
                            "usage": {
                                "input_tokens": actual_input_tokens,
                                "output_tokens": actual_output_tokens,
                                "total_tokens": actual_input_tokens + actual_output_tokens
                            }
                        }
                    }
                    yield f"data: {json.dumps(completed_event, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    
                    logger.info(f"流式完成，tokens: input={actual_input_tokens}, output={actual_output_tokens}")
                    
                    # 更新 usage
                    if actual_input_tokens > 0 or actual_output_tokens > 0:
                        update_daily_usage(config_id, actual_input_tokens + actual_output_tokens, 1)
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE call_logs 
                                SET input_tokens = ?, output_tokens = ?
                                WHERE request_id = ?
                            """, (actual_input_tokens, actual_output_tokens, response_id))
                    else:
                        update_daily_usage(config_id, 0, 1)
                        
                except Exception as e:
                    logger.error(f"流式读取错误：{e}")
                    error_event = {
                        "type": "response.failed",
                        "response": {
                            "id": response_id,
                            "object": "response",
                            "status": "failed",
                            "error": {"message": str(e)}
                        }
                    }
                    yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
            
            # 创建调用日志
            create_call_log({
                "request_id": response_id,
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
                        "X-Request-ID": response_id,
                    }
                )
            }
        else:
            error_text = response.text
            logger.error(f"流式 API 错误：{error_text[:500]}")
            
            create_call_log({
                "request_id": response_id,
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
            "request_id": response_id,
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
            "request_id": response_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": str(e)[:1000],
            "error_code": "EXCEPTION"
        })
        return {"status": "error", "status_code": 502, "error_message": str(e)}


async def forward_to_model_responses(
    model_config: dict,
    chat_request: dict,
    response_id: str,
    api_key_record: dict,
    created_at: int,
    original_model: str
):
    """转发非流式请求到第三方 API，并将响应转换为 Responses API 格式"""
    
    config_id = model_config['config_id']
    api_key = model_config['api_key']
    model_name = model_config['name']
    model_id = model_config.get('model_id', '')
    
    usage = get_daily_usage(config_id)
    daily_token_limit = model_config.get('daily_token_limit', 100000)
    daily_call_limit = model_config.get('daily_call_limit', 1000)
    
    if usage['total_tokens'] >= daily_token_limit:
        create_call_log({
            "request_id": response_id,
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
            "request_id": response_id,
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
    chat_request['model'] = target_model
    
    logger.info(f"转发到：{api_url}, model: {target_model}")
    
    try:
        client = get_global_client()
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=chat_request
        )
        
        logger.info(f"响应状态：{response.status_code}")
        
        if response.status_code == 200:
            chat_response = response.json()
            
            # 转换为 Responses API 格式
            response_data = convert_chat_completion_to_response(
                chat_response, response_id, original_model, created_at
            )
            
            # 提取 usage
            usage_data = chat_response.get('usage', {})
            input_tokens = usage_data.get('prompt_tokens', 0)
            output_tokens = usage_data.get('completion_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            logger.info(f"更新 usage: tokens={total_tokens}, calls=1")
            update_daily_usage(config_id, total_tokens, 1)
            
            create_call_log({
                "request_id": response_id,
                "api_key_id": api_key_record['key_id'],
                "api_key_name": api_key_record['name'],
                "model_config_id": config_id,
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
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
                "request_id": response_id,
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
            "request_id": response_id,
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
            "request_id": response_id,
            "api_key_id": api_key_record['key_id'],
            "api_key_name": api_key_record['name'],
            "model_config_id": config_id,
            "model_name": model_name,
            "status": "failed",
            "error_message": str(e)[:1000],
            "error_code": "EXCEPTION"
        })
        return {"status": "error", "status_code": 502, "error_message": str(e)}
