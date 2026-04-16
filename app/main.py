from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.database import init_database
from app.router.chat_final import router as chat_router
from app.router.responses_api import router as responses_router, responses_api
from app.router.admin import admin_router
import logging
import os

# 配置日志级别为 INFO
logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("app").setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield

app = FastAPI(
    title="AI Proxy API",
    description="Unified API for multiple LLM providers - Supports both Chat Completions and Responses API",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(responses_router)
app.include_router(admin_router)

# 添加直接响应 /responses 的路由（兼容 Codex 等客户端）
@app.post("/responses")
async def responses_api_direct(request: Request):
    """
    直接处理 /responses 请求（不带 /v1 前缀）
    兼容某些客户端配置 base_url 时不带 /v1 的情况
    """
    return await responses_api(request)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 静态文件服务（React 构建产物）
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(os.path.join(STATIC_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="static_assets")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """SPA fallback: 未匹配的路径返回 index.html，由 React Router 处理"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    # 无 index.html 时返回 API 状态（向后兼容纯 API 模式）
    return {"message": "AI Proxy API is running"}
