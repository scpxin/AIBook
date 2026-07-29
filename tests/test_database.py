import importlib
import os
import sqlite3
import tempfile

import pytest


@pytest.fixture(scope="class")
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    old_path = os.environ.get("DB_PATH")
    os.environ["DB_PATH"] = path

    import novel_creator.database as db_module
    importlib.reload(db_module)
    db_module.init_db()

    yield db_module

    os.unlink(path)
    if old_path:
        os.environ["DB_PATH"] = old_path
    else:
        del os.environ["DB_PATH"]


# ======================================================================
# Init / get_db / _now
# ======================================================================

class TestInit:

    def test_init_db_creates_all_tables(self, db):
        conn = db.get_db()
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        conn.close()

        expected = [
            'chapters', 'generation_status',
            'outline_generation_status', 'outlines',
            'projects', 'step_summaries',
        ]
        for table in expected:
            assert table in tables, f"Table {table} not found in {tables}"

    def test_init_db_is_idempotent(self, db):
        db.init_db()
        db.init_db()
        db.init_db()

    def test_get_db_returns_connection(self, db):
        conn = db.get_db()
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory is sqlite3.Row
        conn.close()

    def test_get_db_connects_to_temp_path(self, db):
        conn = db.get_db()
        assert db.DB_PATH not in ("", None)
        conn.close()

    def test_now_returns_formatted_string(self, db):
        result = db._now()
        assert isinstance(result, str)
        assert len(result) == 19
        parts = result.split(" ")
        assert len(parts) == 2
        date_parts = parts[0].split("-")
        time_parts = parts[1].split(":")
        assert len(date_parts) == 3
        assert len(time_parts) == 3

    def test_has_column_true(self, db):
        assert db._has_column("projects", "id")
        assert db._has_column("chapters", "project_id")

    def test_has_column_false(self, db):
        assert not db._has_column("projects", "nonexistent_column_xyz")

    def test_schema_version_is_set(self, db):
        conn = db.get_db()
        row = conn.execute("PRAGMA user_version").fetchone()
        conn.close()
        assert row[0] >= 2


# ======================================================================
# Step Summaries
# ======================================================================

class TestStepSummaries:

    PROJECT = "step-summary-proj"

    def test_save_and_get_step_summary(self, db):
        summary = {"key": "value", "items": [1, 2, 3]}
        db.save_step_summary(self.PROJECT, "outline", summary)

        result = db.get_step_summary(self.PROJECT, "outline")
        assert result is not None
        assert result["project_id"] == self.PROJECT
        assert result["step"] == "outline"
        assert result["summary_json"] == summary

    def test_save_step_summary_updates_existing(self, db):
        db.save_step_summary(self.PROJECT, "characters", {"name": "old"})
        db.save_step_summary(self.PROJECT, "characters", {"name": "new"})

        result = db.get_step_summary(self.PROJECT, "characters")
        assert result["summary_json"] == {"name": "new"}

    def test_get_step_summary_returns_none_for_missing(self, db):
        result = db.get_step_summary(self.PROJECT, "nonexistent_step")
        assert result is None

    def test_get_step_summary_returns_none_for_missing_project(self, db):
        result = db.get_step_summary("no-such-project", "outline")
        assert result is None

    def test_get_all_step_summaries(self, db):
        db.save_step_summary("gsas-proj", "step_a", {"a": 1})
        db.save_step_summary("gsas-proj", "step_b", {"b": 2})

        result = db.get_all_step_summaries("gsas-proj")
        assert len(result) == 2
        steps = {r["step"] for r in result}
        assert steps == {"step_a", "step_b"}

    def test_get_all_step_summaries_empty_project(self, db):
        result = db.get_all_step_summaries("empty-proj")
        assert result == []

    def test_delete_project_step_summaries(self, db):
        db.save_step_summary(self.PROJECT, "to_delete", {"x": 1})
        db.delete_project_step_summaries(self.PROJECT)
        result = db.get_all_step_summaries(self.PROJECT)
        assert result == []

    def test_step_summary_with_string_json(self, db):
        db.save_step_summary(self.PROJECT, "raw_str", '{"raw": true}')
        result = db.get_step_summary(self.PROJECT, "raw_str")
        assert result["summary_json"] == {"raw": True}

    def test_step_summary_with_invalid_json(self, db):
        conn = db.get_db()
        conn.execute(
            "INSERT INTO step_summaries (project_id, step, summary_json) VALUES (?, ?, ?)",
            (self.PROJECT, "bad_json", "not-valid-json{{{")
        )
        conn.commit()
        conn.close()

        result = db.get_step_summary(self.PROJECT, "bad_json")
        assert result["summary_json"] == {}

    def test_save_step_summary_with_complex_object(self, db):
        nested = {"nested": {"deep": {"key": "value"}}, "null_val": None, "bool": True, "num": 42}
        db.save_step_summary("nested-proj", "complex", nested)
        result = db.get_step_summary("nested-proj", "complex")
        assert result["summary_json"] == nested


# ======================================================================
# Projects
# ======================================================================

class TestProjects:

    PROJECT = "proj-crud"

    def test_save_and_get_project(self, db):
        data = {"title": "Test Novel", "chapters": [1, 2, 3]}
        db.save_project(self.PROJECT, "Test Novel", 0, data)

        result = db.get_project(self.PROJECT)
        assert result is not None
        assert result["id"] == self.PROJECT
        assert result["name"] == "Test Novel"
        assert result["step"] == 0
        assert result["data"] == data
        assert "data_json" not in result

    def test_save_project_updates_existing(self, db):
        db.save_project(self.PROJECT, "Old Name", 0, {"v": 1})
        db.save_project(self.PROJECT, "New Name", 2, {"v": 2})

        result = db.get_project(self.PROJECT)
        assert result["name"] == "New Name"
        assert result["step"] == 2
        assert result["data"] == {"v": 2}

    def test_save_project_with_all_fields(self, db):
        data = {"title": "Full Project"}
        metadata = {"genre": "fantasy", "rating": 5}
        db.save_project(
            "proj-full", "Full Project", 3, data,
            tags="fantasy,adventure",
            category="novel",
            metadata=metadata,
            is_archived=0,
        )

        result = db.get_project("proj-full")
        assert result["name"] == "Full Project"
        assert result["step"] == 3
        assert result["data"] == data
        assert result["metadata"] == metadata
        assert result["tags"] == "fantasy,adventure"
        assert result["category"] == "novel"
        assert result["is_archived"] == 0

    def test_save_project_archived(self, db):
        db.save_project("proj-archived", "Archived", 0, {}, is_archived=1)
        result = db.get_project("proj-archived")
        assert result["is_archived"] == 1

    def test_save_project_with_string_data(self, db):
        db.save_project("proj-str", "String Data", 0, "just a string")
        result = db.get_project("proj-str")
        assert result["data"] == {}

    def test_get_project_returns_none_for_missing(self, db):
        result = db.get_project("nonexistent")
        assert result is None

    def test_list_projects(self, db):
        db.save_project("lp-1", "Project 1", 1, {"title": "P1"})
        db.save_project("lp-2", "Project 2", 2, {"title": "P2"})

        projects = db.list_projects()
        ids = [p["id"] for p in projects]
        assert "lp-1" in ids
        assert "lp-2" in ids
        for p in projects:
            assert "id" in p
            assert "name" in p
            assert "step" in p
            assert "chapter_count" in p

    def test_list_projects_excludes_archived(self, db):
        db.save_project("lp-active", "Active", 0, {}, is_archived=0)
        db.save_project("lp-archived2", "Archived2", 0, {}, is_archived=1)

        projects = db.list_projects(include_archived=False)
        project_ids = [p["id"] for p in projects]
        assert "lp-active" in project_ids
        assert "lp-archived2" not in project_ids

    def test_list_projects_include_archived(self, db):
        db.save_project("lp-ia", "Active", 0, {}, is_archived=0)
        db.save_project("lp-ia2", "Archived", 0, {}, is_archived=1)

        projects = db.list_projects(include_archived=True)
        project_ids = [p["id"] for p in projects]
        assert "lp-ia" in project_ids
        assert "lp-ia2" in project_ids

    def test_list_projects_chapter_count(self, db):
        db.save_project("lp-cc", "Chapter Count", 0, {"title": "CC", "chapters": [1, 1, 1]})
        projects = db.list_projects()
        for p in projects:
            if p["id"] == "lp-cc":
                assert p["chapter_count"] == 3

    def test_list_projects_char_count(self, db):
        data = {"title": "CC2", "charactersRaw": ["a", "b", "c", "d"]}
        db.save_project("lp-cr", "Char Count", 0, data)
        projects = db.list_projects()
        for p in projects:
            if p["id"] == "lp-cr":
                assert p["char_count"] == 4

    def test_delete_project_cascade_soft(self, db):
        db.save_project("cascade-proj", "Cascade", 0, {})
        db.save_chapter("cascade-proj", 1, "Ch1", "content")
        db.save_outline("cascade-proj", 1, "Outline 1")
        db.save_step_summary("cascade-proj", "step1", {"a": 1})

        db.delete_project_cascade("cascade-proj")
        result = db.get_project("cascade-proj")
        assert result is None

    def test_hard_delete_project(self, db):
        db.save_project("hard-del", "Hard Delete", 0, {})
        db.save_chapter("hard-del", 1, "Ch1", "content")
        db.save_outline("hard-del", 1, "Outline 1")

        db.hard_delete_project("hard-del")
        result = db.get_project("hard-del")
        assert result is None

        chapters = db.get_all_chapters("hard-del")
        assert chapters == []
        outlines = db.get_all_outlines("hard-del")
        assert outlines == []

    def test_restore_project(self, db):
        db.save_project("restore-proj", "Restore Me", 0, {"title": "R"})
        db.save_chapter("restore-proj", 1, "Ch1", "content", status="done")
        db.delete_project_cascade("restore-proj")

        db.restore_project("restore-proj")
        result = db.get_project("restore-proj")
        assert result is not None
        assert result["name"] == "Restore Me"

    def test_save_project_metadata_none_defaults_to_empty(self, db):
        db.save_project("meta-empty", "Meta", 0, {}, metadata=None)
        result = db.get_project("meta-empty")
        assert result["metadata"] == {}


# ======================================================================
# Chapters
# ======================================================================

class TestChapters:

    PROJECT = "ch-proj"

    def test_save_and_get_chapter(self, db):
        db.save_chapter(self.PROJECT, 1, "Chapter One", "Hello World", "done")

        result = db.get_chapter(self.PROJECT, 1)
        assert result is not None
        assert result["project_id"] == self.PROJECT
        assert result["chapter_number"] == 1
        assert result["title"] == "Chapter One"
        assert result["content"] == "Hello World"
        assert result["word_count"] == 11
        assert result["status"] == "done"
        assert result["version"] == 1

    def test_save_chapter_defaults(self, db):
        db.save_chapter(self.PROJECT, 99, title="", content="")
        result = db.get_chapter(self.PROJECT, 99)
        assert result["title"] == ""
        assert result["content"] == ""
        assert result["word_count"] == 0
        assert result["status"] == "done"

    def test_save_chapter_updates_existing_and_increments_version(self, db):
        db.save_chapter(self.PROJECT, 1, "v1", "content v1")
        v1 = db.get_chapter(self.PROJECT, 1)
        assert v1["version"] == 2
        assert v1["title"] == "v1"
        assert v1["content"] == "content v1"

        db.save_chapter(self.PROJECT, 1, "v2", "content v2")
        v2 = db.get_chapter(self.PROJECT, 1)
        assert v2["version"] == 3
        assert v2["title"] == "v2"

    def test_save_chapter_computes_word_count(self, db):
        content = "one two three four five"
        db.save_chapter(self.PROJECT, 50, "Counting", content)
        result = db.get_chapter(self.PROJECT, 50)
        assert result["word_count"] == len(content)

    def test_save_chapter_with_metadata(self, db):
        db.save_chapter(self.PROJECT, 60, "Meta", "content", metadata={"source": "ai", "score": 0.9})
        result = db.get_chapter(self.PROJECT, 60)
        assert result is not None

    def test_save_chapter_with_error_message(self, db):
        db.save_chapter(self.PROJECT, 70, "Error", "partial", status="failed", error_message="API timeout")
        result = db.get_chapter(self.PROJECT, 70)
        assert result["status"] == "failed"
        assert result["error_message"] == "API timeout"

    def test_save_chapter_content_none_computes_zero(self, db):
        db.save_chapter(self.PROJECT, 80, "None", "", status="done")
        result = db.get_chapter(self.PROJECT, 80)
        assert result["word_count"] == 0

    def test_get_chapter_returns_none_for_missing(self, db):
        result = db.get_chapter(self.PROJECT, 999)
        assert result is None

    def test_get_chapter_excludes_deleted(self, db):
        db.save_chapter(self.PROJECT, 100, "Deleted", "gone", status="deleted")
        result = db.get_chapter(self.PROJECT, 100)
        assert result is None

    def test_get_all_chapters(self, db):
        db.save_chapter(self.PROJECT, 10, "Ch10", "content10")
        db.save_chapter(self.PROJECT, 5, "Ch5", "content5")
        db.save_chapter(self.PROJECT, 15, "Ch15", "content15")

        chapters = db.get_all_chapters(self.PROJECT)
        numbers = [c["chapter_number"] for c in chapters]
        assert len(chapters) >= 3
        for i in range(len(numbers) - 1):
            assert numbers[i] < numbers[i + 1], "Chapters not sorted"

    def test_get_all_chapters_excludes_deleted(self, db):
        db.save_chapter(self.PROJECT, 20, "Visible", "content")
        db.save_chapter(self.PROJECT, 21, "Deleted Ch", "gone", status="deleted")

        chapters = db.get_all_chapters(self.PROJECT)
        assert all(c["status"] != "deleted" for c in chapters)
        numbers = {c["chapter_number"] for c in chapters}
        assert 20 in numbers

    def test_delete_chapter(self, db):
        db.save_chapter(self.PROJECT, 30, "To Delete", "content")
        db.delete_chapter(self.PROJECT, 30)
        result = db.get_chapter(self.PROJECT, 30)
        assert result is None

    def test_delete_project_chapters(self, db):
        db.save_chapter(self.PROJECT, 40, "Keep", "content")
        db.save_chapter(self.PROJECT, 41, "Keep2", "content2")
        db.delete_project_chapters(self.PROJECT)
        chapters = db.get_all_chapters(self.PROJECT)
        assert chapters == []

    def test_get_chapter_count(self, db):
        db.save_chapter("count-proj", 1, "Done", "aaa", status="done")
        db.save_chapter("count-proj", 2, "Pending", "", status="pending")
        db.save_chapter("count-proj", 3, "Done2", "bbb", status="done")

        count = db.get_chapter_count("count-proj")
        assert count["total"] == 3
        assert count["completed"] == 2

    def test_get_chapter_count_empty(self, db):
        count = db.get_chapter_count("empty-ch")
        assert count["total"] == 0
        assert count["completed"] == 0

    def test_save_chapter_status_pending(self, db):
        db.save_chapter("pending-proj", 1, "Pending", "", status="pending")
        result = db.get_chapter("pending-proj", 1)
        assert result["status"] == "pending"

    def test_chapter_unique_constraint(self, db):
        db.save_chapter("uq-proj", 1, "First")
        db.save_chapter("uq-proj", 1, "Second")
        conn = db.get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM chapters WHERE project_id=? AND chapter_number=?",
            ("uq-proj", 1)
        ).fetchone()[0]
        conn.close()
        assert count == 1


# ======================================================================
# Outlines
# ======================================================================

class TestOutlines:

    PROJECT = "out-proj"

    def test_save_and_get_outline(self, db):
        db.save_outline(
            self.PROJECT, 1, "Chapter 1 Outline", "Summary text",
            scenes=[{"name": "scene1"}, {"name": "scene2"}],
            characters=["hero", "villain"],
            key_points=["point1", "point2"],
            emotion="tense",
            goal="establish conflict",
        )

        result = db.get_outline(self.PROJECT, 1)
        assert result is not None
        assert result["project_id"] == self.PROJECT
        assert result["chapter_number"] == 1
        assert result["title"] == "Chapter 1 Outline"
        assert result["summary"] == "Summary text"
        assert result["scenes"] == [{"name": "scene1"}, {"name": "scene2"}]
        assert result["characters"] == ["hero", "villain"]
        assert result["key_points"] == ["point1", "point2"]
        assert result["emotion"] == "tense"
        assert result["goal"] == "establish conflict"

    def test_save_outline_defaults(self, db):
        db.save_outline(self.PROJECT, 50, title="Bare Minimum")
        result = db.get_outline(self.PROJECT, 50)
        assert result["summary"] == ""
        assert result["scenes"] == []
        assert result["characters"] == []
        assert result["key_points"] == []
        assert result["acts"] == []
        assert result["emotion"] == ""

    def test_save_outline_updates_existing(self, db):
        db.save_outline(self.PROJECT, 1, "Old Title", "Old summary")
        db.save_outline(self.PROJECT, 1, "New Title", "New summary")

        result = db.get_outline(self.PROJECT, 1)
        assert result["title"] == "New Title"
        assert result["summary"] == "New summary"

    def test_save_outline_with_all_fields(self, db):
        db.save_outline(
            self.PROJECT, 100,
            title="Full Outline",
            summary="Full summary",
            scenes=[{"s": 1}],
            characters=["c1", "c2"],
            key_points=["kp1"],
            emotion="excited",
            goal="resolve",
            technique_focus="dialogue",
            book_overview="overview text",
            chapter_hook="hook text",
            acts=[{"act": "one"}],
            importance=5,
            status="done",
            error_message="",
            metadata={"version": 2},
        )

        result = db.get_outline(self.PROJECT, 100)
        assert result["title"] == "Full Outline"
        assert result["summary"] == "Full summary"
        assert result["scenes"] == [{"s": 1}]
        assert result["characters"] == ["c1", "c2"]
        assert result["key_points"] == ["kp1"]
        assert result["emotion"] == "excited"
        assert result["goal"] == "resolve"
        assert result["technique_focus"] == "dialogue"
        assert result["book_overview"] == "overview text"
        assert result["chapter_hook"] == "hook text"
        assert result["acts"] == [{"act": "one"}]
        assert result["importance"] == 5
        assert result["status"] == "done"

    def test_get_outline_returns_none_for_missing(self, db):
        result = db.get_outline(self.PROJECT, 999)
        assert result is None

    def test_get_outline_status_pending(self, db):
        db.save_outline(self.PROJECT, 200, "Pending Outline", status="pending", error_message="waiting")
        result = db.get_outline(self.PROJECT, 200)
        assert result["status"] == "pending"
        assert result["error_message"] == "waiting"

    def test_get_all_outlines(self, db):
        db.save_outline(self.PROJECT, 5, "O5")
        db.save_outline(self.PROJECT, 1, "O1")
        db.save_outline(self.PROJECT, 10, "O10")

        outlines = db.get_all_outlines(self.PROJECT)
        numbers = [o["chapter_number"] for o in outlines]
        assert len(outlines) >= 3
        for i in range(len(numbers) - 1):
            assert numbers[i] < numbers[i + 1]

    def test_get_all_outlines_empty_project(self, db):
        result = db.get_all_outlines("empty-out")
        assert result == []

    def test_delete_outline(self, db):
        db.save_outline(self.PROJECT, 30, "To Delete")
        db.delete_outline(self.PROJECT, 30)
        result = db.get_outline(self.PROJECT, 30)
        assert result is None

    def test_delete_project_outlines(self, db):
        db.save_outline(self.PROJECT, 40, "Keep")
        db.save_outline(self.PROJECT, 41, "Keep2")
        db.delete_project_outlines(self.PROJECT)
        outlines = db.get_all_outlines(self.PROJECT)
        assert outlines == []

    def test_get_outline_count(self, db):
        db.save_outline("count-out", 1, "Done", status="done")
        db.save_outline("count-out", 2, "Pending", status="pending")
        db.save_outline("count-out", 3, "Done2", status="done")

        count = db.get_outline_count("count-out")
        assert count["total"] == 3
        assert count["completed"] == 2

    def test_get_outline_count_empty(self, db):
        count = db.get_outline_count("empty-out-cnt")
        assert count["total"] == 0
        assert count["completed"] == 0

    def test_save_outline_scenes_none_defaults_to_empty(self, db):
        db.save_outline(self.PROJECT, 300, "None scenes", scenes=None)
        result = db.get_outline(self.PROJECT, 300)
        assert result["scenes"] == []

    def test_save_outline_characters_none_defaults_to_empty(self, db):
        db.save_outline(self.PROJECT, 301, "None chars", characters=None)
        result = db.get_outline(self.PROJECT, 301)
        assert result["characters"] == []

    def test_save_outline_key_points_none_defaults_to_empty(self, db):
        db.save_outline(self.PROJECT, 302, "None kp", key_points=None)
        result = db.get_outline(self.PROJECT, 302)
        assert result["key_points"] == []


# ======================================================================
# Outline Generation Status
# ======================================================================

class TestOutlineGenerationStatus:

    PROJECT = "ogs-proj"

    def test_get_outline_generation_status_returns_none_for_missing(self, db):
        result = db.get_outline_generation_status("no-such-proj")
        assert result is None

    def test_start_and_get_outline_generation(self, db):
        db.start_outline_generation(self.PROJECT, 10)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result is not None
        assert result["project_id"] == self.PROJECT
        assert result["total_chapters"] == 10
        assert result["is_running"] is True
        assert result["is_paused"] is False
        assert result["current_chapter"] == 0
        assert result["completed_chapters"] == 0
        assert result["failed_chapters"] == 0

    def test_start_outline_generation_with_config(self, db):
        config = '{"model": "gpt-4", "style": "literary"}'
        db.start_outline_generation(self.PROJECT, 10, config=config)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["config"] == config

    def test_start_outline_generation_resets_state(self, db):
        db.start_outline_generation(self.PROJECT, 5)
        db.update_outline_generation_progress(self.PROJECT, 2, completed=2, failed=1)
        db.start_outline_generation(self.PROJECT, 8)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["total_chapters"] == 8
        assert result["current_chapter"] == 0
        assert result["completed_chapters"] == 0
        assert result["failed_chapters"] == 0

    def test_update_outline_generation_progress(self, db):
        db.start_outline_generation(self.PROJECT, 20)
        db.update_outline_generation_progress(self.PROJECT, 5, completed=5, failed=1)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["current_chapter"] == 5
        assert result["completed_chapters"] == 5
        assert result["failed_chapters"] == 1

    def test_update_outline_generation_progress_partial(self, db):
        db.start_outline_generation("ogs-partial", 10)
        db.update_outline_generation_progress("ogs-partial", 3, completed=3)
        result = db.get_outline_generation_status("ogs-partial")
        assert result["current_chapter"] == 3
        assert result["completed_chapters"] == 3
        assert result["failed_chapters"] == 0

    def test_pause_outline_generation(self, db):
        db.start_outline_generation(self.PROJECT, 10)
        db.pause_outline_generation(self.PROJECT)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["is_paused"] is True
        assert result["is_running"] is True

    def test_resume_outline_generation(self, db):
        db.start_outline_generation(self.PROJECT, 10)
        db.pause_outline_generation(self.PROJECT)
        db.resume_outline_generation(self.PROJECT)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["is_paused"] is False

    def test_stop_outline_generation(self, db):
        db.start_outline_generation(self.PROJECT, 10)
        db.stop_outline_generation(self.PROJECT)

        result = db.get_outline_generation_status(self.PROJECT)
        assert result["is_running"] is False
        assert result["is_paused"] is False

    def test_pause_outline_generation_noop_on_missing(self, db):
        db.pause_outline_generation("no-such")
        result = db.get_outline_generation_status("no-such")
        assert result is None

    def test_stop_outline_generation_noop_on_missing(self, db):
        db.stop_outline_generation("no-such")
        result = db.get_outline_generation_status("no-such")
        assert result is None


# ======================================================================
# Chapter Generation Status
# ======================================================================

class TestChapterGenerationStatus:

    PROJECT = "gs-proj"

    def test_get_generation_status_returns_none_for_missing(self, db):
        result = db.get_generation_status("no-such-proj")
        assert result is None

    def test_start_and_get_generation(self, db):
        db.start_generation(self.PROJECT, 15)

        result = db.get_generation_status(self.PROJECT)
        assert result is not None
        assert result["project_id"] == self.PROJECT
        assert result["total_chapters"] == 15
        assert result["is_running"] is True
        assert result["is_paused"] is False
        assert result["current_chapter"] == 0
        assert result["completed_chapters"] == 0
        assert result["failed_chapters"] == 0

    def test_start_generation_with_config(self, db):
        config = '{"model": "claude", "temperature": 0.7}'
        db.start_generation(self.PROJECT, 10, config=config)

        result = db.get_generation_status(self.PROJECT)
        assert result["config"] == config

    def test_start_generation_resets_state(self, db):
        db.start_generation(self.PROJECT, 5)
        db.update_generation_progress(self.PROJECT, 3, completed=3, failed=1)
        db.start_generation(self.PROJECT, 12)

        result = db.get_generation_status(self.PROJECT)
        assert result["total_chapters"] == 12
        assert result["current_chapter"] == 0
        assert result["completed_chapters"] == 0

    def test_update_generation_progress(self, db):
        db.start_generation(self.PROJECT, 30)
        db.update_generation_progress(self.PROJECT, 10, completed=10, failed=2)

        result = db.get_generation_status(self.PROJECT)
        assert result["current_chapter"] == 10
        assert result["completed_chapters"] == 10
        assert result["failed_chapters"] == 2

    def test_update_generation_progress_partial(self, db):
        db.start_generation("gs-partial", 10)
        db.update_generation_progress("gs-partial", 7, failed=0)
        result = db.get_generation_status("gs-partial")
        assert result["current_chapter"] == 7
        assert result["failed_chapters"] == 0
        assert result["completed_chapters"] == 0

    def test_pause_generation(self, db):
        db.start_generation(self.PROJECT, 10)
        db.pause_generation(self.PROJECT)

        result = db.get_generation_status(self.PROJECT)
        assert result["is_paused"] is True
        assert result["is_running"] is True

    def test_resume_generation(self, db):
        db.start_generation(self.PROJECT, 10)
        db.pause_generation(self.PROJECT)
        db.resume_generation(self.PROJECT)

        result = db.get_generation_status(self.PROJECT)
        assert result["is_paused"] is False

    def test_stop_generation(self, db):
        db.start_generation(self.PROJECT, 10)
        db.stop_generation(self.PROJECT)

        result = db.get_generation_status(self.PROJECT)
        assert result["is_running"] is False
        assert result["is_paused"] is False

    def test_get_pending_chapters_all_pending(self, db):
        pending = db.get_pending_chapters("pc-proj", 5)
        assert pending == [1, 2, 3, 4, 5]

    def test_get_pending_chapters_some_done(self, db):
        db.save_chapter("pc-proj", 1, "Done", "content", status="done")
        db.save_chapter("pc-proj", 3, "Done3", "content", status="done")

        pending = db.get_pending_chapters("pc-proj", 5)
        assert pending == [2, 4, 5]

    def test_get_pending_chapters_all_done(self, db):
        db.save_chapter("pc-done", 1, "Done1", "content", status="done")
        db.save_chapter("pc-done", 2, "Done2", "content", status="done")
        db.save_chapter("pc-done", 3, "Done3", "content", status="done")

        pending = db.get_pending_chapters("pc-done", 3)
        assert pending == []

    def test_get_pending_chapters_single(self, db):
        pending = db.get_pending_chapters("pc-single", 1)
        assert pending == [1]

        db.save_chapter("pc-single", 1, "Done", "content", status="done")
        pending = db.get_pending_chapters("pc-single", 1)
        assert pending == []

    def test_pause_generation_noop_on_missing(self, db):
        db.pause_generation("no-such")
        result = db.get_generation_status("no-such")
        assert result is None

    def test_stop_generation_noop_on_missing(self, db):
        db.stop_generation("no-such")
        result = db.get_generation_status("no-such")
        assert result is None
