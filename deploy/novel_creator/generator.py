"""小说创作生成器 - 完整的创作流程"""
import json
import re
from .prompts import (
    WORLD_BUILDING, CHARACTERS_BATCH_GENERATION, OUTLINE_CREATE,
    CHAPTER_GENERATION_NEXT, PLOT_ANALYSIS,
    INSPIRATION_TITLE, INSPIRATION_DESCRIPTION, INSPIRATION_THEME, INSPIRATION_GENRE,
    STYLE_ANALYSIS, format_prompt, parse_json_response
)
from .ai_client import AIClient


class NovelGenerator:
    """小说创作生成器 - 从灵感到大纲到章节的完整流程"""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000):
        self.client = AIClient(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens)

    def _generate_json(self, prompt, system_prompt=None, max_retries=2):
        """生成并解析JSON响应"""
        for attempt in range(max_retries + 1):
            text, err = self.client.generate(prompt, system_prompt=system_prompt)
            if err:
                if attempt == max_retries:
                    return None, err
                continue
            result = parse_json_response(text)
            if result is not None:
                return result, None
            if attempt == max_retries:
                return None, f"JSON解析失败: {text[:200]}"
        return None, "未知错误"

    # ========== 灵感模式 ==========

    def generate_titles(self, user_input=""):
        """生成书名建议"""
        prompt = format_prompt(INSPIRATION_TITLE, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_descriptions(self, title, user_input=""):
        """生成简介选项"""
        prompt = format_prompt(INSPIRATION_DESCRIPTION, title=title, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_themes(self, title, description):
        """生成主题选项"""
        prompt = format_prompt(INSPIRATION_THEME, title=title, description=description)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_genres(self, title, description):
        """生成类型标签"""
        prompt = format_prompt(INSPIRATION_GENRE, title=title, description=description)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    # ========== 世界观构建 ==========

    def generate_world_building(self, title, theme, genre, description):
        """生成世界观"""
        prompt = format_prompt(WORLD_BUILDING, title=title, theme=theme, genre=genre, description=description)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 角色生成 ==========

    def generate_characters(self, world_data, theme, genre, count=6, requirements=""):
        """生成角色"""
        prompt = format_prompt(
            CHARACTERS_BATCH_GENERATION,
            count=count,
            time_period=world_data.get("time_period", ""),
            location=world_data.get("location", ""),
            atmosphere=world_data.get("atmosphere", ""),
            rules=world_data.get("rules", ""),
            theme=theme,
            genre=genre,
            requirements=requirements
        )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 大纲生成 ==========

    def generate_outline(self, title, theme, genre, characters_info, chapter_count=3, narrative_perspective="第三人称"):
        """生成大纲"""
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        prompt = format_prompt(
            OUTLINE_CREATE,
            title=title, theme=theme, genre=genre,
            chapter_count=chapter_count,
            narrative_perspective=narrative_perspective,
            characters_info=chars_text
        )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 章节生成 ==========

    def generate_chapter(self, project_title, genre, chapter_number, chapter_title,
                         chapter_outline, continuation_point="", previous_chapter_summary="",
                         chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                         narrative_perspective="第三人称"):
        """生成章节正文"""
        prompt = format_prompt(
            CHAPTER_GENERATION_NEXT,
            project_title=project_title,
            genre=genre,
            chapter_number=chapter_number,
            chapter_title=chapter_title,
            target_word_count=target_word_count,
            narrative_perspective=narrative_perspective,
            chapter_outline=chapter_outline,
            continuation_point=continuation_point or "（第一章，故事开始）",
            previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
            chapter_characters=chapter_characters or "（见大纲）",
            foreshadow_reminders=foreshadow_reminders or "暂无"
        )
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err

    # ========== 分析功能 ==========

    def analyze_style(self, content):
        """分析写作风格"""
        prompt = format_prompt(STYLE_ANALYSIS, content=content[:6000])
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def analyze_chapter(self, chapter_number, title, content):
        """分析章节"""
        prompt = format_prompt(PLOT_ANALYSIS, chapter_number=chapter_number, title=title, content=content[:6000])
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 仿写生成 ==========

    def generate_with_style(self, style_profile, genre, count, protagonist, world, outline, target_word_count=3000):
        """根据风格仿写生成小说"""
        prompt = f"""你是一位专业小说作家。请根据以下风格特征，创作新的小说内容。

=== 参考风格 ===
{style_profile}

=== 创作要求 ===
- 题材：{genre}
- 主角：{protagonist}
- 世界观：{world}
- 故事大纲：{outline}
- 目标字数：{target_word_count}字

请直接输出小说正文，从故事场景或动作开始。不要写标题，直接开始正文。"""
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err
