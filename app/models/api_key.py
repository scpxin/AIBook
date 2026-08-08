"""API Key 数据模型"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class APIKeyBase(BaseModel):
    """API Key 基础模型"""
    name: str = Field(..., min_length=1, max_length=64, description="密钥名称")
    description: str = Field('', max_length=256, description="密钥描述")


class APIKeyCreate(APIKeyBase):
    """创建 API Key 请求"""
    pass


class APIKey(APIKeyBase):
    """API Key 响应模型"""
    id: int
    key_hash: str
    is_active: bool = True
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class APIKeyInDB(APIKey):
    """数据库中的 API Key"""
    key_hash: str
    user_id: int | None = None
    permissions: list[str] = Field(default_factory=lambda: ['read'])
    raw_key: str | None = Field(default=None, description="创建时返回的原始密钥，仅显示一次")
