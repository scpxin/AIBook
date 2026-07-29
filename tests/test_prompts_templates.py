"""Comprehensive tests for novel_creator/prompts_templates.py"""
import re
import string as string_mod

import pytest

from novel_creator import prompts_templates as pt
from novel_creator.prompts import format_prompt

ALL_NAMES = pt.__all__


def _iter_accessors(obj):
    for entry in ALL_NAMES:
        if not entry.startswith("_"):
            yield entry


def _get_placeholders(template):
    result = []
    for _literal_text, field_name, _format_spec, _conversion in string_mod.Formatter().parse(template):
        if field_name is not None:
            result.append(field_name)
    return result


def _has_json_output_instruction(template):
    return (
        "JSON" in template
        and ("只输出" in template or "不要其他" in template)
        and ("格式" in template)
    )


# ============================================================
# 1. 存在性测试
# ============================================================

class TestConstantsExist:
    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_constant_exists(self, name):
        assert hasattr(pt, name), f"'{name}' not found in prompts_templates"

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_constant_is_non_empty_string(self, name):
        val = getattr(pt, name)
        assert isinstance(val, str), f"'{name}' should be str, got {type(val).__name__}"
        assert len(val) > 0, f"'{name}' is empty string"


# ============================================================
# 2. 格式化占位符测试
# ============================================================

class TestFormatStringPlaceholders:

    TEMPLATE_PLACEHOLDERS = {
        "WORLD_BUILDING": ["title", "theme", "genre", "description"],
        "WORLD_BUILDING_STYLE": [
            "title", "tone", "pacing", "description_style", "emotional_intensity",
            "world_features", "world_building_style", "upgrade_mechanism",
            "overall_summary", "genre", "sub_genres", "theme", "sub_themes",
            "core_drive", "protagonist_archetype",
        ],
        "CHARACTERS_BATCH_GENERATION": [
            "count", "novel_description", "time_period", "location",
            "atmosphere", "rules", "theme", "genre", "requirements",
        ],
        "CHARACTERS_BATCH_GENERATION_STYLE": [
            "count", "protagonist_archetype", "character_growth_pattern",
            "relationship_dynamics", "tone", "emotional_intensity",
            "dialogue_style", "overall_summary", "time_period", "location",
            "atmosphere", "rules", "theme", "genre", "sub_genres",
            "main_conflict", "requirements", "upgrade_mechanism",
        ],
        "BOOK_OVERVIEW_CREATE": [
            "title", "genre", "theme", "narrative_perspective",
            "inspiration_desc", "characters_info", "world_summary",
        ],
        "BOOK_OVERVIEW_CREATE_STYLE": [
            "title", "genre", "sub_genres", "theme", "narrative_perspective",
            "sub_themes", "inspiration_desc", "characters_info", "world_summary",
            "story_framework", "core_drive", "main_conflict", "pacing",
            "emotional_intensity", "satisfaction_type", "satisfaction_pattern",
            "emotional_beats", "hook_design", "transition_style",
            "foreshadowing_style", "writing_techniques", "overall_summary",
        ],
        "CHAPTER_OUTLINE_DETAIL": [
            "project_title", "chapter_number", "degradation_warning",
            "book_overview_json", "world_summary", "act_context",
            "character_milestones", "active_subplots", "foreshadow_to_plant",
            "foreshadow_to_payoff", "pacing_requirement", "prev_chapter_title",
            "prev_chapter_tail", "genre", "narrative_perspective",
            "characters_info", "total_chapters", "my_position",
        ],
        "CHAPTER_OUTLINE_DETAIL_STYLE": [
            "project_title", "chapter_number", "degradation_warning",
            "book_overview_json", "world_summary", "act_context",
            "character_milestones", "active_subplots", "foreshadow_to_plant",
            "foreshadow_to_payoff", "pacing_requirement", "prev_chapter_title",
            "prev_chapter_tail", "genre", "narrative_perspective",
            "characters_info", "total_chapters", "my_position",
            "story_framework", "satisfaction_pattern", "hook_design",
            "transition_style", "foreshadowing_style", "writing_techniques",
            "pacing", "emotional_beats",
        ],
        "OUTLINE_CREATE": [
            "chapter_count", "title", "genre", "theme",
            "narrative_perspective", "world_summary", "characters_info",
        ],
        "OUTLINE_CREATE_STYLE": [
            "chapter_count", "title", "genre", "sub_genres", "theme",
            "narrative_perspective", "world_summary", "characters_info",
            "story_framework", "core_drive", "main_conflict", "pacing",
            "emotional_intensity", "satisfaction_type", "satisfaction_pattern",
            "emotional_beats", "hook_design", "transition_style",
            "foreshadowing_style", "writing_techniques", "overall_summary",
            "sub_themes",
        ],
        "CHAPTER_GENERATION_NEXT": [
            "project_title", "genre", "chapter_number", "chapter_title",
            "target_word_count", "narrative_perspective", "chapter_outline",
            "world_summary", "continuation_point", "previous_chapter_summary",
            "prev_chapter_hook", "chapter_characters", "foreshadow_reminders",
            "first_chapter_note",
        ],
        "CHAPTER_GENERATION_NEXT_STYLE": [
            "project_title", "genre", "chapter_number", "chapter_title",
            "target_word_count", "narrative_perspective", "tone", "pacing",
            "sentence_structure", "dialogue_style", "description_style",
            "emotional_intensity", "writing_techniques", "hook_design",
            "satisfaction_pattern", "satisfaction_type", "transition_style",
            "emotional_beats", "foreshadowing_style", "overall_summary",
            "chapter_outline", "world_summary", "continuation_point",
            "previous_chapter_summary", "prev_chapter_hook",
            "chapter_characters", "foreshadow_reminders", "technique_focus",
            "first_chapter_note",
        ],
        "CHAPTER_CONTINUATION": [
            "project_title", "genre", "chapter_number", "chapter_title",
            "progress_content", "chapter_outline", "prev_chapter_hook",
            "target_word_count", "progress_chars", "segment_chars",
            "style_section",
        ],
        "CHAPTER_CONTINUATION_STYLE": [
            "tone", "pacing", "sentence_structure", "dialogue_style",
            "description_style", "emotional_intensity", "writing_techniques",
            "foreshadowing_style", "overall_summary", "prev_chapter_hook",
        ],
        "INSPIRATION_TITLE": ["style_section", "user_input"],
        "INSPIRATION_TITLE_STYLE": [
            "narrative_perspective", "tone", "pacing", "emotional_intensity",
            "unique_quirks", "overall_summary", "user_input_section",
        ],
        "INSPIRATION_DESCRIPTION": ["style_section", "title", "user_input"],
        "INSPIRATION_DESCRIPTION_STYLE": [
            "title", "narrative_perspective", "tone", "pacing",
            "dialogue_style", "description_style", "sentence_structure",
            "emotional_intensity", "overall_summary", "user_input_section",
        ],
        "INSPIRATION_THEME": ["style_section", "title", "description", "user_input_section"],
        "INSPIRATION_THEME_STYLE": [
            "title", "description", "tone", "emotional_intensity",
            "description_style", "unique_quirks", "overall_summary",
        ],
        "INSPIRATION_GENRE": ["title", "description", "user_input_section"],
        "INSPIRATION_GENRE_STYLE": [
            "title", "description", "narrative_perspective", "tone", "pacing",
            "emotional_intensity", "description_style", "sentence_structure",
            "overall_summary",
        ],
        "CHAPTER_POLISH": [
            "genre", "chapter_number", "chapter_title", "chapter_outline",
            "polish_focus", "tone", "pacing", "sentence_structure",
            "description_style", "original_content",
        ],
    }

    @pytest.mark.parametrize("name,expected_placeholders", sorted(TEMPLATE_PLACEHOLDERS.items()))
    def test_template_has_expected_placeholders(self, name, expected_placeholders):
        template = getattr(pt, name)
        actual = _get_placeholders(template)
        for ph in expected_placeholders:
            assert ph in actual, f"'{name}' missing expected placeholder {{{ph}}}"
        unexpected = set(actual) - set(expected_placeholders)
        assert not unexpected, (
            f"'{name}' has unexpected placeholders: {unexpected}. "
            f"Expected: {expected_placeholders}, Got: {actual}"
        )

    @pytest.mark.parametrize("name,placeholders", sorted(TEMPLATE_PLACEHOLDERS.items()))
    def test_format_prompt_succeeds(self, name, placeholders):
        template = getattr(pt, name)
        kwargs = {ph: f"<{ph}>" for ph in placeholders}
        result = format_prompt(template, **kwargs)
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0
        for ph in placeholders:
            assert f"<{ph}>" in result, f"'{name}': placeholder {{{ph}}} not filled in result"

    @pytest.mark.parametrize("name,placeholders", sorted(TEMPLATE_PLACEHOLDERS.items()))
    def test_missing_placeholder_becomes_empty(self, name, placeholders):
        template = getattr(pt, name)
        result = format_prompt(template)
        unfilled = {
            ph for ph in _get_placeholders(template)
            if ("{" + ph + "}") in result
        }
        assert not unfilled, (
            f"'{name}': placeholders unfilled after format_prompt(): {unfilled}"
        )


# ============================================================
# 3. 关键词内容测试
# ============================================================

class TestKeyContent:

    def test_world_building_contains_dimensions(self):
        t = pt.WORLD_BUILDING
        assert "time_period" in t
        assert "location" in t
        assert "atmosphere" in t
        assert "rules" in t
        assert "300-500字" in t

    def test_world_building_contains_guidance_by_genre(self):
        t = pt.WORLD_BUILDING
        assert "现代都市" in t or "现代" in t
        assert "玄幻" in t or "仙侠" in t
        assert "科幻" in t

    def test_characters_batch_generation_contains_schema(self):
        t = pt.CHARACTERS_BATCH_GENERATION
        assert "name" in t
        assert "age" in t
        assert "gender" in t
        assert "is_organization" in t
        assert "is_organization: true" in t
        assert "role_type" in t
        assert "protagonist" in t
        assert "antagonist" in t
        assert "organization_type" in t
        assert "power_level" in t

    def test_characters_batch_has_json_array_instruction(self):
        t = pt.CHARACTERS_BATCH_GENERATION
        assert "JSON数组" in t

    def test_book_overview_contains_6_dimensions(self):
        t = pt.BOOK_OVERVIEW_CREATE
        assert "core_conflict" in t
        assert "acts" in t
        assert "character_arcs" in t
        assert "subplots" in t
        assert "foreshadowing" in t
        assert "pacing" in t

    def test_book_overview_has_act_structure(self):
        t = pt.BOOK_OVERVIEW_CREATE
        assert "act_number" in t
        assert "chapter_range" in t
        assert "key_turning_point" in t

    def test_chapter_outline_detail_has_required_fields(self):
        t = pt.CHAPTER_OUTLINE_DETAIL
        assert "title" in t
        assert "summary" in t
        assert "scenes" in t
        assert "characters" in t
        assert "key_points" in t
        assert "emotion" in t
        assert "goal" in t
        assert "chapter_hook" in t
        assert "technique_focus" in t

    def test_chapter_outline_detail_has_context_sections(self):
        t = pt.CHAPTER_OUTLINE_DETAIL
        assert "degradation_warning" in t
        assert "book_overview_json" in t
        assert "world_summary" in t
        assert "act_context" in t
        assert "foreshadow_to_plant" in t
        assert "foreshadow_to_payoff" in t
        assert "prev_chapter_title" in t
        assert "prev_chapter_tail" in t

    def test_outline_create_has_fields(self):
        t = pt.OUTLINE_CREATE
        assert "chapter_count" in t
        assert "chapter_number" in t
        assert "summary" in t
        assert "scenes" in t

    def test_chapter_generation_next_has_output_spec(self):
        t = pt.CHAPTER_GENERATION_NEXT
        assert "target_word_count" in t
        assert "直接输出小说正文" in t
        assert "不要写" in t or "不要第" in t

    def test_chapter_generation_next_has_context_sections(self):
        t = pt.CHAPTER_GENERATION_NEXT
        assert "world_summary" in t or "世界观设定" in t
        assert "continuation_point" in t or "衔接锚点" in t
        assert "previous_chapter_summary" in t or "禁止重复" in t
        assert "foreshadow_reminders" in t or "伏笔提醒" in t

    def test_chapter_continuation_is_progress_aware(self):
        t = pt.CHAPTER_CONTINUATION
        assert "progress_content" in t
        assert "progress_chars" in t
        assert "segment_chars" in t
        assert "target_word_count" in t

    def test_inspiration_title_produces_array(self):
        t = pt.INSPIRATION_TITLE
        assert "6个书名" in t
        assert "JSON数组" in t

    def test_inspiration_description_produces_array(self):
        t = pt.INSPIRATION_DESCRIPTION
        assert "6个简介" in t
        assert "JSON数组" in t

    def test_inspiration_theme_produces_array(self):
        t = pt.INSPIRATION_THEME
        assert "6个主题" in t
        assert "JSON数组" in t

    def test_inspiration_genre_produces_array(self):
        t = pt.INSPIRATION_GENRE
        assert "6个类型标签" in t
        assert "JSON数组" in t

    def test_chapter_polish_has_required_sections(self):
        t = pt.CHAPTER_POLISH
        assert "original_content" in t
        assert "chapter_outline" in t
        assert "polish_focus" in t
        assert "润色" in t

    def test_style_templates_contain_style_features(self):
        for name, tpl in [
            ("WORLD_BUILDING_STYLE", pt.WORLD_BUILDING_STYLE),
            ("CHARACTERS_BATCH_GENERATION_STYLE", pt.CHARACTERS_BATCH_GENERATION_STYLE),
            ("BOOK_OVERVIEW_CREATE_STYLE", pt.BOOK_OVERVIEW_CREATE_STYLE),
            ("OUTLINE_CREATE_STYLE", pt.OUTLINE_CREATE_STYLE),
            ("CHAPTER_GENERATION_NEXT_STYLE", pt.CHAPTER_GENERATION_NEXT_STYLE),
            ("INSPIRATION_TITLE_STYLE", pt.INSPIRATION_TITLE_STYLE),
            ("INSPIRATION_DESCRIPTION_STYLE", pt.INSPIRATION_DESCRIPTION_STYLE),
            ("INSPIRATION_THEME_STYLE", pt.INSPIRATION_THEME_STYLE),
            ("INSPIRATION_GENRE_STYLE", pt.INSPIRATION_GENRE_STYLE),
        ]:
            assert "参考风格" in tpl, f"'{name}' should contain style reference block"
            assert "overall_summary" in tpl, (
                f"'{name}' should contain {{overall_summary}} placeholder"
            )

    def test_style_analysis_exists(self):
        assert hasattr(pt, "STYLE_ANALYSIS"), "STYLE_ANALYSIS constant should exist"

    def test_style_analysis_contains_required_fields(self):
        t = pt.STYLE_ANALYSIS
        assert "narrative_perspective" in t
        assert "tone" in t
        assert "pacing" in t
        assert "emotional_intensity" in t
        assert "genre" in t
        assert "overall_summary" in t
        assert "protagonist_archetype" in t
        assert "key_lessons" in t


# ============================================================
# 4. JSON 约束测试
# ============================================================

class TestJsonConstraints:

    JSON_OUTPUT_TEMPLATES = sorted(
        set(ALL_NAMES)
        - {"CHAPTER_CONTINUATION_STYLE",
           "CHAPTER_CONTINUATION",
           "CHAPTER_GENERATION_NEXT",
           "CHAPTER_GENERATION_NEXT_STYLE",
           "CHAPTER_POLISH",
           }
    )

    JSON_ARRAY_TEMPLATES = sorted({
        "CHARACTERS_BATCH_GENERATION",
        "CHARACTERS_BATCH_GENERATION_STYLE",
        "OUTLINE_CREATE",
        "OUTLINE_CREATE_STYLE",
        "INSPIRATION_TITLE",
        "INSPIRATION_TITLE_STYLE",
        "INSPIRATION_DESCRIPTION",
        "INSPIRATION_DESCRIPTION_STYLE",
        "INSPIRATION_THEME",
        "INSPIRATION_THEME_STYLE",
        "INSPIRATION_GENRE",
        "INSPIRATION_GENRE_STYLE",
    })

    JSON_OBJECT_TEMPLATES = sorted({
        "WORLD_BUILDING",
        "WORLD_BUILDING_STYLE",
        "BOOK_OVERVIEW_CREATE",
        "BOOK_OVERVIEW_CREATE_STYLE",
        "CHAPTER_OUTLINE_DETAIL",
        "CHAPTER_OUTLINE_DETAIL_STYLE",
    })

    @pytest.mark.parametrize("name", JSON_OUTPUT_TEMPLATES)
    def test_template_ends_with_json_instruction(self, name):
        template = getattr(pt, name)
        assert _has_json_output_instruction(template), (
            f"'{name}' should instruct JSON-only output. "
            f"Last 100 chars: {template[-100:]!r}"
        )

    @pytest.mark.parametrize("name", JSON_ARRAY_TEMPLATES)
    def test_json_array_template_mentions_array(self, name):
        template = getattr(pt, name)
        assert "数组" in template, f"'{name}' should mention JSON array output"

    @pytest.mark.parametrize("name", JSON_OBJECT_TEMPLATES)
    def test_json_object_template_mentions_format(self, name):
        template = getattr(pt, name)
        assert "格式" in template, f"'{name}' should mention JSON format"

    def test_chapter_generation_direct_output(self):
        for name in ["CHAPTER_GENERATION_NEXT", "CHAPTER_GENERATION_NEXT_STYLE"]:
            t = getattr(pt, name)
            assert "直接输出小说正文" in t, f"'{name}' should output prose, not JSON"

    def test_chapter_continuation_direct_output(self):
        t = pt.CHAPTER_CONTINUATION
        assert "直接续写正文" in t

    def test_chapter_polish_direct_output(self):
        t = pt.CHAPTER_POLISH
        assert "直接输出润色后正文" in t


# ============================================================
# 5. 导入后向兼容测试
# ============================================================

class TestImportBackwardCompat:

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_importable_from_prompts(self, name):
        mod = __import__("novel_creator.prompts", fromlist=[name])
        val = getattr(mod, name)
        assert isinstance(val, str)
        assert len(val) > 0

    def test_format_prompt_importable(self):
        from novel_creator.prompts import format_prompt
        assert callable(format_prompt)

    def test_parse_json_response_importable(self):
        from novel_creator.prompts import parse_json_response
        assert callable(parse_json_response)


# ============================================================
# 6. 模板不包含错误残留测试
# ============================================================

class TestTemplateSanity:

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_no_todo_or_fixme_in_template(self, name):
        template = getattr(pt, name)
        assert "TODO" not in template, f"'{name}' contains TODO"
        assert "FIXME" not in template, f"'{name}' contains FIXME"

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_no_placeholder_in_placeholder(self, name):
        template = getattr(pt, name)
        assert "{{" not in template.replace("{{chapter:", "").replace("{{", ""), (
            f"'{name}' contains literal double braces beyond JSON examples"
        )

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_template_has_no_trailing_newline_fragments(self, name):
        template = getattr(pt, name)
        assert not template.endswith(" \n")
        assert not template.endswith("\n\n\n")

    @pytest.mark.parametrize("name", sorted(ALL_NAMES))
    def test_chinese_characters_present_in_all_templates(self, name):
        template = getattr(pt, name)
        assert re.search(r"[\u4e00-\u9fff]", template), (
            f"'{name}' contains no Chinese characters"
        )


# ============================================================
# 7.  _all_ 与 prompts.py 重导出一致性
# ============================================================

class TestAllConsistency:

    def test_all_sorted_alphabetically(self):
        assert pt.__all__ == sorted(pt.__all__), "__all__ should be sorted alphabetically"

    def test_no_duplicates_in_all(self):
        assert len(pt.__all__) == len(set(pt.__all__)), "__all__ contains duplicates"

    def test_all_count_matches_exported_names(self):
        from novel_creator import prompts
        export_names = []
        for name in ALL_NAMES:
            assert hasattr(prompts, name), (
                f"'{name}' not re-exported from novel_creator.prompts"
            )
            export_names.append(name)
        assert len(export_names) == len(ALL_NAMES)

    def test_style_analysis_not_in_all(self):
        assert "STYLE_ANALYSIS" not in pt.__all__, (
            "STYLE_ANALYSIS should not be in __all__ (it's used internally)"
        )
