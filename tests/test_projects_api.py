from app.api.projects import sanitize_project_name, validate_project_id


class TestSanitizeProjectName:

    def test_normal_name(self):
        assert sanitize_project_name("My Project") == "My Project"

    def test_empty_name(self):
        assert sanitize_project_name("") == "未命名项目"

    def test_whitespace_only(self):
        assert sanitize_project_name("   ") == "未命名项目"

    def test_html_tags_stripped(self):
        assert sanitize_project_name("<script>alert('xss')</script>") == "alert('xss')"

    def test_control_chars_stripped(self):
        assert sanitize_project_name("test\x00name") == "testname"

    def test_truncate_long_name(self):
        long_name = "a" * 100
        result = sanitize_project_name(long_name)
        assert len(result) == 64

    def test_none_input(self):
        assert sanitize_project_name(None) == "未命名项目"


class TestValidateProjectId:
    def test_valid_id(self):
        assert validate_project_id("proj-001") is True

    def test_valid_id_with_underscore(self):
        assert validate_project_id("test_project_123") is True

    def test_empty_string(self):
        assert validate_project_id("") is False

    def test_none(self):
        assert validate_project_id(None) is False

    def test_path_traversal(self):
        assert validate_project_id("../etc/passwd") is False

    def test_spaces(self):
        assert validate_project_id("proj 001") is False

    def test_special_chars(self):
        assert validate_project_id("proj/001") is False


class TestSoftDeleteRestore:
    """软删除/恢复：同步标记 v2_projects.deleted_at，保证列表过滤生效"""

    def test_soft_delete_marks_v2_and_restore_clears(self, app, monkeypatch):
        calls = {"delete": 0, "restore": 0}
        from unittest.mock import MagicMock

        import app.api.projects as projects_mod

        mock_dbv2 = MagicMock()
        mock_dbv2.delete_project_v2.side_effect = lambda pid: calls.__setitem__("delete", calls["delete"] + 1)
        mock_dbv2.restore_project_v2.side_effect = lambda pid: calls.__setitem__("restore", calls["restore"] + 1)

        monkeypatch.setattr(projects_mod, "database_v2", mock_dbv2)
        monkeypatch.setattr(projects_mod.novel_db, "get_project", lambda pid: None)

        from fastapi.testclient import TestClient
        client = TestClient(app)
        r = client.post("/api/v2/projects/soft-delete", json={"project_id": "pj-test-1"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}
        assert calls["delete"] == 1

        r2 = client.post("/api/v2/projects/restore", json={"project_id": "pj-test-1"})
        assert r2.status_code == 200
        assert calls["restore"] == 1

    def test_soft_delete_invalid_id_returns_400(self, app):
        from fastapi.testclient import TestClient
        client = TestClient(app)
        r = client.post("/api/v2/projects/soft-delete", json={"project_id": "../etc/passwd"})
        assert r.status_code == 400
