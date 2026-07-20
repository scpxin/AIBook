"""DataBridge 基础层测试 — 连接管理 + 工具函数"""
import pytest

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


@pytest.fixture
def db():
    """创建临时 SQLite 数据库并初始化表结构"""
    import novel_creator.data_bridge as bridge_mod
    old_path = bridge_mod.DB_PATH
    bridge_mod.DB_PATH = ':memory:'
    DataBridge.close()
    conn = DataBridge._conn()
    from novel_creator.db_schema import V2_SCHEMA_DDL
    conn.executescript(V2_SCHEMA_DDL)
    conn.commit()
    yield
    DataBridge.close()
    bridge_mod.DB_PATH = old_path


class TestWriteIdea:
    def test_write_and_read(self, db):
        DataBridge._write_idea('p1', {'user_input': 'test idea', 'genre_hint': 'fantasy', 'selected_concept': 'hero journey'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_ideas WHERE project_id='p1'").fetchone()
        assert row['user_input'] == 'test idea'
        assert row['genre_hint'] == 'fantasy'
        assert row['selected_concept'] == 'hero journey'

    def test_upsert_updates(self, db):
        DataBridge._write_idea('p1', {'user_input': 'first'})
        DataBridge._write_idea('p1', {'user_input': 'second', 'selected_concept': 'updated'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_ideas WHERE project_id='p1'").fetchone()
        assert row['user_input'] == 'second'
        assert row['selected_concept'] == 'updated'


class TestWriteProject:
    def test_write_basic(self, db):
        DataBridge._write_project('p1', {'platform_choice': 'tomato', 'project_overview': 'test overview'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_projects WHERE project_id='p1'").fetchone()
        assert row['platform_choice'] == 'tomato'
        assert row['project_overview'] == 'test overview'

    def test_upsert_merges(self, db):
        DataBridge._write_project('p1', {'project_overview': 'v1'})
        DataBridge._write_project('p1', {'platform_choice': 'qidian'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_projects WHERE project_id='p1'").fetchone()
        assert row['project_overview'] == ''
        assert row['platform_choice'] == 'qidian'


class TestWriteWorld:
    def test_write_basic(self, db):
        DataBridge._write_world('p1', {'origin': {'type': 'created'}})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_world_buildings WHERE project_id='p1'").fetchone()
        result = _deserialize_row(row)
        assert result['origin'] == {'type': 'created'}

    def test_merge_step_by_step(self, db):
        DataBridge._write_world('p1', {'origin': {'type': 'created'}})
        DataBridge._write_world('p1', {'rules': ['rule1', 'rule2']})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_world_buildings WHERE project_id='p1'").fetchone()
        result = _deserialize_row(row)
        assert result['origin'] == {'type': 'created'}
        assert result['rules'] == ['rule1', 'rule2']


class TestWriteCharacters:
    def test_write_single(self, db):
        DataBridge._write_characters('p1', [{'char_id': 'c1', 'name': 'Alice', 'role_type': 'protagonist'}])
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_characters WHERE project_id='p1' AND char_id='c1'").fetchone()
        assert row['name'] == 'Alice'

    def test_upsert_by_char_id(self, db):
        DataBridge._write_characters('p1', [{'char_id': 'c1', 'name': 'Alice'}])
        DataBridge._write_characters('p1', [{'char_id': 'c1', 'name': 'Alice Updated'}])
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_characters WHERE project_id='p1'").fetchone()[0]
        assert count == 1
        row = conn.execute("SELECT * FROM v2_characters WHERE project_id='p1' AND char_id='c1'").fetchone()
        assert row['name'] == 'Alice Updated'

    def test_list_input(self, db):
        data = [
            {'char_id': 'c1', 'name': 'Alice', 'profile': {'age': 25}},
            {'char_id': 'c2', 'name': 'Bob', 'profile': {'age': 30}},
        ]
        DataBridge._write_characters('p1', data)
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_characters WHERE project_id='p1'").fetchone()[0]
        assert count == 2


class TestWriteRelationMap:
    def test_write(self, db):
        DataBridge._write_relation_map('p1', {'nodes': [{'id': 'n1'}], 'edges': [{'from': 'n1', 'to': 'n2'}]})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_relation_maps WHERE project_id='p1'").fetchone()
        result = _deserialize_row(row)
        assert len(result['nodes']) == 1
        assert result['nodes'][0]['id'] == 'n1'


class TestWriteArchitecture:
    def test_write_basic(self, db):
        DataBridge._write_architecture('p1', {'summary': 'test story', 'theme': 'revenge'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_story_systems WHERE project_id='p1'").fetchone()
        assert row['theme'] == 'revenge'

    def test_merge_step_by_step(self, db):
        DataBridge._write_architecture('p1', {'summary': 'step1'})
        DataBridge._write_architecture('p1', {'theme': 'step2'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_story_systems WHERE project_id='p1'").fetchone()
        assert row['summary'] == 'step1'
        assert row['theme'] == 'step2'


class TestWriteVolumes:
    def test_write_list(self, db):
        vols = [{'name': 'Volume 1'}, {'name': 'Volume 2'}, {'name': 'Volume 3'}]
        DataBridge._write_volumes('p1', vols)
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_volumes WHERE project_id='p1'").fetchone()[0]
        assert count == 3

    def test_delete_and_replace(self, db):
        DataBridge._write_volumes('p1', [{'name': 'V1'}, {'name': 'V2'}])
        DataBridge._write_volumes('p1', [{'name': 'V3'}])
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_volumes WHERE project_id='p1'").fetchone()[0]
        assert count == 1
        row = conn.execute("SELECT name FROM v2_volumes WHERE project_id='p1' AND volume_no=1").fetchone()
        assert row['name'] == 'V3'


class TestWriteDraft:
    def test_write_single(self, db):
        DataBridge._write_draft('p1', {'1': {'content': 'hello world', 'char_count': 11}})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_drafts WHERE project_id='p1' AND chapter_no='1'").fetchone()
        assert row['content'] == 'hello world'

    def test_upsert_updates(self, db):
        DataBridge._write_draft('p1', {'1': {'content': 'v1'}})
        DataBridge._write_draft('p1', {'1': {'content': 'v2'}})
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_drafts WHERE project_id='p1'").fetchone()[0]
        assert count == 1
        row = conn.execute("SELECT content FROM v2_drafts WHERE project_id='p1' AND chapter_no='1'").fetchone()
        assert row['content'] == 'v2'


class TestWriteParse:
    def test_write(self, db):
        DataBridge._write_parse('p1', {'character_states': {'Alice': {'status': 'alive'}}, 'last_chapter_no': '3'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT * FROM v2_knowledge_states WHERE project_id='p1'").fetchone()
        result = _deserialize_row(row)
        assert result['character_states'] == {'Alice': {'status': 'alive'}}
        assert result['last_chapter_no'] == '3'


class TestWritePolish:
    def test_is_noop(self, db):
        DataBridge._write_polish('p1', {'some': 'data'})
        # No error = pass


class TestWriteConsistency:
    def test_write_append(self, db):
        DataBridge._write_consistency('p1', {'chapter_no': '1', 'score': 0.95, 'summary': 'all good', 'items': [], 'fixes': []})
        DataBridge._write_consistency('p1', {'chapter_no': '2', 'score': 0.8, 'summary': 'minor issues', 'items': [], 'fixes': []})
        conn = DataBridge._conn()
        count = conn.execute("SELECT COUNT(*) FROM v2_consistency_reports WHERE project_id='p1'").fetchone()[0]
        assert count == 2


class TestWriteDispatch:
    def test_write_via_dispatch(self, db):
        DataBridge.write('p1', 'idea', {'user_input': 'dispatched'})
        conn = DataBridge._conn()
        row = conn.execute("SELECT user_input FROM v2_ideas WHERE project_id='p1'").fetchone()
        assert row['user_input'] == 'dispatched'

    def test_unknown_module_is_noop(self, db):
        DataBridge.write('p1', 'nonexistent', {'data': 'x'})
        # No error

