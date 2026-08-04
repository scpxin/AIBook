"""AIClient 全局 AI 并发信号量测试"""
import threading
from unittest.mock import patch

from novel_creator import ai_client as ai_client_module


class TestAISemaphore:
    def test_semaphore_initialized(self):
        assert isinstance(ai_client_module._ai_semaphore, threading.BoundedSemaphore)
        assert ai_client_module.MAX_AI_CONCURRENCY == 10
        assert ai_client_module._AI_SEMAPHORE_TIMEOUT > 0

    def test_generate_releases_semaphore_on_success(self):
        sem = threading.BoundedSemaphore(1)
        with patch.object(ai_client_module, "_ai_semaphore", sem):
            client = ai_client_module.AIClient(
                api_key="test-key", base_url="http://localhost:9999/v1", timeout=5
            )
            with patch.object(client, "_client") as mock_http:
                mock_http.post.return_value.raise_for_status.return_value = None
                mock_http.post.return_value.json.return_value = {
                    "choices": [{"message": {"content": "ok"}}]
                }
                content, err = client.generate("hello")
            assert content == "ok"
            assert err is None
            assert sem._value == 1

    def test_generate_stream_releases_semaphore(self):
        sem = threading.BoundedSemaphore(1)
        with patch.object(ai_client_module, "_ai_semaphore", sem):
            client = ai_client_module.AIClient(
                api_key="test-key", base_url="http://localhost:9999/v1", timeout=5
            )
            with patch.object(client, "_client") as mock_http:
                mock_stream = mock_http.stream.return_value.__enter__.return_value
                mock_stream.iter_lines.return_value = []
                chunks = list(client.generate_stream("hello"))
            assert chunks == []
            assert sem._value == 1

    def test_generate_error_path_releases_semaphore(self):
        sem = threading.BoundedSemaphore(1)
        with patch.object(ai_client_module, "_ai_semaphore", sem):
            client = ai_client_module.AIClient(
                api_key="test-key", base_url="http://localhost:9999/v1", timeout=5
            )
            with patch.object(client, "_client") as mock_http:
                mock_http.post.side_effect = Exception("boom")
                content, err = client.generate("hello")
            assert content is None
            assert "boom" in err
            assert sem._value == 1

    def test_saturated_semaphore_returns_error(self):
        sem = threading.BoundedSemaphore(1)
        with patch.object(ai_client_module, "_ai_semaphore", sem):
            with patch.object(sem, "acquire", return_value=False):
                client = ai_client_module.AIClient(
                    api_key="test-key", base_url="http://localhost:9999/v1", timeout=5
                )
                content, err = client.generate("hello")
            assert content is None
            assert "并发" in err

    def test_stream_saturated_returns_error(self):
        sem = threading.BoundedSemaphore(1)
        with patch.object(ai_client_module, "_ai_semaphore", sem):
            with patch.object(sem, "acquire", return_value=False):
                client = ai_client_module.AIClient(
                    api_key="test-key", base_url="http://localhost:9999/v1", timeout=5
                )
                chunks = list(client.generate_stream("hello"))
            assert len(chunks) > 0
            assert chunks[0].get("error") and "并发" in chunks[0]["error"]
