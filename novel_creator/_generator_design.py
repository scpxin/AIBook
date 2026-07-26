import json

from .craft_prompts import INSPIRATION_DESCRIPTION_CRAFT, INSPIRATION_TITLE_CRAFT
from .prompts import (
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
    WORLD_BUILDING,
    WORLD_BUILDING_STYLE,
    format_prompt,
)


class _DesignMixin:

    def generate_titles(self, user_input="", style_profile=None):
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

    def generate_titles_craft(self, user_input=""):
        prompt = format_prompt(INSPIRATION_TITLE_CRAFT, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def generate_descriptions_craft(self, title, user_input=""):
        prompt = format_prompt(INSPIRATION_DESCRIPTION_CRAFT, title=title, user_input=user_input)
        result, err = self._generate_json(prompt)
        if err:
            return None, err
        return result[:10] if isinstance(result, list) else result, None

    def summarize_inspiration(self, title, description, theme, genre):
        return {
            "title": title or "",
            "description": (description or "")[:200],
            "theme": theme or "",
            "genre": genre or "",
            "core_premise": (description or "")[:100]
        }

    # ── World ──

    def generate_world_building(self, title, theme, genre, description, style_profile=None):
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

    def summarize_world(self, world_data, theme, genre):
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

        return {
            "key_locations": self._extract_items(world_text, ["地点", "世界", "区域", "城市", "大陆"])[:5],
            "power_system": self._extract_first_match(world_text, ["修炼体系", "实力等级", "斗气", "魔法", "系统", "境界"]),
            "key_rules": self._extract_items(world_text, ["规则", "法则", "约束", "限制"])[:3],
            "factions": self._extract_items(world_text, ["势力", "宗门", "家族", "组织", "帝国", "国家"])[:5],
            "unique_elements": self._extract_items(world_text, ["特殊", "独特", "异", "神", "灵", "秘"])[:3],
            "summary_text": world_text[:500]
        }

    # ── Character generation ──

    def generate_characters(self, world_data, theme, genre, count=6, requirements="", style_profile=None, description=""):
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

    def summarize_characters(self, characters_info):
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
        names = self._extract_items(text, ["主角", "男主", "女主", "反派", "配角"])
        return {
            "protagonist": {"name": names[0] if names else "", "role": "主角", "personality": "", "goal": "", "special": ""},
            "main_chars": [{"name": n, "role": "", "personality": "", "goal": "", "special": ""} for n in names[1:5]],
            "antagonist": {"name": names[-1] if len(names) > 1 else "", "role": "", "personality": "", "goal": "", "special": ""},
            "char_count": len(names),
            "char_names": names[:8]
        }
