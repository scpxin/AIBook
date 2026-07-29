"""Pipeline API 端到端测试 — 12 端点 + 状态机全生命周期"""
import pytest

# ========== 模块列表 ==========


class TestPipelineModules:
    """GET /api/v2/pipeline/modules"""

    def test_list_13_modules(self, client):
        resp = client.get("/api/v2/pipeline/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 13
        names = [m["name"] for m in data["modules"]]
        assert "idea" in names
        assert "consistency" in names
        assert names[0] == "idea"

    def test_module_has_layer_and_dependencies(self, client):
        resp = client.get("/api/v2/pipeline/modules")
        for m in resp.json()["modules"]:
            assert "name" in m
            assert "layer" in m
            assert "dependencies" in m
            assert "is_parallel" in m
            assert "is_iterative" in m

    def test_first_module_no_dependencies(self, client):
        resp = client.get("/api/v2/pipeline/modules")
        first = resp.json()["modules"][0]
        assert first["name"] == "idea"
        assert first["dependencies"] == []


# ========== 状态机 (mock DB) ==========


class TestPipelineStateMachine:
    """GET/POST /api/v2/pipeline/{id}/status + modules/{name}/status"""

    def test_initial_status_creates_state(self, client):
        resp = client.get("/api/v2/pipeline/test-init/status")
        assert resp.status_code == 200
        state = resp.json()
        assert state["project_id"] == "test-init"
        assert state["total_modules"] == 13
        assert state["completed"] == 0
        assert state["progress_pct"] == 0.0
        assert state["current_module"] == "idea"

    def test_initial_modules_locked_except_idea(self, client):
        resp = client.get("/api/v2/pipeline/test-lock/status")
        modules = resp.json()["modules"]
        assert modules["idea"]["status"] == "pending"
        assert modules["project"]["status"] == "locked"

    def test_update_module_to_done(self, client):
        client.post("/api/v2/pipeline/test-done/modules/idea/status",
                    json={"status": "done"})
        resp = client.get("/api/v2/pipeline/test-done/status")
        assert resp.json()["modules"]["idea"]["status"] == "done"

    def test_done_unlocks_dependent(self, client):
        client.post("/api/v2/pipeline/test-unlock/modules/idea/status",
                    json={"status": "done"})
        resp = client.get("/api/v2/pipeline/test-unlock/status")
        assert resp.json()["modules"]["project"]["status"] == "pending"

    def test_update_to_generating(self, client):
        client.post("/api/v2/pipeline/test-gen/modules/idea/status",
                    json={"status": "generating"})
        resp = client.get("/api/v2/pipeline/test-gen/status")
        assert resp.json()["modules"]["idea"]["status"] == "generating"

    def test_update_to_failed(self, client):
        client.post("/api/v2/pipeline/test-fail/modules/idea/status",
                    json={"status": "failed", "error": "AI 调用超时"})
        resp = client.get("/api/v2/pipeline/test-fail/status")
        mod = resp.json()["modules"]["idea"]
        assert mod["status"] == "failed"
        assert mod["retry_count"] == 1

    def test_invalid_module_name_404(self, client):
        resp = client.get("/api/v2/pipeline/test-x/modules/nonexistent/status")
        assert resp.status_code == 404

    def test_invalid_status_pydantic_rejected(self, client):
        resp = client.post("/api/v2/pipeline/test-x/modules/idea/status",
                          json={"status": "invalid_status"})
        assert resp.status_code == 422

    def test_full_progress_tracking(self, client):
        pid = "test-progress"
        for mod in ["idea", "project", "world"]:
            client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                       json={"status": "done"})
        state = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert state["completed"] == 3
        assert state["progress_pct"] == pytest.approx(23.1, abs=0.1)

    def test_module_status_detail(self, client):
        pid = "test-detail"
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "done"})
        resp = client.get(f"/api/v2/pipeline/{pid}/modules/idea/status")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status"] == "done"
        assert detail["module"]["name"] == "idea"
        assert detail["module"]["display_name"] == "灵感"


# ========== 下一个模块 ==========


class TestNextModule:
    """GET /api/v2/pipeline/{id}/next"""

    def test_next_initial_is_idea(self, client):
        resp = client.get("/api/v2/pipeline/test-next-0/next")
        assert resp.json()["next_module"] == "idea"

    def test_next_after_idea_is_project(self, client):
        pid = "test-next-1"
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "done"})
        resp = client.get(f"/api/v2/pipeline/{pid}/next")
        assert resp.json()["next_module"] == "project"

    def test_next_when_all_done_returns_none(self, client):
        pid = "test-next-all"
        for mod in ["idea", "project", "world", "characters", "architecture",
                    "relation_map", "outline"]:
            client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                       json={"status": "done"})
        remaining = ["volumes", "chapter_plan", "draft", "parse", "polish", "consistency"]
        for mod in remaining:
            client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                       json={"status": "done"})
        resp = client.get(f"/api/v2/pipeline/{pid}/next")
        assert resp.json()["next_module"] is None

    def test_next_skips_failed_respects_deps(self, client):
        pid = "test-next-fail"
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "done"})
        client.post(f"/api/v2/pipeline/{pid}/modules/project/status",
                   json={"status": "failed"})
        resp = client.get(f"/api/v2/pipeline/{pid}/next")
        assert resp.json()["next_module"] is None


# ========== 确认灵感 ==========


class TestConfirmIdea:
    """POST /api/v2/pipeline/{id}/confirm-idea"""

    def test_confirm_idea_marks_done(self, client):
        resp = client.post("/api/v2/pipeline/test-confirm/confirm-idea",
                          json={"idea_id": "idea-1"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_confirm_idea_with_description(self, client):
        resp = client.post("/api/v2/pipeline/test-confirm-desc/confirm-idea",
                          json={"idea": "修仙+都市+复仇"})
        assert resp.json()["success"] is True


# ========== 清理 ==========


class TestCleanup:
    """DELETE /api/v2/pipeline/{id}"""

    def test_delete_without_confirm(self, client):
        resp = client.delete("/api/v2/pipeline/test-del")
        assert resp.status_code == 400

    def test_delete_with_confirm(self, client):
        pid = "test-del-ok"
        client.get(f"/api/v2/pipeline/{pid}/status")
        resp = client.delete(f"/api/v2/pipeline/{pid}?confirm=true")
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ========== 数据查询 ==========


class TestModuleData:
    """GET /api/v2/pipeline/{id}/data + /data/{name}"""

    def test_get_data_unknown_module_404(self, client):
        resp = client.get("/api/v2/pipeline/test-data/nonexistent/data/nonexistent")
        assert resp.status_code == 404

    def test_get_data_for_known_module(self, client):
        resp = client.get("/api/v2/pipeline/test-data-known/data/idea")
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "idea"

    def test_get_all_module_data(self, client):
        resp = client.get("/api/v2/pipeline/test-all-data/data")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-all-data"
        assert "modules" in data


# ========== 状态机边界用例 ==========


class TestPipelineEdgeCases:
    """边界和错误处理"""

    def test_same_project_different_states_independent(self, client):
        client.post("/api/v2/pipeline/p1/modules/idea/status",
                   json={"status": "done"})
        client.post("/api/v2/pipeline/p2/modules/idea/status",
                   json={"status": "failed"})
        s1 = client.get("/api/v2/pipeline/p1/status").json()
        s2 = client.get("/api/v2/pipeline/p2/status").json()
        assert s1["modules"]["idea"]["status"] == "done"
        assert s2["modules"]["idea"]["status"] == "failed"

    def test_concurrent_updates_same_module(self, client):
        pid = "test-concurrent"
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "generating"})
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "done"})
        resp = client.get(f"/api/v2/pipeline/{pid}/status")
        assert resp.json()["modules"]["idea"]["status"] == "done"

    def test_empty_project_id(self, client):
        resp = client.get("/api/v2/pipeline/%20/status")
        assert resp.status_code == 200

    def test_13_modules_all_have_info(self, client):
        modules = client.get("/api/v2/pipeline/modules").json()["modules"]
        for m in modules:
            resp = client.get("/api/v2/pipeline/modules")
            found = [x for x in resp.json()["modules"] if x["name"] == m["name"]]
            assert len(found) == 1
