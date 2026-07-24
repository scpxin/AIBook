"""DataBridge — 统一数据访问层

请求级连接复用 + 单入口读写。替换 database_v2.py 中分散的
_v2_lock / _v2_db() / 多套路由映射, 统一为 DataBridge.read() / DataBridge.write()。
"""
import json
import os
import sqlite3
import threading
from datetime import datetime

_local = threading.local()
_lock = threading.RLock()
DB_PATH = os.environ.get(
    'DB_PATH',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'),
)


class DataBridge:
    """统一数据访问层

    连接: 同一请求内复用一个 sqlite3 连接, 请求结束由 middleware 关闭
    写入: DataBridge.write(project_id, module_name, data)
    读取: DataBridge.read(project_id, module_name)
    全文: DataBridge.read_all(project_id, chapter_no=None)
    """

    WRITE_MAP = {
        "idea":         "_write_idea",
        "project":      "_write_project",
        "world":        "_write_world",
        "characters":   "_write_characters",
        "relation_map": "_write_relation_map",
        "architecture": "_write_architecture",
        "outline":      "_write_outline",
        "volumes":      "_write_volumes",
        "chapter_plan": "_write_chapter_plan",
        "chapter_outline": "_write_chapter_outline",
        "draft":        "_write_draft",
        "parse":        "_write_parse",
        "polish":       "_write_polish",
        "consistency":  "_write_consistency",
    }

    READ_MAP = {
        "idea":         "_read_idea",
        "project":      "_read_project",
        "world":        "_read_world",
        "characters":   "_read_characters",
        "relation_map": "_read_relation_map",
        "architecture": "_read_architecture",
        "outline":      "_read_outline",
        "volumes":      "_read_volumes",
        "chapter_plan": "_read_chapter_plan",
        "chapter_outline": "_read_chapter_outline",
        "draft":        "_read_draft",
        "parse":        "_read_parse",
        "polish":       "_read_polish",
        "consistency":  "_read_consistency",
    }

    @staticmethod
    def _conn():
        if not hasattr(_local, 'conn') or _local.conn is None:
            _local.conn = sqlite3.connect(DB_PATH, timeout=30)
            _local.conn.row_factory = sqlite3.Row
            _local.conn.execute("PRAGMA journal_mode=WAL")
            _local.conn.execute("PRAGMA synchronous=NORMAL")
            _local.conn.execute("PRAGMA busy_timeout=30000")
        return _local.conn

    @staticmethod
    def close():
        if hasattr(_local, 'conn') and _local.conn is not None:
            try:
                _local.conn.close()
            except Exception:
                pass
            _local.conn = None

    @staticmethod
    def write(project_id, module, data):
        with _lock:
            method_name = DataBridge.WRITE_MAP.get(module, "_write_generic")
            method = getattr(DataBridge, method_name, DataBridge._write_generic)
            return method(project_id, data)

    @staticmethod
    def _write_generic(project_id, data):
        pass

    # ========== M1: 灵感 ==========

    @staticmethod
    def _write_idea(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        conn.execute("""
            INSERT INTO v2_ideas (project_id, user_input, genre_hint, reference_works,
                candidates, selected_concept, core_selling_points, target_audience, risks,
                sustainability_estimate, total_score, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                user_input=excluded.user_input, genre_hint=excluded.genre_hint,
                reference_works=excluded.reference_works, candidates=excluded.candidates,
                selected_concept=excluded.selected_concept,
                core_selling_points=excluded.core_selling_points,
                target_audience=excluded.target_audience, risks=excluded.risks,
                sustainability_estimate=excluded.sustainability_estimate,
                total_score=excluded.total_score, status=excluded.status,
                updated_at=excluded.updated_at
        """, (project_id, str(data.get('user_input', '')), str(data.get('genre_hint', '')),
              _j(data.get('reference_works', [])), _j(data.get('candidates', [])),
              str(data.get('selected_concept', '')), _j(data.get('core_selling_points', [])),
              _j(data.get('target_audience', {})), _j(data.get('risks', [])),
              str(data.get('sustainability_estimate', '')), data.get('total_score', 0),
              str(data.get('status', 'draft')), now, now))
        conn.commit()

    # ========== M2: 项目定位 ==========

    @staticmethod
    def _write_project(project_id, data):
        conn = DataBridge._conn()
        now = _now()
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
        """, (project_id, data.get('idea_id', 0), str(data.get('platform_choice', 'tomato')),
              str(data.get('project_overview', '')), _j(data.get('novel_position', {})),
              _j(data.get('platform_config', {})), _j(data.get('audience', {})),
              _j(data.get('commercial', {})), _j(data.get('style', {})),
              _j(data.get('pace', {})), _j(data.get('innovation', [])),
              _j(data.get('content_boundary', [])), _j(data.get('wordcount_plan', {})),
              _j(data.get('update_plan', {})), _j(data.get('risks', [])),
              _j(data.get('derived_fields', {})), now, now))
        conn.commit()

    # ========== M3: 世界观体系 (读-改-写, 支持分步生成) ==========

    @staticmethod
    def _write_world(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        existing_raw = conn.execute(
            "SELECT * FROM v2_world_buildings WHERE project_id=?", (project_id,)).fetchone()
        existing = _deserialize_row(existing_raw) if existing_raw else {}
        merged = {**existing, **data}
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
        """, (project_id, _j(merged.get('origin', {})), _j(merged.get('rules', [])),
              _j(merged.get('structure', {})), _j(merged.get('civilization', {})),
              _j(merged.get('history', [])), str(merged.get('doc_path', '')),
              _j(merged.get('world_foreshadows', [])),
              _j(merged.get('power_system', {})), _j(merged.get('factions', [])),
              now, now))
        conn.commit()

    # ========== M4: 人物系统 (按 char_id UPSERT) ==========

    @staticmethod
    def _write_characters(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        chars = data if isinstance(data, list) else data.get('characters', data.get('items', []))
        for ch in chars:
            char_id = str(ch.get('char_id', ch.get('name', '')))
            if not char_id:
                continue
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
            """, (project_id, char_id, str(ch.get('role_type', 'supporting')),
                  str(ch.get('name', '')), str(ch.get('doc_path', '')),
                  _j(ch.get('profile', {})), _j(ch.get('appearance', {})),
                  _j(ch.get('personality', {})), _j(ch.get('abilities', {})),
                  _j(ch.get('growth_route', [])), _j(ch.get('initial_relations', [])),
                  _j(ch.get('initial_psychology', {})), _j(ch.get('initial_state', {})),
                  now, now))
        conn.commit()

    # ========== 关系网 ==========

    @staticmethod
    def _write_relation_map(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        conn.execute("""
            INSERT INTO v2_relation_maps (project_id, nodes, edges, role_groups, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                nodes=excluded.nodes, edges=excluded.edges, role_groups=excluded.role_groups,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('nodes', [])), _j(data.get('edges', [])),
              _j(data.get('role_groups', {})), now))
        conn.commit()

    # ========== M5: 故事架构+时间线 (读-改-写, 支持3步分步生成) ==========

    @staticmethod
    def _write_architecture(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        existing_raw = conn.execute(
            "SELECT * FROM v2_story_systems WHERE project_id=?", (project_id,)).fetchone()
        existing = _deserialize_row(existing_raw) if existing_raw else {}
        merged = {**existing, **data}
        conn.execute("""
            INSERT INTO v2_story_systems (project_id, summary, conflict_layers, theme,
                volume_cliffhangers, volumes_detail, total_plot_events,
                timeline_events, timeline_consistency, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                summary=excluded.summary, conflict_layers=excluded.conflict_layers,
                theme=excluded.theme, volume_cliffhangers=excluded.volume_cliffhangers,
                volumes_detail=excluded.volumes_detail, total_plot_events=excluded.total_plot_events,
                timeline_events=excluded.timeline_events, timeline_consistency=excluded.timeline_consistency,
                updated_at=excluded.updated_at
        """, (project_id, str(merged.get('summary', '')),
              _j(merged.get('conflict_layers', [])), str(merged.get('theme', '')),
              _j(merged.get('volume_cliffhangers', [])),
              _j(merged.get('volumes_detail', [])),
              _j(merged.get('total_plot_events', [])),
              _j(merged.get('timeline_events', [])),
              _j(merged.get('timeline_consistency', {})),
              now, now))
        conn.commit()

    # ========== M6: 全书大纲 ==========

    @staticmethod
    def _write_outline(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        conn.execute("""
            INSERT INTO v2_outlines (project_id, opening, rising_actions, subplots,
                midpoint_turn, climax, ending, chapters, emotional_curve, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                opening=excluded.opening, rising_actions=excluded.rising_actions,
                subplots=excluded.subplots, midpoint_turn=excluded.midpoint_turn,
                climax=excluded.climax, ending=excluded.ending,
                chapters=excluded.chapters, emotional_curve=excluded.emotional_curve,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('opening', {})),
              _j(data.get('rising_actions', [])), _j(data.get('subplots', [])),
              _j(data.get('midpoint_turn', {})), _j(data.get('climax', {})),
              _j(data.get('ending', {})), _j(data.get('chapters', [])),
              _j(data.get('emotional_curve', [])), now, now))
        conn.commit()

    # ========== M7: 卷纲 (DELETE + INSERT, 数量可变) ==========

    @staticmethod
    def _write_volumes(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        vols = data if isinstance(data, list) else data.get('volumes', data.get('items', []))
        conn.execute("DELETE FROM v2_volumes WHERE project_id=?", (project_id,))
        for i, v in enumerate(vols):
            conn.execute("""
                INSERT INTO v2_volumes (project_id, volume_no, name, target_words, chapter_count,
                    protagonist_start, protagonist_end, key_events, volume_foreshadows,
                    cliffhanger, consistency_status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (project_id, i + 1, str(v.get('name', '')),
                  v.get('target_words', 250000), v.get('chapter_count', 100),
                  _j(v.get('protagonist_start', {})), _j(v.get('protagonist_end', {})),
                  _j(v.get('key_events', [])), _j(v.get('volume_foreshadows', [])),
                  str(v.get('cliffhanger', '')), _j(v.get('consistency_status', {})),
                  now, now))
        conn.commit()

    # ========== M8: 章节规划 (DELETE + INSERT, 章节数可变) ==========

    @staticmethod
    def _write_chapter_plan(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        items = data if isinstance(data, list) else data.get('chapters', data.get('chapter_assignments', data.get('items', [])))
        conn.execute("DELETE FROM v2_chapter_plans WHERE project_id=?", (project_id,))
        for i, c in enumerate(items):
            ch_no = str(c.get('chapter_no', i + 1))
            conn.execute("""
                INSERT INTO v2_chapter_plans (project_id, chapter_no, title, target_words,
                    plot_nodes_covered, timeline_events, hook_type, cliffhanger,
                    protagonist_level, locations, dialogue_ratio, pacing,
                    foreshadows_to_add, foreshadows_to_recycle, emotion_curve,
                    scenes, knowledge_update, scene_designs, status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (project_id, ch_no, str(c.get('title', '')),
                  c.get('target_words', 2000), _j(c.get('plot_nodes_covered', [])),
                  _j(c.get('timeline_events', [])), str(c.get('hook_type', '')),
                  str(c.get('cliffhanger', '')), str(c.get('protagonist_level', '')),
                  _j(c.get('locations', [])), c.get('dialogue_ratio', 0.4),
                  str(c.get('pacing', 'normal')), _j(c.get('foreshadows_to_add', [])),
                  _j(c.get('foreshadows_to_recycle', [])), _j(c.get('emotion_curve', [])),
                  _j(c.get('scenes', [])), _j(c.get('knowledge_update', {})),
                  _j(c.get('scene_designs', [])),
                  str(c.get('status', 'planned')), now, now))
        conn.commit()

    # ========== M9: 章节细纲+场景 (DELETE + INSERT) ==========

    @staticmethod
    def _write_chapter_outline(project_id, data):
        DataBridge._write_chapter_plan(project_id, data)

    # ========== M10: 正文 (按章 UPSERT) ==========

    @staticmethod
    def _write_draft(project_id, data):
        conn = DataBridge._conn()
        now = _now()
        chapters = data if isinstance(data, dict) and 'content' in data else data
        if isinstance(chapters, dict) and 'content' in chapters:
            chapters = {'1': chapters}
        for ch_no, ch in (chapters.items() if isinstance(chapters, dict) else {}):
            content = ch.get('content', '') or ch.get('content_raw', '')
            word_count = ch.get('char_count', ch.get('word_count', len(content)))
            existing = conn.execute(
                "SELECT id FROM v2_drafts WHERE project_id=? AND chapter_no=?",
                (project_id, str(ch_no))).fetchone()
            if existing:
                conn.execute("""
                    UPDATE v2_drafts SET content=?, content_raw=?, word_count_raw=?,
                        word_count_final=?, updated_at=? WHERE project_id=? AND chapter_no=?
                """, (content, content, word_count, word_count, now, project_id, str(ch_no)))
            else:
                conn.execute("""
                    INSERT INTO v2_drafts (project_id, chapter_no, scene_id, content, content_raw,
                        word_count_raw, word_count_final, polish_status, foreshadow_added,
                        continuity_check, version, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (project_id, str(ch_no), str(ch.get('scene_id', '')),
                      content, content, word_count, word_count,
                      'draft', '[]', '{}', 1, now, now))
        conn.commit()

    # ========== M11: 内容解析+知识更新 ==========

    @staticmethod
    def _write_parse(project_id, data):
        conn = DataBridge._conn()
        now = _now()
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
              str(data.get('last_check_at', '')), str(data.get('last_chapter_no', '')),
              now, now))
        conn.commit()

    # ========== M12: 润色 (不写DB) ==========

    @staticmethod
    def _write_polish(project_id, data):
        pass

    # ========== M13: 一致性检查 ==========

    @staticmethod
    def _write_consistency(project_id, data):
        conn = DataBridge._conn()
        conn.execute("""
            INSERT INTO v2_consistency_reports (project_id, chapter_no, score,
                items, summary, fixes, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (project_id, str(data.get('chapter_no', '')), data.get('score', 1.0),
              _j(data.get('items', [])), str(data.get('summary', '')),
              _j(data.get('fixes', [])), _now()))
        conn.commit()

    @staticmethod
    def read(project_id, module, chapter_no=None):
        with _lock:
            method_name = DataBridge.READ_MAP.get(module)
            if not method_name:
                return None
            method = getattr(DataBridge, method_name, None)
            if not method:
                return None
            return method(project_id, chapter_no)

    @staticmethod
    def read_all(project_id, chapter_no=None):
        with _lock:
            return {
                k: getattr(DataBridge, v)(project_id, chapter_no)
                for k, v in DataBridge.READ_MAP.items()
            }

    # ========== M1: 灵感 ==========

    @staticmethod
    def _read_idea(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_ideas WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M2: 项目定位 ==========

    @staticmethod
    def _read_project(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_projects WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M3: 世界观 ==========

    @staticmethod
    def _read_world(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_world_buildings WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M4: 角色 ==========

    @staticmethod
    def _read_characters(project_id, chapter_no=None):
        rows = DataBridge._conn().execute(
            "SELECT * FROM v2_characters WHERE project_id=? ORDER BY id",
            (project_id,)).fetchall()
        return [_deserialize_row(r) for r in rows]

    # ========== 关系网 ==========

    @staticmethod
    def _read_relation_map(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_relation_maps WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M5: 故事体系 ==========

    @staticmethod
    def _read_architecture(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_story_systems WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M6: 全书大纲 ==========

    @staticmethod
    def _read_outline(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_outlines WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M7: 卷纲 ==========

    @staticmethod
    def _read_volumes(project_id, chapter_no=None):
        rows = DataBridge._conn().execute(
            "SELECT * FROM v2_volumes WHERE project_id=? ORDER BY volume_no",
            (project_id,)).fetchall()
        return [_deserialize_row(r) for r in rows]

    # ========== M8: 章节规划 ==========

    @staticmethod
    def _read_chapter_plan(project_id, chapter_no=None):
        if chapter_no:
            row = DataBridge._conn().execute(
                "SELECT * FROM v2_chapter_plans WHERE project_id=? AND chapter_no=?",
                (project_id, chapter_no)).fetchone()
            return _deserialize_row(row)
        rows = DataBridge._conn().execute(
            "SELECT * FROM v2_chapter_plans WHERE project_id=? ORDER BY chapter_no",
            (project_id,)).fetchall()
        return [_deserialize_row(r) for r in rows]

    # ========== M10: 正文 ==========

    @staticmethod
    def _read_draft(project_id, chapter_no=None):
        if chapter_no:
            row = DataBridge._conn().execute(
                "SELECT * FROM v2_drafts WHERE project_id=? AND chapter_no=?",
                (project_id, chapter_no)).fetchone()
            return _deserialize_row(row)
        rows = DataBridge._conn().execute(
            "SELECT * FROM v2_drafts WHERE project_id=? ORDER BY chapter_no",
            (project_id,)).fetchall()
        return [_deserialize_row(r) for r in rows]

    # ========== M11: 内容解析 ==========

    @staticmethod
    def _read_parse(project_id, chapter_no=None):
        row = DataBridge._conn().execute(
            "SELECT * FROM v2_knowledge_states WHERE project_id=?", (project_id,)).fetchone()
        return _deserialize_row(row)

    # ========== M13: 一致性检查 ==========

    @staticmethod
    def _read_consistency(project_id, chapter_no=None):
        rows = DataBridge._conn().execute(
            "SELECT * FROM v2_consistency_reports WHERE project_id=? ORDER BY id DESC",
            (project_id,)).fetchall()
        return [_deserialize_row(r) for r in rows]

    @staticmethod
    def _read_polish(project_id, chapter_no=None):
        return None

    @staticmethod
    def _read_chapter_outline(project_id, chapter_no=None):
        return DataBridge._read_chapter_plan(project_id, chapter_no)


# ========== 工具函数 ==========

def _j(obj):
    """安全 JSON 序列化 — 已是字符串则直通"""
    if isinstance(obj, str):
        return obj
    return json.dumps(obj, ensure_ascii=False) if obj else '{}'


def _jl(val, default=None):
    """安全 JSON 反序列化 — 已是 dict/list 则直通"""
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else val


def _deserialize_row(row):
    """将 sqlite3.Row 转为 dict, JSON 字符串列自动反序列化"""
    if not row:
        return None
    d = {}
    for k, v in dict(row).items():
        if isinstance(v, str) and len(v) > 0 and (v[0] in ('{', '[')):
            d[k] = _jl(v, v)
        else:
            d[k] = v
    return d


def _now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
