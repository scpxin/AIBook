"""小说创作生成器 - 完整的创作流程"""
import json
import logging
import re

logger = logging.getLogger('novel_creator.generator')
from .ai_client import AIClient
from .craft_prompts import (
    CHAPTER_CONTINUATION_CRAFT,
    CHAPTER_CONTINUATION_CRAFT_STYLE,
    CHAPTER_GENERATION_CRAFT,
    CHAPTER_GENERATION_CRAFT_STYLE,
    CHAPTER_OUTLINE_CRAFT,
    CHAPTER_OUTLINE_CRAFT_STYLE,
    INSPIRATION_DESCRIPTION_CRAFT,
    INSPIRATION_TITLE_CRAFT,
    QUALITY_SCORE,
)
from .prompts import (
    BOOK_OVERVIEW_CREATE,
    BOOK_OVERVIEW_CREATE_STYLE,
    CHAPTER_CONTINUATION,
    CHAPTER_CONTINUATION_STYLE,
    CHAPTER_GENERATION_NEXT,
    CHAPTER_GENERATION_NEXT_STYLE,
    CHAPTER_OUTLINE_DETAIL,
    CHAPTER_OUTLINE_DETAIL_STYLE,
    CHAPTER_POLISH,
    CHARACTERS_BATCH_GENERATION,
    CHARACTERS_BATCH_GENERATION_STYLE,
    INSPIRATION_DESCRIPTION,
    INSPIRATION_DESCRIPTION_STYLE,
    INSPIRATION_GENRE,
    INSPIRATION_GENRE_STYLE,
    INSPIRATION_THEME,
    INSPIRATION_THEME_STYLE,
    INSPIRATION_TITLE,
    INSPIRATION_TITLE_STYLE,
    OUTLINE_CREATE,
    OUTLINE_CREATE_STYLE,
    WORLD_BUILDING,
    WORLD_BUILDING_STYLE,
    _fix_truncated_json,
    format_prompt,
    parse_json_response,
)


class NovelGenerator:
    """小说创作生成器 - 从灵感到大纲到章节的完整流程"""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000, timeout=120):
        self.client = AIClient(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        self.max_tokens = max_tokens

    def _generate_json(self, prompt, system_prompt=None, max_retries=2, max_tokens=None, module_name=None):
        """生成并解析JSON响应"""
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
                        from app.services.validation import validate_result
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

    # ========== 灵感模式 ==========

    def _build_style_prompt_vars(self, style, user_input="", title="", description=""):
        """构建风格 prompt 的变量 dict"""
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
            # 非风格分支：只返回基础字段（format_prompt 安全处理缺失的 style 字段）
            return {
                'user_input': user_input,
                'user_input_section': '用户输入：' + user_input + '\n' if user_input else '',
                'title': title,
                'description': description,
            }

    def _format_style(self, style):
        """将风格分析结果扁平化为 prompt 变量 dict（全量字段）"""
        # 如果 AI 错误地嵌套了分组（如 {"基础风格": {"tone": ...}}），自动展平
        if not isinstance(style, dict):
            return {}
        flat = {}
        for key, value in style.items():
            if isinstance(value, dict):
                # 嵌套分组 → 展平子字段
                for sub_key, sub_value in value.items():
                    if sub_key not in flat:  # 外层优先
                        flat[sub_key] = sub_value
            else:
                flat[key] = value
        style = flat

        # list 字段转为字符串
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
            # 基础风格
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
            # 题材与主题
            'genre_style': style.get('genre', ''),
            'sub_genres': sub_genres or '',
            'sub_themes': sub_themes or '',
            # 故事结构
            'plot_structure': style.get('plot_structure', ''),
            'story_framework': style.get('story_framework', ''),
            'core_drive': style.get('core_drive', ''),
            'main_conflict': style.get('main_conflict', ''),
            'upgrade_mechanism': style.get('upgrade_mechanism', ''),
            # 写作技法
            'writing_techniques': writing_techniques or '',
            'hook_design': style.get('hook_design', ''),
            'satisfaction_type': style.get('satisfaction_type', ''),
            'satisfaction_pattern': style.get('satisfaction_pattern', ''),
            'emotional_beats': emotional_beats or '',
            'foreshadowing_style': style.get('foreshadowing_style', ''),
            'transition_style': style.get('transition_style', ''),
            # 人物塑造
            'protagonist_archetype': style.get('protagonist_archetype', ''),
            'character_growth_pattern': style.get('character_growth_pattern', ''),
            'relationship_dynamics': style.get('relationship_dynamics', ''),
            # 世界观特征
            'world_building_style': style.get('world_building_style', ''),
            'world_features': style.get('world_features', ''),
            # 其他
            'key_lessons': ', '.join(style.get('key_lessons', [])) if isinstance(style.get('key_lessons'), list) else str(style.get('key_lessons', '')),
        }

    def generate_titles(self, user_input="", style_profile=None):
        """生成书名建议"""
        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile, user_input)
            prompt = format_prompt(INSPIRATION_TITLE_STYLE, **style_vars)
        else:
            prompt = format_prompt(INSPIRATION_TITLE, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_descriptions(self, title, user_input="", style_profile=None):
        """生成简介选项"""
        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile, user_input, title=title)
            prompt = format_prompt(INSPIRATION_DESCRIPTION_STYLE, **style_vars)
        else:
            prompt = format_prompt(INSPIRATION_DESCRIPTION, title=title, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_themes(self, title, description, user_input="", style_profile=None):
        """生成主题选项"""
        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile, user_input, title=title, description=description)
            prompt = format_prompt(INSPIRATION_THEME_STYLE, **style_vars)
        else:
            prompt = format_prompt(INSPIRATION_THEME, title=title, description=description,
                                   user_input=user_input,
                                   user_input_section='用户输入：' + user_input + '\n' if user_input else '')
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_genres(self, title, description, user_input="", style_profile=None):
        """生成类型标签"""
        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile, user_input, title=title, description=description)
            prompt = format_prompt(INSPIRATION_GENRE_STYLE, **style_vars)
        else:
            prompt = format_prompt(INSPIRATION_GENRE, title=title, description=description,
                                   user_input=user_input,
                                   user_input_section='用户输入：' + user_input + '\n' if user_input else '')
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    # ========== 世界观构建 ==========

    def generate_world_building(self, title, theme, genre, description, style_profile=None):
        """生成世界观"""
        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile, "", title=title, description=description)
            style_vars['theme'] = theme
            style_vars['genre'] = genre
            prompt = format_prompt(WORLD_BUILDING_STYLE, **style_vars)
        else:
            prompt = format_prompt(WORLD_BUILDING, title=title, theme=theme, genre=genre, description=description)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def reparse_world_building(self, world_text, style_profile=None):
        """从已有世界观正文重新提取结构化数据"""
        prompt = f"""从以下世界观描述中提取结构化JSON数据。

世界观正文：
{world_text[:6000]}

请提取以下字段，返回JSON格式：
- time_period: 时间背景（如"现代都市"、"远古洪荒"等）
- location: 空间环境（如"修真界·东域"、"赛博朋克都市"等）
- atmosphere: 情感基调（如"热血激昂"、"阴暗压抑"等）
- rules: 世界规则（如"修炼体系：练气→筑基→金丹"、"异能觉醒规则"等）

只返回JSON，不要其他文字。"""
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def reparse_characters(self, characters_text, style_profile=None):
        """从已有角色正文重新提取结构化角色数据"""
        prompt = f"""从以下角色描述中提取结构化JSON数组。

角色正文：
{characters_text[:6000]}

每个角色提取以下字段：
- name: 名字
- role_type: 角色类型（主角/配角/反派/龙套）
- gender: 性别
- age: 年龄（数字或描述）
- personality: 性格特点
- background: 背景故事
- appearance: 外貌特征
- traits: 特殊能力/标志特征

返回JSON数组格式，只返回JSON，不要其他文字。"""
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        if isinstance(result, list):
            return result, None
        if isinstance(result, dict) and 'characters' in result:
            return result['characters'], None
        return None, "解析结果格式不正确"

    def summarize_inspiration(self, title, description, theme, genre):
        """生成灵感步骤摘要"""
        return {
            "title": title or "",
            "description": (description or "")[:200],
            "theme": theme or "",
            "genre": genre or "",
            "core_premise": (description or "")[:100]
        }

    def summarize_world(self, world_data, theme, genre):
        """生成世界观步骤摘要"""
        if isinstance(world_data, dict):
            world_text = json.dumps(world_data, ensure_ascii=False)
        elif isinstance(world_data, list):
            parts = []
            for w in world_data:
                if isinstance(w, dict):
                    parts.append(w.get('name', '') + ':' + str(w.get('description', ''))[:100])
            world_text = "; ".join(parts)
        else:
            world_text = str(world_data)

        # 提取关键信息
        return {
            "key_locations": self._extract_items(world_text, ["地点", "世界", "区域", "城市", "大陆"])[:5],
            "power_system": self._extract_first_match(world_text, ["修炼体系", "实力等级", "斗气", "魔法", "系统", "境界"]),
            "key_rules": self._extract_items(world_text, ["规则", "法则", "约束", "限制"])[:3],
            "factions": self._extract_items(world_text, ["势力", "宗门", "家族", "组织", "帝国", "国家"])[:5],
            "unique_elements": self._extract_items(world_text, ["特殊", "独特", "异", "神", "灵", "秘"])[:3],
            "summary_text": world_text[:500]
        }

    def summarize_characters(self, characters_info):
        """生成角色步骤摘要"""
        if isinstance(characters_info, str):
            try:
                chars = json.loads(characters_info)
            except (json.JSONDecodeError, TypeError):
                return self._summarize_characters_text(characters_info)
        elif isinstance(characters_info, list):
            chars = characters_info
        else:
            return self._summarize_characters_text(str(characters_info))

        char_summaries = []
        for c in chars[:10]:
            if isinstance(c, dict):
                char_summaries.append({
                    "name": c.get('name', '未知'),
                    "role": c.get('role', c.get('身份', '')),
                    "personality": (c.get('personality', c.get('性格', '')))[:80],
                    "goal": (c.get('goal', c.get('目标', '')))[:60],
                    "special": (c.get('special_ability', c.get('能力', c.get('天赋', ''))))[:60]
                })
            elif isinstance(c, str):
                char_summaries.append({"name": c, "role": "", "personality": "", "goal": "", "special": ""})

        return {
            "protagonist": char_summaries[0] if char_summaries else {},
            "main_chars": char_summaries[1:5],
            "antagonist": char_summaries[-1] if len(char_summaries) > 1 else {},
            "char_count": len(char_summaries),
            "char_names": [c["name"] for c in char_summaries[:8]]
        }

    def _summarize_characters_text(self, text):
        """从纯文本解析角色摘要"""
        names = self._extract_items(text, ["主角", "男主", "女主", "反派", "配角"])
        return {
            "protagonist": {"name": names[0] if names else "", "role": "主角", "personality": "", "goal": "", "special": ""},
            "main_chars": [{"name": n, "role": "", "personality": "", "goal": "", "special": ""} for n in names[1:5]],
            "antagonist": {"name": names[-1] if len(names) > 1 else "", "role": "", "personality": "", "goal": "", "special": ""},
            "char_count": len(names),
            "char_names": names[:8]
        }

    def summarize_book_overview(self, overview_json):
        """生成总纲步骤摘要（提取关键结构信息）"""
        if isinstance(overview_json, str):
            try:
                ov = json.loads(overview_json)
            except (json.JSONDecodeError, TypeError):
                return {"raw_text": overview_json[:500]}
        elif isinstance(overview_json, dict):
            ov = overview_json
        else:
            return {"raw_text": str(overview_json)[:500]}

        cc = ov.get('core_conflict', {})
        acts = ov.get('acts', [])
        chars = ov.get('character_arcs', [])

        return {
            "central_conflict": cc.get('central_conflict', ''),
            "central_question": cc.get('central_question', ''),
            "thematic_statement": cc.get('thematic_statement', ''),
            "act_count": len(acts),
            "act_names": [a.get('name', '') for a in acts],
            "char_arc_count": len(chars),
            "char_names": [c.get('name', '') for c in chars[:8]],
            "foreshadow_count": len(ov.get('foreshadowing', [])),
            "subplot_count": len(ov.get('subplots', [])),
            "pacing_segments": len(ov.get('pacing', []))
        }

    def _extract_items(self, text, keywords):
        """从文本中抽取包含关键词的片段"""
        items = []
        for kw in keywords:
            pattern = kw + r'[：:]([^，。；\n]{2,30})'
            matches = re.findall(pattern, text)
            items.extend(matches)
        # 也去重
        seen = set()
        unique = []
        for item in items:
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                unique.append(item)
        return unique[:8]

    def _extract_first_match(self, text, keywords):
        """提取第一个匹配项"""
        items = self._extract_items(text, keywords)
        return items[0] if items else ""

    def generate_characters(self, world_data, theme, genre, count=6, requirements="", style_profile=None, description=""):
        """生成角色"""
        def truncate(s, max_len=300):
            s = str(s)
            return s[:max_len] + "..." if len(s) > max_len else s

        if style_profile:
            style_vars = self._build_style_prompt_vars(style_profile)
            fmt = style_vars
            prompt = format_prompt(CHARACTERS_BATCH_GENERATION_STYLE,
                count=count,
                time_period=truncate(world_data.get("time_period", "")),
                location=truncate(world_data.get("location", "")),
                atmosphere=truncate(world_data.get("atmosphere", "")),
                rules=truncate(world_data.get("rules", "")),
                theme=truncate(theme, 200),
                genre=genre,
                requirements=truncate(requirements, 200),
                protagonist_archetype=fmt.get('protagonist_archetype', ''),
                character_growth_pattern=fmt.get('character_growth_pattern', ''),
                relationship_dynamics=fmt.get('relationship_dynamics', ''),
                tone=fmt.get('tone', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                upgrade_mechanism=fmt.get('upgrade_mechanism', ''),
                main_conflict=fmt.get('main_conflict', ''),
                sub_genres=fmt.get('sub_genres', ''),
            )
        else:
            prompt = format_prompt(
                CHARACTERS_BATCH_GENERATION,
                count=count,
                time_period=truncate(world_data.get("time_period", "")),
                location=truncate(world_data.get("location", "")),
                atmosphere=truncate(world_data.get("atmosphere", "")),
                rules=truncate(world_data.get("rules", "")),
                theme=truncate(theme, 200),
                genre=genre,
                requirements=truncate(requirements, 200),
                novel_description=truncate(description, 200)
            )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 总纲生成 ==========

    def generate_book_overview(self, title, theme, genre, characters_info,
                               narrative_perspective="第三人称", style_profile=None,
                               world_summary="", inspiration_desc=""):
        """生成全书结构化总纲（6维度蓝图）"""
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        # 构建前序步骤摘要
        world_text = world_summary if world_summary else "（未设定世界观）"
        desc_text = inspiration_desc if inspiration_desc else "（未设定简介）"

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(BOOK_OVERVIEW_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                story_framework=fmt.get('story_framework', ''),
                core_drive=fmt.get('core_drive', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
                sub_genres=fmt.get('sub_genres', ''),
            )
        else:
            prompt = format_prompt(BOOK_OVERVIEW_CREATE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
            )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def generate_book_overview_stream(self, title, theme, genre, characters_info,
                                      narrative_perspective="第三人称", style_profile=None,
                                      world_summary="", inspiration_desc=""):
        """流式生成全书结构化总纲"""
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        world_text = world_summary if world_summary else "（未设定世界观）"
        desc_text = inspiration_desc if inspiration_desc else "（未设定简介）"

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(BOOK_OVERVIEW_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
                story_framework=fmt.get('story_framework', ''),
                core_drive=fmt.get('core_drive', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
                sub_genres=fmt.get('sub_genres', ''),
            )
        else:
            prompt = format_prompt(BOOK_OVERVIEW_CREATE,
                title=title, theme=theme, genre=genre,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_text,
                inspiration_desc=desc_text,
            )

        logger.info(f"generate_book_overview_stream called: title={title}, theme={theme}, genre={genre}, max_tokens={min(self.max_tokens * 2, 32000)}")
        full_text = ''
        overview_max_tokens = min(self.max_tokens * 2, 32000)
        for chunk in self.client.generate_stream(prompt, temperature=0.7, max_tokens=overview_max_tokens):
            if isinstance(chunk, dict):
                if chunk.get('error'):
                    logger.error(f"book-overview AI error: {chunk['error']}")
                    yield {'done': True, 'error': chunk['error']}
                    return
                text = chunk.get('content', '')
            else:
                text = str(chunk)
            if text:
                full_text += text
                yield {'content': text}
        logger.info(f"book-overview raw response: {len(full_text)} chars")
        if len(full_text) < 100:
            logger.warning(f"book-overview response too short: {full_text!r}")
        result = parse_json_response(full_text)
        if result is not None:
            logger.info(f"book-overview JSON parsed successfully: {len(json.dumps(result))} chars")
            yield {'done': True, 'result': result}
        else:
            logger.error(f"book-overview JSON parse failed: {full_text[:500]!r}")
            yield {'done': True, 'error': f'JSON解析失败: {full_text[:200]}'}

    # ========== 章节细纲生成（局部上下文注入）==========

    def generate_chapter_outline(self, project_title, genre, book_overview_json, chapter_number,
                                  total_chapters, characters_info, narrative_perspective="第三人称",
                                  style_profile=None, world_summary="", prev_chapter_title="", prev_chapter_tail="",
                                  use_craft=False):
        """生成单章细纲（注入局部上下文 + 世界观）"""
        import json

        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        # 解析总纲JSON，提取局部上下文
        overview_available = True
        try:
            overview = json.loads(book_overview_json) if isinstance(book_overview_json, str) else book_overview_json
            if not overview or not isinstance(overview, dict):
                overview = {}
                overview_available = False
        except (json.JSONDecodeError, TypeError):
            overview = {}
            overview_available = False

        # 当总纲缺失时注入警告
        degradation_warning = ""
        if not overview_available:
            degradation_warning = "\n⚠️ 注意：全书总纲缺失或格式错误，本章细纲缺少上下文注入（幕信息、角色弧、支线、伏笔均不可用）。建议重新生成总纲后再次生成细纲。"

        # 1. 所属幕信息
        acts = overview.get('acts', [])
        current_act = None
        for act in acts:
            cr = act.get('chapter_range', '')
            parts = cr.split('-')
            if len(parts) == 2:
                try:
                    start, end = int(parts[0]), int(parts[1])
                    if start <= chapter_number <= end:
                        current_act = act
                        break
                except ValueError:
                    pass
        if not current_act and acts:
            idx = min(int(chapter_number / max(total_chapters, 1) * len(acts)), len(acts) - 1)
            current_act = acts[idx]

        act_context = "所属幕：" + (current_act.get('name', '未知') if current_act else '未知')
        if current_act:
            act_context += "\n本幕目标：" + current_act.get('goal', '')
            act_context += "\n本幕情感基调：" + current_act.get('emotional_tone', '')
            if current_act.get('key_turning_point'):
                act_context += "\n本幕关键转折：" + current_act['key_turning_point']

        # 2. 本章触发的角色转变
        char_arcs = overview.get('character_arcs', [])
        milestones_here = []
        for arc in char_arcs:
            for ms in arc.get('milestones', []):
                if ms.get('chapter') == chapter_number:
                    milestones_here.append({"name": arc.get('name', ''), "change": ms.get('change', '')})
        character_milestones = "本章无角色转变" if not milestones_here else "\n".join(
            [f"- {m['name']}: {m['change']}" for m in milestones_here]
        )

        # 3. 当前活跃支线
        subplots = overview.get('subplots', [])
        active_here = [sp for sp in subplots if chapter_number in sp.get('involved_chapters', [])]
        active_subplots = "无活跃支线" if not active_here else "\n".join(
            [f"- {sp['name']}（收束于第{sp.get('resolution_chapter', '?')}章）" for sp in active_here]
        )

        # 4. 伏笔管理
        fores = overview.get('foreshadowing', [])
        plant_here = [f for f in fores if f.get('planted_chapter') == chapter_number]
        payoff_here = [f for f in fores if f.get('payoff_chapter') == chapter_number]
        foreshadow_to_plant = "无需埋设伏笔" if not plant_here else "\n".join(
            [f"- {f['hint']}（将于第{f.get('payoff_chapter', '?')}章回收）" for f in plant_here]
        )
        foreshadow_to_payoff = "无需回收伏笔" if not payoff_here else "\n".join(
            [f"- {f['hint']} → 揭示：{f.get('reveal', '')}" for f in payoff_here]
        )

        # 5. 本章节奏要求
        pacing = overview.get('pacing', [])
        pace_here = None
        for p in pacing:
            pc = p.get('chapters', '')
            parts = pc.split('-')
            if len(parts) == 2:
                try:
                    if int(parts[0]) <= chapter_number <= int(parts[1]):
                        pace_here = p
                        break
                except ValueError:
                    pass
        if not pace_here and pacing:
            pace_here = pacing[min(int(chapter_number / max(total_chapters, 1) * len(pacing)), len(pacing) - 1)]
        pacing_requirement = "节奏：" + (pace_here.get('rhythm', '正常') if pace_here else '正常')
        if pace_here:
            pacing_requirement += "\n爽点类型：" + pace_here.get('satisfaction_type', '无特殊要求')

        # 6. 世界观上下文
        world_ctx = world_summary[:300] if world_summary else "（未设定世界观）"

        # 7. 前一章衔接
        prev_title = prev_chapter_title or "（无前章）"
        prev_tail = (prev_chapter_tail or "")[:300] if prev_chapter_tail else "（无前章结尾）"

        # 8. 本章位置描述
        if total_chapters <= 1:
            position = "这是唯一的一章，需要完整呈现故事。"
        elif chapter_number <= total_chapters * 0.1:
            position = "属于开局阶段，需要建立世界观、引入主角、设置初始矛盾。"
        elif chapter_number <= total_chapters * 0.25:
            position = "属于发展阶段，需要推进剧情、增加冲突复杂度、发展角色关系。"
        elif chapter_number <= total_chapters * 0.5:
            position = "属于中期发展阶段，需要深化主线、设置伏笔、推动角色成长。"
        elif chapter_number <= total_chapters * 0.75:
            position = "属于高潮铺垫期，需要加速节奏、激化矛盾、汇集线索。"
        elif chapter_number < total_chapters:
            position = "属于高潮阶段，需要最激烈的冲突、关键转折、情感爆发。"
        else:
            position = "属于结局阶段，需要收束所有线索、解决核心矛盾、给出情感满足。"

        # 构建prompt参数
        overview_json_str = book_overview_json if isinstance(book_overview_json, str) else json.dumps(book_overview_json, ensure_ascii=False, indent=2)

        prompt_kwargs = {
            'project_title': project_title, 'genre': genre,
            'book_overview_json': overview_json_str,
            'chapter_number': chapter_number,
            'total_chapters': total_chapters, 'characters_info': chars_text,
            'narrative_perspective': narrative_perspective,
            'my_position': position,
            'act_context': act_context,
            'character_milestones': character_milestones,
            'active_subplots': active_subplots,
            'foreshadow_to_plant': foreshadow_to_plant,
            'foreshadow_to_payoff': foreshadow_to_payoff,
            'pacing_requirement': pacing_requirement,
            'world_summary': world_ctx,
            'prev_chapter_title': prev_title,
            'prev_chapter_tail': prev_tail,
            'degradation_warning': degradation_warning,
        }

        if use_craft:
            if style_profile:
                fmt = self._build_style_prompt_vars(style_profile)
                prompt_kwargs.update(fmt)
                prompt = format_prompt(CHAPTER_OUTLINE_CRAFT_STYLE, **prompt_kwargs)
            else:
                prompt = format_prompt(CHAPTER_OUTLINE_CRAFT, **prompt_kwargs)
        elif style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt_kwargs.update({
                'story_framework': fmt.get('story_framework', ''),
                'satisfaction_pattern': fmt.get('satisfaction_pattern', ''),
                'hook_design': fmt.get('hook_design', ''),
                'transition_style': fmt.get('transition_style', ''),
                'foreshadowing_style': fmt.get('foreshadowing_style', ''),
                'writing_techniques': fmt.get('writing_techniques', ''),
                'pacing': fmt.get('pacing', ''),
                'emotional_beats': fmt.get('emotional_beats', ''),
            })
            prompt = format_prompt(CHAPTER_OUTLINE_DETAIL_STYLE, **prompt_kwargs)
        else:
            prompt = format_prompt(CHAPTER_OUTLINE_DETAIL, **prompt_kwargs)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    def generate_chapter_outline_stream(self, project_title, genre, book_overview_json, chapter_number,
                                         total_chapters, characters_info, narrative_perspective="第三人称",
                                         style_profile=None, world_summary="", prev_chapter_title="",
                                         prev_chapter_tail="", use_craft=False):
        """流式生成单章细纲"""
        import json

        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        overview_available = True
        try:
            overview = json.loads(book_overview_json) if isinstance(book_overview_json, str) else book_overview_json
            if not overview or not isinstance(overview, dict):
                overview = {}
                overview_available = False
        except (json.JSONDecodeError, TypeError):
            overview = {}
            overview_available = False

        degradation_warning = ""
        if not overview_available:
            degradation_warning = "\n⚠️ 注意：全书总纲缺失或格式错误，本章细纲缺少上下文注入。"

        acts = overview.get('acts', [])
        current_act = None
        for act in acts:
            cr = act.get('chapter_range', '')
            parts = cr.split('-')
            if len(parts) == 2:
                try:
                    start, end = int(parts[0]), int(parts[1])
                    if start <= chapter_number <= end:
                        current_act = act
                        break
                except ValueError:
                    pass
        if not current_act and acts:
            idx = min(int(chapter_number / max(total_chapters, 1) * len(acts)), len(acts) - 1)
            current_act = acts[idx]

        act_context = "所属幕：" + (current_act.get('name', '未知') if current_act else '未知')
        if current_act:
            act_context += "\n本幕目标：" + current_act.get('goal', '')
            act_context += "\n本幕情感基调：" + current_act.get('emotional_tone', '')
            if current_act.get('key_turning_point'):
                act_context += "\n本幕关键转折：" + current_act['key_turning_point']

        char_arcs = overview.get('character_arcs', [])
        milestones_here = []
        for arc in char_arcs:
            for ms in arc.get('milestones', []):
                if ms.get('chapter') == chapter_number:
                    milestones_here.append({"name": arc.get('name', ''), "change": ms.get('change', '')})
        character_milestones = "本章无角色转变" if not milestones_here else "\n".join(
            [f"- {m['name']}: {m['change']}" for m in milestones_here]
        )

        subplots = overview.get('subplots', [])
        active_here = [sp for sp in subplots if chapter_number in sp.get('involved_chapters', [])]
        active_subplots = "无活跃支线" if not active_here else "\n".join(
            [f"- {sp['name']}（收束于第{sp.get('resolution_chapter', '?')}章）" for sp in active_here]
        )

        fores = overview.get('foreshadowing', [])
        plant_here = [f for f in fores if f.get('planted_chapter') == chapter_number]
        payoff_here = [f for f in fores if f.get('payoff_chapter') == chapter_number]
        foreshadow_to_plant = "无需埋设伏笔" if not plant_here else "\n".join(
            [f"- {f['hint']}（将于第{f.get('payoff_chapter', '?')}章回收）" for f in plant_here]
        )
        foreshadow_to_payoff = "无需回收伏笔" if not payoff_here else "\n".join(
            [f"- {f['hint']} → 揭示：{f.get('reveal', '')}" for f in payoff_here]
        )

        pacing = overview.get('pacing', [])
        pace_here = None
        for p in pacing:
            pc = p.get('chapters', '')
            parts = pc.split('-')
            if len(parts) == 2:
                try:
                    if int(parts[0]) <= chapter_number <= int(parts[1]):
                        pace_here = p
                        break
                except ValueError:
                    pass
        if not pace_here and pacing:
            pace_here = pacing[min(int(chapter_number / max(total_chapters, 1) * len(pacing)), len(pacing) - 1)]
        pacing_requirement = "节奏：" + (pace_here.get('rhythm', '正常') if pace_here else '正常')
        if pace_here:
            pacing_requirement += "\n爽点类型：" + pace_here.get('satisfaction_type', '无特殊要求')

        world_ctx = world_summary[:300] if world_summary else "（未设定世界观）"
        prev_title = prev_chapter_title or "（无前章）"
        prev_tail = (prev_chapter_tail or "")[:300] if prev_chapter_tail else "（无前章结尾）"

        if total_chapters <= 1:
            position = "这是唯一的一章，需要完整呈现故事。"
        elif chapter_number <= total_chapters * 0.1:
            position = "属于开局阶段，需要建立世界观、引入主角、设置初始矛盾。"
        elif chapter_number <= total_chapters * 0.25:
            position = "属于发展阶段，需要推进剧情、增加冲突复杂度、发展角色关系。"
        elif chapter_number <= total_chapters * 0.5:
            position = "属于中期发展阶段，需要深化主线、设置伏笔、推动角色成长。"
        elif chapter_number <= total_chapters * 0.75:
            position = "属于高潮铺垫期，需要加速节奏、激化矛盾、汇集线索。"
        elif chapter_number < total_chapters:
            position = "属于高潮阶段，需要最激烈的冲突、关键转折、情感爆发。"
        else:
            position = "属于结局阶段，需要收束所有线索、解决核心矛盾、给出情感满足。"

        overview_json_str = book_overview_json if isinstance(book_overview_json, str) else json.dumps(book_overview_json, ensure_ascii=False, indent=2)

        prompt_kwargs = {
            'project_title': project_title, 'genre': genre,
            'book_overview_json': overview_json_str,
            'chapter_number': chapter_number,
            'total_chapters': total_chapters, 'characters_info': chars_text,
            'narrative_perspective': narrative_perspective,
            'my_position': position,
            'act_context': act_context,
            'character_milestones': character_milestones,
            'active_subplots': active_subplots,
            'foreshadow_to_plant': foreshadow_to_plant,
            'foreshadow_to_payoff': foreshadow_to_payoff,
            'pacing_requirement': pacing_requirement,
            'world_summary': world_ctx,
            'prev_chapter_title': prev_title,
            'prev_chapter_tail': prev_tail,
            'degradation_warning': degradation_warning,
        }

        if use_craft:
            if style_profile:
                fmt = self._build_style_prompt_vars(style_profile)
                prompt_kwargs.update(fmt)
                prompt = format_prompt(CHAPTER_OUTLINE_CRAFT_STYLE, **prompt_kwargs)
            else:
                prompt = format_prompt(CHAPTER_OUTLINE_CRAFT, **prompt_kwargs)
        elif style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt_kwargs.update({
                'story_framework': fmt.get('story_framework', ''),
                'satisfaction_pattern': fmt.get('satisfaction_pattern', ''),
                'hook_design': fmt.get('hook_design', ''),
                'transition_style': fmt.get('transition_style', ''),
                'foreshadowing_style': fmt.get('foreshadowing_style', ''),
                'writing_techniques': fmt.get('writing_techniques', ''),
                'pacing': fmt.get('pacing', ''),
                'emotional_beats': fmt.get('emotional_beats', ''),
            })
            prompt = format_prompt(CHAPTER_OUTLINE_DETAIL_STYLE, **prompt_kwargs)
        else:
            prompt = format_prompt(CHAPTER_OUTLINE_DETAIL, **prompt_kwargs)

        logger.info(f"generate_chapter_outline_stream called: chapter={chapter_number}, max_tokens={min(self.max_tokens, 16000)}")
        full_text = ''
        outline_max_tokens = min(self.max_tokens, 16000)
        for chunk in self.client.generate_stream(prompt, temperature=0.7, max_tokens=outline_max_tokens):
            if isinstance(chunk, dict):
                if chunk.get('error'):
                    logger.error(f"chapter-outline AI error: {chunk['error']}")
                    yield {'done': True, 'error': chunk['error']}
                    return
                text = chunk.get('content', '')
            else:
                text = str(chunk)
            if text:
                full_text += text
                yield {'content': text}
        logger.info(f"chapter-outline raw response: {len(full_text)} chars")
        result = parse_json_response(full_text)
        if result is not None:
            logger.info("chapter-outline JSON parsed OK")
            yield {'done': True, 'result': result}
        else:
            logger.error(f"chapter-outline JSON parse failed: {full_text[:500]!r}")
            yield {'done': True, 'error': f'JSON解析失败: {full_text[:200]}'}

    # ========== 大纲生成 ==========

    def generate_outline(self, title, theme, genre, characters_info, chapter_count=3,
                         narrative_perspective="第三人称", style_profile=None, world_summary=""):
        """生成大纲"""
        if isinstance(characters_info, list):
            chars_text = "\n".join([f"- {c.get('name', '未知')}: {c.get('personality', '')}" for c in characters_info[:10]])
        else:
            chars_text = str(characters_info)

        if style_profile:
            fmt = self._build_style_prompt_vars(style_profile)
            prompt = format_prompt(OUTLINE_CREATE_STYLE,
                title=title, theme=theme, genre=genre,
                chapter_count=chapter_count,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_summary or "（未设定世界观）",
                sub_genres=fmt.get('sub_genres', ''),
                core_drive=fmt.get('core_drive', ''),
                story_framework=fmt.get('story_framework', ''),
                main_conflict=fmt.get('main_conflict', ''),
                pacing=fmt.get('pacing', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                hook_design=fmt.get('hook_design', ''),
                transition_style=fmt.get('transition_style', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                overall_summary=fmt.get('overall_summary', ''),
                sub_themes=fmt.get('sub_themes', ''),
            )
        else:
            prompt = format_prompt(
                OUTLINE_CREATE,
                title=title, theme=theme, genre=genre,
                chapter_count=chapter_count,
                narrative_perspective=narrative_perspective,
                characters_info=chars_text,
                world_summary=world_summary or "（未设定世界观）",
            )
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result, None

    # ========== 章节生成 ==========

    def generate_chapter(self, project_title, genre, chapter_number, chapter_title,
                         chapter_outline, continuation_point="", previous_chapter_summary="",
                         chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                         narrative_perspective="第三人称", style_profile=None, technique_focus="",
                         book_overview="", world_summary="", first_chapter_strategy="",
                         prev_chapter_hook=""):
        """生成章节正文"""
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_NEXT_STYLE,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''),
                pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
                book_overview=book_overview or "（未填写全书总纲，按章节大纲自由发挥）"
            )
        else:
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
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                book_overview=book_overview or "（未填写全书总纲，按章节大纲自由呈现）"
            )
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err

    def _format_characters(self, chapter_characters):
        """统一角色数据格式：接受 list 或 str，返回格式化后的字符串"""
        if isinstance(chapter_characters, list) and chapter_characters:
            return "\n".join([
                f"- {c.get('name', '未知')}: {c.get('role_type', c.get('role', '角色'))} - "
                f"{c.get('personality', '')} | 背景: {c.get('background', '')[:80]} | "
                f"外貌: {c.get('appearance', '')[:60]}"
                for c in chapter_characters[:10]
            ])
        return str(chapter_characters) if chapter_characters else "（见大纲）"

    def generate_chapter_stream(self, project_title, genre, chapter_number, chapter_title,
                                chapter_outline, continuation_point="", previous_chapter_summary="",
                                chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                                narrative_perspective="第三人称", style_profile=None, technique_focus="",
                                book_overview="", progress_content="", segment_chars=0,
                                world_summary="", first_chapter_strategy="",
                                prev_chapter_hook=""):
        """流式生成章节正文（生成器）- 超时600s
        progress_content: 已生成的内容（续写模式）
        segment_chars: 本段目标字数（续写模式使用，不传则按 target_word_count 生成）
        """
        # 续写模式
        if progress_content and progress_content.strip():
            actual_target = segment_chars if segment_chars > 0 else 800
            # 截断已有内容以适配上下文窗口（假设 prompt 占 ~2000 token，每中文字符 ~1.5 token）
            ctx_limit = getattr(self.client, 'max_tokens', 4000)
            max_progress_chars = min(len(progress_content), int(ctx_limit * 1.2))
            trimmed_progress = progress_content[-max_progress_chars:] if len(progress_content) > max_progress_chars else progress_content
            style_section = ''
            if style_profile:
                style_fmt = self._build_style_prompt_vars(style_profile)
                style_section = format_prompt(CHAPTER_CONTINUATION_STYLE,
                    tone=style_fmt.get('tone', ''),
                    pacing=style_fmt.get('pacing', ''),
                    sentence_structure=style_fmt.get('sentence_structure', ''),
                    dialogue_style=style_fmt.get('dialogue_style', ''),
                    description_style=style_fmt.get('description_style', ''),
                    emotional_intensity=style_fmt.get('emotional_intensity', ''),
                    writing_techniques=style_fmt.get('writing_techniques', ''),
                    foreshadowing_style=style_fmt.get('foreshadowing_style', ''),
                    overall_summary=style_fmt.get('overall_summary', ''),
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                )
            prompt = format_prompt(
                CHAPTER_CONTINUATION,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                progress_content=trimmed_progress,
                chapter_outline=chapter_outline or "（见总纲）",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                target_word_count=target_word_count,
                progress_chars=str(len(progress_content)),
                segment_chars=str(actual_target),
                style_section=style_section,
            )
            for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
                if isinstance(chunk, dict) and chunk.get('error'):
                    yield {'done': True, 'error': chunk['error']}
                    return
                yield chunk
            return

        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        chars_text = self._format_characters(chapter_characters)
        world_text = world_summary if world_summary else "（未设定世界观）"
        first_chapter_note = ""
        if first_chapter_strategy == "first_chapter":
            first_chapter_note = "\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。"

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_NEXT_STYLE,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(
                CHAPTER_GENERATION_NEXT,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def polish_chapter_stream(self, project_title, genre, chapter_number, chapter_title,
                               chapter_outline, original_content, polish_focus="整体优化",
                               style_profile=None):
        """流式润色章节正文"""
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
        prompt = format_prompt(
            CHAPTER_POLISH,
            project_title=project_title,
            genre=genre,
            chapter_number=chapter_number,
            chapter_title=chapter_title or ('第' + str(chapter_number) + '章'),
            chapter_outline=chapter_outline or "（见大纲）",
            original_content=original_content,
            polish_focus=polish_focus,
            tone=fmt.get('tone', ''),
            pacing=fmt.get('pacing', ''),
            sentence_structure=fmt.get('sentence_structure', ''),
            description_style=fmt.get('description_style', ''),
        )
        for chunk in self.client.generate_stream(prompt, temperature=0.6, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def generate_characters_batch(self, world_data, theme, genre, count=6, requirements="", style_profile=None, description=""):
        if count <= 10:
            result, err = self.generate_characters(world_data, theme, genre, count, requirements, style_profile)
            if err:
                return None, err
            return result, None

        batch_size = 5
        all_characters = []
        batches = []
        for i in range(0, count, batch_size):
            batches.append(min(batch_size, count - i))

        for idx, bs in enumerate(batches):
            result, err = self.generate_characters(world_data, theme, genre, bs, requirements, style_profile)
            if err:
                return None, f"第{idx+1}批角色生成失败: {err}"
            if result and isinstance(result, list):
                all_characters.extend(result)
            elif result and isinstance(result, dict) and 'characters' in result:
                all_characters.extend(result['characters'])

        return all_characters, None

    # ========== 网文创作技法（Craft）==========

    def quality_score(self, content, title="", genre=""):
        """质量评分"""
        prompt = format_prompt(QUALITY_SCORE, content=content[:6000], title=title or "未命名", genre=genre or "未知")
        result, err = self._generate_json(prompt)
        return result, err

    def generate_chapter_craft(self, project_title, genre, chapter_number, chapter_title,
                               chapter_outline, continuation_point="", previous_chapter_summary="",
                               chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                               narrative_perspective="第三人称", style_profile=None, technique_focus="",
                               book_overview="", world_summary="", first_chapter_strategy="",
                               prev_chapter_hook=""):
        """生成章节正文（融入网文技法，可选风格仿写）"""
        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT_STYLE,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''),
                pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(
                CHAPTER_GENERATION_CRAFT,
                project_title=project_title,
                genre=genre,
                chapter_number=chapter_number,
                chapter_title=chapter_title,
                target_word_count=target_word_count,
                narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=self._format_characters(chapter_characters),
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_summary if world_summary else "（未设定世界观）",
                first_chapter_note="\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。" if first_chapter_strategy == "first_chapter" else "",
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        text, err = self.client.generate(prompt, temperature=0.8, max_tokens=8000)
        return text, err

    def generate_chapter_craft_stream(self, project_title, genre, chapter_number, chapter_title,
                                      chapter_outline, continuation_point="", previous_chapter_summary="",
                                      chapter_characters="", foreshadow_reminders="", target_word_count=3000,
                                      narrative_perspective="第三人称", style_profile=None, technique_focus="",
                                      book_overview="", progress_content="", segment_chars=0,
                                      world_summary="", first_chapter_strategy="",
                                      prev_chapter_hook=""):
        """流式生成章节正文（融入网文技法，可选风格仿写）"""
        # 续写模式
        if progress_content and progress_content.strip():
            actual_target = segment_chars if segment_chars > 0 else 800
            ctx_limit = getattr(self.client, 'max_tokens', 4000)
            max_progress_chars = min(len(progress_content), int(ctx_limit * 1.2))
            trimmed_progress = progress_content[-max_progress_chars:] if len(progress_content) > max_progress_chars else progress_content
            fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
            if style_profile:
                prompt = format_prompt(
                    CHAPTER_CONTINUATION_CRAFT_STYLE,
                    project_title=project_title, genre=genre,
                    chapter_number=chapter_number, chapter_title=chapter_title,
                    progress_content=trimmed_progress,
                    chapter_outline=chapter_outline or "（见总纲）",
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                    target_word_count=target_word_count,
                    progress_chars=str(len(progress_content)),
                    segment_chars=str(actual_target),
                    tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                    sentence_structure=fmt.get('sentence_structure', ''),
                    dialogue_style=fmt.get('dialogue_style', ''),
                    description_style=fmt.get('description_style', ''),
                    emotional_intensity=fmt.get('emotional_intensity', ''),
                    writing_techniques=fmt.get('writing_techniques', ''),
                    foreshadowing_style=fmt.get('foreshadowing_style', ''),
                    overall_summary=fmt.get('overall_summary', ''),
                )
            else:
                prompt = format_prompt(
                    CHAPTER_CONTINUATION_CRAFT,
                    project_title=project_title, genre=genre,
                    chapter_number=chapter_number, chapter_title=chapter_title,
                    progress_content=trimmed_progress,
                    chapter_outline=chapter_outline or "（见总纲）",
                    prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                    target_word_count=target_word_count,
                    progress_chars=str(len(progress_content)),
                    segment_chars=str(actual_target),
                )
            for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
                if isinstance(chunk, dict) and chunk.get('error'):
                    yield {'done': True, 'error': chunk['error']}
                    return
                yield chunk
            return

        fmt = self._build_style_prompt_vars(style_profile) if style_profile else {}
        chars_text = self._format_characters(chapter_characters)
        world_text = world_summary if world_summary else "（未设定世界观）"
        first_chapter_note = ""
        if first_chapter_strategy == "first_chapter":
            first_chapter_note = "\n本章是全书开篇：需要建立世界观基调、引入主角、抛出核心悬念，开篇3句必须有钩子。"

        if style_profile:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT_STYLE,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
                tone=fmt.get('tone', ''), pacing=fmt.get('pacing', ''),
                sentence_structure=fmt.get('sentence_structure', ''),
                dialogue_style=fmt.get('dialogue_style', ''),
                description_style=fmt.get('description_style', ''),
                emotional_intensity=fmt.get('emotional_intensity', ''),
                writing_techniques=fmt.get('writing_techniques', ''),
                hook_design=fmt.get('hook_design', ''),
                satisfaction_pattern=fmt.get('satisfaction_pattern', ''),
                satisfaction_type=fmt.get('satisfaction_type', ''),
                transition_style=fmt.get('transition_style', ''),
                emotional_beats=fmt.get('emotional_beats', ''),
                foreshadowing_style=fmt.get('foreshadowing_style', ''),
                overall_summary=fmt.get('overall_summary', ''),
                technique_focus=technique_focus or "根据大纲自然呈现",
            )
        else:
            prompt = format_prompt(CHAPTER_GENERATION_CRAFT,
                project_title=project_title, genre=genre,
                chapter_number=chapter_number, chapter_title=chapter_title,
                target_word_count=target_word_count, narrative_perspective=narrative_perspective,
                chapter_outline=chapter_outline,
                continuation_point=continuation_point or "（第一章，故事开始）",
                previous_chapter_summary=previous_chapter_summary or "（第一章，无前文）",
                chapter_characters=chars_text,
                foreshadow_reminders=foreshadow_reminders or "暂无",
                world_summary=world_text,
                first_chapter_note=first_chapter_note,
                prev_chapter_hook=prev_chapter_hook or "（第一章，无上一章钩子）",
            )
        for chunk in self.client.generate_stream(prompt, temperature=0.8, max_tokens=self.client.max_tokens):
            if isinstance(chunk, dict) and chunk.get('error'):
                yield {'done': True, 'error': chunk['error']}
                return
            yield chunk

    def generate_titles_craft(self, user_input=""):
        """生成书名建议（网文风）"""
        prompt = format_prompt(INSPIRATION_TITLE_CRAFT, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_descriptions_craft(self, title, user_input=""):
        """生成简介选项（网文风）"""
        prompt = format_prompt(INSPIRATION_DESCRIPTION_CRAFT, title=title, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

