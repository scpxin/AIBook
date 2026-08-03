"""Settings API 端到端测试 — 3 端点 + 持久化"""



class TestSettingsGet:
    """GET /api/v2/settings"""

    def test_get_settings_returns_200(self, client):
        resp = client.get("/api/v2/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert data["models"] == []


class TestSettingsSaveModels:
    """POST /api/v2/settings/models"""

    def test_save_single_model(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [{"id": "ds1", "name": "DeepSeek", "apiKey": "sk-test123", "endpoint": "https://api.deepseek.com", "model": "deepseek-chat"}],
            "activeModelId": "ds1"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["count"] == 1

    def test_save_multiple_models(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [
                {"id": "a1", "name": "Model-A", "apiKey": "key-a", "endpoint": "https://api.deepseek.com", "model": "a-v1"},
                {"id": "b1", "name": "Model-B", "apiKey": "key-b", "endpoint": "https://api.openai.com", "model": "b-v1"},
            ],
            "activeModelId": "a1"
        })
        assert resp.json()["count"] == 2

    def test_save_empty_models(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [],
            "activeModelId": ""
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_save_rejects_private_endpoint(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [{"id": "evil", "name": "Evil", "apiKey": "sk-x", "endpoint": "http://192.168.1.1/v1", "model": "x"}],
            "activeModelId": "evil"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is False
        assert "SSRF" in body["error"]

    def test_save_rejects_cgnat_endpoint(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [{"id": "evil2", "name": "Evil2", "apiKey": "sk-x", "endpoint": "http://100.64.0.1/v1", "model": "x"}],
            "activeModelId": "evil2"
        })
        body = resp.json()
        assert body["ok"] is False
        assert "SSRF" in body["error"]

    def test_save_allows_loopback_endpoint(self, client):
        resp = client.post("/api/v2/settings/models", json={
            "models": [{"id": "local", "name": "Ollama", "apiKey": "sk-local", "endpoint": "http://localhost:11434/v1", "model": "llama3"}],
            "activeModelId": "local"
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True


class TestSettingsTestConnection:
    """POST /api/v2/settings/test-connection"""

    def test_missing_params(self, client):
        resp = client.post("/api/v2/settings/test-connection", json={})
        assert resp.status_code == 200
        assert resp.json()["ok"] is False

    def test_partial_params(self, client):
        resp = client.post("/api/v2/settings/test-connection", json={
            "endpoint": "https://api.test.com",
            "apiKey": "sk-test"
        })
        assert resp.json()["ok"] is False

    def test_test_connection_with_bad_endpoint(self, client):
        resp = client.post("/api/v2/settings/test-connection", json={
            "endpoint": "https://169.254.255.255:9999/v1",
            "apiKey": "sk-fake",
            "model": "gpt-4"
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is False

    def test_ssrf_blocks_private_ip(self, client):
        for endpoint in [
            "http://10.0.0.1/v1",
            "http://192.168.1.1/v1",
            "http://172.16.0.1/v1",
            "http://100.64.0.1/v1",
        ]:
            resp = client.post("/api/v2/settings/test-connection", json={
                "endpoint": endpoint,
                "apiKey": "sk-fake",
                "model": "gpt-4"
            })
            assert resp.status_code == 200
            body = resp.json()
            assert body["ok"] is False, f"{endpoint} 应被 SSRF 拦截"
            assert "SSRF" in body["error"]

    def test_loopback_allowed(self, client):
        resp = client.post("/api/v2/settings/test-connection", json={
            "endpoint": "http://localhost:11434/v1",
            "apiKey": "sk-local",
            "model": "llama3"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is False
        assert "SSRF" not in body["error"]
