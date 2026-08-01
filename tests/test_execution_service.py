from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_gen():
    gen = MagicMock()
    gen._generate_json = MagicMock()
    gen.client = MagicMock()
    return gen


@pytest.fixture
def mock_databridge():
    with patch("app.services.execution_service.DataBridge") as mock:
        yield mock


@pytest.fixture
def mock_database_v2():
    with patch("app.services.execution_service.database_v2") as mock:
        yield mock


# ========== M14: SceneService ==========

class TestSceneService:
    def test_design_returns_result_with_valid_scenes(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import SceneService

            chapter_outline = {"title": "Chapter 1", "summary": "英雄踏上征程"}
            expected_scenes = {"scenes": [{"scene_id": "s1", "title": "Opening"}]}
            mock_gen._generate_json.return_value = (expected_scenes, None)

            result, err = SceneService.design("proj-1", chapter_outline)

            assert err is None
            assert result == expected_scenes
            mock_gen._generate_json.assert_called_once()
            call_args = mock_gen._generate_json.call_args
            assert call_args[1].get("max_tokens") == 8000
            assert call_args[1].get("module_name") == "scene_design"
            mock_databridge.write.assert_called_once_with(
                "proj-1", "chapter_plan",
                [{"scene_designs": expected_scenes["scenes"]}]
            )

    def test_design_returns_error_when_generator_unavailable(self):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import SceneService

            result, err = SceneService.design("proj-1", {"title": "Test"})

            assert result is None
            assert err == "AI生成器未配置"

    def test_design_returns_error_from_generator(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import SceneService

            mock_gen._generate_json.return_value = (None, "Token limit exceeded")

            result, err = SceneService.design("proj-1", {"title": "Test"})

            assert result is None
            assert err == "Token limit exceeded"

    def test_design_result_is_not_dict_skips_databridge_write(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import SceneService

            mock_gen._generate_json.return_value = ([{"scenes": []}], None)

            result, err = SceneService.design("proj-1", {"title": "Test"})

            assert err is None
            assert result == [{"scenes": []}]
            mock_databridge.write.assert_not_called()

    def test_save_routes_to_chapter_plan(self):
        from app.services.execution_service import SceneService

        result, err = SceneService.save("proj-1", "scene-001", {"title": "Test Scene"})

        assert err is None
        assert result["saved"] is True
        assert result["note"] == "routed to chapter_plan"


# ========== M15: DraftService ==========

class TestDraftService:
    def test_generate_stream_yields_error_when_generator_unavailable(self):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import DraftService

            chunks = list(DraftService.generate_stream("proj-1", "1", {"title": "Scene"}))
            assert len(chunks) == 1
            assert chunks[0] == {"error": "AI生成器未配置"}

    def test_generate_stream_yields_chunks_and_done(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import DraftService

            mock_gen.client.generate_stream.return_value = iter([
                {"content": "第一章开头"},
                {"content": "主角出现在城门前"},
                {"done": True},
            ])

            chunks = list(DraftService.generate_stream("proj-1", "3", {"title": "Scene A"}))

            assert len(chunks) == 3
            assert chunks[0] == {"type": "chunk", "content": "第一章开头", "full_length": 5}
            assert chunks[1] == {"type": "chunk", "content": "主角出现在城门前", "full_length": 13}
            assert chunks[2]["type"] == "done"
            assert chunks[2]["content"] == "第一章开头主角出现在城门前"
            assert chunks[2]["length"] == 13
            mock_databridge.write.assert_called_once()
            call_args = mock_databridge.write.call_args
            assert call_args[0][0] == "proj-1"
            assert call_args[0][1] == "draft"

    def test_generate_stream_handles_string_chunks(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import DraftService

            mock_gen.client.generate_stream.return_value = iter([
                "文字内容",
                "",
                {"done": True},
            ])

            chunks = list(DraftService.generate_stream("proj-1", "2", {"title": "Scene B"}))

            content_chunks = [c for c in chunks if c.get("type") == "chunk"]
            assert len(content_chunks) == 1
            assert content_chunks[0]["content"] == "文字内容"

    def test_generate_stream_handles_error_chunk(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import DraftService

            mock_gen.client.generate_stream.return_value = iter([
                {"error": "rate limit exceeded"},
            ])

            chunks = list(DraftService.generate_stream("proj-1", "1", {"title": "Scene"}))

            assert len(chunks) == 1
            assert chunks[0]["type"] == "error"
            assert chunks[0]["message"] == "rate limit exceeded"

    def test_generate_stream_handles_exception(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import DraftService

            mock_gen.client.generate_stream.side_effect = RuntimeError("Connection lost")

            chunks = list(DraftService.generate_stream("proj-1", "1", {"title": "Scene"}))

            assert len(chunks) == 1
            assert chunks[0]["type"] == "error"
            assert "Connection lost" in chunks[0]["message"]

    def test_save_returns_success(self, mock_databridge):
        from app.services.execution_service import DraftService

        result, err = DraftService.save("proj-1", "5", {"content": "text"})

        assert err is None
        assert result["saved"] is True
        mock_databridge.write.assert_called_once_with("proj-1", "draft", {"5": {"content": "text"}})

    def test_save_returns_error_on_exception(self, mock_databridge):
        from app.services.execution_service import DraftService

        mock_databridge.write.side_effect = OSError("Disk full")

        result, err = DraftService.save("proj-1", "5", {"content": "text"})

        assert result is None
        assert "Disk full" in err
        mock_databridge.write.assert_called_once()


# ========== M16: PolishService ==========

class TestPolishService:
    def test_polish_returns_result(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import PolishService

            expected = {"content": "润色后内容", "changes": ["修改了措辞"], "summary": "优化完成"}
            mock_gen._generate_json.return_value = (expected, None)

            result, err = PolishService.polish("proj-1", "原始正文内容")

            assert err is None
            assert result == expected
            mock_gen._generate_json.assert_called_once()
            call_args = mock_gen._generate_json.call_args
            assert call_args[1].get("max_tokens") == 8000
            assert call_args[1].get("module_name") == "polish"

    def test_polish_returns_error_when_generator_unavailable(self):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import PolishService

            result, err = PolishService.polish("proj-1", "content")

            assert result is None
            assert err == "AI生成器未配置"

    def test_polish_returns_error_from_generator(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import PolishService

            mock_gen._generate_json.return_value = (None, "Model timeout")

            result, err = PolishService.polish("proj-1", "content")

            assert result is None
            assert err == "Model timeout"

    def test_polish_with_style_profile_includes_style_in_prompt(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import PolishService

            style = {"narrative_perspective": "第一人称", "tone": "轻松", "pacing": "快节奏"}
            mock_gen._generate_json.return_value = ({"content": "润色后"}, None)

            PolishService.polish("proj-1", "content", style_profile=style)

            prompt = mock_gen._generate_json.call_args[0][0]
            assert "参考风格" in prompt
            assert "narrative_perspective" in prompt
            assert "第一人称" in prompt

    def test_polish_with_foreshadow_protected(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import PolishService

            mock_gen._generate_json.return_value = ({"content": "润色后"}, None)

            result, err = PolishService.polish(
                "proj-1", "content",
                focus="节奏优化",
                foreshadow_protected=["伏笔A", "伏笔B"]
            )

            assert err is None


# ========== M17: ContentParserService ==========

class TestContentParserService:
    def test_parse_returns_result(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ContentParserService

            expected = {
                "scene_segments": [],
                "dialogue_extraction": [],
                "status_changes": [],
            }
            mock_gen._generate_json.return_value = (expected, None)

            result, err = ContentParserService.parse("proj-1", "3", "正文内容")

            assert err is None
            assert result == expected
            mock_gen._generate_json.assert_called_once()

    def test_parse_returns_error_when_generator_unavailable(self):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import ContentParserService

            result, err = ContentParserService.parse("proj-1", "1", "content")

            assert result is None
            assert err == "AI生成器未配置"

    def test_parse_triggers_knowledge_update_on_status_changes(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ContentParserService

            expected = {
                "scene_segments": [],
                "status_changes": [
                    {"entity": "主角", "attribute": "hp", "old_value": "100", "new_value": "80"},
                    {"entity": "配角", "attribute": "mood", "old_value": "happy", "new_value": "angry"},
                ],
            }
            mock_gen._generate_json.return_value = (expected, None)

            result, err = ContentParserService.parse("proj-1", "2", "正文")

            assert err is None
            assert mock_databridge.write.call_count == 2
            mock_databridge.write.assert_any_call("proj-1", "parse", {
                "change": expected["status_changes"][0],
                "chapter_no": "2",
            })
            mock_databridge.write.assert_any_call("proj-1", "parse", {
                "change": expected["status_changes"][1],
                "chapter_no": "2",
            })

    def test_parse_with_existing_characters_adds_context(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ContentParserService

            mock_gen._generate_json.return_value = ({"scene_segments": []}, None)
            characters = [{"name": "张三"}, {"name": "李四"}, {}]

            ContentParserService.parse("proj-1", "1", "content", existing_characters=characters)

            prompt = mock_gen._generate_json.call_args[0][0]
            assert "已知角色" in prompt
            assert "张三" in prompt
            assert "李四" in prompt

    def test_parse_result_not_dict_skips_knowledge_update(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ContentParserService

            mock_gen._generate_json.return_value = (["not a dict"], None)

            result, err = ContentParserService.parse("proj-1", "1", "content")

            assert err is None
            mock_databridge.write.assert_not_called()


# ========== M18: KnowledgeService ==========

class TestKnowledgeService:
    def test_update_applies_status_changes(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.return_value = {
            "character_states": {"主角.hp": "100"},
            "plot_state": {},
            "world_state": {},
        }
        parse_result = {
            "status_changes": [
                {"entity": "角色_A", "attribute": "hp", "new_value": "80"},
                {"entity": "世界_X", "attribute": "weather", "new_value": "rain"},
                {"entity": "剧情主线", "attribute": "climax", "new_value": "event-A"},
            ],
        }

        result, err = KnowledgeService.update("proj-1", "5", parse_result)

        assert err is None
        assert result["updated"] is True
        mock_databridge.read.assert_called_once_with("proj-1", "parse")
        mock_databridge.write.assert_called_once()
        write_args = mock_databridge.write.call_args
        assert write_args[0][0] == "proj-1"
        assert write_args[0][1] == "parse"
        data = write_args[0][2]
        assert data["character_states"]["角色_A.hp"] == "80"
        assert data["world_state"]["weather"] == "rain"
        assert data["plot_state"]["剧情主线.climax"] == "event-A"
        assert data["last_updated_chapter"] == "5"

    def test_update_handles_non_dict_current_state(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.return_value = "not a dict"

        result, err = KnowledgeService.update("proj-1", "1", {"status_changes": []})

        assert err is None
        assert result["updated"] is True
        mock_databridge.write.assert_not_called()

    def test_update_handles_empty_status_changes(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.return_value = {
            "character_states": {},
            "plot_state": {},
            "world_state": {},
        }

        result, err = KnowledgeService.update("proj-1", "1", {"status_changes": []})

        assert err is None
        assert result["updated"] is True

    def test_update_returns_error_on_exception(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.side_effect = RuntimeError("DB unavailable")

        result, err = KnowledgeService.update("proj-1", "1", {"status_changes": []})

        assert result is None
        assert "DB unavailable" in err

    def test_snapshot_returns_state(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        expected_state = {
            "character_states": {"char1.hp": "50"},
            "plot_state": {"act": "2"},
            "world_state": {"weather": "sunny"},
        }
        mock_databridge.read.return_value = expected_state

        result, err = KnowledgeService.snapshot("proj-1")

        assert err is None
        assert result == expected_state
        mock_databridge.read.assert_called_once_with("proj-1", "parse")

    def test_snapshot_returns_empty_on_no_state(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.return_value = None

        result, err = KnowledgeService.snapshot("proj-1")

        assert err is None
        assert result == {"character_states": {}, "plot_state": {}, "world_state": {}}

    def test_snapshot_returns_error_on_exception(self, mock_databridge):
        from app.services.execution_service import KnowledgeService

        mock_databridge.read.side_effect = RuntimeError("DB unavailable")

        result, err = KnowledgeService.snapshot("proj-1")

        assert result is None
        assert "DB unavailable" in err

    def test_get_foreshadows_returns_list(self, mock_database_v2):
        from app.services.execution_service import KnowledgeService

        foreshadows = [
            {"id": "f1", "description": "戒指的秘密", "status": "planted"},
            {"id": "f2", "description": "老头的身份", "status": "payoff"},
        ]
        mock_database_v2.get_foreshadows.return_value = foreshadows

        result, err = KnowledgeService.get_foreshadows("proj-1", status="planted")

        assert err is None
        assert result["foreshadows"] == foreshadows
        assert result["count"] == 2
        mock_database_v2.get_foreshadows.assert_called_once_with("proj-1", status="planted")

    def test_get_foreshadows_returns_empty_when_none(self, mock_database_v2):
        from app.services.execution_service import KnowledgeService

        mock_database_v2.get_foreshadows.return_value = None

        result, err = KnowledgeService.get_foreshadows("proj-1")

        assert err is None
        assert result["foreshadows"] == []
        assert result["count"] == 0

    def test_get_foreshadows_returns_error_on_exception(self, mock_database_v2):
        from app.services.execution_service import KnowledgeService

        mock_database_v2.get_foreshadows.side_effect = RuntimeError("DB unavailable")

        result, err = KnowledgeService.get_foreshadows("proj-1")

        assert result is None
        assert "DB unavailable" in err


# ========== M19: ConsistencyService ==========

class TestConsistencyService:
    def test_check_returns_result_and_saves_report(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            expected = {
                "overall_score": 85,
                "passed": True,
                "checks": [{"dimension": "character_trait", "score": 90, "issues": []}],
                "critical_issues": [],
                "summary": "一致性优秀",
            }
            mock_gen._generate_json.return_value = (expected, None)

            result, err = ConsistencyService.check("proj-1", "3", content="正文内容")

            assert err is None
            assert result == expected
            mock_databridge.write.assert_called_once_with("proj-1", "consistency", {
                "chapter_no": "3",
                "overall_score": 85,
                "passed": True,
                "checks": [{"dimension": "character_trait", "score": 90, "issues": []}],
                "critical_issues": [],
                **expected,
            })

    def test_check_returns_error_when_generator_unavailable(self):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import ConsistencyService

            result, err = ConsistencyService.check("proj-1", "1")

            assert result is None
            assert err == "AI生成器未配置"

    def test_check_returns_error_from_generator(self, mock_gen):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_gen._generate_json.return_value = (None, "AI service unavailable")

            result, err = ConsistencyService.check("proj-1", "1")

            assert result is None
            assert err == "AI service unavailable"

    def test_check_result_not_dict_skips_databridge_write(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_gen._generate_json.return_value = (["not a dict"], None)

            result, err = ConsistencyService.check("proj-1", "1")

            assert err is None
            assert result == ["not a dict"]
            mock_databridge.write.assert_not_called()

    def test_world_check_returns_error_when_world_data_missing(self, mock_databridge):
        with patch("app.services.execution_service._get_default_generator"):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = None

            result, err = ConsistencyService.world_check("proj-1")

            assert err is None
            assert result["passed"] is False
            assert result["message"] == "世界观数据不存在"
            assert result["score"] == 0

    def test_world_check_skips_check_when_ai_unavailable(self, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = {"origin": {}, "rules": []}

            result, err = ConsistencyService.world_check("proj-1")

            assert err is None
            assert result["passed"] is True
            assert result["message"] == "AI未配置，跳过检查"
            assert result["score"] == 100

    def test_world_check_performs_ai_analysis(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = {
                "origin": {"type": "magic"},
                "rules": [{"rule": "gravity"}],
                "structure": {},
                "civilization": {},
                "history": {},
            }
            mock_gen._generate_json.return_value = (
                {"passed": True, "score": 95, "issues": [], "summary": "世界规则一致"},
                None,
            )

            result, err = ConsistencyService.world_check("proj-1")

            assert err is None
            assert result["passed"] is True
            assert result["score"] == 95
            assert result["summary"] == "世界规则一致"
            assert result["message"] == "AI一致性分析完成"
            mock_gen._generate_json.assert_called_once()
            call_args = mock_gen._generate_json.call_args
            assert call_args[1].get("max_tokens") == 2000
            assert call_args[1].get("module_name") == "world_consistency_check"

    def test_world_check_handles_ai_error(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = {"origin": {}}
            mock_gen._generate_json.return_value = (None, "LLM timeout")

            result, err = ConsistencyService.world_check("proj-1")

            assert err is None
            assert result["passed"] is False
            assert "LLM timeout" in result["message"]
            assert result["status"] == "unavailable"
            assert result["score"] == 0

    def test_world_check_handles_exception(self, mock_databridge):
        from app.services.execution_service import ConsistencyService

        mock_databridge.read.side_effect = RuntimeError("DB connection lost")

        result, err = ConsistencyService.world_check("proj-1")

        assert result is None
        assert "DB connection lost" in err

    def test_character_check_returns_error_when_characters_missing(self, mock_databridge):
        with patch("app.services.execution_service._get_default_generator"):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = None

            result, err = ConsistencyService.character_check("proj-1")

            assert err is None
            assert result["passed"] is False
            assert result["message"] == "角色数据不存在"
            assert result["score"] == 0

    def test_character_check_skips_check_when_ai_unavailable(self, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=None):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = [{"name": "Hero"}]

            result, err = ConsistencyService.character_check("proj-1")

            assert err is None
            assert result["passed"] is True
            assert result["message"] == "AI未配置，跳过检查"
            assert result["score"] == 100

    def test_character_check_performs_ai_analysis(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = [
                {"name": "Alice", "role": "主角", "personality": "勇敢"},
                {"name": "Bob", "role": "配角", "personality": "幽默"},
            ]
            mock_gen._generate_json.return_value = (
                {"passed": True, "score": 90, "issues": [], "summary": "角色一致"},
                None,
            )

            result, err = ConsistencyService.character_check("proj-1")

            assert err is None
            assert result["passed"] is True
            assert result["score"] == 90
            assert result["message"] == "AI一致性分析完成"
            mock_gen._generate_json.assert_called_once()
            call_args = mock_gen._generate_json.call_args
            assert call_args[1].get("module_name") == "character_consistency_check"

    def test_character_check_handles_ai_error(self, mock_gen, mock_databridge):
        with patch("app.services.execution_service._get_default_generator", return_value=mock_gen):
            from app.services.execution_service import ConsistencyService

            mock_databridge.read.return_value = [{"name": "Hero"}]
            mock_gen._generate_json.return_value = (None, "API error")

            result, err = ConsistencyService.character_check("proj-1")

            assert err is None
            assert result["passed"] is False
            assert result["status"] == "unavailable"

    def test_character_check_handles_exception(self, mock_databridge):
        from app.services.execution_service import ConsistencyService

        mock_databridge.read.side_effect = RuntimeError("DB connection lost")

        result, err = ConsistencyService.character_check("proj-1")

        assert result is None
        assert "DB connection lost" in err

    def test_get_report_returns_all_reports(self, mock_database_v2):
        from app.services.execution_service import ConsistencyService

        reports = [
            {"chapter_no": "1", "score": 85, "items": [], "fixes": [], "summary": "s1"},
            {"chapter_no": "2", "score": 90, "items": [], "fixes": [], "summary": "s2"},
        ]
        mock_database_v2.get_consistency_reports.return_value = reports

        result, err = ConsistencyService.get_report("proj-1")

        assert err is None
        assert result["count"] == 2
        assert result["reports"][0]["overall_score"] == 85
        assert result["reports"][1]["overall_score"] == 90
        mock_database_v2.get_consistency_reports.assert_called_once_with("proj-1", limit=50)

    def test_get_report_filters_by_chapter(self, mock_database_v2):
        from app.services.execution_service import ConsistencyService

        reports = [
            {"chapter_no": "1", "score": 85, "items": [], "fixes": [], "summary": "s1"},
            {"chapter_no": "2", "score": 90, "items": [], "fixes": [], "summary": "s2"},
            {"chapter_no": "1", "score": 80, "items": [], "fixes": [], "summary": "s3"},
        ]
        mock_database_v2.get_consistency_reports.return_value = reports

        result, err = ConsistencyService.get_report("proj-1", chapter_no="1")

        assert err is None
        assert result["count"] == 2
        for report in result["reports"]:
            assert report["chapter_no"] == "1"

    def test_get_report_handles_none_reports(self, mock_database_v2):
        from app.services.execution_service import ConsistencyService

        mock_database_v2.get_consistency_reports.return_value = None

        result, err = ConsistencyService.get_report("proj-1")

        assert err is None
        assert result["reports"] == []
        assert result["count"] == 0

    def test_get_report_returns_error_on_exception(self, mock_database_v2):
        from app.services.execution_service import ConsistencyService

        mock_database_v2.get_consistency_reports.side_effect = RuntimeError("DB unavailable")

        result, err = ConsistencyService.get_report("proj-1")

        assert result is None
        assert "DB unavailable" in err
