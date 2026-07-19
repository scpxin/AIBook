from novel_creator.ai_client import AIClient


class TestAIClient:
    def test_init_defaults(self):
        client = AIClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.model == "gpt-4o-mini"
        assert client.temperature == 0.7
        assert client.max_tokens == 4000
        assert client.timeout == 600

    def test_init_custom(self):
        client = AIClient(
            api_key="key123",
            base_url="https://api.longcat.chat/openai",
            model="LongCat-2.0",
            temperature=0.5,
            max_tokens=2000,
            timeout=120
        )
        assert client.model == "LongCat-2.0"
        assert client.temperature == 0.5
        assert client.max_tokens == 2000
        assert client.timeout == 120

    def test_build_request_with_chat_completions_url(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1/chat/completions")
        req = client._build_request({"model": "gpt-4", "messages": []})
        assert req.full_url == "https://api.example.com/v1/chat/completions"
        assert req.get_header("Content-type") == "application/json"
        assert req.get_header("Authorization") == "Bearer k"

    def test_build_request_with_v1_base(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1")
        req = client._build_request({"model": "gpt-4", "messages": []})
        assert req.full_url == "https://api.example.com/v1/chat/completions"

    def test_build_request_with_custom_base(self):
        client = AIClient(api_key="k", base_url="https://api.longcat.chat/openai")
        req = client._build_request({"model": "gpt-4", "messages": []})
        assert req.full_url == "https://api.longcat.chat/openai/v1/chat/completions"

    def test_build_messages_with_system_prompt(self):
        client = AIClient(api_key="k")
        msgs = client._build_messages("hello", "you are helpful")
        assert len(msgs) == 2
        assert msgs[0] == {"role": "system", "content": "you are helpful"}
        assert msgs[1] == {"role": "user", "content": "hello"}

    def test_build_messages_without_system_prompt(self):
        client = AIClient(api_key="k")
        msgs = client._build_messages("hello", None)
        assert len(msgs) == 1
        assert msgs[0] == {"role": "user", "content": "hello"}

    def test_clean_error_body(self):
        client = AIClient(api_key="k")
        result = client._clean_error_body("<html><body>Error</body></html>")
        assert result == "Error"

    def test_clean_error_body_truncates_long(self):
        client = AIClient(api_key="k")
        long_text = "x" * 300
        result = client._clean_error_body(long_text)
        assert len(result) == 200

    def test_generate_error_returns_error_tuple(self):
        client = AIClient(api_key="k", base_url="http://127.0.0.1:19999")
        content, error = client.generate("test")
        assert content is None
        assert error is not None

    def test_ssl_verify_flag_defaults_to_true(self, monkeypatch):
        monkeypatch.delenv("AI_VERIFY_SSL", raising=False)
        import importlib

        import novel_creator.ai_client as ac
        importlib.reload(ac)
        assert ac._ssl_context.check_hostname is True

    def test_ssl_verify_flag_false(self, monkeypatch):
        monkeypatch.setenv("AI_VERIFY_SSL", "false")
        import importlib

        import novel_creator.ai_client as ac
        importlib.reload(ac)
        assert ac._ssl_context.check_hostname is False
        assert ac._ssl_context.verify_mode == ac.ssl.CERT_NONE
        monkeypatch.delenv("AI_VERIFY_SSL", raising=False)
        importlib.reload(ac)


class TestAIClientEndpoint:
    def test_base_url_trailing_slash_stripped(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1/")
        assert client.base_url == "https://api.example.com/v1"

    def test_base_url_no_trailing_slash_preserved(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1")
        assert client.base_url == "https://api.example.com/v1"
