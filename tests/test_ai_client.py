from novel_creator.ai_client import AIClient


class TestAIClient:
    def test_init_defaults(self):
        client = AIClient(api_key="test-key")
        try:
            assert client.api_key == "test-key"
            assert client.base_url == "https://api.openai.com/v1"
            assert client.model == "gpt-4o-mini"
            assert client.temperature == 0.7
            assert client.max_tokens == 4000
            assert client.timeout == 600
        finally:
            client.close()

    def test_init_custom(self):
        client = AIClient(
            api_key="key123",
            base_url="https://api.longcat.chat/openai",
            model="LongCat-2.0",
            temperature=0.5,
            max_tokens=2000,
            timeout=120
        )
        try:
            assert client.model == "LongCat-2.0"
            assert client.temperature == 0.5
            assert client.max_tokens == 2000
            assert client.timeout == 120
        finally:
            client.close()

    def test_build_url_with_chat_completions_url(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1/chat/completions")
        try:
            assert client._build_url() == "https://api.example.com/v1/chat/completions"
        finally:
            client.close()

    def test_build_url_with_v1_base(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1")
        try:
            assert client._build_url() == "https://api.example.com/v1/chat/completions"
        finally:
            client.close()

    def test_build_url_with_custom_base(self):
        client = AIClient(api_key="k", base_url="https://api.longcat.chat/openai")
        try:
            assert client._build_url() == "https://api.longcat.chat/openai/v1/chat/completions"
        finally:
            client.close()

    def test_build_messages_with_system_prompt(self):
        client = AIClient(api_key="k")
        try:
            msgs = client._build_messages("hello", "you are helpful")
            assert len(msgs) == 2
            assert msgs[0] == {"role": "system", "content": "you are helpful"}
            assert msgs[1] == {"role": "user", "content": "hello"}
        finally:
            client.close()

    def test_build_messages_without_system_prompt(self):
        client = AIClient(api_key="k")
        try:
            msgs = client._build_messages("hello", None)
            assert len(msgs) == 1
            assert msgs[0] == {"role": "user", "content": "hello"}
        finally:
            client.close()

    def test_clean_error_body(self):
        client = AIClient(api_key="k")
        try:
            result = client._clean_error_body("<html><body>Error</body></html>")
            assert result == "Error"
        finally:
            client.close()

    def test_clean_error_body_truncates_long(self):
        client = AIClient(api_key="k")
        try:
            long_text = "x" * 300
            result = client._clean_error_body(long_text)
            assert len(result) == 200
        finally:
            client.close()

    def test_generate_error_returns_error_tuple(self):
        client = AIClient(api_key="k", base_url="http://127.0.0.1:19999", timeout=5)
        try:
            content, error = client.generate("test")
            assert content is None
            assert error is not None
        finally:
            client.close()

    def test_context_manager(self):
        with AIClient(api_key="k") as client:
            assert client.api_key == "k"


class TestAIClientEndpoint:
    def test_base_url_trailing_slash_stripped(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1/")
        try:
            assert client.base_url == "https://api.example.com/v1"
        finally:
            client.close()

    def test_base_url_no_trailing_slash_preserved(self):
        client = AIClient(api_key="k", base_url="https://api.example.com/v1")
        try:
            assert client.base_url == "https://api.example.com/v1"
        finally:
            client.close()
