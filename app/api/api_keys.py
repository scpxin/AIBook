"""API Key 管理接口"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import DB_PATH
from app.models.api_key import APIKey, APIKeyCreate, APIKeyInDB
from app.services.api_key_service import get_api_key_service
from app.utils.security import get_current_user, require_auth

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])
logger = logging.getLogger(__name__)


async def require_auth_or_bootstrap(
    current_user: str | None = Depends(get_current_user),  # noqa: B008
) -> str:
    """bootstrap 模式: 数据库无活跃 Key 时允许匿名创建首个 Key (解决引导死锁)。

    一旦存在活跃 Key, 立即恢复强制认证, 防止匿名滥用。
    """
    if current_user:
        return current_user
    service = get_api_key_service(DB_PATH)
    if not service.list_all(active_only=True):
        return "bootstrap"
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未认证或认证失败",
        headers={"WWW-Authenticate": "Bearer, API-Key"},
    )


@router.post("", response_model=APIKeyInDB, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    current_user: str = Depends(require_auth_or_bootstrap),  # noqa: B008
):
    """创建新的 API Key

    - **name**: 密钥名称 (必需)
    - **description**: 密钥描述 (可选)

    - 数据库无活跃 Key 时允许匿名创建首个密钥 (引导模式)
    - 存在活跃 Key 后必须携带 Bearer Token 或有效 API Key

    响应中包含 `raw_key` 字段，这是完整的 API Key，**仅显示一次**,请妥善保存。
    """
    service = get_api_key_service(DB_PATH)
    api_key = service.create(data, expires_days=None)

    logger.info(f"用户 {current_user} 创建了新的 API Key: {api_key.name}")
    return api_key


@router.get("", response_model=list[APIKey])
async def list_api_keys(
    active_only: bool = False,
    current_user: str = Depends(require_auth),
):
    """列出所有 API Key

    - **active_only**: 仅列出活跃的密钥
    """
    service = get_api_key_service(DB_PATH)
    return service.list_all(active_only=active_only)


@router.get("/{key_id}", response_model=APIKey)
async def get_api_key(
    key_id: int,
    current_user: str = Depends(require_auth),
):
    """获取指定 API Key 详情"""
    service = get_api_key_service(DB_PATH)
    api_key = service.get_by_id(key_id)

    if not api_key:
        raise HTTPException(status_code=404, detail="API Key 不存在")

    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: str = Depends(require_auth),
):
    """撤销 API Key

    撤销后的密钥将无法继续用于认证。
    """
    service = get_api_key_service(DB_PATH)

    if not service.get_by_id(key_id):
        raise HTTPException(status_code=404, detail="API Key 不存在")

    service.revoke(key_id)
    logger.info(f"用户 {current_user} 撤销了 API Key #{key_id}")
