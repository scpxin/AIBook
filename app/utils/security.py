"""认证依赖项"""
import re
import sqlite3

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import DB_PATH
from app.utils.auth import get_password_hash, verify_token

# HTTP Bearer Token
http_bearer = HTTPBearer(auto_error=False)

# API Key Header
API_KEY_PATTERN = re.compile(r'^[a-f0-9]{64}$')
api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


def _verify_api_key_in_db(api_key: str) -> bool:
    """从数据库验证 API Key 是否存在且活跃"""
    key_hash = get_password_hash(api_key)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            row = conn.execute(
                "SELECT id FROM api_keys WHERE key_hash = ? AND is_active = 1",
                (key_hash,),
            ).fetchone()
        finally:
            conn.close()
        return row is not None
    except sqlite3.Error:
        return False


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),  # noqa: B008
) -> dict | None:
    """从 Bearer Token 获取当前用户"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        return None

    return payload


async def get_current_user_from_api_key(
    api_key: str | None = Depends(api_key_header)  # noqa: B008
) -> str | None:
    """从 API Key 获取用户标识 (验证密钥存在于数据库且活跃)"""
    if not api_key or not API_KEY_PATTERN.match(api_key):
        return None

    if not _verify_api_key_in_db(api_key):
        return None

    return f"api_key:{api_key[:8]}"


async def get_current_user(
    bearer_user: dict | None = Depends(get_current_user_from_token),  # noqa: B008
    api_key_user: str | None = Depends(get_current_user_from_api_key),  # noqa: B008
) -> str | None:
    """获取当前用户 (支持 Bearer Token 和 API Key 两种方式)"""
    if bearer_user:
        return bearer_user.get('sub') or bearer_user.get('username')
    if api_key_user:
        return api_key_user
    return None


def require_auth(current_user: str | None = Depends(get_current_user)) -> str:
    """要求认证"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证或认证失败",
            headers={"WWW-Authenticate": "Bearer, API-Key"},
        )
    return current_user


def require_admin(current_user: str = Depends(require_auth)) -> str:
    """要求管理员权限"""
    # TODO: 检查用户角色
    # if not user_is_admin(current_user):
    #     raise HTTPException(status_code=403, detail="权限不足")
    return current_user
