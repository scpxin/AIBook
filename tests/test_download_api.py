from unittest.mock import patch

import pytest

from app.api.download import ALLOWED_HOSTS, router


class TestDownloadApiSecurity:
    def test_router_exists(self):
        assert router is not None

    def test_allowed_proxy_domains_default_empty(self):
        import os
        domains = os.environ.get('ALLOWED_PROXY_DOMAINS', '').split(',')
        empty_result = [d for d in domains if d]
        assert len(empty_result) == 0


class TestHttpGetHostWhitelist:
    def test_allowed_hosts_contains_expected(self):
        assert 'novel.snssdk.com' in ALLOWED_HOSTS
        assert 'fanqienovel.com' in ALLOWED_HOSTS
        assert 'localhost' in ALLOWED_HOSTS
        assert '127.0.0.1' in ALLOWED_HOSTS

    def test_allowed_host_passes(self):
        from app.api.download import _http_get
        with patch("urllib.request.urlopen") as mock_open, patch("app.api.download.HTTP_TIMEOUT", 5):
            mock_open.return_value.__enter__.return_value.read.return_value = b"{}"
            data = _http_get("https://novel.snssdk.com/api/test")
            assert data == b"{}"

    def test_disallowed_host_blocked(self):
        from app.api.download import _http_get
        with patch("urllib.request.urlopen") as mock_open, patch("app.api.download.HTTP_TIMEOUT", 5):
            with pytest.raises(ValueError, match="SSRF blocked"):
                _http_get("http://192.168.1.1/v1")

    def test_localhost_allowed(self):
        from app.api.download import _http_get
        with patch("urllib.request.urlopen") as mock_open, patch("app.api.download.HTTP_TIMEOUT", 5):
            mock_open.return_value.__enter__.return_value.read.return_value = b"{}"
            data = _http_get("http://localhost:5000/api/content?item_id=1")
            assert data == b"{}"

    def test_ipv6_host_parsing(self):
        """host 提取使用 hostname, 正确处理 IPv6"""
        from app.api.download import _http_get
        with patch("urllib.request.urlopen") as mock_open, patch("app.api.download.HTTP_TIMEOUT", 5):
            mock_open.return_value.__enter__.return_value.read.return_value = b"{}"
            data = _http_get("http://[::1]:8000/api/health")
            assert data == b"{}"
