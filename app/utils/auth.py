"""API 认证授权模块

功能:
- JWT Token 认证
- API Key 管理
- 用户角色权限
"""
import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta

from jose import JWTError, jwt

# 配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# API Key 存储时使用 SHA-256 加盐哈希
API_KEY_SALT = os.environ.get('API_KEY_SALT', '')


def _require_configured(env_name: str) -> str:
    """读取必须配置的环境变量，缺失时返回空 (调用方负责拒绝/降级)"""
    return os.environ.get(env_name, '')


def get_api_key_secret() -> str:
    """获取 JWT 签名密钥 (必须从环境变量配置，禁止使用可预测的默认值)"""
    secret = os.environ.get('API_KEY_SECRET', '')
    if not secret:
        raise RuntimeError(
            "API_KEY_SECRET 未配置：JWT 认证需要强随机密钥，请在环境变量中设置 (如 python3 -c \"import secrets; print(secrets.token_urlsafe(64))\")"
        )
    return secret


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 (常量时间比较)"""
    return hmac.compare_digest(
        get_password_hash(plain_password),
        hashed_password,
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希 (SHA-256 + salt) — 需配置 API_KEY_SALT"""
    salt = os.environ.get('API_KEY_SALT', '')
    if not salt:
        raise RuntimeError("API_KEY_SALT 未配置：API Key 哈希需要强随机盐，请在环境变量中设置")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_api_key_secret(), algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_api_key_secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码令牌"""
    try:
        payload = jwt.decode(token, get_api_key_secret(), algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> dict | None:
    """验证令牌是否有效"""
    payload = decode_token(token)
    if payload and 'exp' in payload and payload['exp'] > time.time():
        return payload
    return None


def generate_api_key() -> str:
    """生成随机 API Key"""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def validate_api_key_format(api_key: str) -> bool:
    """验证 API Key 格式 (64 字符十六进制)"""
    if len(api_key) != 64:
        return False
    try:
        int(api_key, 16)
        return True
    except ValueError:
        return False
