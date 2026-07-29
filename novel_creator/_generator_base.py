import logging
import re

from .prompts import (
    _fix_truncated_json,
    parse_json_response,
)

logger = logging.getLogger('novel_creator.generator')


class _BaseGeneratorMixin:

    def _generate_json(self, prompt, system_prompt=None, max_retries=2, max_tokens=None, module_name=None):
        for attempt in range(max_retries + 1):
            text, err = self.client.generate(prompt, system_prompt=system_prompt, max_tokens=max_tokens)
            if err:
                if attempt < max_retries:
                    continue
                return None, err
            if text and text.strip().startswith("<"):
                return None, "API返回错误页面(可能是认证失败或模型不存在)"
            result = parse_json_response(text)
            if result is not None:
                if module_name:
                    try:
                        from ._validator import validate_result
                        valid, val_err = validate_result(module_name, result)
                        if not valid and attempt < max_retries:
                            prompt = prompt + f"\n\n上次返回格式错误: {val_err}。请确保返回完整JSON。"
                            continue
                    except ImportError:
                        pass
                return result, None
            if text and ('{' in text or '[' in text):
                fixed = _fix_truncated_json(text)
                if fixed:
                    return fixed, None
            if attempt < max_retries:
                continue
        return None, f"JSON解析失败 (重试{max_retries}次)"

    def _build_style_prompt_vars(self, style, user_input="", title="", description=""):
        if style:
            fmt = self._format_style(style)
            return {
                'style_section': '',
                'user_input_section': '用户输入：' + user_input + '\n\n' if user_input else '',
                'user_input': user_input,
                'title': title,
                'description': description,
                **fmt,
            }
        else:
            return {
                'user_input': user_input,
                'user_input_section': '用户输入：' + user_input + '\n' if user_input else '',
                'title': title,
                'description': description,
            }

    def _format_style(self, style):
        if not isinstance(style, dict):
            return {}
        flat = {}
        for key, value in style.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in flat:
                        flat[sub_key] = sub_value
            else:
                flat[key] = value
        style = flat

        unique_quirks = style.get('unique_quirks', [])
        if isinstance(unique_quirks, list):
            unique_quirks = ', '.join(unique_quirks)

        writing_techniques = style.get('writing_techniques', [])
        if isinstance(writing_techniques, list):
            writing_techniques = ', '.join(writing_techniques)

        sub_genres = style.get('sub_genres', [])
        if isinstance(sub_genres, list):
            sub_genres = '/'.join(sub_genres)

        sub_themes = style.get('sub_themes', [])
        if isinstance(sub_themes, list):
            sub_themes = '/'.join(sub_themes)

        emotional_beats = style.get('emotional_beats', [])
        if isinstance(emotional_beats, list):
            emotional_beats = '→'.join(emotional_beats) if isinstance(emotional_beats, list) else str(emotional_beats)

        return {
            'narrative_perspective': style.get('narrative_perspective', '未指定'),
            'tone': style.get('tone', '未指定'),
            'pacing': style.get('pacing', '未指定'),
            'dialogue_style': style.get('dialogue_style', '未指定'),
            'description_style': style.get('description_style', '未指定'),
            'vocabulary_level': style.get('vocabulary_level', '未指定'),
            'sentence_structure': style.get('sentence_structure', '未指定'),
            'emotional_intensity': style.get('emotional_intensity', '未指定'),
            'unique_quirks': unique_quirks or '未指定',
            'overall_summary': style.get('overall_summary', '未指定'),
            'genre_style': style.get('genre', ''),
            'sub_genres': sub_genres or '',
            'sub_themes': sub_themes or '',
            'plot_structure': style.get('plot_structure', ''),
            'story_framework': style.get('story_framework', ''),
            'core_drive': style.get('core_drive', ''),
            'main_conflict': style.get('main_conflict', ''),
            'upgrade_mechanism': style.get('upgrade_mechanism', ''),
            'writing_techniques': writing_techniques or '',
            'hook_design': style.get('hook_design', ''),
            'satisfaction_type': style.get('satisfaction_type', ''),
            'satisfaction_pattern': style.get('satisfaction_pattern', ''),
            'emotional_beats': emotional_beats or '',
            'foreshadowing_style': style.get('foreshadowing_style', ''),
            'transition_style': style.get('transition_style', ''),
            'protagonist_archetype': style.get('protagonist_archetype', ''),
            'character_growth_pattern': style.get('character_growth_pattern', ''),
            'relationship_dynamics': style.get('relationship_dynamics', ''),
            'world_building_style': style.get('world_building_style', ''),
            'world_features': style.get('world_features', ''),
            'key_lessons': ', '.join(style.get('key_lessons', [])) if isinstance(style.get('key_lessons'), list) else str(style.get('key_lessons', '')),
        }

    def _format_characters(self, chapter_characters):
        if isinstance(chapter_characters, list) and chapter_characters:
            return "\n".join([
                f"- {c.get('name', '未知')}: {c.get('role_type', c.get('role', '角色'))} - "
                f"{c.get('personality', '')} | 背景: {c.get('background', '')[:80]} | "
                f"外貌: {c.get('appearance', '')[:60]}"
                for c in chapter_characters[:10]
            ])
        return str(chapter_characters) if chapter_characters else "（见大纲）"

    def _extract_items(self, text, keywords):
        items = []
        for kw in keywords:
            pattern = kw + r'[：:]([^，。；\n]{2,30})'
            matches = re.findall(pattern, text)
            items.extend(matches)
        seen = set()
        unique = []
        for item in items:
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                unique.append(item)
        return unique[:8]

    def _extract_first_match(self, text, keywords):
        items = self._extract_items(text, keywords)
        return items[0] if items else ""
