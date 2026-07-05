"""V2 结构层服务 — M6-M13

M6: power_system — 力量体系(等级/战斗/升级/限制)
M7: factions — 势力体系(5-8势力设计)
M8: timeline — 时间线(整合历史+剧情)
M9: master_outline — 全书大纲(起承转合/卷结构)
M10: volumes — 卷纲(单卷详细设计)
M11: plot_nodes — 剧情节点(事件具体化)
M12: chapter_plan — 章节规划(事件→章)
M13: chapter_outline — 章节细纲(逐章展开)
"""
import sys
import os
import json
import logging
from typing import Optional, Dict, Any, List

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from novel_creator import database_v2
from app.services.novel_generator import get_generator

logger = logging.getLogger('novel_creator.structure')


# ========== M6: 力量体系 ==========

class PowerSystemService:
    """力量体系服务 — 等级/战斗/升级/限制"""

    @staticmethod
    def generate(project_id: str, world_rules: dict, character_abilities: list = None,
                 style_profile: dict = None) -> tuple:
        """完整力量体系设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)
        prompt = f"""{style_str}
设计完整的小说【力量体系】(Power System)。

世界规则: {json.dumps(world_rules, ensure_ascii=False)[:2000]}
角色能力参考: {json.dumps(character_abilities or [], ensure_ascii=False)[:1000]}

设计内容:
1. tiers — 等级体系(8-15个等级,每个:name+threshold+abilities+lifespan+power_description)
2. combat_categories — 战斗体系(物理/法术/精神/辅助等,每个:category+styles+counters+special_moves)
3. growth_method — 升级方式(method+requirements+breakthrough_triggers+failure_consequences+resources)
4. limits — 限制体系(瓶颈/天劫/心魔/资源限制/血脉限制,每个:type+trigger+effect+solution)
5. bottlenecks — 瓶颈设计(stage+manifestation+breakthrough_method+%_stuck+significance)
6. resources — 修炼资源(灵石/丹药/灵器等,每种:name+tier+source+effect+rarity)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存
        if isinstance(result, dict):
            database_v2.save_power_system(project_id, {
                'tiers': result.get('tiers', []),
                'combat_categories': result.get('combat_categories', []),
                'growth_method': result.get('growth_method', ''),
                'limits': result.get('limits', []),
                'bottlenecks': result.get('bottlenecks', []),
            })

        return result, None

    @staticmethod
    def save(project_id: str, data: dict) -> tuple:
        """保存力量体系"""
        try:
            database_v2.save_power_system(project_id, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M7: 势力体系 ==========

class FactionService:
    """势力体系服务 — 5-8势力设计"""

    @staticmethod
    def generate(project_id: str, civilization: dict, characters: list = None) -> tuple:
        """5-8势力设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""设计小说世界的【势力体系】(Factions)。

文明体系: {json.dumps(civilization, ensure_ascii=False)[:1500]}
角色归属参考: {json.dumps([{'name': c.get('name',''), 'affiliation': c.get('affiliation','')} for c in (characters or [])[:10]], ensure_ascii=False)}

设计5-8个势力,每个势力包含:
1. name + title — 势力名称/别称
2. faction_type — 类型(宗门/帝国/商会/杀手组织/隐世家族等)
3. tier — 实力等级(一品至九品/一流至三流)
4. territory — 领地范围
5. leader_info — 领袖信息(name+title+power+personality)
6. power_base — 实力根基(弟子数/高手数/底蕴)
7. resource_control — 掌控资源
8. foreign_relations — 对外关系(abc三方的立场)
9. internal_conflicts — 内部矛盾(派系/继承/理念)
10. plot_function — 剧情功能(如主角盟友/宿敌/踏板)
11. secrets — 隐藏秘密(1-2个)
12. fate_arc — 命运走向(兴盛/衰落/覆灭/隐匿)

返回JSON: {{"factions": [上述12要素], "meta_analysis": "势力格局总评(200字)"}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        # 保存势力
        if isinstance(result, dict):
            for i, faction in enumerate(result.get('factions', [])):
                fid = f"faction-{i+1}-{project_id[:8]}"
                database_v2.save_faction(project_id, fid, faction)

        return result, None

    @staticmethod
    def save(project_id: str, factions: list) -> tuple:
        """保存势力"""
        try:
            for i, f in enumerate(factions):
                fid = f.get('faction_id', f'faction-{i+1}-{project_id[:8]}')
                database_v2.save_faction(project_id, fid, f)
            return {"saved": True, "count": len(factions)}, None
        except Exception as e:
            return None, str(e)


# ========== M8: 时间线 ==========

class TimelineService:
    """时间线服务 — 整合世界历史+剧情事件"""

    @staticmethod
    def build(project_id: str, world_history: dict, story_events: dict) -> tuple:
        """整合世界历史+剧情事件为统一时间线"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""整合世界历史和剧情事件为统一【时间线】(Timeline)。

世界历史: {json.dumps(world_history, ensure_ascii=False)[:2000]}
剧情事件: {json.dumps(story_events, ensure_ascii=False)[:2000]}

整合要求:
1. 合并两段时间线,处理冲突和矛盾
2. 补充缺失的时间节点
3. 标注时间线上的"关键分歧点"(读者需要记住的)
4. 计算每段剧情的持续时间(用于把控节奏)
5. 古代历史和现代剧情的时间换算

返回JSON:
{{"events": [{{"year": 1, "era": "太古", "event": "事件", "type": "history/plot", "impact": "high", "description": "100字"}}],
 "time_conversion": "古今时间换算规则",
 "era_definitions": {{"name": "太古", "start": -10000, "end": -5000, "characteristics": "xxx"}},
 "consistency_status": {{"conflicts": [], "gaps": [], "resolved": true}}}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        if isinstance(result, dict):
            database_v2.save_timeline(project_id, result)

        return result, None

    @staticmethod
    def save(project_id: str, data: dict) -> tuple:
        """保存时间线"""
        try:
            database_v2.save_timeline(project_id, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M9: 全书大纲 ==========

class MasterOutlineService:
    """全书大纲服务 — 起承转合/卷结构"""

    @staticmethod
    def generate(project_id: str, story_system: dict, volumes: list = None,
                 style_profile: dict = None) -> tuple:
        """全书大纲"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = _build_style_str(style_profile)
        prompt = f"""{style_str}
设计小说的【全书大纲】(Master Outline)。

故事体系: {json.dumps(story_system, ensure_ascii=False)[:2000]}

大纲内容:
1. opening — 开篇设计(hook+首章内容+黄金三章规划)
2. rising_actions — 上升阶段(3-5个阶段,每阶段:phase+main_progress+character_change+wordcount)
3. subplots — 支线规划(3-8条,每条:type+start_chapter+end_chapter+function+resolution)
4. midpoint_turn — 中点转折(第几章+发生了什么+为什么重要)
5. climax_buildup — 高潮铺垫(多长+几个层次+每层的conflict_increase)
6. final_climax — 总高潮设计(位置+conflict+stakes+participants+resolution_type)
7. ending_type — 结局类型(大团圆/开放/悲剧/circular)
8. rewatch_hooks — 重读钩子(隐藏细节/伏笔设计,让读者有二刷欲望)
9. volume_structure — 卷结构(几卷+每卷定位+字数+关键事件)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def save(project_id: str, data: dict) -> tuple:
        """保存全书大纲"""
        try:
            # 存储到 story_systems 表的扩展字段
            existing = database_v2.get_story(project_id) or {}
            existing['master_outline'] = data
            database_v2.save_story(project_id, existing)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M10: 卷纲 ==========

class VolumeService:
    """卷纲服务 — 单卷详细设计"""

    @staticmethod
    def generate(project_id: str, volume_no: int, master_outline: dict,
                 world: dict = None, characters: list = None) -> tuple:
        """单卷详细设计"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""生成第{volume_no}卷的详细卷纲。

全书大纲: {json.dumps(master_outline, ensure_ascii=False)[:2000]}

卷纲内容:
1. title + theme — 卷名/卷主题
2. wordcount_target — 目标字数
3. story_arc — 卷内故事弧线(beginning→development→climax→resolution,每阶段:phase+key_events+emotional_tone)
4. chapter_breakdown — 章节分配(15-50章,每章:title+hook+main_event+cliffhanger+wordcount)
5. character_focus — 角色着墨(本卷核心/辅助角色的塑造进度)
6. power_progress — 力量体系进展(主角等级/新能力/瓶颈)
7. world_exposure — 世界观揭示(本卷揭示的世界秘密)
8. foreshadow_plan — 伏笔计划(埋设3-5个/回收2-3个)
9. emotional_curve — 情绪曲线(高峰和低谷的分布)
10. subplot_threads — 支线的推进和收束

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        if isinstance(result, dict):
            database_v2.save_volume(project_id, volume_no, result)

        return result, None

    @staticmethod
    def save(project_id: str, volume_no: int, data: dict) -> tuple:
        """保存卷纲"""
        try:
            database_v2.save_volume(project_id, volume_no, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M11: 剧情节点 ==========

class PlotNodeService:
    """剧情节点服务 — 事件具体化"""

    @staticmethod
    def generate(project_id: str, chapter_plan: dict, master_outline: dict,
                 power_system: dict = None, characters: list = None) -> tuple:
        """事件具体化"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""将章节规划中的事件细化为具体剧情节点。

章节规划: {json.dumps(chapter_plan, ensure_ascii=False)[:1500]}

每个剧情节点包含:
1. event_id + title — 节点标识
2. trigger — 触发条件(事件因何而发)
3. scenes — 场景列表(每个:location+characters+action+dialogue_highlight+duration)
4. turning_point — 转折点(决策/发现/反转)
5. consequences — 直接后果(影响哪些角色/势力/线索)
6. emotional_beats — 情绪节拍(紧张/放松/愤怒/喜悦等节奏)
7. knowledge_update — 知识库更新(角色学到什么/世界揭示什么)
8. foreshadow_triggers — 触发的伏笔(埋/收)

返回JSON: {{"events": [...]}}"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        if isinstance(result, dict):
            for event in result.get('events', []):
                eid = event.get('event_id', f'evt-{project_id[:8]}')
                database_v2.save_plot_node(project_id, eid, event)

        return result, None

    @staticmethod
    def save(project_id: str, event_id: str, data: dict) -> tuple:
        """保存剧情节点"""
        try:
            database_v2.save_plot_node(project_id, event_id, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M12: 章节规划 ==========

class ChapterPlanService:
    """章节规划服务 — 事件→章"""

    @staticmethod
    def plan(project_id: str, master_outline: dict, plot_events: list,
             target_wordcount: int = 2000) -> tuple:
        """章节分配"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""将事件分配到具体章节。

全书大纲: {json.dumps(master_outline, ensure_ascii=False)[:2000]}
剧情事件: {json.dumps(plot_events[:30], ensure_ascii=False)}

每章目标字数: {target_wordcount}

规划内容:
1. chapter_assignments — 章节分配(每章:chapter_no+events[对应事件ID]+target_words+hook+cliffhanger_type)
2. pacing_analysis — 节奏分析(快/慢/张/弛的分布)
3. hook_distribution — 钩子分配(每3-5章一个大钩子)
4. milestone_chapters — 里程碑章节(必须精彩的关键章)
5. total_chapters — 总章节数

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err

        if isinstance(result, dict):
            for ch in result.get('chapter_assignments', []):
                ch_no = str(ch.get('chapter_no', '1'))
                database_v2.save_chapter_plan(project_id, ch_no, ch)

        return result, None

    @staticmethod
    def save(project_id: str, chapter_no: str, data: dict) -> tuple:
        """保存章节规划"""
        try:
            database_v2.save_chapter_plan(project_id, chapter_no, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M13: 章节细纲 ==========

class ChapterOutlineService:
    """章节细纲服务 — 逐章展开"""

    @staticmethod
    def generate(project_id: str, chapter_no: str, chapter_plan: dict,
                 foreshadow_plan: dict = None, knowledge_state: dict = None) -> tuple:
        """逐章展开"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""为第{chapter_no}章撰写详细章节细纲。

章节规划: {json.dumps(chapter_plan, ensure_ascii=False)[:1500]}

细纲内容:
1. scenes — 场景设计(每个:scene_no+location+characters+goal+conflict+outcome+sensory_details)
2. emotional_curve — 情绪曲线(起始情绪→最高点→最低点→结束情绪,四阶段的具体描写)
3. pov_shifts — 视角切换(几段/每段长度/切换原因)
4. foreshadow_ops — 伏笔操作(埋设{content+placement+payoff_hint}/回收{original_id+resolution})
5. knowledge_ops — 知识库操作(揭示{hide+reveal}/升级{old+new})
6. dialogue_beats — 关键对话(dialogue_type+characters+purpose+subtext)
7. action_beats — 关键动作(action_type+characters+consequence+tension_level)
8. transition — 章末过渡(方式+效果+下章伏笔)

返回JSON格式"""

        result, err = gen._generate_json(prompt)
        if err:
            return None, err
        return result, None

    @staticmethod
    def save(project_id: str, chapter_no: str, data: dict) -> tuple:
        """保存章节细纲"""
        try:
            existing = database_v2.get_chapter_plans(project_id) or []
            # Merge outline into chapter plan
            for ch in (existing if isinstance(existing, list) else []):
                if str(ch.get('chapter_no', '')) == str(chapter_no):
                    ch['outline'] = data
                    database_v2.save_chapter_plan(project_id, chapter_no, ch)
                    break
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== 工具函数 ==========

def _get_default_generator():
    """获取默认生成器"""
    endpoint = os.environ.get('AI_ENDPOINT', '')
    api_key = os.environ.get('AI_API_KEY', '')
    model = os.environ.get('AI_MODEL', 'gpt-4o-mini')
    if not endpoint or not api_key:
        logger.warning("AI endpoint/api_key未配置")
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
