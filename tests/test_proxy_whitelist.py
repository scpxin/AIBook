"""ALLOWED_PROXY_DOMAINS 白名单匹配测试"""
from unittest.mock import patch

from app.utils.security import is_allowed_proxy_host, validate_public_endpoint


class TestIsAllowedProxyHost:
    def test_empty_whitelist_returns_false(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", []):
            assert is_allowed_proxy_host("api.example.com") is False

    def test_exact_match(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["api.example.com"]):
            assert is_allowed_proxy_host("api.example.com") is True

    def test_case_insensitive(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["API.Example.COM"]):
            assert is_allowed_proxy_host("api.example.com") is True

    def test_wildcard_matches_subdomain(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["*.example.com"]):
            assert is_allowed_proxy_host("sub.example.com") is True
            assert is_allowed_proxy_host("a.b.example.com") is True
            assert is_allowed_proxy_host("example.com") is True

    def test_wildcard_rejects_other_domain(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["*.example.com"]):
            assert is_allowed_proxy_host("example.org") is False
            assert is_allowed_proxy_host("evil-example.com") is False

    def test_trailing_dot_normalized(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["api.example.com"]):
            assert is_allowed_proxy_host("api.example.com.") is True


class TestValidatePublicEndpointWhitelist:
    def test_whitelisted_private_host_passes(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["internal.llm.local"]):
            assert validate_public_endpoint("http://internal.llm.local/v1") is True

    def test_non_whitelisted_private_host_rejected(self):
        with patch("app.utils.security.ALLOWED_PROXY_DOMAINS", ["internal.llm.local"]):
            assert validate_public_endpoint("http://other.llm.local/v1") is False
