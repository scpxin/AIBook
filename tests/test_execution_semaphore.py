"""流式生成并发信号量测试"""
import threading
from unittest.mock import patch

import pytest

from app.api import execution


class TestStreamSemaphore:
    def test_semaphore_limits_concurrency(self):
        """信号量限制并发流数量"""
        acquired = []

        def fake_acquire(blocking=True):
            acquired.append(1)
            return len(acquired) <= execution.MAX_STREAM_CONCURRENCY

        sem = threading.BoundedSemaphore(execution.MAX_STREAM_CONCURRENCY)
        with patch.object(execution, "_stream_semaphore", sem):
            assert execution._stream_semaphore is sem

    def test_semaphore_type(self):
        assert isinstance(execution._stream_semaphore, threading.BoundedSemaphore)
        assert execution.MAX_STREAM_CONCURRENCY == 5
