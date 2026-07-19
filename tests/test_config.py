from app.config import PROJECT_ID_PATTERN


class TestConfig:
    def test_project_id_pattern_valid(self):
        assert PROJECT_ID_PATTERN.match("proj-001") is not None
        assert PROJECT_ID_PATTERN.match("test_project") is not None
        assert PROJECT_ID_PATTERN.match("a-b-c") is not None
        assert PROJECT_ID_PATTERN.match("pj-123-abc") is not None

    def test_project_id_pattern_invalid(self):
        assert PROJECT_ID_PATTERN.match("proj 001") is None
        assert PROJECT_ID_PATTERN.match("../etc") is None
        assert PROJECT_ID_PATTERN.match("proj/001") is None
        assert PROJECT_ID_PATTERN.match("proj\x00bad") is None

    def test_project_id_pattern_empty(self):
        assert PROJECT_ID_PATTERN.match("") is None

    def test_project_id_pattern_long(self):
        long_id = "x" * 128
        assert PROJECT_ID_PATTERN.match(long_id) is not None

    def test_project_id_pattern_too_long(self):
        too_long = "x" * 129
        assert PROJECT_ID_PATTERN.match(too_long) is None

    def test_default_port(self, monkeypatch):
        monkeypatch.delenv("PORT", raising=False)
        import importlib

        import app.config as cfg
        importlib.reload(cfg)
        assert cfg.PORT == 8000

    def test_custom_port(self, monkeypatch):
        monkeypatch.setenv("PORT", "9000")
        import importlib

        import app.config as cfg
        importlib.reload(cfg)
        assert cfg.PORT == 9000
        monkeypatch.delenv("PORT", raising=False)
        importlib.reload(cfg)

    def test_allowed_proxy_domains(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_PROXY_DOMAINS", "api.example.com,api2.example.org")
        import importlib

        import app.config as cfg
        importlib.reload(cfg)
        assert "api.example.com" in cfg.ALLOWED_PROXY_DOMAINS
        assert "api2.example.org" in cfg.ALLOWED_PROXY_DOMAINS
        monkeypatch.delenv("ALLOWED_PROXY_DOMAINS", raising=False)
        importlib.reload(cfg)

    def test_allowed_proxy_domains_empty(self, monkeypatch):
        monkeypatch.delenv("ALLOWED_PROXY_DOMAINS", raising=False)
        import importlib

        import app.config as cfg
        importlib.reload(cfg)
        assert cfg.ALLOWED_PROXY_DOMAINS == []
