"""SQLite 数据库扩展模块 — V2 18模块创作流水线的数据模型

包含13张新表,覆盖从灵感到完整小说创作的全流程。
独立于 database.py,通过 init_db_v2() 在启动时创建。
"""
import json
import os
import sqlite3
import threading
import time

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'))
V2_SCHEMA_VERSION = 1
_v2_lock = threading.RLock()


def _v2_now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _v2_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def init_db_v2():
    """初始化V2表结构(幂等,可重复调用)"""
    from .db_schema import V2_SCHEMA_DDL
    with _v2_lock:
        conn = _v2_db()
        conn.executescript(V2_SCHEMA_DDL)

        # 迁移: 添加 deleted_at 列(软删除支持)
        v2_tables = [
            'v2_ideas', 'v2_projects', 'v2_world_buildings', 'v2_characters',
            'v2_relation_maps', 'v2_story_systems', 'v2_power_systems', 'v2_factions',
            'v2_timelines', 'v2_volumes', 'v2_plot_nodes', 'v2_chapter_plans',
            'v2_scenes', 'v2_foreshadowings', 'v2_knowledge_states', 'v2_drafts',
            'v2_consistency_reports', 'v2_ai_generations', 'v2_pipeline_states'
        ]
        for table in v2_tables:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at TEXT DEFAULT NULL")
            except Exception:
                pass  # 列已存在

        # 迁移: v2 schema 新增列 (power_system, factions, timeline_*, scene_designs)
        from .db_schema import V2_SCHEMA_MIGRATIONS
        for mig in V2_SCHEMA_MIGRATIONS:
            try:
                conn.execute(mig)
            except Exception:
                pass  # 列已存在

        # 迁移: v2_ideas 添加 project_id UNIQUE 约束
        try:
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_ideas_project_unique ON v2_ideas(project_id)")
        except Exception:
            pass

        conn.commit()
        conn.close()


# ========== V2 JSON 辅助 ==========

def _j(obj):
    """安全JSON序列化"""
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, ensure_ascii=False) if obj else '{}'


def _jd(s, default=None):
    """安全JSON反序列化(兼容纯字符串)"""
    if not s:
        return default if default is not None else {}
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return s  # 兼容纯字符串值


def _jl(s):
    """安全JSON反序列化为list"""
    try:
        return json.loads(s) if s else []
    except (json.JSONDecodeError, TypeError):
        return []


# ========== 灵感 CRUD ==========

def save_idea(project_id, data):
    """保存或更新灵感"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_ideas (project_id, user_input, genre_hint, reference_works, candidates,
                selected_concept, core_selling_points, target_audience, risks,
                sustainability_estimate, total_score, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                user_input=excluded.user_input, genre_hint=excluded.genre_hint,
                reference_works=excluded.reference_works, candidates=excluded.candidates,
                selected_concept=excluded.selected_concept, core_selling_points=excluded.core_selling_points,
                target_audience=excluded.target_audience, risks=excluded.risks,
                sustainability_estimate=excluded.sustainability_estimate, total_score=excluded.total_score,
                status=excluded.status, updated_at=excluded.updated_at
        """, (project_id, data.get('user_input', ''), data.get('genre_hint', ''),
              _j(data.get('reference_works', [])), _j(data.get('candidates', [])),
              data.get('selected_concept', ''), _j(data.get('core_selling_points', [])),
              _j(data.get('target_audience', {})), _j(data.get('risks', [])),
              data.get('sustainability_estimate', ''), data.get('total_score', 0),
              data.get('status', 'draft'), now, now))
        conn.commit()
        conn.close()


def get_idea(project_id):
    """获取项目灵感"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_ideas WHERE project_id=? ORDER BY id DESC LIMIT 1", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['reference_works'] = _jl(d.get('reference_works', '[]'))
    d['candidates'] = _jl(d.get('candidates', '[]'))
    d['core_selling_points'] = _jl(d.get('core_selling_points', '[]'))
    d['target_audience'] = _jd(d.get('target_audience', '{}'))
    d['risks'] = _jl(d.get('risks', '[]'))
    return d


# ========== 项目定位 CRUD ==========

def save_project_detail(project_id, data):
    """保存项目定位详情"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_projects (project_id, idea_id, platform_choice, project_overview,
                novel_position, platform_config, audience, commercial, style, pace,
                innovation, content_boundary, wordcount_plan, update_plan, risks,
                derived_fields, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                idea_id=excluded.idea_id, platform_choice=excluded.platform_choice,
                project_overview=excluded.project_overview, novel_position=excluded.novel_position,
                platform_config=excluded.platform_config, audience=excluded.audience,
                commercial=excluded.commercial, style=excluded.style, pace=excluded.pace,
                innovation=excluded.innovation, content_boundary=excluded.content_boundary,
                wordcount_plan=excluded.wordcount_plan, update_plan=excluded.update_plan,
                risks=excluded.risks, derived_fields=excluded.derived_fields,
                updated_at=excluded.updated_at
        """, (project_id, data.get('idea_id', 0), data.get('platform_choice', 'tomato'),
              data.get('project_overview', ''), _j(data.get('novel_position', {})),
              _j(data.get('platform_config', {})), _j(data.get('audience', {})),
              _j(data.get('commercial', {})), _j(data.get('style', {})),
              _j(data.get('pace', {})), _j(data.get('innovation', [])),
              _j(data.get('content_boundary', [])), _j(data.get('wordcount_plan', {})),
              _j(data.get('update_plan', {})), _j(data.get('risks', [])),
              _j(data.get('derived_fields', {})), now, now))
        conn.commit()
        conn.close()


def get_project_detail(project_id):
    """获取项目定位详情"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_projects WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    for key in ['novel_position', 'platform_config', 'audience', 'commercial', 'style', 'pace',
                'wordcount_plan', 'update_plan', 'derived_fields']:
        d[key] = _jd(d.get(key, '{}'), {})
    for key in ['innovation', 'content_boundary', 'risks']:
        d[key] = _jl(d.get(key, '[]'))
    return d


# ========== 世界观 CRUD ==========

def save_world(project_id, data):
    """保存世界观"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_world_buildings (project_id, origin, rules, structure, civilization,
                history, doc_path, world_foreshadows, power_system, factions, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                origin=excluded.origin, rules=excluded.rules, structure=excluded.structure,
                civilization=excluded.civilization, history=excluded.history,
                doc_path=excluded.doc_path, world_foreshadows=excluded.world_foreshadows,
                power_system=excluded.power_system, factions=excluded.factions,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('origin', {})), _j(data.get('rules', [])),
              _j(data.get('structure', {})), _j(data.get('civilization', {})),
              _j(data.get('history', [])), data.get('doc_path', ''),
              _j(data.get('world_foreshadows', [])),
              _j(data.get('power_system', {})), _j(data.get('factions', [])),
              now, now))
        conn.commit()
        conn.close()


def get_world(project_id):
    """获取世界观"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_world_buildings WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['origin'] = _jd(d.get('origin', '{}'), {})
    d['rules'] = _jl(d.get('rules', '[]'))
    d['structure'] = _jd(d.get('structure', '{}'), {})
    d['civilization'] = _jd(d.get('civilization', '{}'), {})
    d['history'] = _jl(d.get('history', '[]'))
    d['world_foreshadows'] = _jl(d.get('world_foreshadows', '[]'))
    d['power_system'] = _jd(d.get('power_system', '{}'), {})
    d['factions'] = _jl(d.get('factions', '[]'))
    return d


# ========== 角色 CRUD ==========

def save_character(project_id, char_id, data):
    """保存角色"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_characters (project_id, char_id, role_type, name, doc_path,
                profile, appearance, personality, abilities, growth_route,
                initial_relations, initial_psychology, initial_state, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, char_id) DO UPDATE SET
                role_type=excluded.role_type, name=excluded.name, doc_path=excluded.doc_path,
                profile=excluded.profile, appearance=excluded.appearance,
                personality=excluded.personality, abilities=excluded.abilities,
                growth_route=excluded.growth_route, initial_relations=excluded.initial_relations,
                initial_psychology=excluded.initial_psychology, initial_state=excluded.initial_state,
                updated_at=excluded.updated_at
        """, (project_id, char_id, data.get('role_type', 'supporting'),
              data.get('name', ''), data.get('doc_path', ''),
              _j(data.get('profile', {})), _j(data.get('appearance', {})),
              _j(data.get('personality', {})), _j(data.get('abilities', {})),
              _j(data.get('growth_route', [])), _j(data.get('initial_relations', [])),
              _j(data.get('initial_psychology', {})), _j(data.get('initial_state', {})),
              now, now))
        conn.commit()
        conn.close()


def get_character(project_id, char_id):
    """获取单个角色"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_characters WHERE project_id=? AND char_id=?",
                          (project_id, char_id)).fetchone()
        conn.close()
    return _parse_character(row) if row else None


def get_all_characters(project_id):
    """获取项目所有角色"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_characters WHERE project_id=? ORDER BY id",
                          (project_id,)).fetchall()
        conn.close()
    return [_parse_character(r) for r in rows]


def _parse_character(row):
    """解析角色JSON字段"""
    d = dict(row)
    for key in ['profile', 'appearance', 'personality', 'abilities', 'initial_psychology', 'initial_state']:
        d[key] = _jd(d.get(key, '{}'), {})
    d['growth_route'] = _jl(d.get('growth_route', '[]'))
    d['initial_relations'] = _jl(d.get('initial_relations', '[]'))
    return d


def save_relation_map(project_id, data):
    """保存关系网络"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_relation_maps (project_id, nodes, edges, role_groups, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                nodes=excluded.nodes, edges=excluded.edges, role_groups=excluded.role_groups,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('nodes', [])), _j(data.get('edges', [])),
              _j(data.get('role_groups', {})), now))
        conn.commit()
        conn.close()


def get_relation_map(project_id):
    """获取关系网络"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_relation_maps WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['nodes'] = _jl(d.get('nodes', '[]'))
    d['edges'] = _jl(d.get('edges', '[]'))
    d['role_groups'] = _jd(d.get('role_groups', '{}'), {})
    return d



# ========== 力量/势力/时间线 CRUD ==========

def save_power_system(*args, **kwargs):
    """[DEPRECATED] 力量体系 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "world", ...)', DeprecationWarning, stacklevel=2)
    return None

def get_power_system(*args, **kwargs):
    """[DEPRECATED] 力量体系 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "world", ...)', DeprecationWarning, stacklevel=2)
    return None

def save_faction(*args, **kwargs):
    """[DEPRECATED] 势力 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "world", ...)', DeprecationWarning, stacklevel=2)
    return None

def get_factions(*args, **kwargs):
    """[DEPRECATED] 势力 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "world", ...)', DeprecationWarning, stacklevel=2)
    return None

def save_timeline(*args, **kwargs):
    """[DEPRECATED] 时间线 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "architecture", ...)', DeprecationWarning, stacklevel=2)
    return None

def get_timeline(*args, **kwargs):
    """[DEPRECATED] 时间线 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "architecture", ...)', DeprecationWarning, stacklevel=2)
    return None

# ========== 卷纲/剧情节点/章节/场景 CRUD ==========

def save_volume(project_id, volume_no, data):
    """保存卷纲"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_volumes (project_id, volume_no, name, target_words, chapter_count,
                protagonist_start, protagonist_end, key_events, volume_foreshadows,
                cliffhanger, consistency_status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, volume_no) DO UPDATE SET
                name=excluded.name, target_words=excluded.target_words,
                chapter_count=excluded.chapter_count, protagonist_start=excluded.protagonist_start,
                protagonist_end=excluded.protagonist_end, key_events=excluded.key_events,
                volume_foreshadows=excluded.volume_foreshadows,
                cliffhanger=excluded.cliffhanger,
                consistency_status=excluded.consistency_status,
                updated_at=excluded.updated_at
        """, (project_id, volume_no, data.get('name', ''),
              data.get('target_words', 250000), data.get('chapter_count', 100),
              _j(data.get('protagonist_start', {})), _j(data.get('protagonist_end', {})),
              _j(data.get('key_events', [])), _j(data.get('volume_foreshadows', [])),
              data.get('cliffhanger', ''), _j(data.get('consistency_status', {})),
              now, now))
        conn.commit()
        conn.close()


def get_volumes(project_id):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_volumes WHERE project_id=? ORDER BY volume_no",
                          (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['protagonist_start'] = _jd(d.get('protagonist_start', '{}'), {})
        d['protagonist_end'] = _jd(d.get('protagonist_end', '{}'), {})
        d['key_events'] = _jl(d.get('key_events', '[]'))
        d['volume_foreshadows'] = _jl(d.get('volume_foreshadows', '[]'))
        d['consistency_status'] = _jd(d.get('consistency_status', '{}'), {})
        result.append(d)
    return result


def save_plot_node(*args, **kwargs):
    """[DEPRECATED] 剧情节点 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "architecture", ...)', DeprecationWarning, stacklevel=2)
    return None

def get_plot_nodes(*args, **kwargs):
    """[DEPRECATED] 剧情节点 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "architecture", ...)', DeprecationWarning, stacklevel=2)
    return None

def save_chapter_plan(project_id, chapter_no, data):
    """保存章节规划/细纲"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_chapter_plans (project_id, chapter_no, title, target_words,
                plot_nodes_covered, timeline_events, hook_type, cliffhanger,
                protagonist_level, locations, dialogue_ratio, pacing,
                foreshadows_to_add, foreshadows_to_recycle, emotion_curve,
                scenes, knowledge_update, scene_designs, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, chapter_no) DO UPDATE SET
                title=excluded.title, target_words=excluded.target_words,
                plot_nodes_covered=excluded.plot_nodes_covered,
                timeline_events=excluded.timeline_events, hook_type=excluded.hook_type,
                cliffhanger=excluded.cliffhanger, protagonist_level=excluded.protagonist_level,
                locations=excluded.locations, dialogue_ratio=excluded.dialogue_ratio,
                pacing=excluded.pacing, foreshadows_to_add=excluded.foreshadows_to_add,
                foreshadows_to_recycle=excluded.foreshadows_to_recycle,
                emotion_curve=excluded.emotion_curve, scenes=excluded.scenes,
                knowledge_update=excluded.knowledge_update,
                scene_designs=excluded.scene_designs, status=excluded.status,
                updated_at=excluded.updated_at
        """, (project_id, chapter_no, data.get('title', ''),
              data.get('target_words', 2000), _j(data.get('plot_nodes_covered', [])),
              _j(data.get('timeline_events', [])), data.get('hook_type', ''),
              data.get('cliffhanger', ''), data.get('protagonist_level', ''),
              _j(data.get('locations', [])), data.get('dialogue_ratio', 0.4),
              data.get('pacing', 'normal'), _j(data.get('foreshadows_to_add', [])),
              _j(data.get('foreshadows_to_recycle', [])), _j(data.get('emotion_curve', [])),
              _j(data.get('scenes', [])), _j(data.get('knowledge_update', {})),
              _j(data.get('scene_designs', [])),
              data.get('status', 'planned'), now, now))
        conn.commit()
        conn.close()


def get_chapter_plans(project_id):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_chapter_plans WHERE project_id=?  ORDER BY chapter_no",
                          (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        for key in ['plot_nodes_covered', 'timeline_events', 'locations',
                     'foreshadows_to_add', 'foreshadows_to_recycle', 'emotion_curve', 'scenes']:
            d[key] = _jl(d.get(key, '[]'))
        d['knowledge_update'] = _jd(d.get('knowledge_update', '{}'), {})
        result.append(d)
    return result


def save_scene(*args, **kwargs):
    """[DEPRECATED] 场景设计 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "chapter_plan", ...)', DeprecationWarning, stacklevel=2)
    return None

def get_scenes(*args, **kwargs):
    """[DEPRECATED] 场景设计 — 数据已合并，请通过 DataBridge 写入"""
    import warnings
    warnings.warn('use DataBridge.write(project_id, "chapter_plan", ...)', DeprecationWarning, stacklevel=2)
    return None

# ========== 伏笔 CRUD ==========

def save_foreshadow(project_id, foreshadow_id, data):
    """保存伏笔"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_foreshadowings (project_id, foreshadow_id, source_type, source_id,
                foreshadow_type, description, trigger_text, target_volume, target_chapter,
                status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, foreshadow_id) DO UPDATE SET
                source_type=excluded.source_type, source_id=excluded.source_id,
                foreshadow_type=excluded.foreshadow_type, description=excluded.description,
                trigger_text=excluded.trigger_text, target_volume=excluded.target_volume,
                target_chapter=excluded.target_chapter, status=excluded.status,
                updated_at=excluded.updated_at
        """, (project_id, foreshadow_id, data.get('source_type', ''),
              data.get('source_id', ''), data.get('foreshadow_type', ''),
              data.get('description', ''), data.get('trigger_text', ''),
              data.get('target_volume', 0), data.get('target_chapter', 0),
              data.get('status', 'active'), now, now))
        conn.commit()
        conn.close()


def get_foreshadows(project_id, status=None):
    with _v2_lock:
        conn = _v2_db()
        if status:
            rows = conn.execute("SELECT * FROM v2_foreshadowings WHERE project_id=? AND status=? ORDER BY id",
                              (project_id, status)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM v2_foreshadowings WHERE project_id=?  ORDER BY id",
                              (project_id,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]

def get_consistency_reports(project_id, limit=20):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute(
            "SELECT * FROM v2_consistency_reports WHERE project_id=? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit)).fetchall()
        conn.close()
    return [dict(r) for r in rows]



# ========== 知识库/一致性/草稿 CRUD ==========

def save_knowledge_state(project_id, data):
    """保存知识库快照"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_knowledge_states (project_id, character_states, world_state,
                plot_state, consistency_status, last_check_at, last_chapter_no,
                created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                character_states=excluded.character_states, world_state=excluded.world_state,
                plot_state=excluded.plot_state, consistency_status=excluded.consistency_status,
                last_check_at=excluded.last_check_at, last_chapter_no=excluded.last_chapter_no,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('character_states', {})),
              _j(data.get('world_state', {})), _j(data.get('plot_state', {})),
              _j(data.get('consistency_status', {})),
              data.get('last_check_at', ''), data.get('last_chapter_no', ''),
              now, now))
        conn.commit()
        conn.close()




def mark_module_done(project_id, module_name):
    """Mark a pipeline module as done (upsert)"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        existing = conn.execute("SELECT id FROM v2_pipeline_states WHERE project_id=? AND module_name=?", (project_id, module_name)).fetchone()
        if existing:
            conn.execute("UPDATE v2_pipeline_states SET status='done', completed_at=?, updated_at=? WHERE project_id=? AND module_name=?", (now, now, project_id, module_name))
        else:
            conn.execute("INSERT INTO v2_pipeline_states (project_id, module_name, status, completed_at, updated_at, data_json) VALUES (?,?,?,?,?,?)", (project_id, module_name, 'done', now, now, '{}'))
        conn.commit()
        conn.close()

def get_knowledge_state(project_id):
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_knowledge_states WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    for key in ['character_states', 'world_state', 'plot_state', 'consistency_status']:
        d[key] = _jd(d.get(key, '{}'), {})
    return d


def save_consistency_report(project_id, data):
    """保存一致性检查报告"""
    with _v2_lock:
        conn = _v2_db()
        conn.execute("""
            INSERT INTO v2_consistency_reports (project_id, chapter_no, score,
                items, summary, fixes, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (project_id, data.get('chapter_no', ''), data.get('score', 1.0),
              _j(data.get('items', [])), data.get('summary', ''),
              _j(data.get('fixes', [])), _v2_now()))
        conn.commit()
        conn.close()


def save_draft(project_id, chapter_no, data):
    """保存草稿"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        word_count_raw = data.get('word_count_raw', len(data.get('content_raw', '')))
        word_count_final = data.get('word_count_final', len(data.get('content', '')))
        conn.execute("""
            INSERT INTO v2_drafts (project_id, chapter_no, scene_id, content, content_raw,
                word_count_raw, word_count_final, polish_status, foreshadow_added,
                continuity_check, version, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (project_id, chapter_no, data.get('scene_id', ''),
              data.get('content', ''), data.get('content_raw', ''),
              word_count_raw, word_count_final,
              data.get('polish_status', 'draft'),
              _j(data.get('foreshadow_added', [])),
              _j(data.get('continuity_check', {})),
              data.get('version', 1), now, now))
        conn.commit()
        conn.close()


def get_drafts(project_id):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_drafts WHERE project_id=?  ORDER BY chapter_no",
                          (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['foreshadow_added'] = _jl(d.get('foreshadow_added', '[]'))
        d['continuity_check'] = _jd(d.get('continuity_check', '{}'), {})
        result.append(d)
    return result


# ========== AI生成日志 ==========

def log_ai_generation(project_id, data):
    """记录AI生成"""
    with _v2_lock:
        conn = _v2_db()
        conn.execute("""
            INSERT INTO v2_ai_generations (project_id, module_name, entity_type,
                entity_id, prompt_hash, prompt_text, response_text, model_used,
                tokens_input, tokens_output, duration_ms, status, error_message, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (project_id, data.get('module_name', ''), data.get('entity_type', ''),
              data.get('entity_id', ''), data.get('prompt_hash', ''),
              data.get('prompt_text', ''), data.get('response_text', ''),
              data.get('model_used', ''), data.get('tokens_input', 0),
              data.get('tokens_output', 0), data.get('duration_ms', 0),
              data.get('status', 'success'), data.get('error_message', ''),
              _v2_now()))
        conn.commit()
        conn.close()


def get_ai_generations(project_id, module_name=None, limit=100):
    with _v2_lock:
        conn = _v2_db()
        if module_name:
            rows = conn.execute(
                "SELECT * FROM v2_ai_generations WHERE project_id=? AND module_name=? ORDER BY id DESC LIMIT ?",
                (project_id, module_name, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM v2_ai_generations WHERE project_id=? ORDER BY id DESC LIMIT ?",
                (project_id, limit)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


# ========== 级联删除 ==========

def save_pipeline_state(project_id, module_name, data):
    """保存或更新流水线模块状态(含完整数据JSON)"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        module_data = _j(data.get('module_data', data))

        # 查询现有状态,保存数据时不意外覆盖 locked/done 等状态
        existing = conn.execute(
            "SELECT status FROM v2_pipeline_states WHERE project_id=? AND module_name=?",
            (project_id, module_name)
        ).fetchone()

        if 'status' in data:
            new_status = data['status']
        elif existing:
            new_status = existing[0]
        else:
            new_status = 'pending'

        conn.execute("""
            INSERT INTO v2_pipeline_states (project_id, module_name, status, retry_count,
                error, consistency_score, started_at, completed_at, updated_at, data_json)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, module_name) DO UPDATE SET
                status=excluded.status, retry_count=excluded.retry_count,
                error=excluded.error, consistency_score=excluded.consistency_score,
                started_at=excluded.started_at, completed_at=excluded.completed_at,
                updated_at=excluded.updated_at, data_json=excluded.data_json
        """, (project_id, module_name, new_status,
              data.get('retry_count', 0), data.get('error', ''),
              data.get('consistency_score', 0), data.get('started_at', ''),
              data.get('completed_at', ''), now, module_data))
        conn.commit()
        conn.close()


def get_pipeline_module_data(project_id, module_name):
    """读取模块完整数据JSON"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute(
            "SELECT data_json FROM v2_pipeline_states WHERE project_id=? AND module_name=?",
            (project_id, module_name)).fetchone()
        conn.close()
    if row and row[0]:
        return _jd(row[0], {})
    return None


def get_pipeline_state(project_id):
    """获取项目所有流水线模块状态"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_pipeline_states WHERE project_id=?", (project_id,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def delete_project_v2(project_id):
    """软删除项目所有V2数据（标记 deleted_at）"""
    tables = [
        'v2_ideas', 'v2_projects', 'v2_world_buildings', 'v2_characters',
        'v2_relation_maps', 'v2_story_systems', 'v2_power_systems', 'v2_factions',
        'v2_timelines', 'v2_volumes', 'v2_plot_nodes', 'v2_chapter_plans',
        'v2_scenes', 'v2_foreshadowings', 'v2_knowledge_states', 'v2_drafts',
        'v2_consistency_reports', 'v2_ai_generations', 'v2_pipeline_states'
    ]
    now = _v2_now()
    with _v2_lock:
        conn = _v2_db()
        for table in tables:
            try:
                conn.execute(f"UPDATE {table} SET deleted_at=? WHERE project_id=? AND deleted_at IS NULL", (now, project_id))
            except Exception:
                # 表可能没有 deleted_at 列，回退到硬删除
                conn.execute(f"DELETE FROM {table} WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


def hard_delete_project_v2(project_id):
    """硬删除项目所有V2数据（用于30天后的垃圾回收）"""
    tables = [
        'v2_ideas', 'v2_projects', 'v2_world_buildings', 'v2_characters',
        'v2_relation_maps', 'v2_story_systems', 'v2_power_systems', 'v2_factions',
        'v2_timelines', 'v2_volumes', 'v2_plot_nodes', 'v2_chapter_plans',
        'v2_scenes', 'v2_foreshadowings', 'v2_knowledge_states', 'v2_drafts',
        'v2_consistency_reports', 'v2_ai_generations', 'v2_pipeline_states'
    ]
    with _v2_lock:
        conn = _v2_db()
        for table in tables:
            conn.execute(f"DELETE FROM {table} WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


# ── Settings (模型配置持久化) ──────────────────────────────────────

def get_setting(key: str) -> str | None:
    """获取单个设置值"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close()
    return row['value'] if row else None


def set_setting(key: str, value: str):
    """设置单个键值（若不存在则插入，存在则更新）"""
    with _v2_lock:
        conn = _v2_db()
        conn.execute(
            "INSERT INTO settings(key, value, updated_at) VALUES(?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, _v2_now())
        )
        conn.commit()
        conn.close()


def get_all_settings() -> dict:
    """获取所有设置"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        conn.close()
    return {r['key']: r['value'] for r in rows}


# ── 灵感离线模板 ─────────────────────────────────────────────────

def create_idea_template(project_id: str, name: str, genre: str, prompt: str,
                         icon: str = '💡', reference: str = '') -> dict:
    """创建灵感模板"""
    with _v2_lock:
        conn = _v2_db()
        try:
            cur = conn.execute(
                "INSERT INTO idea_templates(project_id, name, icon, genre, prompt, reference) VALUES(?,?,?,?,?,?)",
                (project_id, name, icon, genre, prompt, reference)
            )
            tid = cur.lastrowid
            row = conn.execute("SELECT * FROM idea_templates WHERE id=?", (tid,)).fetchone()
            conn.commit()
            return dict(row)
        except sqlite3.IntegrityError:
            raise ValueError("模板名称已存在")
        finally:
            conn.close()


def get_idea_templates(project_id: str) -> list:
    """获取项目的模板列表（按updated_at倒序）"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute(
            "SELECT * FROM idea_templates WHERE project_id=? ORDER BY updated_at DESC",
            (project_id,)
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def get_idea_template(template_id: int) -> dict | None:
    """获取单个模板"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM idea_templates WHERE id=?", (template_id,)).fetchone()
        conn.close()
    return dict(row) if row else None


def update_idea_template(template_id: int, **fields) -> dict:
    """更新模板"""
    allowed = {'name', 'icon', 'genre', 'prompt', 'reference'}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        raise ValueError("无有效更新字段")
    updates['updated_at'] = _v2_now()
    set_clause = ', '.join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [template_id]
    with _v2_lock:
        conn = _v2_db()
        conn.execute(f"UPDATE idea_templates SET {set_clause} WHERE id=?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM idea_templates WHERE id=?", (template_id,)).fetchone()
        conn.close()
    return dict(row) if row else None


def delete_idea_template(template_id: int) -> bool:
    """删除模板"""
    with _v2_lock:
        conn = _v2_db()
        cur = conn.execute("DELETE FROM idea_templates WHERE id=?", (template_id,))
        conn.commit()
        conn.close()
    return cur.rowcount > 0


# ========== 生成模板库（全模块） ==========

def save_generation_template(
    name: str,
    module_key: str,
    output_data: any,
    input_context: any = None,
    entity_refs: any = None,
    compatibility_group: str = '',
    source_project_id: str = '',
    genre: str = '',
    sub_genre: str = '',
    tone: str = '',
    world_type: str = '',
    target_audience: str = '',
    input_fingerprint: str = '',
    is_public: bool = False,
) -> dict:
    """保存AI生成结果为模板"""
    with _v2_lock:
        conn = _v2_db()
        try:
            cur = conn.execute("""
                INSERT INTO v2_generation_templates
                    (name, module_key, genre, sub_genre, tone, world_type, target_audience,
                     source_project_id, input_fingerprint, output_data, input_context,
                     entity_refs, compatibility_group, is_public)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                name, module_key, genre, sub_genre, tone, world_type, target_audience,
                source_project_id, input_fingerprint,
                _j(output_data), _j(input_context or {}), _j(entity_refs or {}),
                compatibility_group, 1 if is_public else 0,
            ))
            tid = cur.lastrowid
            row = conn.execute("SELECT * FROM v2_generation_templates WHERE id=?", (tid,)).fetchone()
            conn.commit()
            return dict(row)
        finally:
            conn.close()


def get_generation_template(template_id: int) -> dict | None:
    """获取单个生成模板"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_generation_templates WHERE id=?", (template_id,)).fetchone()
        conn.close()
    return dict(row) if row else None


def list_generation_templates(
    module_key: str = None,
    genre: str = None,
    world_type: str = None,
    compatibility_group: str = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """查询生成模板列表（支持筛选）"""
    conditions = []
    params = []
    if module_key:
        conditions.append("module_key=?")
        params.append(module_key)
    if genre:
        conditions.append("genre=?")
        params.append(genre)
    if world_type:
        conditions.append("world_type=?")
        params.append(world_type)
    if compatibility_group:
        conditions.append("compatibility_group=?")
        params.append(compatibility_group)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute(
            f"SELECT * FROM v2_generation_templates {where} ORDER BY usage_count DESC, created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset]
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def update_generation_template(template_id: int, **fields) -> dict | None:
    """更新生成模板"""
    allowed = {'name', 'genre', 'sub_genre', 'tone', 'world_type', 'target_audience',
               'is_public', 'quality_rating'}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        raise ValueError("无有效更新字段")
    if 'is_public' in updates:
        updates['is_public'] = 1 if updates['is_public'] else 0
    updates['updated_at'] = _v2_now()
    set_clause = ', '.join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [template_id]
    with _v2_lock:
        conn = _v2_db()
        try:
            conn.execute(f"UPDATE v2_generation_templates SET {set_clause} WHERE id=?", values)
            conn.commit()
            row = conn.execute("SELECT * FROM v2_generation_templates WHERE id=?", (template_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()


def delete_generation_template(template_id: int) -> bool:
    """删除生成模板"""
    with _v2_lock:
        conn = _v2_db()
        cur = conn.execute("DELETE FROM v2_generation_templates WHERE id=?", (template_id,))
        conn.commit()
        conn.close()
    return cur.rowcount > 0


def increment_template_usage(template_id: int):
    """增加模板复用次数"""
    with _v2_lock:
        conn = _v2_db()
        conn.execute("UPDATE v2_generation_templates SET usage_count = usage_count + 1 WHERE id=?", (template_id,))
        conn.commit()
        conn.close()


def get_compatibility_group_templates(compat_group: str) -> list:
    """获取同一兼容组的所有模板"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute(
            "SELECT * FROM v2_generation_templates WHERE compatibility_group=? ORDER BY module_key",
            (compat_group,)
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def get_project_templates(project_id: str) -> list:
    """获取指定项目的所有生成模板"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute(
            "SELECT * FROM v2_generation_templates WHERE source_project_id=? ORDER BY created_at DESC",
            (project_id,)
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def save_drafts_batch(project_id, chapters_data):
    """批量保存草稿 — chapters_data格式: {"1": {"title":"...", "content":"...", "char_count":3000}, ...}"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        for ch_num, ch in chapters_data.items():
            content = ch.get('content', '') or ch.get('content_raw', '')
            word_count = ch.get('char_count', len(content))
            existing = conn.execute(
                "SELECT id FROM v2_drafts WHERE project_id=? AND chapter_no=?",
                (project_id, str(ch_num))
            ).fetchone()
            if existing:
                conn.execute("""
                    UPDATE v2_drafts SET
                        content=?, content_raw=?, word_count_raw=?, word_count_final=?,
                        chapter_no=?, updated_at=?
                    WHERE project_id=? AND chapter_no=?
                """, (content, content, word_count, word_count,
                      str(ch_num), now, project_id, str(ch_num)))
            else:
                conn.execute("""
                    INSERT INTO v2_drafts (project_id, chapter_no, scene_id, content, content_raw,
                        word_count_raw, word_count_final, polish_status, foreshadow_added,
                        continuity_check, version, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (project_id, str(ch_num), ch.get('scene_id', ''),
                      content, content, word_count, word_count,
                      'draft', '[]', '{}', 1, now, now))
        conn.commit()
        conn.close()
