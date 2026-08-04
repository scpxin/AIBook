from unittest.mock import MagicMock, patch

import pytest

from app.services.structure_service import (
    ChapterOutlineService,
    ChapterPlanService,
    MasterOutlineService,
    PlotNodeService,
    VolumeService,
)


@pytest.fixture
def mock_databridge():
    with patch("app.services.structure_service.DataBridge") as mock:
        yield mock


@pytest.fixture
def mock_generator():
    with patch("app.services.structure_service.get_default_generator") as mock_get:
        mock_gen = MagicMock()
        mock_get.return_value = mock_gen
        yield mock_gen, mock_get


@pytest.fixture
def no_generator():
    with patch("app.services.structure_service.get_default_generator", return_value=None):
        yield


# ========== M9: MasterOutlineService ==========


class TestMasterOutlineGenerate:

    def test_no_generator_returns_error(self, no_generator):
        result, err = MasterOutlineService.generate("proj-1", {"genre": "玄幻"})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Token exhausted")

        result, err = MasterOutlineService.generate("proj-1", {"genre": "玄幻"})

        assert result is None
        assert "Token" in err

    def test_generate_success_returns_result(self, mock_generator):
        mock_gen, _ = mock_generator
        outline = {
            "opening": {"hook": "开篇钩子"},
            "volume_structure": [{"volume_no": 1, "title": "卷1"}],
        }
        mock_gen._generate_json.return_value = (outline, None)

        result, err = MasterOutlineService.generate("proj-1", {"genre": "玄幻"})

        assert err is None
        assert result["opening"]["hook"] == "开篇钩子"
        assert len(result["volume_structure"]) == 1

    def test_generate_with_style_profile_calls_ai(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({}, None)

        style = {"tone": "dark", "pacing": "fast"}
        result, err = MasterOutlineService.generate("proj-1", {"genre": "玄幻"}, style_profile=style)

        assert err is None
        call_args = mock_gen._generate_json.call_args
        prompt = call_args[0][0]
        assert "=== 参考风格 ===" in prompt
        assert "dark" in prompt


class TestMasterOutlineSave:

    def test_save_writes_to_databridge(self, mock_databridge):
        mock_databridge.read.return_value = {}

        result, err = MasterOutlineService.save("proj-1", {"opening": {"hook": "test"}})

        assert err is None
        assert result["saved"] is True
        mock_databridge.write.assert_called_once()
        args = mock_databridge.write.call_args
        assert args[0][0] == "proj-1"
        assert args[0][1] == "architecture"
        assert args[0][2]["master_outline"]["opening"]["hook"] == "test"

    def test_save_merges_with_existing_data(self, mock_databridge):
        existing = {"existing_field": "value"}
        mock_databridge.read.return_value = existing

        result, err = MasterOutlineService.save("proj-1", {"opening": {"hook": "test"}})

        assert err is None
        args = mock_databridge.write.call_args
        assert args[0][2]["existing_field"] == "value"
        assert "master_outline" in args[0][2]

    def test_save_handles_exception(self, mock_databridge):
        mock_databridge.read.side_effect = RuntimeError("数据库故障")

        result, err = MasterOutlineService.save("proj-1", {"opening": {}})

        assert result is None
        assert "数据库故障" in err


# ========== M10: VolumeService ==========


class TestVolumeGenerate:

    def test_no_generator_returns_error(self, no_generator):
        result, err = VolumeService.generate("proj-1", 1, {"volume_structure": []})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Rate limit exceeded")

        result, err = VolumeService.generate("proj-1", 1, {})

        assert result is None
        assert "Rate limit" in err

    def test_generate_success_writes_volume(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        vol_data = {
            "title": "觉醒之路",
            "theme": "成长",
            "wordcount_target": 60000,
        }
        mock_gen._generate_json.return_value = (vol_data, None)

        result, err = VolumeService.generate("proj-1", 1, {})

        assert err is None
        assert result["title"] == "觉醒之路"
        mock_databridge.write.assert_called_once_with("proj-1", "volumes", [vol_data])


class TestVolumeGenerateBatch:

    def test_no_generator_returns_error(self, no_generator):
        result, err = VolumeService.generate_batch("proj-1", 5, {})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Service unavailable")

        result, err = VolumeService.generate_batch("proj-1", 3, {})

        assert result is None
        assert "Service" in err

    def test_generate_batch_list_result(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        volumes = [
            {"volume_no": 1, "title": "卷一"},
            {"volume_no": 2, "title": "卷二"},
        ]
        mock_gen._generate_json.return_value = (volumes, None)

        result, err = VolumeService.generate_batch("proj-1", 2, {})

        assert err is None
        assert len(result["volumes"]) == 2
        mock_databridge.write.assert_called_once()

    def test_generate_batch_dict_with_wrapped_volumes(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        ai_output = {
            "volume_1": {"title": "卷一", "volume_no": 1},
            "volume_2": {"title": "卷二", "volume_no": 2},
        }
        mock_gen._generate_json.return_value = (ai_output, None)

        result, err = VolumeService.generate_batch("proj-1", 2, {})

        assert err is None
        assert len(result["volumes"]) == 2
        assert result["volumes"][0]["volume_no"] == 1

    def test_generate_batch_dict_without_volume_no_extracts_from_key(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        ai_output = {
            "volume_1": {"title": "卷一"},
            "volume_2": {"title": "卷二"},
        }
        mock_gen._generate_json.return_value = (ai_output, None)

        result, err = VolumeService.generate_batch("proj-1", 2, {})

        assert err is None
        vols = result["volumes"]
        assert all("volume_no" in v for v in vols)
        assert vols[0]["volume_no"] == 1
        assert vols[1]["volume_no"] == 2

    def test_generate_batch_single_dict_wraps_as_list(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({"title": "单卷"}, None)

        result, err = VolumeService.generate_batch("proj-1", 1, {})

        assert err is None
        assert len(result["volumes"]) == 1
        assert result["volumes"][0]["title"] == "单卷"


class TestVolumeSave:

    def test_save_new_volume_appends(self, mock_databridge):
        mock_databridge.read.return_value = []

        result, err = VolumeService.save("proj-1", 1, {"title": "卷一"})

        assert err is None
        assert result["saved"] is True
        args = mock_databridge.write.call_args
        assert len(args[0][2]) == 1
        assert args[0][2][0]["title"] == "卷一"

    def test_save_updates_existing_volume(self, mock_databridge):
        existing = [
            {"volume_no": 1, "title": "旧数据"},
            {"volume_no": 2, "title": "卷二"},
        ]
        mock_databridge.read.return_value = existing

        result, err = VolumeService.save("proj-1", 1, {"volume_no": 1, "title": "新数据"})

        assert err is None
        args = mock_databridge.write.call_args
        written = args[0][2]
        assert len(written) == 2
        titles = [v["title"] for v in written]
        assert "新数据" in titles
        assert "旧数据" not in titles

    def test_save_handles_exception(self, mock_databridge):
        mock_databridge.read.side_effect = RuntimeError("存储故障")

        result, err = VolumeService.save("proj-1", 1, {"title": "test"})

        assert result is None
        assert "存储故障" in err


# ========== M11: PlotNodeService ==========


class TestPlotNodeGenerate:

    def test_no_generator_returns_error(self, no_generator):
        result, err = PlotNodeService.generate("proj-1", {}, {})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Generation failed")

        result, err = PlotNodeService.generate("proj-1", {}, {})

        assert result is None
        assert "Generation" in err

    def test_generate_success_returns_result(self, mock_generator):
        mock_gen, _ = mock_generator
        events = {"events": [{"event_id": "evt_1", "title": "危机爆发"}]}
        mock_gen._generate_json.return_value = (events, None)

        result, err = PlotNodeService.generate("proj-1", {}, {})

        assert err is None
        assert len(result["events"]) == 1
        assert result["events"][0]["event_id"] == "evt_1"


class TestPlotNodeSave:

    def test_save_is_deprecated_noop(self, mock_databridge):
        result, err = PlotNodeService.save("proj-1", "evt_1", {"title": "test"})

        assert err is None
        assert result["saved"] is True
        assert result["deprecated"] is True
        mock_databridge.write.assert_not_called()


# ========== M12: ChapterPlanService ==========


class TestChapterPlanServicePlan:

    def test_no_generator_returns_error(self, no_generator):
        result, err = ChapterPlanService.plan("proj-1", {}, [])
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "API error")

        result, err = ChapterPlanService.plan("proj-1", {}, [])

        assert result is None
        assert "API" in err

    def test_plan_success_returns_result(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        plan = {
            "chapter_assignments": [
                {"chapter_no": 1, "events": [], "hook": "悬念"},
                {"chapter_no": 2, "events": [], "hook": "冲突"},
            ],
            "pacing_analysis": "fast",
            "total_chapters": 2,
        }
        mock_gen._generate_json.return_value = (plan, None)

        result, err = ChapterPlanService.plan("proj-1", {}, [])

        assert err is None
        assert result["total_chapters"] == 2
        assert len(result["chapter_assignments"]) == 2

    def test_plan_writes_chapter_plan_to_databridge(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        chapters = [{"chapter_no": 1, "events": ["e1"]}]
        plan = {"chapter_assignments": chapters, "total_chapters": 1}
        mock_gen._generate_json.return_value = (plan, None)

        result, err = ChapterPlanService.plan("proj-1", {}, [])

        assert err is None
        mock_databridge.write.assert_called_once_with("proj-1", "chapter_plan", chapters)

    def test_plan_no_chapters_does_not_write(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({"total_chapters": 0}, None)

        result, err = ChapterPlanService.plan("proj-1", {}, [])

        assert err is None
        mock_databridge.write.assert_not_called()

    def test_plan_preserves_target_wordcount(self, mock_generator, mock_databridge):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({}, None)

        result, err = ChapterPlanService.plan("proj-1", {}, [], target_wordcount=5000)

        assert err is None
        prompt = mock_gen._generate_json.call_args[0][0]
        assert "5000" in prompt


class TestChapterPlanSave:

    def test_save_new_chapter_appends(self, mock_databridge):
        mock_databridge.read.return_value = []

        result, err = ChapterPlanService.save("proj-1", "1", {"chapter_no": 1, "title": "第一章"})

        assert err is None
        assert result["saved"] is True
        args = mock_databridge.write.call_args
        assert len(args[0][2]) == 1

    def test_save_updates_existing_chapter(self, mock_databridge):
        existing = [
            {"chapter_no": 1, "title": "旧标题"},
            {"chapter_no": 2, "title": "第二章"},
        ]
        mock_databridge.read.return_value = existing

        result, err = ChapterPlanService.save("proj-1", 1, {"chapter_no": 1, "title": "新标题"})

        assert err is None
        args = mock_databridge.write.call_args
        written = args[0][2]
        assert len(written) == 2
        assert any(v["title"] == "新标题" for v in written)
        assert all(v["title"] != "旧标题" for v in written)

    def test_save_handles_exception(self, mock_databridge):
        mock_databridge.read.side_effect = RuntimeError("数据库异常")

        result, err = ChapterPlanService.save("proj-1", "1", {"title": "test"})

        assert result is None
        assert "数据库异常" in err


# ========== M13: ChapterOutlineService ==========


class TestChapterOutlineGenerate:

    def test_no_generator_returns_error(self, no_generator):
        result, err = ChapterOutlineService.generate("proj-1", "1", {})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Generation failed")

        result, err = ChapterOutlineService.generate("proj-1", "1", {})

        assert result is None
        assert "Generation" in err

    def test_generate_success_returns_outline(self, mock_generator):
        mock_gen, _ = mock_generator
        outline = {
            "scenes": [{"scene_no": 1, "location": "城堡"}],
            "emotional_curve": {"start": "平静"},
            "key_points": ["看点1"],
        }
        mock_gen._generate_json.return_value = (outline, None)

        result, err = ChapterOutlineService.generate("proj-1", "3", {})

        assert err is None
        assert len(result["scenes"]) == 1
        assert result["emotional_curve"]["start"] == "平静"

    def test_generate_non_dict_result_returns_error(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ("not_a_dict", None)

        result, err = ChapterOutlineService.generate("proj-1", "1", {})

        assert result is None
        assert "非预期的返回类型" in err

    def test_generate_error_only_field_returns_error(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({"error": "内容违规"}, None)

        result, err = ChapterOutlineService.generate("proj-1", "1", {})

        assert result is None
        assert "AI返回错误" in err
        assert "内容违规" in err

    def test_generate_empty_content_returns_error(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({"extra": "无有效内容"}, None)

        result, err = ChapterOutlineService.generate("proj-1", "1", {})

        assert result is None
        assert "未返回有效章节内容" in err

    def test_generate_with_foreshadow_and_knowledge_state(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (
            {"scenes": [{"scene_no": 1}], "key_points": ["k1"]},
            None,
        )

        fs = {"埋入": [{"id": "f1"}]}
        ks = {"当前知识": "基础"}
        result, err = ChapterOutlineService.generate(
            "proj-1", "5", {}, foreshadow_plan=fs, knowledge_state=ks
        )

        assert err is None


class TestChapterOutlineGenerateBatch:

    def test_no_generator_returns_error(self, no_generator):
        result, err = ChapterOutlineService.generate_batch("proj-1", 10, {})
        assert result is None
        assert err == "AI生成器未配置"

    def test_ai_error_propagates(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = (None, "Batch generation failed")

        result, err = ChapterOutlineService.generate_batch("proj-1", 5, {})

        assert result is None
        assert "Batch" in err

    def test_generate_batch_list_result(self, mock_generator):
        mock_gen, _ = mock_generator
        outlines = [
            {"chapter_no": 1, "title": "第一章", "summary": "开端"},
            {"chapter_no": 2, "title": "第二章", "summary": "发展"},
        ]
        mock_gen._generate_json.return_value = (outlines, None)

        result, err = ChapterOutlineService.generate_batch("proj-1", 2, {})

        assert err is None
        assert len(result["outlines"]) == 2

    def test_generate_batch_single_dict_wraps_as_list(self, mock_generator):
        mock_gen, _ = mock_generator
        mock_gen._generate_json.return_value = ({"chapter_no": 1, "title": "单章"}, None)

        result, err = ChapterOutlineService.generate_batch("proj-1", 1, {})

        assert err is None
        assert len(result["outlines"]) == 1


class TestChapterOutlineSave:

    def test_save_to_existing_chapter(self, mock_databridge):
        existing = [
            {"chapter_no": 1, "title": "第一章"},
            {"chapter_no": 2, "title": "第二章"},
        ]
        mock_databridge.read.return_value = existing

        outline_data = {"scenes": [{"scene_no": 1}]}
        result, err = ChapterOutlineService.save("proj-1", "1", outline_data)

        assert err is None
        assert result["saved"] is True
        args = mock_databridge.write.call_args
        assert args[0][1] == "chapter_plan"
        assert args[0][2][0]["outline"] == outline_data

    def test_save_chapter_not_found_no_write(self, mock_databridge):
        existing = [{"chapter_no": 2, "title": "第二章"}]
        mock_databridge.read.return_value = existing

        result, err = ChapterOutlineService.save("proj-1", "99", {"scenes": []})

        assert err is None
        mock_databridge.write.assert_not_called()

    def test_save_handles_exception(self, mock_databridge):
        mock_databridge.read.side_effect = RuntimeError("数据库异常")

        result, err = ChapterOutlineService.save("proj-1", "1", {"scenes": []})

        assert result is None
        assert "数据库异常" in err
