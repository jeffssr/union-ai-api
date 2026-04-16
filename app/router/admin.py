"""Admin API 路由 - 管理员认证端点"""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Form, status
from typing import Optional
import hashlib
import base64
from datetime import datetime, timedelta
from app.database import (
    get_user, create_user, verify_password, has_users,
    update_user_password, hash_password
)

admin_router = APIRouter(prefix="/api/admin")

# 与 Streamlit 现有逻辑保持一致
SECRET_KEY = "union_ai_secret"


# ========== Session Token 函数 ==========

def create_session_token(username: str) -> str:
    """生成 base64 编码的 session token（username:timestamp:sha256_hash[:16]）"""
    timestamp = str(int(datetime.now().timestamp()))
    token_data = f"{username}:{timestamp}"
    token_hash = hashlib.sha256(f"{token_data}:{SECRET_KEY}".encode()).hexdigest()[:16]
    auth_token = f"{token_data}:{token_hash}"
    return base64.b64encode(auth_token.encode()).decode()


def verify_session_token(token_b64: str) -> Optional[str]:
    """验证 session token，返回用户名或 None"""
    try:
        auth_token = base64.b64decode(token_b64.encode()).decode()
        parts = auth_token.split(":")
        if len(parts) != 3:
            return None
        username, timestamp, token_hash = parts
        # 验证是否过期（7天）
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.now() - token_time > timedelta(days=7):
            return None
        # 验证签名
        expected_hash = hashlib.sha256(f"{username}:{timestamp}:{SECRET_KEY}".encode()).hexdigest()[:16]
        if token_hash != expected_hash:
            return None
        # 验证用户是否存在
        user = get_user(username)
        return username if user else None
    except Exception:
        return None


# ========== 依赖注入认证 ==========

async def get_current_user(session_token: Optional[str] = Cookie(None, alias="session_token")):
    """从 Cookie 中提取并验证当前用户"""
    if not session_token:
        raise HTTPException(status_code=401, detail="未认证")
    username = verify_session_token(session_token)
    if not username:
        raise HTTPException(status_code=401, detail="会话已过期")
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    # 不返回敏感字段
    return {"username": user["username"], "created_at": user.get("created_at")}


# ========== Cookie 辅助 ==========

COOKIE_MAX_AGE = 7 * 24 * 3600  # 7天


def set_auth_cookie(response: Response, token: str):
    """设置 HttpOnly 认证 Cookie"""
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
        path="/"
    )


# ========== 认证端点 ==========

@admin_router.post("/auth/register")
async def register(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """注册管理员（仅在无用户时允许）"""
    # 已有用户时不允许注册
    if has_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="已存在管理员账户，不允许注册"
        )
    # 验证输入
    if not username or not username.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名不能为空"
        )
    if not password or len(password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少4位"
        )
    # 创建用户
    success = create_user(username.strip(), password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    # 自动登录：设置 Cookie
    token = create_session_token(username.strip())
    set_auth_cookie(response, token)
    return {"message": "注册成功", "username": username.strip()}


@admin_router.post("/auth/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)
):
    """管理员登录"""
    user = get_user(username)
    if not user or not verify_password(password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    # 设置 Cookie
    token = create_session_token(username)
    set_auth_cookie(response, token)
    return {"message": "登录成功", "username": username}


@admin_router.post("/auth/logout")
async def logout(
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """退出登录"""
    response.delete_cookie(key="session_token", path="/")
    return {"message": "已退出登录"}


@admin_router.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return {"username": current_user["username"]}


@admin_router.post("/auth/change-password")
async def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    user = get_user(current_user["username"])
    if not user or not verify_password(old_password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    # 验证新密码
    if not new_password or len(new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少4位"
        )
    # 更新密码
    update_user_password(current_user["username"], new_password)
    return {"message": "密码修改成功"}
