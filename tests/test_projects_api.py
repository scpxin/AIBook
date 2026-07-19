import pytest
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
