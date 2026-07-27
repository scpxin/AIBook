from unittest.mock import MagicMock, patch

import pytest

from app.services.design_service import (
    _assess_series_potential,
    _estimate_chapters,
    _estimate_words,
    _extract_keywords,
    _generate_tags,
)


@pytest.fixture
def mock_databridge():
    with patch("app.services.design_service.DataBridge") as mock:
        yield mock


# ========== M2: 衍生字段私有函数 ==========

class TestEstimateChapters:

    def test_estimate_chapters_default_for_empty(self):
        assert _estimate_chapters("") == 300
        assert _estimate_chapters(None) == 300

    def test_estimate_chapters_non_string_returns_default(self):
        assert _estimate_chapters(123) == 300
        assert _estimate_chapters([]) == 300

    def test_estimate_chapters_qianwan_scale(self):
        assert _estimate_chapters("千万级别的玄幻巨作") == 800

    def test_estimate_chapters_baiwan_scale(self):
        assert _estimate_chapters("百万字的长篇史诗") == 500

    def test_estimate_chapters_long_novel(self):
        assert _estimate_chapters("这是一部长篇小说") == 500

    def test_estimate_chapters_medium_length(self):
        assert _estimate_chapters("中篇故事集") == 200

    def test_estimate_chapters_default_for_unmatched(self):
        assert _estimate_chapters("一个普通的短篇") == 300


class TestEstimateWords:

    def test_estimate_words_default_for_empty(self):
        assert _estimate_words("") == 100
        assert _estimate_words(None) == 100

    def test_estimate_words_qianwan_scale(self):
        assert _estimate_words("千万字规模的巨著") == 500

    def test_estimate_words_baiwan_scale(self):
        assert _estimate_words("百万字级别作品") == 200

    def test_estimate_words_default_for_unmatched(self):
        assert _estimate_words("一句话简介") == 100


class TestExtractKeywords:

    def test_extract_keywords_splits_and_deduplicates(self):
        result = _extract_keywords("重生 穿越 修仙 都市 重生 穿越")
        assert len(result) == 4
        assert set(result) == {"重生", "穿越", "修仙", "都市"}

    def test_extract_keywords_filters_single_char(self):
        result = _extract_keywords("a b c 修仙")
        assert all(len(w) >= 2 for w in result)
        assert "修仙" in result

    def test_extract_keywords_limit_to_ten(self):
        words = " ".join(f"词{i:02d}" for i in range(15))
        result = _extract_keywords(words)
        assert len(result) == 10

    def test_extract_keywords_empty_string(self):
        assert _extract_keywords("") == []


class TestGenerateTags:

    def test_generate_tags_matches_keywords(self):
        overview = "升级系统 无敌 重生修仙都市"
        result = _generate_tags(overview)
        assert "升级流" in result
        assert "系统流" in result
        assert "仙侠" in result

    def test_generate_tags_no_match_returns_empty(self):
        assert _generate_tags("一个普通浪漫爱情故事") == []

    def test_generate_tags_limit_to_five(self):
        overview = "升级 系统 无敌 重生 穿越 修仙 都市 赘婿"
        result = _generate_tags(overview)
        assert len(result) <= 5

    def test_generate_tags_preserves_tag_keyword_order(self):
        overview = "修仙 都市"
        result = _generate_tags(overview)
        assert result == ["仙侠", "都市"]


class TestAssessSeriesPotential:

    def test_assess_potential_high_with_indicators(self):
        assert _assess_series_potential("这是一个系列作品") == "高"
        assert _assess_series_potential("多部联动的宇宙故事") == "高"
        assert _assess_series_potential("完整的世界观设定") == "高"

    def test_assess_potential_medium_by_default(self):
        assert _assess_series_potential("独立故事") == "中"
        assert _assess_series_potential("") == "中"


# ========== M2: ProjectService ==========

class TestProjectService:

    def test_derive_fields_computes_all_fields(self):
        from app.services.design_service import ProjectService

        project_data = {
            "title": "修仙 重生 穿越 无敌",
            "project_overview": "千百万字级别的修仙长篇巨著",
        }

        result, err = ProjectService.derive_fields("proj-1", project_data)

        assert err is None
        assert result["estimated_chapters"] == 500
        assert result["estimated_words"] == 200
        assert len(result["title_keywords"]) == 4
        assert "仙侠" in result["content_tags"]
        assert result["series_potential"] == "中"

    def test_derive_fields_handles_empty_project_data(self):
        from app.services.design_service import ProjectService

        result, err = ProjectService.derive_fields("proj-1", {})

        assert err is None
        assert result["estimated_chapters"] == 300
        assert result["estimated_words"] == 100
        assert result["title_keywords"] == []
        assert result["content_tags"] == []
        assert result["series_potential"] == "中"


# ========== M1: IdeaService.generate 结果解析 ==========

class TestIdeaServiceGenerate:

    def test_generate_error_when_no_generator(self):
        with patch("app.services.design_service.get_default_generator", return_value=None):
            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert result is None
            assert err == "AI生成器未配置"

    def test_generate_error_from_ai(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (None, "Rate limit")
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert result is None
            assert "Rate limit" in err

    def test_generate_single_object_wrapped_as_list(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            single = {"concept": "修仙重生", "hook": "逆袭之路"}
            mock_gen._generate_json.return_value = (single, None)
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "user input", "玄幻")

            assert err is None
            assert len(result["ideas"]) == 1
            assert result["ideas"][0]["concept"] == "修仙重生"

    def test_generate_assigns_index_to_ideas(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            ideas = [
                {"concept": "创意A"}, {"concept": "创意B"}, {"concept": "创意C"},
            ]
            mock_gen._generate_json.return_value = (ideas, None)
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert err is None
            assert result["ideas"][0]["_index"] == 1
            assert result["ideas"][1]["_index"] == 2
            assert result["ideas"][2]["_index"] == 3

    def test_generate_filters_none_and_invalid_items(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            items = [
                None,
                "not_a_dict",
                {"concept": "有效创意"},
                42,
                {"concept": "有效创意2"},
            ]
            mock_gen._generate_json.return_value = (items, None)
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert err is None
            assert len(result["ideas"]) == 2

    def test_generate_all_invalid_returns_error(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = ([None, "bad"], None)
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert result is None
            assert "格式不正确" in err

    def test_generate_ai_returns_none(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (None, None)
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "test")

            assert result is None
            assert "AI返回空结果" in err

    def test_generate_writes_to_databridge(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (
                [{"concept": "创意", "hook": "钩子"}],
                None,
            )
            mock_get.return_value = mock_gen

            from app.services.design_service import IdeaService

            result, err = IdeaService.generate("p1", "输入", "玄幻")

            assert err is None
            mock_databridge.write.assert_called_once()
            args = mock_databridge.write.call_args
            assert args[0][0] == "p1"
            assert args[0][1] == "idea"
            assert args[0][2]["status"] == "draft"


# ========== M2: ProjectService.analyze 维度规范化 ==========

class TestProjectServiceAnalyze:

    def _run_analyze_with_mock_result(self, ai_result):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (ai_result, None)
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            with patch("app.services.design_service.DataBridge"):
                return ProjectService.analyze("p1", "创意概念", "tomato")

    def test_analyze_normalizes_digit_keys_to_dimension_names(self):
        ai_output = {
            "1": {"title": "target", "content": "xxxx"},
            "2": {"title": "core", "content": "xxxx"},
            "3": {"title": "novelty", "content": "xxxx"},
            "4": {"title": "emotional", "content": "xxxx"},
            "5": {"title": "update", "content": "xxxx"},
            "6": {"title": "title", "content": "xxxx"},
            "7": {"title": "cover", "content": "xxxx"},
            "8": {"title": "opener", "content": "xxxx"},
            "9": {"title": "main", "content": "xxxx"},
            "10": {"title": "subplot", "content": "xxxx"},
            "11": {"title": "climax", "content": "xxxx"},
            "12": {"title": "ending", "content": "xxxx"},
        }

        result, err = self._run_analyze_with_mock_result(ai_output)

        assert err is None
        assert "target_audience" in result
        assert result["target_audience"]["title"] == "target"

    def test_analyze_preserves_already_named_keys(self):
        ai_output = {
            "target_audience": {"title": "受众", "content": "xxxx"},
            "core_hook": {"title": "卖点", "content": "xxxx"},
        }

        result, err = self._run_analyze_with_mock_result(ai_output)

        assert err is None
        assert "target_audience" in result
        assert "core_hook" in result

    def test_analyze_keeps_non_digit_extra_keys(self):
        ai_output = {
            "1": {"title": "ta", "content": "xxx"},
            "extra_key": {"title": "额外", "content": "yyy"},
        }

        result, err = self._run_analyze_with_mock_result(ai_output)

        assert err is None
        assert "target_audience" in result
        assert "extra_key" in result

    def test_analyze_error_from_generator(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (None, "Token exhausted")
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze("p1", "概念", "tomato")

            assert result is None
            assert "Token" in err

    def test_analyze_no_generator(self):
        with patch("app.services.design_service.get_default_generator", return_value=None):
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze("p1", "概念")

            assert result is None
            assert err == "AI生成器未配置"


# ========== M2: ProjectService.analyze_batch ==========

class TestProjectServiceAnalyzeBatch:

    def test_analyze_batch_batch_index_out_of_range(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze_batch("p1", "概念", "tomato", 99)

            assert result is None
            assert "批次超出范围" in err

    def test_analyze_batch_no_generator(self):
        with patch("app.services.design_service.get_default_generator", return_value=None):
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze_batch("p1", "概念", "tomato", 0)

            assert result is None
            assert err == "AI生成器未配置"

    def test_analyze_batch_returns_anomalous_result(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = ("not_a_dict", None)
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze_batch("p1", "概念", "tomato", 0)

            assert result is None
            assert "格式异常" in err

    def test_analyze_batch_wraps_result_with_metadata(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (
                {"dimensions": []}, None
            )
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze_batch("p1", "概念", "tomato", 0)

            assert err is None
            assert result["_batch_index"] == 0
            assert result["_total_batches"] == 3

    def test_analyze_batch_adds_dimensions_when_missing(self):
        with patch("app.services.design_service.get_default_generator") as mock_get:
            mock_gen = MagicMock()
            mock_gen._generate_json.return_value = (
                {"d1": {"content": "内容1"}, "d2": {"content": "内容2"}},
                None,
            )
            mock_get.return_value = mock_gen
            from app.services.design_service import ProjectService

            result, err = ProjectService.analyze_batch("p1", "概念", "tomato", 0)

            assert err is None
            assert "dimensions" in result
            assert len(result["dimensions"]) == 2


# ========== M3: WorldService.save_world 数据规范化 ==========

class TestWorldServiceSaveWorld:

    def test_save_world_normalizes_rules_list_to_dict(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            world_data = {
                "origin": {"worldType": "仙侠世界"},
                "rules": [
                    {"name": "rule1", "description": "灵力规则"},
                    {"name": "rule2", "description": "修炼规则"},
                ],
                "structure": {},
                "civilization": {},
                "history": [],
            }

            result, err = WorldService.save_world("p1", world_data)
            assert err is None
            assert result["saved"] is True
            written = mock_databridge.write.call_args[0][2]["rules"]
            assert isinstance(written, dict)
            assert written["rule1"] == "灵力规则"

    def test_save_world_normalizes_history_dict_with_wrapper(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            world_data = {
                "origin": {"worldType": "科幻宇宙"},
                "rules": {},
                "structure": {},
                "civilization": {},
                "history": {
                    "history": [{"era": "太古", "description": "宇宙诞生"}],
                },
            }

            result, err = WorldService.save_world("p1", world_data)
            assert err is None
            history = mock_databridge.write.call_args[0][2]["history"]
            assert isinstance(history, list)
            assert history[0]["era"] == "太古"

    def test_save_world_normalizes_history_dict_no_wrapper(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            world_data = {
                "origin": {"worldType": "奇幻世界"},
                "rules": {},
                "structure": {},
                "civilization": {},
                "history": {"era1": "描述1", "era2": "描述2"},
            }

            result, err = WorldService.save_world("p1", world_data)
            assert err is None
            history = mock_databridge.write.call_args[0][2]["history"]
            assert isinstance(history, list)
            assert len(history) == 2

    def test_save_world_normalizes_origin_from_flat_data(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            world_data = {
                "origin": {},
                "worldType": "末日废土",
                "originStory": "核战后世界",
                "hiddenTruth": "真相",
                "rules": {},
                "structure": {},
                "civilization": {},
                "history": [],
            }

            result, err = WorldService.save_world("p1", world_data)
            assert err is None
            origin = mock_databridge.write.call_args[0][2]["origin"]
            assert origin["worldType"] == "末日废土"
            assert origin["originStory"] == "核战后世界"

    def test_save_world_error_on_exception(self, mock_databridge):
        mock_databridge.write.side_effect = RuntimeError("数据库写入失败")
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            result, err = WorldService.save_world(
                "p1",
                {"origin": {}, "rules": {}, "structure": {}, "civilization": {}, "history": []},
            )

            assert result is None
            assert "数据库写入失败" in err

    def test_save_world_preserves_structure_and_civilization(self, mock_databridge):
        with patch("app.services.design_service.get_default_generator"):
            from app.services.design_service import WorldService

            world_data = {
                "origin": {"worldType": "仙侠"},
                "rules": {"power": "灵力"},
                "structure": {"levels": [{"name": "仙界"}]},
                "civilization": {"government": "天庭"},
                "history": [],
                "doc_path": "/docs/world.md",
            }

            result, err = WorldService.save_world("p1", world_data)
            assert err is None
            written = mock_databridge.write.call_args[0][2]
            assert written["structure"]["levels"][0]["name"] == "仙界"
            assert written["civilization"]["government"] == "天庭"
            assert written["doc_path"] == "/docs/world.md"


# ========== M2: ProjectService.PLATFORM_PRESETS ==========

class TestPlatformPresets:

    def test_presets_contain_expected_platforms(self):
        from app.services.design_service import ProjectService

        assert "tomato" in ProjectService.PLATFORM_PRESETS
        assert "qidian" in ProjectService.PLATFORM_PRESETS
        assert "fanqie" in ProjectService.PLATFORM_PRESETS

    def test_preset_has_required_fields(self):
        from app.services.design_service import ProjectService

        for preset in ProjectService.PLATFORM_PRESETS.values():
            assert "name" in preset
            assert "style" in preset
            assert "update" in preset
