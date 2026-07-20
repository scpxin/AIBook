"""DataBridge 基础层测试 — 连接管理 + 工具函数"""
import os
import tempfile

from novel_creator.data_bridge import DataBridge, _deserialize_row, _j, _jl, _now


class TestHelpers:
    def test_j_string_passthrough(self):
        assert _j("hello") == "hello"

    def test_j_dict(self):
        assert _j({"a": 1}) == '{"a": 1}'

    def test_j_empty(self):
        assert _j({}) == '{}'
        assert _j(None) == '{}'

    def test_jl_string(self):
        assert _jl('{"a": 1}') == {"a": 1}

    def test_jl_already_dict(self):
        data = {"a": 1}
        assert _jl(data) is data

    def test_jl_none_default(self):
        assert _jl(None) is None
        assert _jl(None, []) == []

    def test_jl_broken_json(self):
        assert _jl("not json") == "not json"
        assert _jl("not json", []) == []

    def test_now_format(self):
        now = _now()
        assert len(now) == 19
        assert now[4] == '-' and now[7] == '-'
        assert now[10] == ' ' and now[13] == ':'

    def test_deserialize_row_none(self):
        assert _deserialize_row(None) is None

    def test_deserialize_row_json_fields(self):
        class FakeRow(dict):
            pass

        row = FakeRow({"name": "test", "data": '{"key": "val"}', "items": '["a","b"]'})
        result = _deserialize_row(row)
        assert result["name"] == "test"
        assert result["data"] == {"key": "val"}
        assert result["items"] == ["a", "b"]

    def test_deserialize_row_plain_strings(self):
        class FakeRow(dict):
            pass

        row = FakeRow({"title": "Hello World", "count": 42})
        result = _deserialize_row(row)
        assert result["title"] == "Hello World"
        assert result["count"] == 42


class TestDataBridgeConnection:
    def test_conn_creates_and_reuses(self):
        conn1 = DataBridge._conn()
        conn2 = DataBridge._conn()
        assert conn1 is conn2
        assert conn1.row_factory is not None

    def test_close_releases(self):
        conn1 = DataBridge._conn()
        DataBridge.close()
        conn2 = DataBridge._conn()
        assert conn1 is not conn2

    def test_reconnect_after_close(self):
        DataBridge.close()
        conn = DataBridge._conn()
        assert conn is not None
        conn.execute("SELECT 1").fetchone()
        DataBridge.close()
