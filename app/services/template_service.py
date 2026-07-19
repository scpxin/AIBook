"""生成模板服务 — 实体提取、自动保存、匹配引擎"""
import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger('novel_creator.service.template')


def _extract_entities(module_key: str, data: Any) -> dict[str, Any]:
    """从AI生成结果中提取关键实体引用"""
    if not data:
        return {}

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return {}

    if not isinstance(data, dict):
        return {}

    entities = {}

    if module_key == 'world':
        wb = data.get('world_building', data)
        if isinstance(wb, dict):
            entities['world_type'] = wb.get('world_type', wb.get('worldType', ''))
            entities['locations'] = wb.get('locations', wb.get('territories', []))
            if isinstance(entities['locations'], str):
                entities['locations'] = [l.strip() for l in entities['locations'].split('\n') if l.strip()]
            entities['factions'] = wb.get('factions_races', wb.get('races', []))
            if isinstance(entities['factions'], str):
                entities['factions'] = [f.strip() for f in entities['factions'].split('\n') if f.strip()]
            entities['power_system'] = wb.get('power_system_overview', wb.get('magic_system', ''))

    elif module_key == 'characters':
        chars = []
        for role_key in ['protagonist', 'supporting', 'villains', 'antagonists']:
            items = data.get(role_key, [])
            if isinstance(items, dict):
                items = [items]
            if isinstance(items, list):
                for c in items:
                    if isinstance(c, dict) and c.get('name'):
                        chars.append(c['name'])
        entities['characters'] = chars

    elif module_key == 'factions':
        fac_list = data.get('factions', [])
        if isinstance(fac_list, list):
            entities['faction_names'] = [f.get('name', '') for f in fac_list if isinstance(f, dict)]

    elif module_key == 'power_system':
        entities['system_type'] = data.get('system_type', data.get('systemType', ''))
        levels = data.get('levels', data.get('tiers', []))
        if isinstance(levels, str):
            entities['levels'] = [l.strip() for l in levels.split('\n') if l.strip()]
        elif isinstance(levels, list):
            entities['levels'] = [l.get('name', str(l)) if isinstance(l, dict) else str(l) for l in levels]

    elif module_key == 'story_architecture':
        entities['plot_nodes'] = data.get('plot_nodes', data.get('key_events', []))
        if isinstance(entities['plot_nodes'], list):
            entities['plot_nodes'] = [p.get('name', p.get('event', '')) if isinstance(p, dict) else str(p) for p in entities['plot_nodes']]

    elif module_key == 'outline':
        chapters = data.get('chapters', data.get('outline', []))
        if isinstance(chapters, list):
            entities['chapter_titles'] = [c.get('title', c.get('name', '')) if isinstance(c, dict) else str(c) for c in chapters]

    elif module_key == 'volumes':
        vols = data.get('volumes', data if isinstance(data, list) else [])
        if isinstance(vols, list):
            entities['volume_names'] = [v.get('name', v.get('title', '')) if isinstance(v, dict) else str(v) for v in vols]

    elif module_key == 'chapter_plan':
        plans = data.get('chapterPlans', data.get('plans', []))
        if isinstance(plans, list):
            entities['chapter_count'] = len(plans)

    elif module_key == 'scene_design':
        scenes = data.get('scenes', [])
        if isinstance(scenes, list):
            entities['scene_locations'] = [s.get('location', s.get('place', '')) if isinstance(s, dict) else '' for s in scenes]

    elif module_key == 'timeline':
        events = data.get('events', data.get('timeline', []))
        if isinstance(events, list):
            entities['event_count'] = len(events)

    return entities


def compute_input_fingerprint(input_context: dict) -> str:
    """计算输入上下文指纹（用于判断模板是否适用于当前输入）"""
    key_fields = ['genre', 'world_type', 'sub_genre', 'tone', 'target_audience']
    sig = {k: input_context.get(k, '') for k in key_fields}
    return hashlib.md5(json.dumps(sig, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def auto_save_template(
    project_id: str,
    module_key: str,
    module_data: Any,
    input_context: dict = None,
    existing_compat_group: str = '',
) -> dict | None:
    """AI生成成功后自动保存为模板（非阻塞异常处理）"""
    try:
        from novel_creator.database_v2 import (
            save_generation_template,
        )

        entities = _extract_entities(module_key, module_data)

        if not existing_compat_group:
            existing_compat_group = f"compat_{project_id}_{int(time.time())}"

        ctx = input_context or {}
        # Supplement context from extracted entities (so world_type is always populated)
        if not ctx.get('world_type') and entities.get('world_type'):
            wt_val = entities['world_type']
            ctx['world_type'] = wt_val if isinstance(wt_val, str) else str(wt_val)

        name = _auto_generate_name(module_key, ctx, entities)

        template = save_generation_template(
            name=name,
            module_key=module_key,
            output_data=module_data,
            input_context=ctx,
            entity_refs=entities,
            compatibility_group=existing_compat_group,
            source_project_id=project_id,
            genre=ctx.get('genre', ''),
            sub_genre=ctx.get('sub_genre', ''),
            tone=ctx.get('tone', ''),
            world_type=ctx.get('world_type', ''),
            target_audience=ctx.get('target_audience', ''),
            input_fingerprint=compute_input_fingerprint(ctx),
        )

        logger.info(f"自动保存模板: project={project_id}, module={module_key}, template_id={template['id']}")
        return template

    except Exception as e:
        logger.warning(f"自动保存模板失败（不影响主流程）: {e}")
        return None


def _auto_generate_name(module_key: str, ctx: dict, entities: dict) -> str:
    """自动生成模板名称"""
    genre = ctx.get('genre', '通用')
    module_names = {
        'world': '世界观',
        'characters': '角色',
        'factions': '势力',
        'power_system': '力量体系',
        'story_architecture': '故事架构',
        'outline': '全书大纲',
        'volumes': '卷纲',
        'chapter_plan': '章节规划',
        'chapter_outline': '章节细纲',
        'scene_design': '场景设计',
        'plot_nodes': '剧情节点',
        'timeline': '时间线',
        'idea': '灵感',
        'project': '项目定位',
        'draft_generation': '正文',
    }
    module_name = module_names.get(module_key, module_key)
    world_type = ctx.get('world_type', '')
    if world_type:
        return f"{genre}-{world_type}-{module_name}"
    sub_genre = ctx.get('sub_genre', '')
    if sub_genre:
        return f"{genre}-{sub_genre}-{module_name}"
    return f"{genre}-{module_name}"


def match_templates_strict(
    candidate_template: dict,
    project_context: dict,
    selected_templates: dict[str, str],
    all_templates: list[dict],
) -> dict:
    """严格模式模板匹配"""
    score = 0

    # 1. 世界类型冲突检查
    if candidate_template.get('world_type') and project_context.get('world_type'):
        if candidate_template['world_type'] != project_context['world_type']:
            return {
                'template': candidate_template,
                'score': 0,
                'is_compatible': False,
                'reason': f'世界类型不匹配：模板为"{candidate_template["world_type"]}"，当前项目为"{project_context["world_type"]}"'
            }

    # 2. 受众类型冲突
    if candidate_template.get('target_audience') and project_context.get('target_audience'):
        if candidate_template['target_audience'] != project_context['target_audience']:
            return {
                'template': candidate_template,
                'score': 0,
                'is_compatible': False,
                'reason': f'受众类型不匹配：模板为"{candidate_template["target_audience"]}"，当前项目为"{project_context["target_audience"]}"'
            }

    # 3. 与已选模板的实体引用冲突检查
    for sel_module_key, sel_tpl_id in selected_templates.items():
        if not sel_tpl_id:
            continue
        sel_tpl = next((t for t in all_templates if str(t.get('id')) == str(sel_tpl_id)), None)
        if not sel_tpl:
            continue

        # 同一兼容组直接放行
        if (candidate_template.get('compatibility_group') and
                candidate_template['compatibility_group'] == sel_tpl.get('compatibility_group')):
            continue

        # 实体引用冲突检测
        cand_entities = _jd_safe(candidate_template.get('entity_refs', '{}'))
        sel_entities = _jd_safe(sel_tpl.get('entity_refs', '{}'))

        if _has_entity_conflict(candidate_template['module_key'], cand_entities,
                                sel_module_key, sel_entities):
            return {
                'template': candidate_template,
                'score': 0,
                'is_compatible': False,
                'reason': f'与已选的{sel_module_key}模板数据冲突：存在风格或实体引用不兼容'
            }

    # 计算匹配分数
    selected_groups = set()
    for sel_tpl_id in selected_templates.values():
        if not sel_tpl_id:
            continue
        sel_tpl = next((t for t in all_templates if str(t.get('id')) == str(sel_tpl_id)), None)
        if sel_tpl and sel_tpl.get('compatibility_group'):
            selected_groups.add(sel_tpl['compatibility_group'])

    # 同兼容组优先 +40
    if candidate_template.get('compatibility_group') in selected_groups:
        score += 40

    # 题材一致 +25
    if candidate_template.get('genre') == project_context.get('genre'):
        score += 25

    # 世界类型一致 +20
    if candidate_template.get('world_type') and candidate_template.get('world_type') == project_context.get('world_type'):
        score += 20

    # 子类型一致 +20
    if candidate_template.get('sub_genre') == project_context.get('sub_genre'):
        score += 20

    # 风格一致 +15
    if candidate_template.get('tone') == project_context.get('tone'):
        score += 15

    # 质量加权
    rating = candidate_template.get('quality_rating', 0) or 0
    usage = candidate_template.get('usage_count', 0) or 0
    quality_factor = 0.5 + (rating / 10) if rating else 1.0
    usage_factor = min(1.5, 1.0 + (usage / 20))
    score = int(score * quality_factor * usage_factor)

    return {
        'template': candidate_template,
        'score': min(100, score),
        'is_compatible': True,
        'reason': None
    }


def _jd_safe(val):
    """安全解析JSON"""
    if isinstance(val, dict):
        return val
    if not val:
        return {}
    try:
        return json.loads(val) if isinstance(val, str) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _has_entity_conflict(module_a: str, entities_a: dict, module_b: str, entities_b: dict) -> bool:
    """检查两个模块的实体引用是否冲突"""
    type_dependent_pairs = {
        ('characters', 'world'): [('characters', 'world_type')],
        ('factions', 'world'): [('faction_names', 'world_type')],
        ('scene_design', 'characters'): [('scene_locations', 'characters')],
        ('outline', 'world'): [('chapter_titles', 'world_type')],
    }

    pair = type_dependent_pairs.get((module_a, module_b)) or type_dependent_pairs.get((module_b, module_a))
    if not pair:
        return False

    for field_a, field_b in pair:
        vals_a = entities_a.get(field_a, [])
        vals_b = entities_b.get(field_b, [])
        if vals_a and vals_b and not isinstance(vals_a, list):
            vals_a = [str(vals_a)]
        if vals_b and vals_b and not isinstance(vals_b, list):
            vals_b = [str(vals_b)]
        if vals_a and vals_b:
            return False

    return False


def apply_template_to_project(template_id: int, project_id: str) -> dict[str, Any]:
    """将模板数据应用到项目（不触发自动保存，直接写入数据库）"""
    from app.services.pipeline import (
        ModuleStatus,
        _get_project_lock,
        get_pipeline_state,
    )
    from novel_creator.database_v2 import (
        _v2_db,
        _v2_lock,
        _v2_now,
        get_generation_template,
        increment_template_usage,
    )

    tpl = get_generation_template(template_id)
    if not tpl:
        raise ValueError(f"模板不存在: {template_id}")

    module_key = tpl['module_key']
    output_data = json.loads(tpl.get('output_data', '{}'))

    # 直接写入 pipeline_state 表（不经过 save_module_data，避免触发自动存模板）
    now = _v2_now()
    data_json = json.dumps(output_data, ensure_ascii=False)

    lock = _get_project_lock(project_id)
    with lock:
        db_rows = get_pipeline_state(project_id)
        existing = next((r for r in db_rows if r["module_name"] == module_key), None)
        started_at = existing.get("started_at", "") if existing else now
        retry_count = existing.get("retry_count", 0) if existing else 0

        with _v2_lock:
            conn = _v2_db()
            try:
                conn.execute("""
                    INSERT INTO v2_pipeline_states
                        (project_id, module_name, status, retry_count, error,
                         consistency_score, started_at, completed_at, updated_at, data_json)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(project_id, module_name) DO UPDATE SET
                        status=excluded.status,
                        data_json=excluded.data_json,
                        completed_at=excluded.completed_at,
                        updated_at=excluded.updated_at
                """, (project_id, module_key, ModuleStatus.DONE.value, retry_count,
                      "", 0, started_at, now, now, data_json))
                conn.commit()
            finally:
                conn.close()

    # 解锁后续模块
    from app.services.pipeline import _unlock_dependents_db
    _unlock_dependents_db(project_id, module_key)

    # 增加复用计数
    increment_template_usage(template_id)

    return {
        'success': True,
        'module': module_key,
        'project_id': project_id,
        'template_id': template_id,
        'data': output_data,
        'applied_as': 'template'
    }


def seed_system_templates():
    """初始化系统预置模板 — 让新用户也有可用模板（幂等）"""
    from novel_creator.database_v2 import list_generation_templates, save_generation_template

    existing = list_generation_templates(limit=200)
    existing_names = {t['name'] for t in existing}
    if len(existing) >= 5:
        # 即使总数够，也检查预置模板是否都在
        preset_names = {'玄幻-东方修真-世界观模板', '都市-现代都市-世界观模板',
                        '玄幻-东方修真-修炼体系模板', '玄幻-东方修真-故事架构模板',
                        '都市-现代-故事架构模板', '玄幻-主角-角色设定模板'}
        if preset_names.issubset(existing_names):
            return

    presets = [
        {
            'name': '玄幻-东方修真-世界观模板',
            'module_key': 'world',
            'genre': '玄幻',
            'world_type': '东方',
            'tone': '热血',
            'target_audience': '男性',
            'input_context': {'genre': '玄幻', 'world_type': '东方', 'tone': '热血', 'target_audience': '男性'},
            'output_data': {
                '世界名称': '玄天大陆',
                '修炼体系': '炼气→筑基→金丹→元婴→化神→合体→大乘→渡劫',
                '地理格局': '东胜神洲、西牛贺洲、南赡部洲、北俱芦洲',
                '核心冲突': '正魔两道争夺飞升之路',
                '天道法则': '因果轮回，强者为尊',
            },
        },
        {
            'name': '都市-现代都市-世界观模板',
            'module_key': 'world',
            'genre': '都市',
            'world_type': '现代',
            'tone': '轻松',
            'target_audience': '女性',
            'input_context': {'genre': '都市', 'world_type': '现代', 'tone': '轻松', 'target_audience': '女性'},
            'output_data': {
                '城市设定': '繁华现代大都市',
                '社会背景': '当代都市职场与情感生活',
                '核心场景': '写字楼、咖啡厅、商圈',
                '生活节奏': '快节奏，高压，社交碎片化',
            },
        },
        {
            'name': '玄幻-东方修真-修炼体系模板',
            'module_key': 'power_system',
            'genre': '玄幻',
            'world_type': '东方',
            'tone': '热血',
            'target_audience': '男性',
            'input_context': {'genre': '玄幻', 'world_type': '东方', 'tone': '热血', 'target_audience': '男性'},
            'output_data': {
                '境界划分': '炼气→筑基→金丹→元婴→化神→合体→大乘→渡劫',
                '每层特点': '寿命翻倍、神通渐增、天劫降临',
                '修炼资源': '灵石、丹药、功法、法器',
                '瓶颈突破': '心境+机缘+丹药辅助',
            },
        },
        {
            'name': '玄幻-东方修真-故事架构模板',
            'module_key': 'story_architecture',
            'genre': '玄幻',
            'world_type': '东方',
            'tone': '热血',
            'target_audience': '男性',
            'input_context': {'genre': '玄幻', 'world_type': '东方', 'tone': '热血', 'target_audience': '男性'},
            'output_data': {
                '主线': '主角从凡人到飞升的修行之路',
                '开篇': '废柴逆袭/天才跌落/意外获得机缘',
                '核心矛盾': '正魔之争、资源争夺、天劫考验',
                '节奏': '修炼升级→冒险历练→境界突破→终极决战',
                '爽点设计': '越级挑战、扮猪吃虎、打脸反派',
            },
        },
        {
            'name': '都市-现代-故事架构模板',
            'module_key': 'story_architecture',
            'genre': '都市',
            'world_type': '现代',
            'tone': '轻松',
            'target_audience': '女性',
            'input_context': {'genre': '都市', 'world_type': '现代', 'tone': '轻松', 'target_audience': '女性'},
            'output_data': {
                '主线': '主角在职场与爱情中的成长故事',
                '开篇': '初入职场/公司危机/偶遇贵人',
                '核心矛盾': '职场竞争、爱情抉择、友情考验',
                '节奏': '日常→冲突→和解→成长',
                '情感线': '双向奔赴、互相救赎、甜虐交织',
            },
        },
        {
            'name': '玄幻-主角-角色设定模板',
            'module_key': 'characters',
            'genre': '玄幻',
            'world_type': '东方',
            'tone': '热血',
            'target_audience': '男性',
            'input_context': {'genre': '玄幻', 'world_type': '东方', 'tone': '热血', 'target_audience': '男性'},
            'output_data': {
                '主角': {'身份': '没落修仙家族子弟', '性格': '坚韧不拔、重情重义', '目标': '重振家族、证道长生'},
                '女主': {'身份': '正道宗门天才', '性格': '清冷高傲、内心柔软', '与主角关系': '亦敌亦友→携手共进'},
                '反派': {'身份': '魔道宗主', '性格': '野心勃勃、手段狠辣', '动机': '一统三界、打破天道'},
                '师父': {'身份': '隐世高人', '性格': '深谋远虑、护犊子', '作用': '传道授业、关键救援'},
            },
        },
    ]

    for preset in presets:
        try:
            save_generation_template(
                name=preset['name'],
                module_key=preset['module_key'],
                output_data=preset['output_data'],
                input_context=preset.get('input_context', {}),
                genre=preset.get('genre', ''),
                world_type=preset.get('world_type', ''),
                tone=preset.get('tone', ''),
                target_audience=preset.get('target_audience', ''),
                is_public=True,
            )
            logger.info(f'预置模板已创建: {preset["name"]}')
        except Exception as e:
            logger.warning(f'创建预置模板失败: {e}')
