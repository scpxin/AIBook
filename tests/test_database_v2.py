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
        from novel_creator.database_v2 import init_db_v2, save_pipeline_state, get_pipeline_module_data
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
