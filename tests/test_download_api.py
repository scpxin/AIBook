import pytest
from app.api.download import router
from app.config import ALLOWED_PROXY_DOMAINS


class TestDownloadApiSecurity:
    def test_router_exists(self):
        assert router is not None

    def test_allowed_proxy_domains_default_empty(self):
        import os
        domains = os.environ.get('ALLOWED_PROXY_DOMAINS', '').split(',')
        empty_result = [d for d in domains if d]
        assert len(empty_result) == 0
