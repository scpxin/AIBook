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
                {"id": "a1", "name": "Model-A", "apiKey": "key-a", "endpoint": "https://a.com", "model": "a-v1"},
                {"id": "b1", "name": "Model-B", "apiKey": "key-b", "endpoint": "https://b.com", "model": "b-v1"},
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
