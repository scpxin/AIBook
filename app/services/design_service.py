"""V2 设计层服务 — 实现 M1-M5 五个设计模块

M1: idea        — 灵感生成/评分/升级/风险分析
M2: project     — 项目定位/平台兼容性/衍生字段
M3: world       — 世界观(本源/规则/结构/文明/历史)
M4: characters  — 角色系统(主角/配角/反派/关系)
M5: story       — 故事体系(总纲/卷纲/一致性)
"""
import json
import logging
import os
import sys

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from app.services.service_utils import build_style_str, get_default_generator
from novel_creator import database_v2

logger = logging.getLogger('novel_creator.design')


# ========== M1: 灵感服务 ==========

class IdeaService:
    """灵感生成服务 — 发散、评分、升级、风险分析"""

    @staticmethod
    def generate(project_id: str, user_input: str, genre_hint: str = "",
                 style_profile: dict = None, count: int = 5) -> tuple:
        """发散生成N个创意（单次批量生成）"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)

        prompt = f"""{style_str}
基于以下用户输入，发散生成 {count} 个不同的小说创意方向。

用户输入: {user_input}
题材偏好: {"无特殊偏好" if not genre_hint else genre_hint}

要求:
1. 每个创意必须原创，不能是常见套路
2. 包含独特的世界观或设定亮点
3. 考虑网络小说的商业潜力
4. 每个创意方向必须完全不同（题材/风格/核心卖点各异）

返回JSON数组格式:
[{{"concept": "核心概念(一句话)",
  "hook": "钩子(吸引读者的点)",
  "premise": "前提设定(200字内)",
  "genre": "所属题材",
  "differentiator": "差异化亮点",
  "reference_works": ["参考作品1", "参考作品2"]}}]

直接返回JSON数组，不要markdown代码块，不要额外说明。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="idea")
        if err:
            logger.error(f"创意批量生成失败: {err}")
            return None, f"创意生成失败: {err}"

        # Handle both array and single object responses
        if result is None:
            return None, "创意生成失败：AI返回空结果"
        ideas = result if isinstance(result, list) else [result]
        # 过滤掉 None 或无效元素
        ideas = [idea for idea in ideas if idea and isinstance(idea, dict)]
        if not ideas:
            return None, "创意生成失败：返回结果为空或格式不正确"

        for i, idea in enumerate(ideas):
            idea['_index'] = i + 1

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
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        # 更新数据库中的评分
        for item in result:
            item['index'] = item.get('index', 0)

        return {"scored_ideas": result}, None

    @staticmethod
    def upgrade(project_id: str, top_ideas: list) -> tuple:
        """TOP3创意升级 — 增加矛盾/设计限制"""
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        return {"upgraded": result}, None

    @staticmethod
    def analyze_risks(project_id: str, concept: str, **kwargs) -> tuple:
        """风险分析 — 内容管控/政策/逻辑漏洞"""
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        return result, None


# ========== M2: 项目定位服务 ==========

class ProjectService:
    """项目定位服务 — 12维度策划 + 平台兼容性"""

    DIMENSION_NAMES = [
        "target_audience", "core_hook", "novelty_angle",
        "emotional_resonance", "update_strategy", "title_direction",
        "cover_concept", "opener_strategy", "main_conflict",
        "subplot_count", "climax_pattern", "ending_direction"
    ]

    @staticmethod
    def analyze_batch(project_id: str, idea: str, platform: str,
                      batch_index: int) -> tuple:
        """分批次分析项目定位 — 每批4维度,共3批(0/1/2)"""
        gen = get_default_generator()
        if gen is None:
            return None, "AI生成器未配置"

        preset = ProjectService.PLATFORM_PRESETS.get(platform, {})
        all_dims = ProjectService.DIMENSION_NAMES
        batch_size = 4
        start = batch_index * batch_size
        end = min(start + batch_size, len(all_dims))
        if start >= len(all_dims):
            return None, "批次超出范围"

        batch_dims = all_dims[start:end]
        total_batches = (len(all_dims) + batch_size - 1) // batch_size

        dim_labels = {
            "target_audience": "目标读者画像", "core_hook": "核心卖点",
            "novelty_angle": "新颖角度", "emotional_resonance": "情感共鸣点",
            "update_strategy": "更新策略", "title_direction": "书名方向",
            "cover_concept": "封面概念", "opener_strategy": "开篇策略",
            "main_conflict": "主线矛盾", "subplot_count": "支线数量建议",
            "climax_pattern": "高潮模式", "ending_direction": "结局方向",
        }

        dims_desc = "\n".join([f"{i+1+start}. {d} — {dim_labels.get(d, d)}" for i, d in enumerate(batch_dims)])

        prompt = f"""作为网文策划专家,对以下小说创意进行项目策划。

核心创意: {idea}
目标平台: {preset.get('name', platform)}
平台风格要求: {preset.get('style', '通用')}

请分析第 {batch_index+1}/{total_batches} 批次的 {len(batch_dims)} 个维度:
{dims_desc}

返回JSON: {{"dimensions": [{{"key": "维度key", "title": "维度名", "content": "内容(200字内)", "priority": "高/中/低"}}]}}"""

        result, err = gen._generate_json(prompt, max_tokens=4000)
        if err:
            return None, err

        if isinstance(result, dict):
            result['_batch_index'] = batch_index
            result['_total_batches'] = total_batches
            if 'dimensions' not in result:
                wrapped = []
                for item in result.values():
                    if isinstance(item, dict) and 'content' in item:
                        wrapped.append(item)
                result = {"dimensions": wrapped, "_batch_index": batch_index, "_total_batches": total_batches}
            return result, None
        return None, "返回格式异常"

    PLATFORM_PRESETS = {
        "tomato": {"name": "番茄小说", "style": "快节奏/强情绪/短句式", "update": "日更4000+"},
        "qidian": {"name": "起点中文网", "style": "升级流/爽文/世界观宏大", "update": "日更6000+"},
        "fanqie": {"name": "番茄免费小说", "style": "都市/赘婿/神医/萌宝", "update": "日更4000+"},
    }

    @staticmethod
    def analyze(project_id: str, idea: str, platform: str = "tomato",
                style_profile: dict = None) -> tuple:
        """12维度项目策划"""
        gen = get_default_generator()
        if gen is None:
            return None, "AI生成器未配置"

        preset = ProjectService.PLATFORM_PRESETS.get(platform, {})
        style_str = build_style_str(style_profile)

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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        # 规范化维度key: 数字字符串 → 维度名称
        dimension_names = [
            "target_audience", "core_hook", "novelty_angle",
            "emotional_resonance", "update_strategy", "title_direction",
            "cover_concept", "opener_strategy", "main_conflict",
            "subplot_count", "climax_pattern", "ending_direction"
        ]
        if isinstance(result, dict):
            normalized = {}
            for i, name in enumerate(dimension_names, 1):
                if str(i) in result:
                    normalized[name] = result[str(i)]
                elif name in result:
                    normalized[name] = result[name]
            # 合并其他非数字key
            for k, v in result.items():
                if not k.isdigit() and k not in normalized:
                    normalized[k] = v
            result = normalized if normalized else result

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
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def derive_fields(project_id: str, project_data: dict) -> tuple:
        """衍生字段计算(基于项目定位自动计算其他字段)"""

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
    if not overview or not isinstance(overview, str):
        return 300
    if '千万' in overview:
        return 800
    if '百万' in overview or '长篇' in overview:
        return 500
    if '中篇' in overview:
        return 200
    return 300


def _estimate_words(overview: str) -> int:
    """估算总字数(万)"""
    if not overview or not isinstance(overview, str):
        return 100
    if '千万' in overview:
        return 500
    if '百万' in overview:
        return 200
    return 100


def _extract_keywords(text: str) -> list:
    """提取关键词"""
    return list({w for w in text.split() if len(w) >= 2})[:10]


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
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【世界本源】(the Origin)。

核心创意: {idea}
题材: {genre}

返回JSON(必须包含以下3个key):
{{"worldType": "世界类型(低魔世界/中魔世界/高魔世界/科幻宇宙/末日废土/现实平行)",
 "originStory": "世界起源故事(200字以内)",
 "hiddenTruth": "世界背后隐藏的真相(100字以内)"}}

只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="world_origin")
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_rules(project_id: str, origin: dict, power_system: dict = None) -> tuple:
        """世界规则设计 — 每条规则6要素"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【运行规则】(World Rules)。

世界本源: {json.dumps(origin, ensure_ascii=False, indent=2)}

返回JSON(必须包含以下6个key,每个值50-100字):
{{"power": "修炼/异能的核心规则",
 "economy": "货币、资源、交易规则",
 "politics": "国家、势力、权力分配",
 "technology": "科技树限制、核心原理",
 "culture": "节日、禁忌、礼仪",
 "taboo": "世界底层限制、因果律"}}

key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_structure(project_id: str, origin: dict) -> tuple:
        """世界结构设计 — 层级+地点"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【空间结构】(World Structure)。

世界本源: {origin.get('worldType', '')}

返回JSON(必须包含levels数组):
{{"levels": [
  {{"name": "仙界", "nodes": ["天庭", "瑶池", "凌霄殿", "南天门"]}},
  {{"name": "凡间", "nodes": ["东胜神洲", "西牛贺洲", "南赡部洲", "北俱芦洲"]}},
  {{"name": "冥界", "nodes": ["鬼门关", "奈何桥", "阎罗殿", "忘川河"]}}
]}}

3-5个层级,每个层级2-8个标志性地点。key必须是"name"和"nodes"。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_civilization(project_id: str, structure: dict) -> tuple:
        """文明体系设计 — 8维度"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计世界的【文明体系】(Civilization)。

世界结构概要: {json.dumps(structure, ensure_ascii=False)[:1000]}

返回JSON(必须包含以下8个key,每个值50-100字):
{{"government": "政体结构",
 "religion": "信仰体系",
 "military": "军事制度",
 "education": "教育方式",
 "art": "艺术文化",
 "trade": "贸易体系",
 "law": "法律规则",
 "class": "社会阶级"}}

key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def design_history(project_id: str, structure: dict, civilization: dict) -> tuple:
        """历史时间线设计"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = """设计世界的【历史时间线】(World History)。

返回JSON(必须包含history数组):
{"history": [
  {"era": "太古", "description": "世界诞生,混沌初开(50字以内)"},
  {"era": "上古", "description": "神魔大战,天地分裂(50字以内)"},
  {"era": "中古", "description": "灵气衰退,修仙式微(50字以内)"},
  {"era": "近代", "description": "王朝更迭,群雄并起(50字以内)"}
]}

4-8个历史事件,每个事件包含"era"(时代名)和"description"(事件描述)。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def check_consistency(project_id: str, world_data: dict) -> tuple:
        """世界观一致性检查"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""检查世界观体系的一致性。

世界观数据: {json.dumps(world_data, ensure_ascii=False, indent=2)[:4000]}

检查维度:
1. logic_coherence — 逻辑自洽性(设定之间有无矛盾)
2. power_system_balance — 战力体系平衡(修炼/魔法体系是否合理)
3. civilization_alignment — 文明与社会结构匹配度
4. history_continuity — 历史时间线连续性

返回JSON:
{{"passed": true, "score": 85,
  "issues": [{{"type": "logic", "severity": "med", "description": "...", "fix": "建议"}}],
  "summary": "一致性总结"}}"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None

    @staticmethod
    def save_world(project_id: str, world_data: dict) -> tuple:
        """保存完整世界观"""
        try:
            origin = world_data.get('origin', {})
            if not origin.get('worldType') and world_data.get('worldType'):
                origin = {'worldType': world_data.get('worldType', ''), 'originStory': world_data.get('originStory', ''), 'hiddenTruth': world_data.get('hiddenTruth', '')}
            rules = world_data.get('rules', {})
            if isinstance(rules, list):
                rules = {r.get('name', f'rule{i}'): r.get('description', '') for i, r in enumerate(rules)}
            history = world_data.get('history', [])
            if isinstance(history, dict):
                if 'history' in history:
                    history = history['history']
                else:
                    history = [{'era': k, 'description': str(v)} for k, v in history.items()]
            database_v2.save_world(project_id, {
                'origin': origin,
                'rules': rules,
                'structure': world_data.get('structure', {}),
                'civilization': world_data.get('civilization', {}),
                'history': history,
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
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【主角】档案。

故事概念: {story_concept}
世界规则约束: {json.dumps(world_rules, ensure_ascii=False)[:1000]}

返回JSON(必须包含以下9个key):
{{"name": "主角姓名",
 "gender": "男/女",
 "age": "年龄(数字)",
 "appearance": "外貌特征(30字以内)",
 "personality": "核心性格特点(50字以内)",
 "background": "出身背景故事(100字以内)",
 "goal": "角色追求目标(50字以内)",
 "flaw": "致命弱点/缺点(50字以内)",
 "arc": "角色成长方向(50字以内)"}}

key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="protagonist")
        if err:
            return None, err

        if isinstance(result, dict):
            char_id = f"char-protagonist-{project_id[:8]}"
            database_v2.save_character(project_id, char_id, {
                'name': result.get('name', '未知'),
                'role_type': 'protagonist',
                'appearance': result.get('appearance', ''),
                'personality': result.get('personality', ''),
                'growth_route': result.get('arc', ''),
                'profile': json.dumps(result, ensure_ascii=False),
            })

        return result, None

    @staticmethod
    def generate_supporting(project_id: str, protagonist: dict, count: int = 5) -> tuple:
        """配角设计"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""基于以下主角,设计{count}个配角。

主角: {json.dumps(protagonist, ensure_ascii=False)[:500]}

配角类型分布: 1个导师 + 1个挚友 + 1个对手 + 2个功能角色

返回JSON(必须包含characters数组,每个角色7个key):
{{"characters": [
  {{"name": "角色名",
   "role": "角色定位(导师/挚友/对手/盟友/敌人)",
   "trait": "性格特点(30字以内)",
   "appearance": "外貌特征(30字以内)",
   "background": "背景故事(50字以内)",
   "goal": "角色追求(30字以内)",
   "relation": "与主角的关系(如:挚友/暗恋/师徒,30字以内)"}}
]}}

每个角色的key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="supporting")
        if err:
            return None, err

        if isinstance(result, dict):
            for i, char in enumerate(result.get('characters', [])):
                char_id = f"char-supporting-{i+1}-{project_id[:8]}"
                database_v2.save_character(project_id, char_id, {
                    'name': char.get('name', f'配角{i+1}'),
                    'role_type': char.get('role', 'supporting'),
                    'appearance': char.get('appearance', ''),
                    'personality': char.get('trait', ''),
                    'profile': json.dumps(char, ensure_ascii=False),
                })

        return result, None

    @staticmethod
    def generate_antagonists(project_id: str, protagonist: dict, world: dict) -> tuple:
        """反派体系设计"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计反派体系。

主角: {protagonist.get('name', '主角')}
世界观: {json.dumps(world, ensure_ascii=False)[:500]}

返回JSON(必须包含villains数组,每个反派7个key):
{{"villains": [
  {{"name": "反派名",
   "role": "角色定位(宿敌/幕后黑手/干部/叛徒)",
   "trait": "性格特点(30字以内)",
   "appearance": "外貌特征(30字以内)",
   "background": "背景故事(50字以内)",
   "goal": "角色追求(30字以内)",
   "relation": "与主角的关系(如:宿敌/背叛者/仇敌,30字以内)"}}
]}}

3-5个反派。每个反派的key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="villains")
        if err:
            return None, err
        return result, None

    @staticmethod
    def generate_relations(project_id: str, characters: list) -> tuple:
        """关系网络生成"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        char_summary = [{"name": c.get('name', ''), "role": c.get('role_type', ''),
                        "id": c.get('char_id', '')} for c in characters[:10]]

        prompt = f"""为以下角色构建关系网络。

角色: {json.dumps(char_summary, ensure_ascii=False)}

返回JSON(必须包含relations数组):
{{"relations": [
  {{"from": "角色A名",
   "to": "角色B名",
   "type": "关系类型(师徒/挚友/宿敌/恋人/血缘/盟友/上下级)",
   "description": "关系描述(50字以内)"}}
]}}

关系类型限制为: 师徒/挚友/宿敌/恋人/血缘/盟友/上下级/暗恋/仇敌/同门。
每个关系包含from/to/type/description四个key。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        # 保存关系图
        if isinstance(result, dict):
            database_v2.save_relation_map(project_id, result)

        return result, None

    @staticmethod
    def check_consistency(project_id: str, characters: list) -> tuple:
        """角色一致性检查"""
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None


# ========== M5: 故事体系服务

class StoryService:
    """故事体系服务 — 总纲/卷纲/一致性"""

    @staticmethod
    def generate_master(project_id: str, protagonist: dict, world: dict,
                        characters: list, style_profile: dict = None) -> tuple:
        """总纲设计 — 冲突/主题/事件集"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【故事架构】。

主角: {protagonist.get('name', '主角')}
主角成长路线: {protagonist.get('arc', '')}
世界观要点: {json.dumps(world, ensure_ascii=False)[:1000]}

返回JSON(必须包含以下5个key):
{{"oneLiner": "用一句话描述整个故事(30字以内)",
 "theme": "核心主题(50字以内)",
 "coreConflict": "主角面临的核心矛盾(100字以内)",
 "volumes": [
   {{"no": 1, "title": "卷名", "world": "发生世界", "chapters": 5, "summary": "卷概要(50字以内)"}},
   {{"no": 2, "title": "卷名", "world": "发生世界", "chapters": 5, "summary": "卷概要(50字以内)"}}
 ],
 "plotEvents": [
   {{"chapter": 3, "event": "事件描述(30字以内)"}},
   {{"chapter": 8, "event": "事件描述(30字以内)"}}
 ]}}

3-5卷,5-10个关键事件。所有key必须与上述完全一致。只返回JSON,不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        # 保存故事体系(pipeline state通过前端saveModuleData)
        if isinstance(result, dict):
            database_v2.save_story(project_id, {
                'summary': result.get('oneLiner', ''),
                'conflict_layers': {'main': result.get('coreConflict', '')},
                'theme': result.get('theme', ''),
                'volumes_detail': result.get('volumes', []),
                'total_plot_events': len(result.get('plotEvents', [])),
                **result,
            })

        return result, None

    @staticmethod
    def generate_volumes(project_id: str, master_story: dict,
                         volume_count: int = 5) -> tuple:
        """每卷卷纲生成"""
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
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
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err
        return result, None



