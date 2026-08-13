import os
import sqlite3
import tempfile

import pytest


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    old_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = path
    yield path
    os.unlink(path)
    if old_path:
        os.environ["DB_PATH"] = old_path
    else:
        del os.environ["DB_PATH"]


class TestDatabaseV2Init:
    def test_init_db_v2_creates_all_tables(self, temp_db):
        from novel_creator.database_v2 import _v2_db, init_db_v2
        init_db_v2()

        conn = _v2_db()
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        conn.close()

        expected = [
            'idea_templates', 'settings',
            'v2_characters', 'v2_chapter_plans', 'v2_consistency_reports',
            'v2_drafts', 'v2_factions', 'v2_ideas',
            'v2_knowledge_states', 'v2_pipeline_states', 'v2_plot_nodes',
            'v2_power_systems', 'v2_projects', 'v2_relation_maps',
            'v2_scenes', 'v2_story_systems', 'v2_timelines',
            'v2_volumes', 'v2_world_buildings',
        ]
        for table in expected:
            assert table in tables, f"Table {table} not found in {tables}"

    def test_init_db_v2_is_idempotent(self, temp_db):
        from novel_creator.database_v2 import init_db_v2
        init_db_v2()
        init_db_v2()
        init_db_v2()

    def test_v2_now_returns_string(self, temp_db):
        from novel_creator.database_v2 import _v2_now
        result = _v2_now()
        assert isinstance(result, str)
        assert len(result) == 19


class TestDatabaseV2CRUD:
    def test_settings_set_and_get(self, temp_db):
        from novel_creator.database_v2 import _v2_db, _v2_lock, init_db_v2
        init_db_v2()

        with _v2_lock:
            conn = _v2_db()
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("test_key", "test_value")
            )
            conn.commit()
            row = conn.execute(
                "SELECT value FROM settings WHERE key=?", ("test_key",)
            ).fetchone()
            conn.close()

        assert row is not None
        assert row["value"] == "test_value"

    def test_v2_idea_insert_and_query(self, temp_db):
        from novel_creator.database_v2 import _v2_db, _v2_lock, init_db_v2
        init_db_v2()

        with _v2_lock:
            conn = _v2_db()
            conn.execute(
                "INSERT INTO v2_ideas (project_id, user_input, genre_hint, status) VALUES (?, ?, ?, ?)",
                ("proj-001", "test idea", "fantasy", "draft")
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM v2_ideas WHERE project_id=?", ("proj-001",)
            ).fetchone()
            conn.close()

        assert row is not None
        assert row["project_id"] == "proj-001"
        assert row["user_input"] == "test idea"
        assert row["genre_hint"] == "fantasy"
        assert row["status"] == "draft"

    def test_project_unique_constraint(self, temp_db):
        from novel_creator.database_v2 import _v2_db, _v2_lock, init_db_v2
        init_db_v2()

        with _v2_lock:
            conn = _v2_db()
            conn.execute(
                "INSERT INTO v2_projects (project_id, platform_choice) VALUES (?, ?)",
                ("proj-dup", "tomato")
            )
            conn.commit()

            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO v2_projects (project_id, platform_choice) VALUES (?, ?)",
                    ("proj-dup", "qidian")
                )
            conn.close()

    def test_character_insert_and_relation(self, temp_db):
        from novel_creator.database_v2 import _v2_db, _v2_lock, init_db_v2
        init_db_v2()

        with _v2_lock:
            conn = _v2_db()
            conn.execute(
                "INSERT INTO v2_projects (project_id) VALUES (?)", ("proj-c001",)
            )
            conn.execute(
                "INSERT INTO v2_characters (project_id, char_id, role_type, name) VALUES (?, ?, ?, ?)",
                ("proj-c001", "char-01", "protagonist", "Hero")
            )
            conn.execute(
                "INSERT INTO v2_characters (project_id, char_id, role_type, name) VALUES (?, ?, ?, ?)",
                ("proj-c001", "char-02", "antagonist", "Villain")
            )
            conn.commit()

            rows = conn.execute(
                "SELECT count(*) as cnt FROM v2_characters WHERE project_id=?",
                ("proj-c001",)
            ).fetchone()
            conn.close()

        assert rows["cnt"] == 2

    def test_v2_pipeline_state_modules(self, temp_db):
        from novel_creator.database_v2 import get_pipeline_module_data, init_db_v2, save_pipeline_state
        init_db_v2()

        test_cases = [
            ("architecture", {"type": "framework", "sections": 5}),
            ("outline", {"chapters": 10, "theme": "adventure"}),
            ("parse", {"status": "done", "parsed": 5}),
            ("polish", {"round": 1, "changes": 3}),
        ]

        for module_name, data in test_cases:
            save_pipeline_state("test-ps", module_name, data)

        for module_name, expected in test_cases:
            result = get_pipeline_module_data("test-ps", module_name)
            assert result == expected, f"模块 {module_name} 数据不匹配: {result} != {expected}"


class TestSoftDeleteV2:
    def test_soft_delete_marks_all_tables(self, temp_db):
        from novel_creator.database_v2 import _v2_db, delete_project_v2, init_db_v2
        init_db_v2()
        conn = _v2_db()
        conn.execute("INSERT INTO v2_projects(project_id, project_overview) VALUES('p1','测试')")
        conn.execute("INSERT INTO idea_templates(project_id, name, genre, prompt) VALUES('p1','t','g','p')")
        conn.commit()
        conn.close()

        delete_project_v2('p1')

        conn = _v2_db()
        row = conn.execute("SELECT deleted_at FROM v2_projects WHERE project_id='p1'").fetchone()
        assert row is not None and row[0] is not None
        # idea_templates 无 deleted_at 列，软删回退为硬删除
        trow = conn.execute("SELECT * FROM idea_templates WHERE project_id='p1'").fetchone()
        assert trow is None
        conn.close()

    def test_restore_clears_deleted_at(self, temp_db):
        from novel_creator.database_v2 import _v2_db, delete_project_v2, init_db_v2, restore_project_v2
        init_db_v2()
        conn = _v2_db()
        conn.execute("INSERT INTO v2_projects(project_id, project_overview) VALUES('p2','测试')")
        conn.commit()
        conn.close()

        delete_project_v2('p2')
        restore_project_v2('p2')

        conn = _v2_db()
        row = conn.execute("SELECT deleted_at FROM v2_projects WHERE project_id='p2'").fetchone()
        assert row is not None and row[0] is None
        conn.close()

    def test_hard_delete_removes_rows(self, temp_db):
        from novel_creator.database_v2 import _v2_db, hard_delete_project_v2, init_db_v2
        init_db_v2()
        conn = _v2_db()
        conn.execute("INSERT INTO v2_projects(project_id, project_overview) VALUES('p3','测试')")
        conn.commit()
        conn.close()

        hard_delete_project_v2('p3')

        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_projects WHERE project_id='p3'").fetchone()
        assert row is None
        conn.close()


class TestSavePipelineStatePreservesStatus:
    def test_partial_save_preserves_retry_and_timestamps(self, temp_db):
        from novel_creator.database_v2 import _v2_db, init_db_v2, save_pipeline_state
        init_db_v2()
        save_pipeline_state('p1', 'world', {
            'status': 'generating', 'retry_count': 3,
            'error': '', 'started_at': '2026-01-01 00:00:00',
            'module_data': {'origin': {'name': 'world'}},
        })
        # 全量保存：只带 module_data，不带状态字段
        save_pipeline_state('p1', 'world', {'module_data': {'origin': {'name': 'updated'}}})

        conn = _v2_db()
        row = conn.execute(
            "SELECT status, retry_count, started_at, data_json FROM v2_pipeline_states "
            "WHERE project_id='p1' AND module_name='world'"
        ).fetchone()
        conn.close()
        assert row['status'] == 'generating'
        assert row['retry_count'] == 3
        assert row['started_at'] == '2026-01-01 00:00:00'
        import json as _json
        assert 'updated' in _json.loads(row['data_json'])['origin']['name']

    def test_explicit_status_update_wins(self, temp_db):
        from novel_creator.database_v2 import _v2_db, init_db_v2, save_pipeline_state
        init_db_v2()
        save_pipeline_state('p1', 'idea', {
            'status': 'generating', 'retry_count': 1, 'started_at': '2026-01-01 00:00:00',
            'module_data': {'a': 1},
        })
        save_pipeline_state('p1', 'idea', {
            'status': 'done', 'retry_count': 2,
            'module_data': {'a': 2},
        })
        conn = _v2_db()
        row = conn.execute(
            "SELECT status, retry_count FROM v2_pipeline_states WHERE project_id='p1' AND module_name='idea'"
        ).fetchone()
        conn.close()
        assert row['status'] == 'done'
        assert row['retry_count'] == 2
