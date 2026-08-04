"""认证依赖项"""
import ipaddress
import re
import socket
import sqlite3
from urllib.parse import urlparse

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import ALLOWED_PROXY_DOMAINS, DB_PATH
from app.utils.auth import get_password_hash, verify_token

# HTTP Bearer Token
http_bearer = HTTPBearer(auto_error=False)

# API Key Header
API_KEY_PATTERN = re.compile(r'^[a-f0-9]{64}$')
api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


def _is_private_ip(ip: str) -> bool:
    """判断 IP 是否为私网/链路本地/保留地址 (回环地址放行, 支持本地模型服务)"""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if addr.is_loopback:
        return False
    if addr.is_private or addr.is_link_local or addr.is_multicast:
        return True
    # CGNAT 共享地址空间 100.64.0.0/10 不标记为 private, 需显式拦截
    if isinstance(addr, ipaddress.IPv4Address):
        first = int(addr) >> 24
        if first == 100:
            return True
        # IPv4 保留/未分配块由 is_reserved 覆盖, 但 0.0.0.0 已放行, 其余保守拒绝
        return addr.is_reserved or addr.is_global is False
    return addr.is_reserved


def is_allowed_proxy_host(host: str) -> bool:
    """判断域名是否命中 ALLOWED_PROXY_DOMAINS 白名单。

    支持 `*.example.com` 通配前缀匹配任意子域名（含裸域本身）。
    未配置白名单时返回 False。大小写不敏感。
    """
    if not host or not ALLOWED_PROXY_DOMAINS:
        return False
    host = host.rstrip('.').lower()
    allowed = [d.rstrip('.').lower() for d in ALLOWED_PROXY_DOMAINS]
    if host in allowed:
        return True
    for d in allowed:
        if d.startswith('*.'):
            suffix = d[1:]  # 去掉 '*'
            if host == suffix.lstrip('.'):
                return True
            if host.endswith(suffix) and host != suffix.lstrip('.'):
                return True
    return False


def validate_public_endpoint(endpoint: str) -> bool:
    """SSRF 防护：校验 URL 的 host 不得解析到内网/云元数据等敏感地址。

    - 返回 False 表示不安全（私网/链路本地/保留地址或无法解析）
    - 回环地址 (127.0.0.1 / localhost) 放行, 支持本地 LLM 测试
    - 命中 ALLOWED_PROXY_DOMAINS 白名单的域名直接放行（供自建内网模型服务）
    """
    if not endpoint:
        return False
    parsed = urlparse(endpoint)
    host = parsed.hostname
    if not host:
        return False
    host = host.rstrip('.').lower()
    if is_allowed_proxy_host(host):
        return True
    if host in ('localhost', '127.0.0.1', '::1'):
        return True
    # 字面 IP 直接判断
    if re.match(r'^[0-9a-fA-F:.]+$', host):
        return not _is_private_ip(host)
    # 域名: 解析所有 A/AAAA 记录, 任一命中私网即拒绝
    try:
        addrs = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except (socket.gaierror, OSError):
        return False
    ips = {info[4][0] for info in addrs}
    if not ips:
        return False
    return not any(_is_private_ip(ip) for ip in ips)


def _verify_api_key_in_db(api_key: str) -> bool:
    """从数据库验证 API Key 是否存在、活跃且未过期"""
    key_hash = get_password_hash(api_key)
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            row = conn.execute(
                "SELECT id FROM api_keys WHERE key_hash = ? AND is_active = 1 "
                "AND (expires_at IS NULL OR expires_at > datetime('now'))",
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
