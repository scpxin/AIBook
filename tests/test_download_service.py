"""下载服务并发限制测试"""
import threading
from unittest.mock import patch

import pytest

from app.services import download_service


class TestDownloadConcurrencyLimit:
    def test_exceeds_max_concurrent_rejected(self):
        """超过并发上限时拒绝创建新会话"""
        fake_sessions = {
            f"sid{i}": {"status": "downloading"}
            for i in range(download_service.MAX_CONCURRENT_DOWNLOADS)
        }
        with patch("app.services.download_service.sessions", fake_sessions), \
             patch("app.services.download_service.sessions_lock", threading.RLock()), \
             patch("os.path.exists", return_value=False):
            with pytest.raises(ValueError, match="下载会话过多"):
                download_service.create_download("123", "测试")

    def test_under_limit_creates_session(self):
        """低于上限时正常创建会话"""
        fake_sessions = {"sid1": {"status": "done"}}
        with patch("app.services.download_service.sessions", fake_sessions), \
             patch("app.services.download_service.sessions_lock", threading.RLock()), \
             patch("os.path.exists", return_value=False), \
             patch("app.services.download_service._download_worker"):
            sid = download_service.create_download("123", "测试")
            assert sid
            assert len(fake_sessions) == 2

    def test_done_sessions_do_not_count(self):
        """已完成/暂停的会话不计入并发数"""
        fake_sessions = {
            f"sid{i}": {"status": "done" if i % 2 else "paused"}
            for i in range(download_service.MAX_CONCURRENT_DOWNLOADS * 2)
        }
        with patch("app.services.download_service.sessions", fake_sessions), \
             patch("app.services.download_service.sessions_lock", threading.RLock()), \
             patch("os.path.exists", return_value=False), \
             patch("app.services.download_service._download_worker"):
            sid = download_service.create_download("456", "测试")
            assert sid
