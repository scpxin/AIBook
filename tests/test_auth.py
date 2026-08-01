"""API Key 管理与认证测试"""
import os
import time
from datetime import timedelta

import pytest
from datetime import timedelta

from app.config import DB_PATH
from app.models.api_key import APIKeyCreate
from app.services.api_key_service import APIKeyService
from app.utils.auth import (
    create_access_token,
    decode_token,
    generate_api_key,
    get_password_hash,
    validate_api_key_format,
    verify_password,
    verify_token,
)


@pytest.fixture(scope="module")
def test_db(tmp_path_factory):
    """隔离的测试数据库"""
    db_path = str(tmp_path_factory.mktemp("auth") / "api_keys.db")
    return db_path


@pytest.fixture(scope="module")
def api_key_service(test_db):
    """API Key 服务实例"""
    return APIKeyService(test_db)


@pytest.fixture(scope="module")
def created_key(api_key_service):
    """预先创建的 API Key"""
    return api_key_service.create(APIKeyCreate(name="测试密钥", description="集成测试"))


@pytest.fixture(scope="module")
def auth_token():
    """有效的 JWT Token"""
    return create_access_token({"sub": "tester", "role": "admin"})


class TestPasswordHash:
    def test_hash_roundtrip(self):
        """密码哈希往返验证"""
        hashed = get_password_hash("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed)

    def test_wrong_password(self):
        """错误密码验证失败"""
        hashed = get_password_hash("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_deterministic(self):
        """相同密码生成相同哈希"""
        assert get_password_hash("abc") == get_password_hash("abc")

    def test_hash_different_for_different_input(self):
        """不同密码生成不同哈希"""
        assert get_password_hash("abc") != get_password_hash("abd")


class TestAPIKeyFormat:
    def test_valid_key(self):
        """有效 API Key (64 位十六进制)"""
        assert validate_api_key_format(generate_api_key())

    def test_too_short(self):
        """过短密钥无效"""
        assert not validate_api_key_format("abc")

    def test_too_long(self):
        """过长密钥无效"""
        assert not validate_api_key_format("f" * 65)

    def test_non_hex(self):
        """非十六进制字符无效"""
        assert not validate_api_key_format("g" * 64)

    def test_generate_unique(self):
        """生成的密钥唯一"""
        assert generate_api_key() != generate_api_key()


class TestJWTAuth:
    def test_create_and_decode(self):
        """JWT 创建与解码"""
        token = create_access_token({"sub": "user1"})
        payload = decode_token(token)
        assert payload["sub"] == "user1"

    def test_verify_valid_token(self):
        """有效令牌通过验证"""
        token = create_access_token({"sub": "user1"})
        assert verify_token(token) is not None

    def test_verify_expired_token(self):
        """过期令牌验证失败"""
        token = create_access_token(
            {"sub": "user1"},
            expires_delta=timedelta(seconds=-1),
        )
        assert verify_token(token) is None

    def test_verify_tampered_token(self):
        """篡改令牌验证失败"""
        token = create_access_token({"sub": "user1"})
        tampered = token[:-5] + "xxxxx"
        assert verify_token(tampered) is None

    def test_verify_empty_token(self):
        """空令牌验证失败"""
        assert verify_token("") is None

    def test_verify_garbage_token(self):
        """垃圾令牌验证失败"""
        assert verify_token("not.a.jwt") is None


class TestAPIKeyService:
    def test_create_returns_raw_key(self, api_key_service):
        """创建返回原始密钥"""
        key = api_key_service.create(APIKeyCreate(name="临时", description=""))
        assert key.raw_key is not None
        assert len(key.raw_key) == 64

    def test_get_by_id(self, api_key_service, created_key):
        """按 ID 获取"""
        found = api_key_service.get_by_id(created_key.id)
        assert found is not None
        assert found.name == "测试密钥"

    def test_get_by_id_not_found(self, api_key_service):
        """不存在的 ID 返回 None"""
        assert api_key_service.get_by_id(99999) is None

    def test_list_all(self, api_key_service, created_key):
        """列出所有密钥"""
        keys = api_key_service.list_all()
        assert any(k.id == created_key.id for k in keys)

    def test_list_all_masks_hash(self, api_key_service, created_key):
        """列表中的哈希被脱敏"""
        keys = api_key_service.list_all()
        target = next(k for k in keys if k.id == created_key.id)
        assert "..." in target.key_hash

    def test_revoke(self, api_key_service, created_key):
        """撤销密钥"""
        assert api_key_service.revoke(created_key.id)
        revoked = api_key_service.get_by_id(created_key.id)
        assert revoked is not None
        assert not revoked.is_active

    def test_revoke_not_found(self, api_key_service):
        """撤销不存在的密钥返回 False"""
        assert not api_key_service.revoke(99999)

    def test_list_active_only(self, api_key_service):
        """仅列出活跃密钥"""
        keys = api_key_service.list_all(active_only=True)
        assert all(k.is_active for k in keys)


class TestAPIKeyEndpoints:
    def test_create_without_auth(self, client):
        """无认证创建密钥返回 401"""
        response = client.post("/api/api-keys", json={"name": "无认证"})
        assert response.status_code == 401

    def test_list_without_auth(self, client):
        """无认证列出密钥返回 401"""
        response = client.get("/api/api-keys")
        assert response.status_code == 401

    def test_create_with_token(self, client, auth_token):
        """带 Token 创建密钥"""
        response = client.post(
            "/api/api-keys",
            json={"name": "授权创建", "description": "带 Token"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        assert "raw_key" in response.json()

    def test_list_with_token(self, client, auth_token):
        """带 Token 列出密钥"""
        response = client.get(
            "/api/api-keys",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_with_token(self, client, auth_token):
        """带 Token 获取密钥详情"""
        service = APIKeyService(DB_PATH)
        key = service.create(APIKeyCreate(name="详情", description=""))
        response = client.get(
            f"/api/api-keys/{key.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "详情"

    def test_get_not_found(self, client, auth_token):
        """获取不存在的密钥返回 404"""
        response = client.get(
            "/api/api-keys/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    def test_revoke_with_token(self, client, auth_token):
        """带 Token 撤销密钥"""
        service = APIKeyService(DB_PATH)
        key = service.create(APIKeyCreate(name="待撤销", description=""))
        response = client.delete(
            f"/api/api-keys/{key.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204
        assert not service.get_by_id(key.id).is_active

    def test_invalid_token(self, client):
        """无效 Token 返回 401"""
        response = client.get(
            "/api/api-keys",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


class TestAPIKeyAuthentication:
    """API Key 数据库校验 (Bearer 之外的 X-API-Key 认证路径)"""

    def test_valid_api_key_allows_access(self, client):
        """数据库中存在的活跃密钥可通过认证"""
        service = APIKeyService(DB_PATH)
        key = service.create(APIKeyCreate(name="认证测试", description=""))
        assert key.raw_key

        response = client.get(
            "/api/api-keys",
            headers={"X-API-Key": key.raw_key},
        )
        assert response.status_code == 200

    def test_invalid_format_api_key_rejected(self, client):
        """格式错误的密钥被拒绝"""
        response = client.get(
            "/api/api-keys",
            headers={"X-API-Key": "short"},
        )
        assert response.status_code == 401

    def test_nonexistent_api_key_rejected(self, client):
        """未注册的密钥被拒绝"""
        fake_key = "a" * 64
        response = client.get(
            "/api/api-keys",
            headers={"X-API-Key": fake_key},
        )
        assert response.status_code == 401

    def test_revoked_api_key_rejected(self, client):
        """已撤销的密钥被拒绝"""
        service = APIKeyService(DB_PATH)
        key = service.create(APIKeyCreate(name="待撤销认证", description=""))
        service.revoke(key.id)

        response = client.get(
            "/api/api-keys",
            headers={"X-API-Key": key.raw_key},
        )
        assert response.status_code == 401
