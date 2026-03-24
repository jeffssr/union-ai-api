"""
诊断工具：捕获完整的请求和响应
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from typing import Optional
import json
from app.database import get_model_by_priority, get_api_key, get_default_model, get_auto_switch_status

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/diagnose/chat")
async def diagnose_chat(request: Request, authorization: Optional[str] = Header(None)):
    """诊断端点：记录完整的请求内容"""
    
    # 1. 获取原始请求
    request_body = await request.json()
    
    # 2. 记录完整请求
    diagnose_info = {
        "request_id": str(uuid.uuid4()),
        "headers": dict(request.headers),
        "body": request_body,
        "body_str": json.dumps(request_body, ensure_ascii=False)
    }
    
    logger.info("=" * 100)
    logger.info("完整请求诊断")
    logger.info(f"Request ID: {diagnose_info['request_id']}")
    logger.info(f"Headers: {diagnose_info['headers']}")
    logger.info(f"Body: {diagnose_info['body_str'][:1000]}")
    logger.info("=" * 100)
    
    # 3. 保存到文件
    with open(f"/tmp/diagnose_{diagnose_info['request_id']}.json", "w") as f:
        json.dump(diagnose_info, f, ensure_ascii=False, indent=2)
    
    # 4. 返回诊断信息
    return JSONResponse(content={
        "status": "received",
        "request_id": diagnose_info["request_id"],
        "message": "请求已记录，请查看日志和文件"
    })

@router.get("/diagnose/logs")
async def get_diagnose_logs():
    """获取诊断日志"""
    import os
    log_files = []
    for f in os.listdir("/tmp"):
        if f.startswith("diagnose_"):
            log_files.append(f)
    return JSONResponse(content={"files": log_files})
