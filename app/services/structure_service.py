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
import json
import logging
import os
import sys

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from app.services.service_utils import build_style_str, get_default_generator
from novel_creator import data_bridge

DataBridge = data_bridge.DataBridge

logger = logging.getLogger('novel_creator.structure')



# ========== M9: 全书大纲 ==========

class MasterOutlineService:
    """全书大纲服务 — 起承转合/卷结构"""

    @staticmethod
    def generate(project_id: str, story_system: dict, volumes: list = None,
                 style_profile: dict = None) -> tuple:
        """全书大纲"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)
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

        result, err = gen._generate_json(prompt, max_tokens=16000, module_name="master_outline")
        if err:
            return None, err
        return result, None

    @staticmethod
    def save(project_id: str, data: dict) -> tuple:
        """保存全书大纲 → 架构"""
        try:
            existing = DataBridge.read(project_id, "architecture") or {}
            existing['master_outline'] = data
            DataBridge.write(project_id, "architecture", existing)
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
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""生成第{volume_no}卷的卷纲。返回JSON，总字数控制在3000字以内。

全书大纲: {json.dumps(master_outline, ensure_ascii=False)[:1500]}

JSON结构:
{{"title":"卷名","theme":"主题","wordcount_target":60000,
"story_arc":{{"beginning":{{"phase":"开篇","key_events":["事件1"],"emotional_tone":"期待"}},"development":{{"phase":"发展","key_events":["事件2"],"emotional_tone":"紧张"}},"climax":{{"phase":"高潮","key_events":["事件3"],"emotional_tone":"激昂"}},"resolution":{{"phase":"收尾","key_events":["事件4"],"emotional_tone":"释然"}}}},
"chapters":["第1章名","第2章名","第3章名"],
"character_focus":["角色A进步","角色B成长"],
"power_progress":"主角突破到新等级",
"world_exposure":"揭示世界秘密",
"foreshadow_plan":["埋设伏笔X","回收伏笔Y"],
"emotional_curve":["开篇平缓","中期攀升","高潮爆发","结尾余韵"],
"subplot_threads":["支线1推进","支线2收束"]}}

直接返回JSON，不要markdown代码块。"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="volumes")
        if err:
            return None, err

        if isinstance(result, dict):
            DataBridge.write(project_id, "volumes", [result])

        return result, None

    @staticmethod
    def generate_batch(project_id: str, count: int, master_outline: dict,
                       world: dict = None, characters: list = None) -> tuple:
        """批量生成多卷卷纲（每卷独立调用避免JSON截断）"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""一次性生成全部 {count} 卷的卷纲设计。

全书大纲: {json.dumps(master_outline, ensure_ascii=False)[:2000]}

生成 {count} 卷,每卷包含:
1. volume_no — 卷序号(1-{count})
2. title + theme — 卷名/卷主题
3. target_words — 目标字数
4. chapter_count — 章节数
5. protagonist_start — 卷初主角状态
6. protagonist_end — 卷末主角状态
7. key_events — 关键事件列表
8. cliffhanger — 卷尾悬念

返回JSON数组格式: [{{volume_no:1, ...}}, {{volume_no:2, ...}}, ...]"""

        result, err = gen._generate_json(prompt, max_tokens=16000, module_name="volumes")
        if err:
            return None, err

        # AI可能返回list或dict格式{volume_1:{...}, volume_2:{...}}
        if isinstance(result, dict):
            # 如果是dict，检查是否是{volume_1:{...}}格式
            if all(isinstance(v, dict) for v in result.values()):
                volumes = []
                for k, v in result.items():
                    if 'volume_no' not in v:
                        # 尝试从key提取序号
                        import re
                        m = re.search(r'(\d+)', k)
                        v['volume_no'] = int(m.group(1)) if m else len(volumes) + 1
                    volumes.append(v)
            else:
                volumes = [result]
        else:
            volumes = result if isinstance(result, list) else [result]

        for vol in volumes:
            if isinstance(vol, dict):
                no = vol.get('volume_no', vol.get('volume_id', ''))
                vol['volume_no'] = no
        if volumes:
            DataBridge.write(project_id, "volumes", volumes)

        return {"volumes": volumes}, None

    @staticmethod
    def save(project_id: str, volume_no: int, data: dict) -> tuple:
        """保存卷纲"""
        try:
            existing_vols = DataBridge.read(project_id, "volumes") or []
            existing_vols = [v for v in existing_vols if str(v.get('volume_no', '')) != str(volume_no)]
            existing_vols.append(data)
            DataBridge.write(project_id, "volumes", existing_vols)
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
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        if isinstance(result, dict):
            # plot_nodes 已废弃, 不再写入数据库
            logger.warning("plot_nodes 模块已废弃, 跳过 save_plot_node")

        return result, None

    @staticmethod
    def save(project_id: str, event_id: str, data: dict) -> tuple:
        """保存剧情节点 (已废弃, no-op)"""
        logger.warning("plot_nodes 模块已废弃, save_plot_node 为 no-op")
        return {"saved": True, "deprecated": True}, None


# ========== M12: 章节规划 ==========

class ChapterPlanService:
    """章节规划服务 — 事件→章"""

    @staticmethod
    def plan(project_id: str, master_outline: dict, plot_events: list,
             target_wordcount: int = 2000) -> tuple:
        """章节分配"""
        gen = get_default_generator()
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

        result, err = gen._generate_json(prompt, max_tokens=16000, module_name="chapter_plan")
        if err:
            return None, err

        if isinstance(result, dict):
            chapters = result.get('chapter_assignments', [])
            if chapters:
                DataBridge.write(project_id, "chapter_plan", chapters)

        return result, None

    @staticmethod
    def save(project_id: str, chapter_no: str, data: dict) -> tuple:
        """保存章节规划"""
        try:
            existing = DataBridge.read(project_id, "chapter_plan") or []
            existing = [c for c in existing if str(c.get('chapter_no', '')) != str(chapter_no)]
            existing.append(data)
            DataBridge.write(project_id, "chapter_plan", existing)
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
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""为第{chapter_no}章撰写详细章节细纲。

章节规划: {json.dumps(chapter_plan, ensure_ascii=False)[:1500]}

细纲内容:
1. scenes — 场景设计(每个:scene_no+location+characters+goal+conflict+outcome+sensory_details)
2. emotional_curve — 情绪曲线(起始情绪→最高点→最低点→结束情绪,四阶段的具体描写)
3. pov_shifts — 视角切换(几段/每段长度/切换原因)
4. foreshadow_ops — 伏笔操作(埋设{{content+placement+payoff_hint}}/回收{{original_id+resolution}})
5. knowledge_ops — 知识库操作(揭示{{hide+reveal}}/升级{{old+new}})
6. dialogue_beats — 关键对话(dialogue_type+characters+purpose+subtext)
7. action_beats — 关键动作(action_type+characters+consequence+tension_level)
8. transition — 章末过渡(方式+效果+下章伏笔)

返回JSON格式"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="chapter_outline")
        if err:
            return None, err

        if not isinstance(result, dict):
            return None, f"章节细纲生成失败: 非预期的返回类型 {type(result).__name__}"

        error_only = result.get('error')
        if error_only is not None and len(result) == 1:
            return None, f"章节细纲生成失败: AI返回错误 - {error_only}"

        if not result.get('scenes') and not result.get('emotional_curve') and not result.get('key_points'):
            return None, "章节细纲生成失败: AI未返回有效章节内容"

        return result, None

    @staticmethod
    def generate_batch(project_id: str, total_chapters: int, chapter_plan: dict,
                       foreshadow_plan: dict = None, knowledge_state: dict = None) -> tuple:
        """批量生成全部章纲"""
        gen = get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""为全部 {total_chapters} 章一次性撰写章节细纲。

章节规划: {json.dumps(chapter_plan, ensure_ascii=False)[:1500]}

每章包含:
1. chapter_no — 章节序号(1-{total_chapters})
2. title — 章标题
3. summary — 章概要(100字内)
4. scenes[1-3] — 场景(每个:setting+characters+goal+conflict+outcome)
5. key_points — 核心看点列表
6. word_count — 目标字数
7. cliffhanger — 章尾悬念

返回JSON数组: [{{chapter_no:1, ...}}, {{chapter_no:2, ...}}, ...]"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        outlines = result if isinstance(result, list) else [result]
        return {"outlines": outlines}, None

    @staticmethod
    def save(project_id: str, chapter_no: str, data: dict) -> tuple:
        """保存章节细纲 → chapter_plan"""
        try:
            existing = DataBridge.read(project_id, "chapter_plan") or []
            updated = False
            for ch in existing:
                if str(ch.get('chapter_no', '')) == str(chapter_no):
                    ch['outline'] = data
                    updated = True
                    break
            if updated:
                DataBridge.write(project_id, "chapter_plan", existing)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)
            return None, str(e)



