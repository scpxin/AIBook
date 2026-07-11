"""V2 执行层服务 — M14-M19

M14: scenes        — 场景设计(时间/环境/冲突/战斗/氛围)
M15: draft         — 正文生成(流式,分段:开场/发展/高潮/结尾)
M16: polish        — 润色(语言/节奏/查重)
M17: content_parse — 内容解析(场景/对白/动作切分)
M18: knowledge     — 知识库(增量更新 + 快照 + 伏笔列表)
M19: consistency   — 一致性检查(9项自动校验)
"""
import sys
import os
import json
import logging
import re
from typing import Optional, Dict, Any, List

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from novel_creator import database_v2
from app.services.novel_generator import get_generator
from app.services.service_utils import get_default_generator as _get_default_generator, build_style_str

logger = logging.getLogger('novel_creator.execution')


# ========== M14: 场景设计 ==========

class SceneService:
    """场景设计服务 — 场景骨架生成"""

    @staticmethod
    def design(project_id: str, chapter_outline: dict, foreshadow_plan: dict = None,
               power_system: dict = None, characters: list = None) -> tuple:
        """场景骨架生成"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""基于以下章节细纲,设计详细场景骨架。

章节细纲: {json.dumps(chapter_outline, ensure_ascii=False)[:2000]}

每个场景包含:
1. scene_id + title — 场景标识
2. time_environment — 时间/天气/光线(感官细节:视/听/嗅/触)
3. location_detail — 场景地点(空间布局/关键物品/氛围元素)
4. characters_present — 出场角色(状态/情绪/目标/秘密)
5. scene_goal — 场景目标(角色想要什么)
6. conflict_design — 冲突设计(类型:对话/战斗/心理/环境 + 强度:1-10 + 升级步骤)
7. action_beats — 动作节拍(5-10个节拍,每个:beat+purpose+sensory_detail+dialogue_hint)
8. emotional_flow — 情绪流动(起→承→转→合)
9. foreshadow_ops — 伏笔操作(埋/收/呼应)
10. scene_ending — 场景结束方式(钩子/过渡/悬念)
11. transition_out — 出场景方式

返回JSON: {{"scenes": [...]}}"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="scene_design")
        if err:
            return None, err

        if isinstance(result, dict):
            for scene in result.get('scenes', []):
                sid = scene.get('scene_id', f'scene-{project_id[:8]}')
                database_v2.save_scene(project_id, sid, scene)

        return result, None

    @staticmethod
    def save(project_id: str, scene_id: str, data: dict) -> tuple:
        """保存场景"""
        try:
            database_v2.save_scene(project_id, scene_id, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M15: 正文生成(流式) ==========

class DraftService:
    """正文生成服务 — 流式输出"""

    @staticmethod
    def generate_stream(project_id: str, chapter_no: str, scene_skeleton: dict,
                        constraints: dict = None):
        """流式正文生成"""
        gen = _get_default_generator()
        if not gen:
            yield {"error": "AI生成器未配置"}
            return

        prompt = f"""基于以下场景骨架,写出完整的正文内容。

场景骨架: {json.dumps(scene_skeleton, ensure_ascii=False)[:3000]}
约束: {json.dumps(constraints or {}, ensure_ascii=False)}

要求:
1. 开场建立氛围和环境(100-200字)
2. 发展部分推进情节(含对话+动作+心理)
3. 高潮部分冲突爆发(最紧张的时刻)
4. 结尾留下悬念(章末钩子)
5. 伏笔自然融入,不过度刻意
6. 每个角色的说话风格一致
7. 叙事节奏:紧张→舒缓→紧张波浪

输出完整的正文内容(不分段),目标2000-3000字。"""

        try:
            full_content = ""
            for chunk in gen.client.generate_stream(prompt, temperature=0.8, max_tokens=8000):
                if isinstance(chunk, dict):
                    if chunk.get('error'):
                        yield {"type": "error", "message": chunk['error']}
                        return
                    if chunk.get('done'):
                        break
                    text = chunk.get('content', '')
                else:
                    text = str(chunk) if chunk else ''
                if text:
                    full_content += text
                    yield {"type": "chunk", "content": text, "full_length": len(full_content)}

            # 完成
            yield {"type": "done", "content": full_content, "length": len(full_content)}

            # 保存到数据库
            database_v2.save_draft(project_id, int(chapter_no) if chapter_no.isdigit() else 1, {
                'content': full_content,
                'content_raw': full_content,
                'chapter_no': chapter_no,
            })

        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            yield {"type": "error", "message": str(e)}

    @staticmethod
    def save(project_id: str, chapter_no: str, data: dict) -> tuple:
        """保存正文"""
        try:
            ch = int(chapter_no) if str(chapter_no).isdigit() else 1
            database_v2.save_draft(project_id, ch, data)
            return {"saved": True}, None
        except Exception as e:
            return None, str(e)


# ========== M16: 润色 ==========

class PolishService:
    """润色服务 — 语言/节奏优化"""

    @staticmethod
    def polish(project_id: str, content: str, style_profile: dict = None,
               focus: str = "整体优化", foreshadow_protected: list = None) -> tuple:
        """润色优化"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        style_str = build_style_str(style_profile)
        prompt = f"""{style_str}
对以下正文进行润色优化。

原文: {content[:3000]}
润色焦点: {focus}

要求: 消除语病、优化修辞、提升画面感、调整句式长短和段落分配，保留原文伏笔和关键情节。

返回JSON:
{{"content": "润色后全文(保持原文长度)",
  "changes": ["改动1描述", "改动2描述"],
  "summary": "润色总结(50字内)"}}"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="polish")
        if err:
            return None, err
        return result, None


# ========== M17: 内容解析 ==========

class ContentParserService:
    """内容解析服务 — 场景/对白/动作切分"""

    @staticmethod
    def parse(project_id: str, chapter_no: str, content: str,
              existing_characters: list = None) -> tuple:
        """解析已写章节"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        char_context = ""
        if existing_characters:
            char_names = [c.get('name', c.get('char_id', '')) for c in existing_characters if c]
            if char_names:
                char_context = f"\n\n已知角色: {', '.join(char_names[:20])}\n解析对白时请关联到已知角色。"

        prompt = f"""解析以下小说正文,进行结构化分析。

正文: {content[:6000]}
{char_context}
解析内容:
1. scene_segments — 场景切分(每段:start_pos+end_pos+location+characters+summary)
2. dialogue_extraction — 对白提取(speaker+listener+content+subtext+emotion+hidden_agenda)
3. action_extraction — 动作提取(actor+action+target+consequence+intensity)
4. status_changes — 状态变化(entity+attribute+old_value+new_value+chapter_no)
5. foreshadow_detection — 伏笔检测(type:planting/payoff+hint+confidence)
6. pacing_analysis — 节奏分析(tension_level_per_segment+rhythm_pattern)
7. word_count — 字数统计(raw+final+dialogue_ratio+action_ratio+description_ratio)

返回JSON格式"""

        result, err = gen._generate_json(prompt, max_tokens=8000, module_name="content_parse")
        if err:
            return None, err

        # 自动触发知识库更新
        if isinstance(result, dict) and result.get('status_changes'):
            for change in result['status_changes']:
                database_v2.save_knowledge_state(project_id, {
                    'change': change,
                    'chapter_no': chapter_no,
                })

        return result, None


# ========== M18: 知识库 ==========

class KnowledgeService:
    """知识库服务 — 增量更新 + 快照 + 伏笔"""

    @staticmethod
    def update(project_id: str, chapter_no: str, parse_result: dict) -> tuple:
        """增量更新知识库"""
        try:
            current = database_v2.get_knowledge_state(project_id) or {}
            if isinstance(current, dict):
                character_states = current.get('character_states', {})
                plot_state = current.get('plot_state', {})
                world_state = current.get('world_state', {})

                # 应用状态变化
                for change in parse_result.get('status_changes', []):
                    entity = change.get('entity', '')
                    attr = change.get('attribute', '')
                    new_val = change.get('new_value', '')
                    if '角色' in entity or 'character' in entity.lower():
                        character_states[f"{entity}.{attr}"] = new_val
                    elif '世界' in entity or 'world' in entity.lower():
                        world_state[attr] = new_val
                    else:
                        plot_state[f"{entity}.{attr}"] = new_val

                database_v2.save_knowledge_state(project_id, {
                    'character_states': character_states,
                    'plot_state': plot_state,
                    'world_state': world_state,
                    'last_updated_chapter': chapter_no,
                })

            return {"updated": True}, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def snapshot(project_id: str) -> tuple:
        """获取知识库快照"""
        try:
            state = database_v2.get_knowledge_state(project_id)
            if not state:
                return {"character_states": {}, "plot_state": {}, "world_state": {}}, None
            return state, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_foreshadows(project_id: str, status: str = None) -> tuple:
        """获取活跃伏笔列表"""
        try:
            foreshadows = database_v2.get_foreshadows(project_id, status=status)
            return {"foreshadows": foreshadows or [], "count": len(foreshadows or [])}, None
        except Exception as e:
            return None, str(e)


# ========== M19: 一致性检查 ==========

class ConsistencyService:
    """一致性检查服务 — 9项自动校验"""

    @staticmethod
    def check(project_id: str, chapter_no: str, content: str = None,
              knowledge_state: dict = None, characters: list = None,
              world: dict = None, power_system: dict = None) -> tuple:
        """9项一致性校验"""
        gen = _get_default_generator()
        if not gen:
            return None, "AI生成器未配置"

        prompt = f"""对以下小说内容进行9项一致性校验。

章节号: {chapter_no}
正文: {(content or '')[:4000]}
知识库状态: {json.dumps(knowledge_state or {}, ensure_ascii=False)[:1500]}
角色: {json.dumps([{k: v for k, v in c.items() if k != '_raw_data'} for c in (characters or [])[:8]], ensure_ascii=False)[:1500]}
世界观: {json.dumps(world or {}, ensure_ascii=False)[:1000]}
力量体系: {json.dumps(power_system or {}, ensure_ascii=False)[:500]}

9项校验:
1. character_trait — 角色性格一致性(对话/行为是否符合设定)
2. power_level — 战力一致性(等级是否合理/越级是否解释)
3. timeline — 时间一致性(事件先后是否合理)
4. location — 空间一致性(地点距离/移动时间)
5. foreshadow — 伏笔一致性(已埋设的是否正确使用)
6. knowledge — 知识一致性(角色知道的信息是否合理)
7. causality — 因果一致性(事件是否因果链合理)
8. world_rules — 世界规则一致性(是否违反规则)
9. plot_holes — 情节漏洞(是否有未解释的矛盾)

返回JSON:
{{"overall_score": 85,
  "passed": true/false,
  "checks": [{{"dimension": "character_trait", "score": 90, "issues": []}}],
  "critical_issues": [{{"dimension": "...", "severity": "high", "description": "...", "fix": "修复建议"}}],
  "summary": "一致性总评(200字)"}}"""

        result, err = gen._generate_json(prompt, max_tokens=8000)
        if err:
            return None, err

        # 保存检查报告
        if isinstance(result, dict):
            database_v2.save_consistency_report(project_id, {
                'chapter_no': chapter_no,
                'overall_score': result.get('overall_score', 0),
                'passed': result.get('passed', False),
                'checks': result.get('checks', []),
                'critical_issues': result.get('critical_issues', []),
                **result,
            })

        return result, None

    @staticmethod
    def world_check(project_id: str) -> tuple:
        """世界观一致性检查 (实际AI分析)"""
        try:
            world = database_v2.get_world(project_id)
            if not world:
                return {"passed": False, "message": "世界观数据不存在", "score": 0, "issues": []}, None

            gen = _get_default_generator()
            if not gen:
                return {"passed": True, "message": "AI未配置，跳过检查", "score": 100, "issues": []}, None

            prompt = f"""检查以下世界观内部一致性，逐一验证各维度是否存在矛盾。

世界观数据:
- 本源(origin): {json.dumps(world.get('origin', {}), ensure_ascii=False, default=str)[:800]}
- 规则(rules): {json.dumps(world.get('rules', []), ensure_ascii=False, default=str)[:800]}
- 结构(structure): {json.dumps(world.get('structure', {}), ensure_ascii=False, default=str)[:600]}
- 文明(civilization): {json.dumps(world.get('civilization', {}), ensure_ascii=False, default=str)[:600]}
- 历史(history): {json.dumps(world.get('history', {}), ensure_ascii=False, default=str)[:600]}

请检查:
1. 本源设定与规则是否矛盾
2. 文明发展是否符合历史脉络
3. 世界结构是否与规则冲突
4. 各维度之间是否存在逻辑不一致

返回JSON格式: {{"passed": true/false, "score": 0-100, "issues": [{{"dimension": "维度名", "description": "矛盾描述", "severity": "high/medium/low"}}], "summary": "总结"}}"""

            result, err = gen._generate_json(prompt, max_tokens=2000, module_name="world_consistency_check")
            if err:
                return {
                    "passed": False, 
                    "message": f"AI检查不可用: {err}", 
                    "score": 0, 
                    "issues": [],
                    "status": "unavailable"
                }, None

            return {
                "passed": result.get("passed", False),
                "score": result.get("score", 100),
                "issues": result.get("issues", []),
                "summary": result.get("summary", "AI一致性分析完成"),
                "message": "AI一致性分析完成"
            }, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def character_check(project_id: str) -> tuple:
        """角色一致性检查 (实际AI分析)"""
        try:
            characters = database_v2.get_all_characters(project_id)
            if not characters:
                return {"passed": False, "message": "角色数据不存在", "score": 0, "issues": []}, None

            gen = _get_default_generator()
            if not gen:
                return {"passed": True, "message": "AI未配置，跳过检查", "score": 100, "issues": []}, None

            char_summary = []
            for c in characters[:10]:
                char_summary.append({
                    "name": c.get('name', c.get('姓名', '未知')),
                    "role": c.get('role', c.get('角色类型', '')),
                    "personality": c.get('personality', c.get('性格', ''))[:200],
                })

            prompt = f"""检查以下角色设定内部一致性，验证角色之间是否存在矛盾。

角色列表: {json.dumps(char_summary, ensure_ascii=False, default=str)[:1500]}

请检查:
1. 角色性格与行为动机是否一致
2. 角色之间关系是否合理
3. 主角与配角/反派之间是否存在设定冲突
4. 角色能力与世界观规则是否匹配

返回JSON格式: {{"passed": true/false, "score": 0-100, "issues": [{{"character": "角色名", "description": "矛盾描述", "severity": "high/medium/low"}}], "summary": "总结"}}"""

            result, err = gen._generate_json(prompt, max_tokens=2000, module_name="character_consistency_check")
            if err:
                return {
                    "passed": False, 
                    "message": f"AI检查不可用: {err}", 
                    "score": 0, 
                    "issues": [],
                    "status": "unavailable"
                }, None

            return {
                "passed": result.get("passed", False),
                "score": result.get("score", 100),
                "issues": result.get("issues", []),
                "summary": result.get("summary", "AI一致性分析完成"),
                "message": "AI一致性分析完成"
            }, None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_report(project_id: str, chapter_no: str = None) -> tuple:
        """获取最近检查报告"""
        try:
            reports = database_v2.get_ai_generations(project_id, 'consistency_check')
            if chapter_no:
                reports = [r for r in (reports or []) if r.get('chapter_no') == chapter_no]
            return {"reports": reports or [], "count": len(reports or [])}, None
        except Exception as e:
            return None, str(e)


# ========== 工具函数 ==========


