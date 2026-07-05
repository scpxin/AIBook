"""V2 设计层服务 — 实现 M1-M5 五个设计模块

M1: idea        — 灵感生成/评分/升级/风险分析
M2: project     — 项目定位/平台兼容性/衍生字段
M3: world       — 世界观(本源/规则/结构/文明/历史)
M4: characters  — 角色系统(主角/配角/反派/关系)
M5: story       — 故事体系(总纲/卷纲/一致性)
"""
import sys
import os
import json
import logging
from typing import Optional, Dict, Any, List

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from novel_creator import database_v2
from app.services.novel_generator import get_generator, parse_style_profile

logger = logging.getLogger('novel_creator.design')


# ========== M1: 灵感服务 ==========

class IdeaService:
    """灵感生成服务 — 发散、评分、升级、风险分析"""

    @staticmethod
    def generate(project_id: str, user_input: str, genre_hint: str = "",
                 style_profile: dict = None, count: int = 5) -> tuple:
        """发散生成N个创意"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)

        ideas = []
        for i in range(count):
            prompt = f"""{style_str}
基于以下用户输入,发散生成一个新颖的小说创意。

用户输入: {user_input}
题材偏好: {"无特殊偏好" if not genre_hint else genre_hint}

要求:
1. 创意必须原创,不能是常见套路
2. 包含独特的世界观或设定亮点
3. 考虑网络小说的商业潜力
4. 每次生成不同的创意方向

返回JSON格式:
{{"concept": "核心概念(一句话)",
  "hook": "钩子(吸引读者的点)",
  "premise": "前提设定(200字内)",
  "genre": "所属题材",
  "differentiator": "差异化亮点",
  "reference_works": ["参考作品1", "参考作品2"]}}"""

            result, err = gen._generate_json(prompt)
            if err:
                logger.error(f"创意生成失败 #{i+1}: {err}")
                continue
            result['_index'] = i + 1
            ideas.append(result)

        if not ideas:
            return None, "所有创意生成失败"

        # 保存到数据库
        database_v2.save_idea(project_id, {
            'user_input': user_input,
            'genre_hint': genre_hint,
            'selected_concept': ideas[0].get('concept', ''),
            'total_score': 0,
            'status': 'draft',
            '_raw_ideas': ideas,
        })

        return {"ideas": ideas, "project_id": project_id}, None

    @staticmethod
    def score(project_id: str, ideas: list) -> tuple:
        """创意评分 — 创新性/商业性/可持续性/差异化/难度"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""作为网文小说专家,对以下创意进行多维度评分。

待评分创意:
{json.dumps(ideas[:5], ensure_ascii=False, indent=2)}

评分维度(每项1-10分):
1. innovation — 创新性(设定的新颖程度)
2. commercial — 商业性(读者付费意愿)
3. sustainability — 可持续性(能写多长不崩)
4. differentiation — 差异化(与现有作品的区分度)
5. difficulty — 写作难度(1=极易,10=极难)
6. total_score — 加权总分(自动计算)

返回JSON格式:
[{{"index": 1, "innovation": 8, "commercial": 7, "sustainability": 9,
   "differentiation": 6, "difficulty": 5, "total_score": 7.0,
   "rationale": "评分理由(50字内)"}}]"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 更新数据库中的评分
        for item in result:
            item['index'] = item.get('index', 0)

        return {"scored_ideas": result}, None

    @staticmethod
    def upgrade(project_id: str, top_ideas: list) -> tuple:
        """TOP3创意升级 — 增加矛盾/设计限制"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""作为网文专家,对以下TOP3创意进行升级强化。

待升级创意:
{json.dumps(top_ideas, ensure_ascii=False, indent=2)}

升级要求:
1. 为核心概念增加内在矛盾(张力来源)
2. 设计瓶颈/限制体系(不能为所欲为)
3. 预埋主线伏笔方向
4. 强化升级/成长体系

返回JSON格式:
[{{"index": 1, "original_concept": "...",
   "upgraded_concept": "升级后的概念",
   "core_conflict": "核心矛盾(100字)",
   "limitations": ["限制1", "限制2"],
   "foreshadow_hints": ["伏笔方向1"],
   "growth_system": "成长体系简述"}}]"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        return {"upgraded": result}, None

    @staticmethod
    def analyze_risks(project_id: str, concept: str, **kwargs) -> tuple:
        """风险分析 — 内容管控/政策/逻辑漏洞"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""作为网文编辑和风控专家,分析以下小说创意的风险。

核心概念: {concept}
详细信息: {json.dumps(kwargs, ensure_ascii=False)}

分析维度:
1. content_risk — 内容风险(暴力/色情/政治等)
2. policy_risk — 政策合规风险
3. logic_gaps — 逻辑漏洞
4. market_risk — 市场风险(读者不买账)
5. writing_risk — 写作风险(设定太复杂写不长)

每个维度: level(高/中/低) + description(具体说明) + suggestion(规避建议)

返回JSON格式:
{{"overall_risk": "中",
  "risks": [
    {{"dimension": "content_risk", "level": "低", "description": "...", "suggestion": "..."}}
  ],
  "fatal_issues": ["致命问题(如有)"],
  "summary": "风险总评(100字)"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        return result, None


# ========== M2: 项目定位服务 ==========

class ProjectService:
    """项目定位服务 — 12维度策划 + 平台兼容性"""

    PLATFORM_PRESETS = {
        "tomato": {"name": "番茄小说", "style": "快节奏/强情绪/短句式", "update": "日更4000+"},
        "qidian": {"name": "起点中文网", "style": "升级流/爽文/世界观宏大", "update": "日更6000+"},
        "fanqie": {"name": "番茄免费小说", "style": "都市/赘婿/神医/萌宝", "update": "日更4000+"},
    }

    @staticmethod
    def analyze(project_id: str, idea: str, platform: str = "tomato",
                style_profile: dict = None) -> tuple:
        """12维度项目策划"""
        gen = _get_default_generator()
        if gen is None:
            return None, "AI生成器未配置"

        preset = ProjectService.PLATFORM_PRESETS.get(platform, {})
        style_str = _build_style_str(style_profile)

        prompt = f"""{style_str}
作为网文策划专家,对以下小说创意进行全面项目策划。

核心创意: {idea}
目标平台: {preset.get('name', platform)}
平台风格要求: {preset.get('style', '通用')}

12维度策划维度:
1. target_audience — 目标读者画像(readers+age+preference)
2. core_hook — 核心卖点(一句话)
3. novelty_angle — 新颖角度
4. emotional_resonance — 情感共鸣点
5. update_strategy — 更新策略(节奏/爆点分布)
6. title_direction — 书名方向(3个候选)
7. cover_concept — 封面概念
8. opener_strategy — 开篇策略(黄金3章)
9. main_conflict — 主线矛盾
10. subplot_count — 支线数量建议
11. climax_pattern — 高潮模式
12. ending_direction — 结局方向

返回JSON: 每个维度的title+content(200字内)+priority(高/中/低)"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存项目定位
        database_v2.save_project_detail(project_id, {
            'project_overview': idea[:500],
            'platform_choice': platform,
            'novel_position': result if isinstance(result, dict) else {"raw": result},
        })

        return result, None

    @staticmethod
    def check_compatibility(project_id: str, idea: str, platform: str) -> tuple:
        """平台×灵感兼容性检查"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""评估小说创意与平台的兼容性。

创意: {idea}
平台: {platform}
平台特点: {json.dumps(ProjectService.PLATFORM_PRESETS.get(platform, {}), ensure_ascii=False)}

返回JSON:
{{"score": 85, "fit": "高",
  "pros": ["优势1"], "cons": ["劣势1"],
  "adjustment": "调整建议(200字)"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def derive_fields(project_id: str, project_data: dict) -> tuple:
        """衍生字段计算(基于项目定位自动计算其他字段)"""
        import re

        title = project_data.get('title', '')
        overview = project_data.get('project_overview', '')

        derived = {
            'estimated_chapters': _estimate_chapters(overview),
            'estimated_words': _estimate_words(overview),
            'title_keywords': _extract_keywords(title),
            'content_tags': _generate_tags(overview),
            'series_potential': _assess_series_potential(overview),
        }
        return derived, None


def _estimate_chapters(overview: str) -> int:
    """估算章节数"""
    if '百万' in overview or '长篇' in overview:
        return 500
    elif '中篇' in overview:
        return 200
    return 300


def _estimate_words(overview: str) -> int:
    """估算总字数(万)"""
    if '百万' in overview:
        return 200
    elif '千万' in overview:
        return 500
    return 100


def _extract_keywords(text: str) -> list:
    """提取关键词"""
    return list(set([w for w in text.split() if len(w) >= 2]))[:10]


def _generate_tags(overview: str) -> list:
    """生成内容标签"""
    tags = []
    tag_keywords = {
        '升级': '升级流', '系统': '系统流', '无敌': '无敌流',
        '重生': '重生', '穿越': '穿越', '修仙': '仙侠',
        '都市': '都市', '赘婿': '赘婿', '战神': '战神',
    }
    for kw, tag in tag_keywords.items():
        if kw in overview:
            tags.append(tag)
    return tags[:5]


def _assess_series_potential(overview: str) -> str:
    """评估系列作品潜力"""
    if any(w in overview for w in ['系列', '多部', '宇宙', '世界观']):
        return '高'
    return '中'


# ========== M3: 世界观服务 ==========

class WorldService:
    """世界观构建服务 — 本源/规则/结构/文明/历史"""

    @staticmethod
    def design_origin(project_id: str, idea: str, genre: str = "",
                      style_profile: dict = None) -> tuple:
        """世界本源设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【世界本源】(the Origin)。

核心创意: {idea}
题材: {genre}

设计内容:
1. cosmology — 宇宙起源(世界如何诞生,300字)
2. fundamental_forces — 基础力量/本源能量(3-5种)
3. creation_myth — 创世神话/传说(200字)
4. world_views — 世界观核心理念(如"弱肉强食"、"道法自然")
5. chaos_order — 混沌与秩序的平衡(100字)

返回JSON: 上述5个字段"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_rules(project_id: str, origin: dict, power_system: dict = None) -> tuple:
        """世界规则设计 — 每条规则6要素"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【运行规则】(World Rules)。

世界本源: {json.dumps(origin, ensure_ascii=False, indent=2)}

设计5-8条核心规则,每条规则包含6要素:
- name: 规则名称
- description: 规则描述(100字)
- scope: 作用范围
- cost: 违反代价
- exception: 例外情况
- evidence: 在故事中的体现

返回JSON: {{"rules": [{{"name": "...", "description": "...", "scope": "...", "cost": "...", "exception": "...", "evidence": "..."}}], "meta_rule": "元规则(统摄所有规则的最高原则)"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_structure(project_id: str, origin: dict) -> tuple:
        """世界结构设计 — 层级+地点"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【空间结构】(World Structure)。

世界本源: {origin.get('cosmology', '')[:300]}

设计内容:
1. dimensions — 世界层级(如凡间/仙界/神界,3-5层)
2. realms — 主要界域(每个界域:name+description+characteristics+connections)
3. landmark_locations — 标志性地点(5-10个,每个:name+type+significance+geography)
4. spatial_rules — 空间规则(跨界条件/传送/传送阵)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_civilization(project_id: str, structure: dict) -> tuple:
        """文明体系设计 — 8维度"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【文明体系】(Civilization)。

世界结构概要: {json.dumps(structure, ensure_ascii=False)[:1000]}

8维度设计:
1. political_system — 政治结构
2. economic_system — 经济体系
3. technological_level — 技术水平
4. cultural_identity — 文化标识
5. religious_beliefs — 宗教信仰
6. social_hierarchy — 社会阶层
7. warfare_system — 战争体系
8. daily_life — 日常生活

每个维度: name + description(150字) + key_features(3-5个)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_history(project_id: str, structure: dict, civilization: dict) -> tuple:
        """历史时间线设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【历史时间线】(World History)。

设计内容:
1. timeline_events — 关键历史事件(8-12个,每个:era+year_range+event+impact+aftermath)
2. ancient_mysteries — 上古谜团(3-5个,推动主线用)
3. prophecy_system — 预言体系(2-3条核心预言)
4. decline_cycles — 兴盛衰落循环规律

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def check_consistency(project_id: str, world_data: dict) -> tuple:
        """世界一致性检查"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""检查以下世界观的一致性。

世界观数据: {json.dumps(world_data, ensure_ascii=False, indent=2)[:5000]}

检查维度:
1. internal_logic — 内部逻辑(规则是否自洽)
2. causal_consistency — 因果一致性(历史→现在是否符合因果)
3. spatial_consistency — 空间一致性(地理/界域是否矛盾)
4. temporal_consistency — 时间一致性(时间线是否有漏洞)

返回JSON:
{{"passed": true/false,
  "score": 85,
  "issues": [{{"type": "logic", "severity": "high/med/low", "description": "...", "fix": "修复建议"}}],
  "summary": "一致性总结"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def save_world(project_id: str, world_data: dict) -> tuple:
        """保存完整世界观"""
        try:
            database_v2.save_world(project_id, {
                'origin': world_data.get('origin', world_data.get('cosmology', {})),
                'rules': world_data.get('rules', []),
                'structure': world_data.get('structure', {}),
                'civilization': world_data.get('civilization', {}),
                'history': world_data.get('history', {}),
                'doc_path': world_data.get('doc_path', ''),
            })
            return {"saved": True, "project_id": project_id}, None
        except Exception as e:
            return None, str(e)


# ========== M4: 角色系统服务 ==========

class CharacterService:
    """角色系统服务 — 主角/配角/反派/关系"""

    @staticmethod
    def generate_protagonist(project_id: str, world_rules: dict,
                             story_concept: str = "", style_profile: dict = None) -> tuple:
        """主角九维档案生成"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【主角】档案(九维体系)。

故事概念: {story_concept}
世界规则约束: {json.dumps(world_rules, ensure_ascii=False)[:1000]}

九维档案:
1. basic_info — 基本信息(name+age+gender+nationality+appearance+birth)
2. personality — 性格(traits[5个]+mbti+strengths+flaws+contradictions)
3. backstory — 背景(origin+childhood_trauma+turning_point+secret)
4. motivation — 动机(outer_goal+inner_need+literal_wish+true_desire)
5. abilities — 能力(initial_power+signature_skill+growth_route+limits+awakening)
6. relationships — 关系(mentor+rival+ally+enemy+love_interest)
7. character_arc — 成长弧线(zero_state+awakening+setback+breakthrough+final_state)
8. voice — 语言特征(speech_patterns+inner_monologue+tells+catchphrases)
9. symbols — 象征符号(item+animal+color+theme_motif)

返回JSON格式: 上述9个维度"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存角色
        if isinstance(result, dict):
            char_id = f"char-protagonist-{project_id[:8]}"
            database_v2.save_character(project_id, char_id, {
                'name': result.get('basic_info', {}).get('name', '未知'),
                'role_type': 'protagonist',
                **result,
            })

        return result, None

    @staticmethod
    def generate_supporting(project_id: str, protagonist: dict, count: int = 5) -> tuple:
        """配角设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""基于以下主角,设计{count}个配角。

主角: {json.dumps(protagonist.get('basic_info', {}), ensure_ascii=False)}

配角类型分布: 1个导师 + 1个挚友 + 1个对手 + 2个功能角色

每个配角包含:
- name + role_type + description(200字)
- relationship_to_protagonist(与主角的关系,100字)
- function(剧情功能:如经验包/对比剂/推动者)
- character_arc(角色成长,100字)
- fate_hint(命运暗示)

返回JSON: {{"characters": [...]}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存配角
        if isinstance(result, dict):
            for i, char in enumerate(result.get('characters', [])):
                char_id = f"char-supporting-{i+1}-{project_id[:8]}"
                database_v2.save_character(project_id, char_id, {
                    'name': char.get('name', f'配角{i+1}'),
                    'role_type': 'supporting',
                    **char,
                })

        return result, None

    @staticmethod
    def generate_antagonists(project_id: str, protagonist: dict, world: dict) -> tuple:
        """反派体系设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计反派体系(金字塔结构)。

主角: {protagonist.get('basic_info', {}).get('name', '主角')}
世界观: {json.dumps(world, ensure_ascii=False)[:500]}

反派层级:
1. shadow_boss — 影子BOSS(隐藏最深的大敌)
2. arch_enemy — 宿敌(贯穿全书的核心对手)
3. lieutenants — 干部(3-5个直属部下,各有独立动机)
4. minions — 杂兵体系(组织+等级)

每个反派: name+title+motivation+power+weakness+fate+symbol

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def generate_relations(project_id: str, characters: list) -> tuple:
        """关系网络生成"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        char_summary = [{"name": c.get('name', ''), "role": c.get('role_type', ''),
                        "id": c.get('char_id', '')} for c in characters[:10]]

        prompt = f"""为以下角色构建关系网络。

角色: {json.dumps(char_summary, ensure_ascii=False)}

设计内容:
1. edges — 关系边(source+target+type+intensity+description+dynamic)
   type: ally/rival/lover/family/mentor/enemy/neutral/mastermind
2. factions — 阵营归属(group_name+members+goal+internal_dynamic)
3. love_polygon — 感情线(love_triangles+unrequited+hints)
4. hidden_connections — 隐藏关联(秘密/未知的血缘/前世)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存关系图
        if isinstance(result, dict):
            database_v2.save_relation_map(project_id, result)

        return result, None

    @staticmethod
    def check_consistency(project_id: str, characters: list) -> tuple:
        """角色一致性检查"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""检查角色体系的一致性。

角色: {json.dumps([{k: v for k, v in c.items() if k != '_raw_data'} for c in characters[:8]], ensure_ascii=False, indent=2)[:4000]}

检查维度:
1. motivation_clarity — 动机明确性(每个角色的目标是否清晰)
2. power_balance — 战力平衡(无明显碾压/越级击杀不合理)
3. relation_completeness — 关系完整性(角色之间是否都有联系)
4. arc_independence — 成长独立性(角色的成长弧线是否独立且合理)

返回JSON:
{{"passed": true, "score": 85,
  "issues": [{{"char": "角色名", "type": "motivation", "description": "..."}}],
  "summary": "一致性总结"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None


# ========== M5: 故事体系服务 ==========

class StoryService:
    """故事体系服务 — 总纲/卷纲/一致性"""

    @staticmethod
    def generate_master(project_id: str, protagonist: dict, world: dict,
                        characters: list, style_profile: dict = None) -> tuple:
        """总纲设计 — 冲突/主题/事件集"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【总纲】(Master Story)。

主角: {protagonist.get('basic_info', {}).get('name', '主角')}
主角成长路线: {json.dumps(protagonist.get('character_arc', {}), ensure_ascii=False)[:500]}
世界观要点: {json.dumps(world, ensure_ascii=False)[:1000]}

总纲要素:
1. theme — 主题(核心思想+表现层次)
2. conflict_hierarchy — 冲突层级(main_conflict+secondary_conflicts[3-5个]+internal_conflicts[2-3个])
3. event_chain — 核心事件链(10-15个关键事件,每个:event+trigger+consequence+chapter_hint)
4. emotional_arc — 情感弧线(低谷→高峰的循环,标注关键转折点)
5. narrative_promise — 叙事承诺(对读者的承诺+兑现方式)
6. stakes — 筹码体系(主角逐步失去/获得的重要事物)
7. climax_setup — 高潮预埋(全书最大高潮的伏笔)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存故事体系
        if isinstance(result, dict):
            database_v2.save_story(project_id, {
                'summary': result.get('theme', ''),
                'conflict_layers': result.get('conflict_hierarchy', {}),
                'theme': result.get('theme', ''),
                'volumes_detail': {},
                'total_plot_events': len(result.get('event_chain', [])),
                **result,
            })

        return result, None

    @staticmethod
    def generate_volumes(project_id: str, master_story: dict,
                         volume_count: int = 5) -> tuple:
        """每卷卷纲生成"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""基于总纲,生成每卷的卷纲。

总纲概要: {json.dumps(master_story, ensure_ascii=False)[:3000]}
卷数: {volume_count}

每卷包含:
- volume_no: 卷号
- title: 卷名
- theme: 卷主题
- wordcount_target: 目标字数
- main_events: 本卷核心事件(3-5个,每个:event_name+significance)
- character_focus: 重点刻画的角色
- cliffhanger: 卷末悬念
- arc_contribution: 对主线的推进作用

返回JSON: {{"volumes": [...]}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存卷纲
        if isinstance(result, dict):
            for vol in result.get('volumes', []):
                vol_no = vol.get('volume_no', 1)
                database_v2.save_volume(project_id, vol_no, {
                    'name': vol.get('title', f'第{vol_no}卷'),
                    'summary': vol.get('theme', ''),
                    'target_words': vol.get('wordcount_target', 250000),
                    **vol,
                })

        return result, None

    @staticmethod
    def check_consistency(project_id: str, story_data: dict,
                          characters: list) -> tuple:
        """故事一致性检查"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""检查故事体系的一致性。

故事: {json.dumps(story_data, ensure_ascii=False, indent=2)[:4000]}

检查维度:
1. plot_holes — 情节漏洞
2. character_arc_alignment — 角色成长与剧情对齐
3. theme_consistency — 主题一致性(各卷是否偏离主题)
4. climax_buildup — 高潮铺垫是否充分

返回JSON:
{{"passed": true, "score": 85,
  "issues": [{{"type": "plot", "severity": "med", "description": "...", "fix": "建议"}}],
  "summary": "一致性总结"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None


# ========== 工具函数 ==========

def _get_default_generator():
    """获取默认生成器(使用环境变量中的配置)"""
    endpoint = os.environ.get('AI_ENDPOINT', '')
    api_key = os.environ.get('AI_API_KEY', '')
    model = os.environ.get('AI_MODEL', 'gpt-4o-mini')

    if not endpoint or not api_key:
        logger.warning("AI endpoint/api_key未配置,使用mock模式")
        return None

    return get_generator(endpoint, api_key, model)


def _build_style_str(style_profile: dict = None) -> str:
    """构建风格提示词片段"""
    if not style_profile:
        return ""
    parts = []
    for key in ['narrative_perspective', 'tone', 'pacing', 'emotional_intensity']:
        val = style_profile.get(key)
        if val:
            parts.append(f"- {key}: {val}")
    if not parts:
        return ""
    return "=== 参考风格 ===\n" + "\n".join(parts) + "\n\n"
