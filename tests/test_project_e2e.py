"""项目保存/加载 + 完整创作流水线端到端测试"""
import uuid

# ========== 项目保存 ==========


class TestProjectSaveV2:
    """POST /api/projects/save-v2"""

    def test_save_new_project(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "id": "test-proj-001",
            "name": "测试项目",
            "modules": {
                "idea": {"selected": 1, "concept": "修仙+都市"},
                "project": {"genre": "玄幻"},
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["id"] == "test-proj-001"
        assert data["name"] == "测试项目"

    def test_save_auto_generate_id(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "name": "自动生成ID",
            "modules": {}
        })
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("proj_")

    def test_save_with_pipeline_state(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "id": "test-proj-002",
            "name": "含流水线",
            "modules": {
                "idea": {"status": "done"},
                "project": {"status": "pending"},
            },
            "pipeline": {
                "modules": {
                    "idea": {"status": "done"},
                    "project": {"status": "pending"},
                }
            }
        })
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_save_with_template_and_context(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "id": "test-proj-003",
            "name": "含模板",
            "modules": {},
            "templateSelections": {"idea": {"templateId": 1}},
            "sharedContext": {"worldType": "玄幻"}
        })
        assert resp.status_code == 200

    def test_invalid_id_rejected(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "id": "id with spaces!",
            "name": "无效ID"
        })
        assert resp.status_code == 400

    def test_modules_not_dict(self, client):
        resp = client.post("/api/projects/save-v2", json={
            "id": "test-proj-004",
            "modules": "not-a-dict"
        })
        assert resp.status_code == 400


# ========== 项目列表 ==========


class TestProjectListV2:
    """GET /api/v2/projects/list"""

    def test_list_endpoint_available(self, client):
        resp = client.get("/api/v2/projects/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data


# ========== 完整流水线流程 ==========


class TestFullPipelineFlow:
    """完整创作流水线: 创建项目 → M1-M13 推进 → 保存"""

    def test_full_create_to_save_flow(self, client):
        pid = f"flow-{uuid.uuid4().hex[:6]}"

        resp = client.get("/api/v2/pipeline/modules")
        assert resp.status_code == 200

        resp = client.get(f"/api/v2/pipeline/{pid}/status")
        assert resp.status_code == 200
        assert resp.json()["current_module"] == "idea"

        resp = client.post(f"/api/v2/pipeline/{pid}/confirm-idea",
                          json={"idea_id": "1"})
        assert resp.json()["success"] is True

        for mod in ["idea", "project", "world", "characters", "architecture", "relation_map"]:
            resp = client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                             json={"status": "done"})
            assert resp.json()["success"] is True

        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["completed"] == 6

        client.post(f"/api/v2/pipeline/{pid}/modules/outline/status",
                   json={"status": "done"})
        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["completed"] == 7

        for mod in ["volumes", "chapter_plan"]:
            client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                       json={"status": "done"})
        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["completed"] == 9

        for mod in ["draft", "parse", "polish", "consistency"]:
            client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                       json={"status": "done"})
        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["completed"] == 13
        assert status["progress_pct"] == 100.0

        resp = client.post("/api/projects/save-v2", json={
            "id": pid,
            "name": "完整流水线测试",
            "modules": {"idea": {"status": "done"}},
            "pipeline": status,
        })
        assert resp.status_code == 200

    def test_iterative_execution_loop(self, client):
        pid = f"flow-iter-{uuid.uuid4().hex[:6]}"
        for mod in ["idea", "project", "world", "characters", "architecture",
                    "relation_map", "outline", "volumes", "chapter_plan"]:
            resp = client.post(f"/api/v2/pipeline/{pid}/modules/{mod}/status",
                             json={"status": "done"})
            assert resp.status_code == 200, f"Failed to mark {mod} done: {resp.text}"

        # Mark draft done
        resp = client.post(f"/api/v2/pipeline/{pid}/modules/draft/status",
                         json={"status": "done"})
        assert resp.status_code == 200, f"Failed draft: {resp.text}"

        status = client.get(f"/api/v2/pipeline/{pid}/next").json()
        assert status["next_module"] == "parse", f"Expected parse, got: {status}"

        client.post(f"/api/v2/pipeline/{pid}/modules/parse/status",
                   json={"status": "done"})
        status = client.get(f"/api/v2/pipeline/{pid}/next").json()
        assert status["next_module"] == "polish"

        client.post(f"/api/v2/pipeline/{pid}/modules/polish/status",
                   json={"status": "done"})
        status = client.get(f"/api/v2/pipeline/{pid}/next").json()
        assert status["next_module"] == "consistency"

        client.post(f"/api/v2/pipeline/{pid}/modules/consistency/status",
                   json={"status": "done", "consistency_score": 75})
        final = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert final["completed"] == 13

    def test_failure_and_retry_flow(self, client):
        pid = f"flow-retry-{uuid.uuid4().hex[:6]}"
        client.post(f"/api/v2/pipeline/{pid}/modules/idea/status",
                   json={"status": "done"})
        client.post(f"/api/v2/pipeline/{pid}/modules/project/status",
                   json={"status": "failed", "error": "API Timeout"})

        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["modules"]["project"]["status"] == "failed"
        assert status["modules"]["project"]["retry_count"] == 1

        client.post(f"/api/v2/pipeline/{pid}/modules/project/status",
                   json={"status": "generating"})
        client.post(f"/api/v2/pipeline/{pid}/modules/project/status",
                   json={"status": "done"})

        status = client.get(f"/api/v2/pipeline/{pid}/status").json()
        assert status["modules"]["project"]["status"] == "done"
        assert status["modules"]["world"]["status"] == "pending"
