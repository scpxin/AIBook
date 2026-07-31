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
API_KEY_SALT = os.environ.get('API_KEY_SALT', 'novel-creator-api-key-salt')


def get_api_key_secret() -> str:
    """获取 JWT 签名密钥 (从环境变量或生成默认值)"""
    secret = os.environ.get('API_KEY_SECRET', '')
    if not secret:
        # 使用环境变量生成确定性密钥
        default_secret = os.environ.get('DATABASE_PATH', '/app/data/fanqie.db')
        secret = hashlib.sha256(default_secret.encode()).hexdigest()
    return secret


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 (常量时间比较)"""
    return hmac.compare_digest(
        get_password_hash(plain_password),
        hashed_password,
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希 (SHA-256 + salt)"""
    return hashlib.sha256(f"{API_KEY_SALT}:{password}".encode()).hexdigest()


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
