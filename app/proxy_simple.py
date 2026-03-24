"""
最简单的 OpenAI 兼容代理服务
参考成熟项目：LiteLLM、OpenAI-Proxy-Api
核心原则：最小干预，完全透传
"""
import httpx
import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Header = None):
    """完全透传的 chat completions 端点"""
    
    logger.info(f"收到请求")
    
    # 1. 验证 API Key
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    api_key = authorization.replace("Bearer ", "").strip()
    
    # 这里应该验证 API Key，从数据库读取
    # 简化版本：直接验证
    from app.database import get_api_key
    api_key_record = get_api_key(api_key)
    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # 2. 获取原始请求体（不进行 Pydantic 验证）
    request_body = await request.json()
    logger.info(f"原始请求: {json.dumps(request_body, ensure_ascii=False)[:500]}")
    
    # 3. 获取默认模型配置
    from app.database import get_default_model
    default_model = get_default_model()
    if not default_model:
        raise HTTPException(status_code=500, detail="No default model configured")
    
    # 4. 构建转发 URL
    api_url = default_model['api_url'].rstrip('/')
    if not api_url.endswith('/chat/completions'):
        api_url = f"{api_url}/chat/completions"
    
    # 5. 替换 model 为配置的 model_id
    request_body['model'] = default_model.get('model_id') or default_model['name']
    
    logger.info(f"转发到: {api_url}")
    logger.info(f"使用 model: {request_body['model']}")
    
    # 6. 发送请求到第三方 API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {default_model['api_key']}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            logger.info(f"第三方 API 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                # 7. 直接返回响应
                return response.json()
            else:
                # 返回第三方 API 的错误
                error_text = response.text
                logger.error(f"第三方 API 错误: {error_text}")
                return JSONResponse(
                    status_code=response.status_code,
                    content=response.json() if response.text else {"error": error_text}
                )
                
    except httpx.TimeoutException:
        logger.error("请求超时")
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"请求失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
