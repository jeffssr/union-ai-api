"""Admin API 路由 - 管理员认证与管理 CRUD 端点"""

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, Form, Body, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import hashlib
import base64
import io
from datetime import datetime, timedelta, date as date_type
import pandas as pd
from app.database import (
    get_user, create_user, verify_password, has_users,
    update_user_password, hash_password,
    # 模型 CRUD
    get_all_models, create_model as db_create_model, update_model as db_update_model, delete_model as db_delete_model, get_model_by_config_id,
    # API Key 管理
    get_all_api_keys, create_api_key as db_create_api_key, delete_api_key as db_delete_api_key,
    # 统计
    get_call_logs, get_daily_stats,
    # 系统配置
    get_auto_switch_status, set_auto_switch_status
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


# ========== 辅助函数 ==========

def mask_api_key(api_key: str) -> str:
    """对 API Key 脱敏，只显示前 6 位 + ****"""
    if api_key and len(api_key) > 6:
        return api_key[:6] + "****"
    return api_key


# ========== 模型 CRUD 端点 ==========

@admin_router.get("/models")
async def list_models(current_user: dict = Depends(get_current_user)):
    """列出所有模型配置（api_key 脱敏）"""
    models = get_all_models()
    for m in models:
        m["api_key"] = mask_api_key(m.get("api_key", ""))
    return {"models": models}


@admin_router.post("/models")
async def create_model_endpoint(
    current_user: dict = Depends(get_current_user),
    body: dict = Body(...)
):
    """创建模型配置"""
    name = body.get("name", "").strip()
    api_url = body.get("api_url", "").strip()
    api_key = body.get("api_key", "").strip()
    if not name or not api_url or not api_key:
        raise HTTPException(status_code=400, detail="name, api_url, api_key 为必填字段")
    model_data = {
        "name": name,
        "api_url": api_url,
        "api_key": api_key,
        "model_id": body.get("model_id", ""),
        "daily_token_limit": body.get("daily_token_limit", 100000),
        "daily_call_limit": body.get("daily_call_limit", 1000),
        "is_default_model": body.get("is_default_model", 0),
        "priority": body.get("priority", 0),
    }
    config_id = db_create_model(model_data)
    return {"message": "创建成功", "config_id": config_id}


@admin_router.put("/models/{config_id}")
async def update_model_endpoint(
    config_id: str,
    current_user: dict = Depends(get_current_user),
    body: dict = Body(...)
):
    """更新模型配置"""
    model_data = {
        "name": body.get("name", ""),
        "api_url": body.get("api_url", ""),
        "api_key": body.get("api_key", ""),
        "model_id": body.get("model_id", ""),
        "daily_token_limit": body.get("daily_token_limit", 100000),
        "daily_call_limit": body.get("daily_call_limit", 1000),
        "is_default_model": body.get("is_default_model", 0),
        "priority": body.get("priority", 0),
    }
    db_update_model(config_id, model_data)
    return {"message": "更新成功"}


@admin_router.delete("/models/{config_id}")
async def delete_model_endpoint(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除模型配置"""
    db_delete_model(config_id)
    return {"message": "删除成功"}


@admin_router.put("/models/{config_id}/set-default")
async def set_default_model(
    config_id: str,
    current_user: dict = Depends(get_current_user)
):
    """设置默认模型"""
    model = get_model_by_config_id(config_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    db_update_model(config_id, {**model, "is_default_model": 1})
    return {"message": "默认模型已设置"}


# ========== API Key 管理端点 ==========

@admin_router.get("/keys")
async def list_keys(current_user: dict = Depends(get_current_user)):
    """列出所有 API Key"""
    keys = get_all_api_keys()
    return {"keys": keys}


@admin_router.post("/keys")
async def create_key_endpoint(
    current_user: dict = Depends(get_current_user),
    body: dict = Body(...)
):
    """创建 API Key（仅此一次返回完整 key）"""
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name 为必填字段")
    result = db_create_api_key(name)
    return {"message": "创建成功", "key": result}


@admin_router.delete("/keys/{key_id}")
async def delete_key_endpoint(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除（软删除）API Key"""
    db_delete_api_key(key_id)
    return {"message": "删除成功"}


# ========== 统计端点 ==========

@admin_router.get("/stats/daily")
async def daily_stats(current_user: dict = Depends(get_current_user)):
    """每日统计（api_key 脱敏）"""
    stats = get_daily_stats()
    for s in stats:
        # 统计数据不含 api_key，但保留脱敏逻辑以防字段扩展
        if "api_key" in s:
            s["api_key"] = mask_api_key(s["api_key"])
    return {"stats": stats}


@admin_router.get("/stats/call-logs")
async def call_logs(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """调用日志（分页）"""
    logs = get_call_logs(limit=limit, offset=offset)
    return {"logs": logs, "limit": limit, "offset": offset}


# ========== 系统配置端点 ==========

@admin_router.get("/system/auto-switch")
async def get_auto_switch(current_user: dict = Depends(get_current_user)):
    """获取自动切换状态"""
    enabled = get_auto_switch_status()
    return {"enabled": enabled}


@admin_router.put("/system/auto-switch")
async def set_auto_switch(
    current_user: dict = Depends(get_current_user),
    body: dict = Body(...)
):
    """设置自动切换"""
    enabled = body.get("enabled")
    if enabled is None:
        raise HTTPException(status_code=400, detail="enabled 为必填字段")
    set_auto_switch_status(bool(enabled))
    return {"message": "设置成功", "enabled": bool(enabled)}


# ========== Excel 导入导出端点 ==========

# 中英文列名映射
COLUMN_MAPPING = {
    'name': ['模型名称', 'name', 'Name'],
    'api_url': ['API地址', 'api_url', 'API URL', 'api url'],
    'api_key': ['API密钥', 'api_key', 'API Key', 'api key'],
    'model_id': ['Model ID', 'model_id', 'model id', 'ModelId'],
    'daily_token_limit': ['每日Token上限', 'daily_token_limit', 'Token Limit'],
    'daily_call_limit': ['每日调用上限', 'daily_call_limit', 'Call Limit'],
    'priority': ['优先级', 'priority', 'Priority']
}

EXPORT_COLUMNS = ['name', 'api_url', 'api_key', 'model_id', 'daily_token_limit',
                  'daily_call_limit', 'priority', 'is_active', 'is_default_model']
EXPORT_COLUMN_NAMES = ['模型名称', 'API地址', 'API密钥', 'Model ID', '每日Token上限',
                       '每日调用上限', '优先级', '是否启用', '是否默认']


@admin_router.get("/config/export-excel")
async def export_excel(current_user: dict = Depends(get_current_user)):
    """导出模型配置为 Excel 文件"""
    models = get_all_models()
    if not models:
        raise HTTPException(status_code=404, detail="无模型配置可导出")
    df = pd.DataFrame(models)
    df_export = df[EXPORT_COLUMNS].copy()
    df_export.columns = EXPORT_COLUMN_NAMES

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='模型配置')
    output.seek(0)

    today = date_type.today().isoformat()
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=models_export_{today}.xlsx"}
    )


@admin_router.post("/config/import-excel")
async def import_excel(
    current_user: dict = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """导入 Excel 批量创建模型"""
    # 校验文件类型
    filename = file.filename or ""
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="仅支持 xlsx/xls 格式文件")

    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))

    # 构建列名映射
    col_map = {}
    for key, possible_names in COLUMN_MAPPING.items():
        for col in df.columns:
            if col in possible_names:
                col_map[key] = col
                break

    # 必须列检查
    missing = [k for k in ('name', 'api_url', 'api_key') if k not in col_map]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Excel 文件缺少必要的列（{', '.join(missing)}）"
        )

    success_count = 0
    for _, row in df.iterrows():
        try:
            name = str(row.get(col_map['name'], '')).strip()
            api_url = str(row.get(col_map['api_url'], '')).strip()
            api_key = str(row.get(col_map['api_key'], '')).strip()
            if not name or not api_url or not api_key:
                continue
            model_data = {
                "name": name,
                "api_url": api_url,
                "api_key": api_key,
                "model_id": str(row.get(col_map.get('model_id', ''), '')),
                "daily_token_limit": int(row.get(col_map.get('daily_token_limit', 'daily_token_limit'), 100000)),
                "daily_call_limit": int(row.get(col_map.get('daily_call_limit', 'daily_call_limit'), 1000)),
                "priority": int(row.get(col_map.get('priority', 'priority'), 0)),
            }
            db_create_model(model_data)
            success_count += 1
        except Exception:
            continue

    return {"message": "导入成功", "count": success_count}
