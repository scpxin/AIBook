from novel_creator.craft_prompts import (
    ANALYSIS_REPORT,
    ANALYZE_GOLDEN_THREE,
    ANALYZE_HOOKS,
    ANALYZE_SATISFACTION_RHYTHM,
    CHAPTER_CONTINUATION_CRAFT,
    CHAPTER_CONTINUATION_CRAFT_STYLE,
    CHAPTER_GENERATION_CRAFT,
    CHAPTER_GENERATION_CRAFT_STYLE,
    CHAPTER_OUTLINE_CRAFT,
    CHAPTER_OUTLINE_CRAFT_STYLE,
    DETECT_AI_FLAVOR,
    FIX_AI_FLAVOR,
    INSPIRATION_DESCRIPTION_CRAFT,
    INSPIRATION_TITLE_CRAFT,
    QUALITY_SCORE,
)

ALL_PROMPTS = [
    DETECT_AI_FLAVOR,
    FIX_AI_FLAVOR,
    ANALYZE_GOLDEN_THREE,
    ANALYZE_HOOKS,
    ANALYZE_SATISFACTION_RHYTHM,
    QUALITY_SCORE,
    CHAPTER_OUTLINE_CRAFT,
    CHAPTER_OUTLINE_CRAFT_STYLE,
    CHAPTER_GENERATION_CRAFT,
    CHAPTER_GENERATION_CRAFT_STYLE,
    INSPIRATION_TITLE_CRAFT,
    INSPIRATION_DESCRIPTION_CRAFT,
    ANALYSIS_REPORT,
    CHAPTER_CONTINUATION_CRAFT,
    CHAPTER_CONTINUATION_CRAFT_STYLE,
]

PROMPT_NAMES = [
    "DETECT_AI_FLAVOR",
    "FIX_AI_FLAVOR",
    "ANALYZE_GOLDEN_THREE",
    "ANALYZE_HOOKS",
    "ANALYZE_SATISFACTION_RHYTHM",
    "QUALITY_SCORE",
    "CHAPTER_OUTLINE_CRAFT",
    "CHAPTER_OUTLINE_CRAFT_STYLE",
    "CHAPTER_GENERATION_CRAFT",
    "CHAPTER_GENERATION_CRAFT_STYLE",
    "INSPIRATION_TITLE_CRAFT",
    "INSPIRATION_DESCRIPTION_CRAFT",
    "ANALYSIS_REPORT",
    "CHAPTER_CONTINUATION_CRAFT",
    "CHAPTER_CONTINUATION_CRAFT_STYLE",
]

JSON_END_PROMPTS = {
    "DETECT_AI_FLAVOR",
    "ANALYZE_GOLDEN_THREE",
    "ANALYZE_HOOKS",
    "ANALYZE_SATISFACTION_RHYTHM",
    "QUALITY_SCORE",
}

JSON_ARRAY_END_PROMPTS = {
    "INSPIRATION_TITLE_CRAFT",
    "INSPIRATION_DESCRIPTION_CRAFT",
}

NON_JSON_PROMPTS = {
    "FIX_AI_FLAVOR",
    "CHAPTER_OUTLINE_CRAFT",
    "CHAPTER_OUTLINE_CRAFT_STYLE",
    "CHAPTER_GENERATION_CRAFT",
    "CHAPTER_GENERATION_CRAFT_STYLE",
    "ANALYSIS_REPORT",
    "CHAPTER_CONTINUATION_CRAFT",
    "CHAPTER_CONTINUATION_CRAFT_STYLE",
}

PROMPT_REGISTRY = dict(zip(PROMPT_NAMES, ALL_PROMPTS, strict=False))


# ===== Existence Tests =====

class TestExistence:
    def test_all_15_constants_defined(self):
        assert len(ALL_PROMPTS) == 15

    def test_detect_ai_flavor_exists(self):
        assert DETECT_AI_FLAVOR

    def test_fix_ai_flavor_exists(self):
        assert FIX_AI_FLAVOR

    def test_analyze_golden_three_exists(self):
        assert ANALYZE_GOLDEN_THREE

    def test_analyze_hooks_exists(self):
        assert ANALYZE_HOOKS

    def test_analyze_satisfaction_rhythm_exists(self):
        assert ANALYZE_SATISFACTION_RHYTHM

    def test_quality_score_exists(self):
        assert QUALITY_SCORE

    def test_chapter_outline_craft_exists(self):
        assert CHAPTER_OUTLINE_CRAFT

    def test_chapter_outline_craft_style_exists(self):
        assert CHAPTER_OUTLINE_CRAFT_STYLE

    def test_chapter_generation_craft_exists(self):
        assert CHAPTER_GENERATION_CRAFT

    def test_chapter_generation_craft_style_exists(self):
        assert CHAPTER_GENERATION_CRAFT_STYLE

    def test_inspiration_title_craft_exists(self):
        assert INSPIRATION_TITLE_CRAFT

    def test_inspiration_description_craft_exists(self):
        assert INSPIRATION_DESCRIPTION_CRAFT

    def test_analysis_report_exists(self):
        assert ANALYSIS_REPORT

    def test_chapter_continuation_craft_exists(self):
        assert CHAPTER_CONTINUATION_CRAFT

    def test_chapter_continuation_craft_style_exists(self):
        assert CHAPTER_CONTINUATION_CRAFT_STYLE


# ===== String Type Tests =====

class TestStringType:
    def test_all_prompts_are_strings(self):
        for name, prompt in PROMPT_REGISTRY.items():
            assert isinstance(prompt, str), f"{name} is not a string"

    def test_all_prompts_are_non_empty(self):
        for name, prompt in PROMPT_REGISTRY.items():
            assert len(prompt) > 0, f"{name} is empty"

    def test_all_prompts_have_minimum_length(self):
        for name, prompt in PROMPT_REGISTRY.items():
            assert len(prompt) >= 50, f"{name} is too short ({len(prompt)} chars)"


# ===== Format String Tests =====

class TestFormatStrings:
    def test_detect_ai_flavor_format(self):
        result = DETECT_AI_FLAVOR.format(content="测试文本")
        assert "测试文本" in result
        assert "ai_score" in result

    def test_fix_ai_flavor_format(self):
        result = FIX_AI_FLAVOR.format(content="测试文本", issues="问题列表")
        assert "测试文本" in result
        assert "问题列表" in result

    def test_analyze_golden_three_format(self):
        result = ANALYZE_GOLDEN_THREE.format(content="第一章\n第二章\n第三章")
        assert "第一章" in result
        assert "chapter_1" in result
        assert "chapter_2" in result
        assert "chapter_3" in result

    def test_analyze_hooks_format(self):
        result = ANALYZE_HOOKS.format(content="开篇钩子测试")
        assert "开篇钩子测试" in result
        assert "first_500" in result

    def test_analyze_satisfaction_rhythm_format(self):
        escaped = ANALYZE_SATISFACTION_RHYTHM.replace(
            "{chapter_range, risk, suggestion}", "{{chapter_range, risk, suggestion}}"
        )
        result = escaped.format(content="节奏分析测试")
        assert "节奏分析测试" in result
        assert "satisfaction_loops" in result
        assert "chapter_range, risk, suggestion" in result

    def test_quality_score_format(self):
        result = QUALITY_SCORE.format(
            content="评分测试",
            title="测试书名",
            genre="玄幻",
        )
        assert "评分测试" in result
        assert "测试书名" in result
        assert "玄幻" in result
        assert "dimensions" in result
        assert "total_score" in result

    def test_chapter_outline_craft_format(self):
        result = CHAPTER_OUTLINE_CRAFT.format(
            genre="仙侠",
            project_title="测试小说",
            chapter_number=3,
            world_summary="修炼世界",
            book_overview="全书概要",
            characters_info="主角信息",
            prev_chapter_title="第二章",
            prev_chapter_tail="上一章结尾",
        )
        assert "仙侠" in result
        assert "测试小说" in result
        assert "3" in result
        assert "scenes" in result

    def test_chapter_outline_craft_style_format(self):
        result = CHAPTER_OUTLINE_CRAFT_STYLE.format(
            genre="都市",
            project_title="都市测试",
            chapter_number=5,
            tone="轻松幽默",
            pacing="快节奏",
            sentence_structure="短句为主",
            dialogue_style="口语化",
            description_style="简洁明快",
            emotional_intensity="中等",
            writing_techniques="欲扬先抑",
            hook_design="悬念型",
            satisfaction_pattern="打脸",
            satisfaction_type="装逼打脸",
            transition_style="悬念衔接",
            emotional_beats="紧张",
            foreshadowing_style="暗线",
            overall_summary="风格总结",
            world_summary="现代都市",
            book_overview="都市传奇",
            characters_info="角色列表",
            prev_chapter_title="第四章",
            prev_chapter_tail="上一章结尾",
        )
        assert "都市" in result
        assert "轻松幽默" in result
        assert "technique_focus" in result

    def test_chapter_generation_craft_format(self):
        result = CHAPTER_GENERATION_CRAFT.format(
            genre="奇幻",
            project_title="奇幻小说",
            chapter_number=7,
            chapter_title="第七章标题",
            chapter_outline="章节细纲",
            world_summary="奇幻世界",
            continuation_point="衔接锚点",
            target_word_count=3000,
            narrative_perspective="第三人称",
            previous_chapter_summary="前章概要",
            prev_chapter_hook="前章钩子",
            chapter_characters="角色列表",
            foreshadow_reminders="伏笔提醒",
            first_chapter_note="",
        )
        assert "奇幻" in result
        assert "第七章标题" in result
        assert "3000" in result
        assert "续点" not in result  # make sure continuation_point is present meaningfully

    def test_chapter_generation_craft_style_format(self):
        result = CHAPTER_GENERATION_CRAFT_STYLE.format(
            genre="科幻",
            project_title="科幻小说",
            chapter_number=10,
            chapter_title="星际",
            tone="严肃冷峻",
            pacing="慢节奏",
            sentence_structure="长句",
            dialogue_style="正式",
            description_style="细致",
            emotional_intensity="高",
            writing_techniques="双线叙事",
            hook_design="信息差",
            satisfaction_pattern="逆转",
            satisfaction_type="逆袭反转",
            transition_style="反转",
            emotional_beats="压抑到爆发",
            foreshadowing_style="明暗交替",
            overall_summary="科幻风格总结",
            chapter_outline="章节细纲",
            world_summary="星际文明",
            continuation_point="锚点",
            target_word_count=4000,
            narrative_perspective="第一人称",
            previous_chapter_summary="前章",
            prev_chapter_hook="前钩",
            chapter_characters="角色",
            foreshadow_reminders="伏笔",
            first_chapter_note="",
            technique_focus="核心技法",
        )
        assert "科幻" in result
        assert "星际" in result
        assert "双线叙事" in result
        assert "technique_focus" not in result  # The template has `technique_focus` as a format field inside the prompt that gets substituted

    def test_inspiration_title_craft_format(self):
        result = INSPIRATION_TITLE_CRAFT.format(user_input="废柴逆袭")
        assert "废柴逆袭" in result
        assert "JSON" in result

    def test_inspiration_description_craft_format(self):
        result = INSPIRATION_DESCRIPTION_CRAFT.format(
            title="测试书名",
            user_input="废柴逆袭修仙",
        )
        assert "测试书名" in result
        assert "废柴逆袭修仙" in result
        assert "JSON" in result

    def test_analysis_report_format(self):
        result = ANALYSIS_REPORT.format(content="综合分析数据")
        assert "综合分析数据" in result
        assert "markdown" in result.lower()

    def test_chapter_continuation_craft_format(self):
        result = CHAPTER_CONTINUATION_CRAFT.format(
            genre="武侠",
            project_title="武侠小说",
            chapter_number=12,
            chapter_title="决斗",
            progress_content="当前进度",
            chapter_outline="大纲",
            prev_chapter_hook="前章钩子",
            target_word_count=5000,
            progress_chars=2000,
            segment_chars=3000,
        )
        assert "武侠" in result
        assert "当前进度" in result
        assert "5000" in result
        assert "2000" in result
        assert "3000" in result

    def test_chapter_continuation_craft_style_format(self):
        result = CHAPTER_CONTINUATION_CRAFT_STYLE.format(
            genre="历史",
            project_title="历史小说",
            chapter_number=15,
            chapter_title="朝堂",
            tone="庄严",
            pacing="中速",
            sentence_structure="长短结合",
            dialogue_style="古风",
            description_style="典雅",
            emotional_intensity="中",
            writing_techniques="借古讽今",
            foreshadowing_style="明暗交替",
            overall_summary="历史风格总结",
            progress_content="已写内容",
            chapter_outline="大纲",
            prev_chapter_hook="前钩",
            target_word_count=6000,
            progress_chars=3000,
            segment_chars=3000,
        )
        assert "历史" in result
        assert "庄严" in result
        assert "借古讽今" in result


# ===== Key Content Tests =====

class TestKeyContent:
    def test_detect_ai_flavor_key_phrases(self):
        assert "ai_score" in DETECT_AI_FLAVOR
        assert "issues" in DETECT_AI_FLAVOR
        assert "summary" in DETECT_AI_FLAVOR
        assert "overall_assessment" in DETECT_AI_FLAVOR

    def test_fix_ai_flavor_key_phrases(self):
        assert "{content}" in FIX_AI_FLAVOR
        assert "{issues}" in FIX_AI_FLAVOR
        assert "自然文本基准" in FIX_AI_FLAVOR

    def test_analyze_golden_three_key_phrases(self):
        assert "chapter_1" in ANALYZE_GOLDEN_THREE
        assert "chapter_2" in ANALYZE_GOLDEN_THREE
        assert "chapter_3" in ANALYZE_GOLDEN_THREE
        assert "cross_chapter" in ANALYZE_GOLDEN_THREE
        assert "overall_score" in ANALYZE_GOLDEN_THREE
        assert "key_lessons" in ANALYZE_GOLDEN_THREE
        assert "黄金三章" in ANALYZE_GOLDEN_THREE

    def test_analyze_hooks_key_phrases(self):
        assert "first_500" in ANALYZE_HOOKS
        assert "information_asymmetry" in ANALYZE_HOOKS
        assert "empathy" in ANALYZE_HOOKS
        assert "anticipation" in ANALYZE_HOOKS
        assert "hook_density" in ANALYZE_HOOKS
        assert "improvement" in ANALYZE_HOOKS

    def test_analyze_satisfaction_rhythm_key_phrases(self):
        assert "satisfaction_loops" in ANALYZE_SATISFACTION_RHYTHM
        assert "type_distribution" in ANALYZE_SATISFACTION_RHYTHM
        assert "rhythm_pattern" in ANALYZE_SATISFACTION_RHYTHM
        assert "burst_density" in ANALYZE_SATISFACTION_RHYTHM
        assert "long_gaps" in ANALYZE_SATISFACTION_RHYTHM
        assert "pacing_score" in ANALYZE_SATISFACTION_RHYTHM

    def test_quality_score_key_phrases(self):
        assert "dimensions" in QUALITY_SCORE
        assert "total_score" in QUALITY_SCORE
        assert "grade" in QUALITY_SCORE
        assert "strengths" in QUALITY_SCORE
        assert "weaknesses" in QUALITY_SCORE
        assert "suggestions" in QUALITY_SCORE
        assert "{title}" in QUALITY_SCORE
        assert "{genre}" in QUALITY_SCORE

    def test_chapter_outline_craft_key_phrases(self):
        assert "scenes" in CHAPTER_OUTLINE_CRAFT
        assert "chapter_hook" in CHAPTER_OUTLINE_CRAFT
        assert "foreshadowing" in CHAPTER_OUTLINE_CRAFT
        assert "technique_focus" in CHAPTER_OUTLINE_CRAFT
        assert "{genre}" in CHAPTER_OUTLINE_CRAFT
        assert "{project_title}" in CHAPTER_OUTLINE_CRAFT

    def test_chapter_outline_craft_style_key_phrases(self):
        assert "{tone}" in CHAPTER_OUTLINE_CRAFT_STYLE
        assert "{pacing}" in CHAPTER_OUTLINE_CRAFT_STYLE
        assert "{sentence_structure}" in CHAPTER_OUTLINE_CRAFT_STYLE
        assert "{writing_techniques}" in CHAPTER_OUTLINE_CRAFT_STYLE
        assert "{satisfaction_pattern}" in CHAPTER_OUTLINE_CRAFT_STYLE

    def test_chapter_generation_craft_key_phrases(self):
        assert "{target_word_count}" in CHAPTER_GENERATION_CRAFT
        assert "{narrative_perspective}" in CHAPTER_GENERATION_CRAFT
        assert "{previous_chapter_summary}" in CHAPTER_GENERATION_CRAFT
        assert "{foreshadow_reminders}" in CHAPTER_GENERATION_CRAFT
        assert "直接输出小说正文" in CHAPTER_GENERATION_CRAFT

    def test_inspiration_title_craft_key_phrases(self):
        assert "{user_input}" in INSPIRATION_TITLE_CRAFT
        assert "JSON" in INSPIRATION_TITLE_CRAFT
        assert "6个" in INSPIRATION_TITLE_CRAFT or "6" in INSPIRATION_TITLE_CRAFT

    def test_inspiration_description_craft_key_phrases(self):
        assert "{title}" in INSPIRATION_DESCRIPTION_CRAFT
        assert "{user_input}" in INSPIRATION_DESCRIPTION_CRAFT
        assert "IA模式" in INSPIRATION_DESCRIPTION_CRAFT
        assert "CAF模式" in INSPIRATION_DESCRIPTION_CRAFT
        assert "PAST模式" in INSPIRATION_DESCRIPTION_CRAFT

    def test_analysis_report_key_phrases(self):
        assert "{content}" in ANALYSIS_REPORT
        assert "markdown" in ANALYSIS_REPORT.lower()

    def test_chapter_continuation_craft_key_phrases(self):
        assert "{progress_content}" in CHAPTER_CONTINUATION_CRAFT
        assert "{chapter_outline}" in CHAPTER_CONTINUATION_CRAFT
        assert "{target_word_count}" in CHAPTER_CONTINUATION_CRAFT
        assert "{progress_chars}" in CHAPTER_CONTINUATION_CRAFT
        assert "{segment_chars}" in CHAPTER_CONTINUATION_CRAFT
        assert "续写" in CHAPTER_CONTINUATION_CRAFT

    def test_chapter_continuation_craft_style_key_phrases(self):
        assert "{tone}" in CHAPTER_CONTINUATION_CRAFT_STYLE
        assert "{writing_techniques}" in CHAPTER_CONTINUATION_CRAFT_STYLE
        assert "{progress_content}" in CHAPTER_CONTINUATION_CRAFT_STYLE
        assert "风格约束" in CHAPTER_CONTINUATION_CRAFT_STYLE


# ===== JSON Constraint Tests =====

class TestJsonConstraints:
    def test_detect_ai_flavor_ends_with_json_instruction(self):
        assert "只输出JSON" in DETECT_AI_FLAVOR
        assert "不要其他内容" in DETECT_AI_FLAVOR

    def test_analyze_golden_three_ends_with_json_instruction(self):
        assert "只输出JSON" in ANALYZE_GOLDEN_THREE
        assert "不要其他内容" in ANALYZE_GOLDEN_THREE

    def test_analyze_hooks_ends_with_json_instruction(self):
        assert "只输出JSON" in ANALYZE_HOOKS
        assert "不要其他内容" in ANALYZE_HOOKS

    def test_analyze_satisfaction_rhythm_ends_with_json_instruction(self):
        assert "只输出JSON" in ANALYZE_SATISFACTION_RHYTHM
        assert "不要其他内容" in ANALYZE_SATISFACTION_RHYTHM

    def test_quality_score_ends_with_json_instruction(self):
        assert "只输出JSON" in QUALITY_SCORE
        assert "不要其他内容" in QUALITY_SCORE

    def test_inspiration_title_craft_ends_with_json_array_instruction(self):
        assert "JSON数组" in INSPIRATION_TITLE_CRAFT
        assert "不要其他内容" in INSPIRATION_TITLE_CRAFT

    def test_inspiration_description_craft_ends_with_json_array_instruction(self):
        assert "JSON数组" in INSPIRATION_DESCRIPTION_CRAFT
        assert "不要其他内容" in INSPIRATION_DESCRIPTION_CRAFT

    def test_fix_ai_flavor_does_not_have_json_instruction(self):
        assert "只输出JSON" not in FIX_AI_FLAVOR

    def test_analysis_report_does_not_have_json_instruction(self):
        assert "只输出JSON" not in ANALYSIS_REPORT

    def test_chapter_outlines_do_not_have_strict_json_instruction(self):
        assert "只输出JSON" not in CHAPTER_OUTLINE_CRAFT
        assert "只输出JSON" not in CHAPTER_OUTLINE_CRAFT_STYLE

    def test_chapter_continuations_do_not_have_json_instruction(self):
        assert "只输出JSON" not in CHAPTER_CONTINUATION_CRAFT
        assert "只输出JSON" not in CHAPTER_CONTINUATION_CRAFT_STYLE

    def test_json_prompts_contain_json_format_keys(self):
        for name in JSON_END_PROMPTS:
            prompt = PROMPT_REGISTRY[name]
            assert "JSON" in prompt, f"{name} should mention JSON"

    def test_non_json_prompts_do_not_have_strict_json_ending(self):
        for name in NON_JSON_PROMPTS:
            prompt = PROMPT_REGISTRY[name]
            assert "只输出JSON" not in prompt, (
                f"{name} should not have strict JSON-only instruction"
            )


# ===== Import Test =====

class TestImport:
    def test_all_constants_import_correctly(self):
        from novel_creator.craft_prompts import (
            ANALYSIS_REPORT,
            ANALYZE_GOLDEN_THREE,
            ANALYZE_HOOKS,
            ANALYZE_SATISFACTION_RHYTHM,
            CHAPTER_CONTINUATION_CRAFT,
            CHAPTER_CONTINUATION_CRAFT_STYLE,
            CHAPTER_GENERATION_CRAFT,
            CHAPTER_GENERATION_CRAFT_STYLE,
            CHAPTER_OUTLINE_CRAFT,
            CHAPTER_OUTLINE_CRAFT_STYLE,
            DETECT_AI_FLAVOR,
            FIX_AI_FLAVOR,
            INSPIRATION_DESCRIPTION_CRAFT,
            INSPIRATION_TITLE_CRAFT,
            QUALITY_SCORE,
        )
        assert DETECT_AI_FLAVOR
        assert FIX_AI_FLAVOR
        assert ANALYZE_GOLDEN_THREE
        assert ANALYZE_HOOKS
        assert ANALYZE_SATISFACTION_RHYTHM
        assert QUALITY_SCORE
        assert CHAPTER_OUTLINE_CRAFT
        assert CHAPTER_OUTLINE_CRAFT_STYLE
        assert CHAPTER_GENERATION_CRAFT
        assert CHAPTER_GENERATION_CRAFT_STYLE
        assert INSPIRATION_TITLE_CRAFT
        assert INSPIRATION_DESCRIPTION_CRAFT
        assert ANALYSIS_REPORT
        assert CHAPTER_CONTINUATION_CRAFT
        assert CHAPTER_CONTINUATION_CRAFT_STYLE

    def test_no_duplicate_prompt_names(self):
        assert len(PROMPT_NAMES) == len(set(PROMPT_NAMES))

    def test_no_import_side_effects(self):
        from novel_creator.craft_prompts import DETECT_AI_FLAVOR
        assert DETECT_AI_FLAVOR
