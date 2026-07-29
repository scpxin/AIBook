from unittest.mock import MagicMock, patch

import pytest

import novel_creator.database_v2  # noqa: F401


@pytest.fixture
def app():
    """创建 FastAPI TestClient 的 app 实例（mock 启动流程和数据库依赖），每次调用完全隔离"""
    _pipeline_store = {}

    mock_db_v2 = MagicMock()
    mock_db_v2.get_pipeline_module_data.return_value = None
    mock_db_v2.get_world.return_value = None
    mock_db_v2.get_all_characters.return_value = []
    mock_db_v2.get_relation_map.return_value = None
    mock_db_v2.get_volumes.return_value = []
    mock_db_v2.get_chapter_plans.return_value = {}
    mock_db_v2.get_drafts.return_value = []
    mock_db_v2.get_consistency_reports.return_value = []
    mock_db_v2.delete_project_v2.return_value = True
    mock_db_v2.get_all_settings.return_value = {}
    mock_db_v2.set_setting.return_value = None
    mock_db_v2.save_pipeline_state.return_value = None

    _project_store = {}

    mock_novel_db = MagicMock()

    def _get_project(pid):
        return _project_store.get(pid)

    def _save_project(pid, name, step, data, cat):
        _project_store[pid] = {
            "id": pid, "name": name, "data": data,
            "updated_at": "2026-01-01 00:00:00"
        }

    mock_novel_db.get_project = MagicMock(side_effect=_get_project)
    mock_novel_db.save_project = MagicMock(side_effect=_save_project)
    mock_novel_db.init_db = MagicMock()

    mock_databridge = MagicMock()
    mock_conn = MagicMock()
    mock_conn.row_factory = None

    def _conn_execute(sql, params=()):
        result = MagicMock()
        result.fetchone.return_value = None
        result.fetchall.return_value = []
        sql_upper = sql.strip().upper()

        if sql_upper.startswith("INSERT") or "ON CONFLICT" in sql_upper:
            pid = params[0] if len(params) > 0 else ""
            mod = params[1] if len(params) > 1 else ""
            key = f"{pid}:{mod}"
            _pipeline_store[key] = {
                "id": len(_pipeline_store) + 1,
                "project_id": pid,
                "module_name": mod,
                "status": params[2] if len(params) > 2 else "pending",
                "retry_count": params[3] if len(params) > 3 else 0,
                "error": params[4] if len(params) > 4 else "",
                "consistency_score": params[5] if len(params) > 5 else 0,
                "started_at": params[6] if len(params) > 6 else "",
                "completed_at": params[7] if len(params) > 7 else "",
                "updated_at": params[8] if len(params) > 8 else "",
                "data_json": params[9] if len(params) > 9 else "{}",
            }

        elif sql_upper.startswith("SELECT"):
            pid = params[0] if len(params) > 0 else ""
            mod = params[1] if len(params) > 1 else None
            matching = []
            for k, v in _pipeline_store.items():
                if v["project_id"] == pid and (mod is None or v["module_name"] == mod):
                    matching.append(v)
            result.fetchall.return_value = matching
            if matching:
                result.fetchone.return_value = matching[0]

        return result

    mock_conn.execute = MagicMock(side_effect=_conn_execute)
    mock_conn.commit = MagicMock()
    mock_databridge._conn.return_value = mock_conn

    with patch("app.database.novel_db.init_db"), \
         patch("app.database.novel_db", mock_novel_db), \
         patch("novel_creator.database_v2.init_db_v2"), \
         patch("novel_creator.database_v2", mock_db_v2), \
         patch("novel_creator.data_bridge.DataBridge", mock_databridge), \
         patch("app.services.template_service.seed_system_templates"), \
         patch("app.api.projects.novel_db", mock_novel_db):
        import app.main
        from app.main import app as fastapi_app
        app.main._rate_limit_store.clear()
        yield fastapi_app
        app.main._rate_limit_store.clear()


@pytest.fixture
def client(app):
    """FastAPI TestClient"""
    from fastapi.testclient import TestClient
    return TestClient(app)
