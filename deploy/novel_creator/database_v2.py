"""SQLite 数据库扩展模块 — V2 18模块创作流水线的数据模型

包含13张新表,覆盖从灵感到完整小说创作的全流程。
独立于 database.py,通过 init_db_v2() 在启动时创建。
"""
import sqlite3
import os
import time
import json
import threading

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'))
V2_SCHEMA_VERSION = 1
_v2_lock = threading.Lock()


def _v2_now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def _v2_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db_v2():
    """初始化V2表结构(幂等,可重复调用)"""
    with _v2_lock:
        conn = _v2_db()
        conn.executescript("""
            /* ========================================
             * V2 数据库 — 18模块创作流水线
             * Schema Version: 1
             * ======================================== */

            /* 1. 灵感 (模块1) */
            CREATE TABLE IF NOT EXISTS v2_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                user_input TEXT DEFAULT '',
                genre_hint TEXT DEFAULT '',
                reference_works TEXT DEFAULT '[]',
                candidates TEXT DEFAULT '[]',
                selected_concept TEXT DEFAULT '',
                core_selling_points TEXT DEFAULT '[]',
                target_audience TEXT DEFAULT '{}',
                risks TEXT DEFAULT '[]',
                sustainability_estimate TEXT DEFAULT '',
                total_score REAL DEFAULT 0,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 2. 项目定位 (模块2) */
            CREATE TABLE IF NOT EXISTS v2_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                idea_id INTEGER DEFAULT 0,
                platform_choice TEXT DEFAULT 'tomato',
                project_overview TEXT DEFAULT '',
                novel_position TEXT DEFAULT '{}',
                platform_config TEXT DEFAULT '{}',
                audience TEXT DEFAULT '{}',
                commercial TEXT DEFAULT '{}',
                style TEXT DEFAULT '{}',
                pace TEXT DEFAULT '{}',
                innovation TEXT DEFAULT '[]',
                content_boundary TEXT DEFAULT '[]',
                wordcount_plan TEXT DEFAULT '{}',
                update_plan TEXT DEFAULT '{}',
                risks TEXT DEFAULT '[]',
                derived_fields TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 3. 世界观 (模块3) */
            CREATE TABLE IF NOT EXISTS v2_world_buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                origin TEXT DEFAULT '{}',
                rules TEXT DEFAULT '[]',
                structure TEXT DEFAULT '{}',
                civilization TEXT DEFAULT '{}',
                history TEXT DEFAULT '[]',
                doc_path TEXT DEFAULT '',
                world_foreshadows TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 4. 角色 (模块4) */
            CREATE TABLE IF NOT EXISTS v2_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                char_id TEXT NOT NULL,
                role_type TEXT DEFAULT 'supporting',
                name TEXT DEFAULT '',
                doc_path TEXT DEFAULT '',
                profile TEXT DEFAULT '{}',
                appearance TEXT DEFAULT '{}',
                personality TEXT DEFAULT '{}',
                abilities TEXT DEFAULT '{}',
                growth_route TEXT DEFAULT '[]',
                initial_relations TEXT DEFAULT '[]',
                initial_psychology TEXT DEFAULT '{}',
                initial_state TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, char_id)
            );

            CREATE TABLE IF NOT EXISTS v2_relation_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                nodes TEXT DEFAULT '[]',
                edges TEXT DEFAULT '[]',
                role_groups TEXT DEFAULT '{}',
                FOREIGN KEY (project_id) REFERENCES v2_projects(project_id)
            );

            /* 5. 故事体系 (模块5) */
            CREATE TABLE IF NOT EXISTS v2_story_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                summary TEXT DEFAULT '',
                conflict_layers TEXT DEFAULT '[]',
                theme TEXT DEFAULT '',
                volume_cliffhangers TEXT DEFAULT '[]',
                volumes_detail TEXT DEFAULT '[]',
                total_plot_events TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 6. 力量体系 (模块6) */
            CREATE TABLE IF NOT EXISTS v2_power_systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                tiers TEXT DEFAULT '[]',
                combat_categories TEXT DEFAULT '[]',
                growth_method TEXT DEFAULT '',
                limits TEXT DEFAULT '[]',
                bottlenecks TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 7. 势力体系 (模块7) */
            CREATE TABLE IF NOT EXISTS v2_factions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                faction_id TEXT NOT NULL,
                name TEXT DEFAULT '',
                faction_type TEXT DEFAULT '',
                territory TEXT DEFAULT '',
                leader_char_id TEXT DEFAULT '',
                military_strength TEXT DEFAULT '',
                core_value TEXT DEFAULT '',
                relations TEXT DEFAULT '[]',
                protagonist_status TEXT DEFAULT '',
                members TEXT DEFAULT '[]',
                internal_conflicts TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, faction_id)
            );

            /* 8. 时间线 (模块8) */
            CREATE TABLE IF NOT EXISTS v2_timelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                events TEXT DEFAULT '[]',
                consistency_status TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 9. 卷纲 (模块9) */
            CREATE TABLE IF NOT EXISTS v2_volumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                volume_no INTEGER NOT NULL,
                name TEXT DEFAULT '',
                target_words INTEGER DEFAULT 250000,
                chapter_count INTEGER DEFAULT 100,
                protagonist_start TEXT DEFAULT '{}',
                protagonist_end TEXT DEFAULT '{}',
                key_events TEXT DEFAULT '[]',
                volume_foreshadows TEXT DEFAULT '[]',
                cliffhanger TEXT DEFAULT '',
                consistency_status TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, volume_no)
            );

            /* 10. 剧情节点 (模块10) */
            CREATE TABLE IF NOT EXISTS v2_plot_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                title TEXT DEFAULT '',
                trigger TEXT DEFAULT '',
                scene_location TEXT DEFAULT '',
                characters TEXT DEFAULT '[]',
                action_purpose TEXT DEFAULT '',
                dialogue_points TEXT DEFAULT '[]',
                climax TEXT DEFAULT '',
                consequence TEXT DEFAULT '',
                next_events TEXT DEFAULT '[]',
                word_count_min INTEGER DEFAULT 1500,
                word_count_max INTEGER DEFAULT 3000,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, event_id)
            );

            /* 11. 章节扩展 (模块11-12) */
            CREATE TABLE IF NOT EXISTS v2_chapter_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT NOT NULL,
                title TEXT DEFAULT '',
                target_words INTEGER DEFAULT 2000,
                plot_nodes_covered TEXT DEFAULT '[]',
                timeline_events TEXT DEFAULT '[]',
                hook_type TEXT DEFAULT '',
                cliffhanger TEXT DEFAULT '',
                protagonist_level TEXT DEFAULT '',
                locations TEXT DEFAULT '[]',
                dialogue_ratio REAL DEFAULT 0.4,
                pacing TEXT DEFAULT 'normal',
                foreshadows_to_add TEXT DEFAULT '[]',
                foreshadows_to_recycle TEXT DEFAULT '[]',
                emotion_curve TEXT DEFAULT '[]',
                scenes TEXT DEFAULT '[]',
                knowledge_update TEXT DEFAULT '{}',
                status TEXT DEFAULT 'planned',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, chapter_no)
            );

            /* 12. 场景设计 (模块14) */
            CREATE TABLE IF NOT EXISTS v2_scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                scene_id TEXT NOT NULL,
                chapter_no TEXT DEFAULT '',
                setting TEXT DEFAULT '{}',
                plot_purpose TEXT DEFAULT '',
                core_conflict TEXT DEFAULT '',
                combat_strategy TEXT DEFAULT '',
                foreshadow_integration TEXT DEFAULT '',
                atmosphere TEXT DEFAULT '',
                reader_reaction TEXT DEFAULT '',
                expected_emotion TEXT DEFAULT '{}',
                scene_hooks TEXT DEFAULT '{}',
                word_count_actual INTEGER DEFAULT 0,
                content_path TEXT DEFAULT '',
                state_diff TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, scene_id)
            );

            /* 13. 伏笔管理 (M2+M9+M12+M17共享) */
            CREATE TABLE IF NOT EXISTS v2_foreshadowings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                foreshadow_id TEXT NOT NULL,
                source_type TEXT DEFAULT '',
                source_id TEXT DEFAULT '',
                foreshadow_type TEXT DEFAULT '',
                description TEXT DEFAULT '',
                trigger_text TEXT DEFAULT '',
                target_volume INTEGER DEFAULT 0,
                target_chapter INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                resolved_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, foreshadow_id)
            );

            /* 14. 知识库 (模块17-18) */
            CREATE TABLE IF NOT EXISTS v2_knowledge_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                character_states TEXT DEFAULT '{}',
                world_state TEXT DEFAULT '{}',
                plot_state TEXT DEFAULT '{}',
                consistency_status TEXT DEFAULT '{}',
                last_check_at TEXT DEFAULT '',
                last_chapter_no TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 15. AI生成日志 (全流程共享) */
            CREATE TABLE IF NOT EXISTS v2_ai_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                entity_type TEXT DEFAULT '',
                entity_id TEXT DEFAULT '',
                prompt_hash TEXT DEFAULT '',
                prompt_text TEXT DEFAULT '',
                response_text TEXT DEFAULT '',
                model_used TEXT DEFAULT '',
                tokens_input INTEGER DEFAULT 0,
                tokens_output INTEGER DEFAULT 0,
                duration_ms INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                error_message TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 16. 一致性检查日志 (模块18) */
            CREATE TABLE IF NOT EXISTS v2_consistency_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT DEFAULT '',
                score REAL DEFAULT 1.0,
                items TEXT DEFAULT '[]',
                summary TEXT DEFAULT '',
                fixes TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* 17. 正文草稿 (模块15) */
            CREATE TABLE IF NOT EXISTS v2_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_no TEXT NOT NULL,
                scene_id TEXT DEFAULT '',
                content TEXT DEFAULT '',
                content_raw TEXT DEFAULT '',
                word_count_raw INTEGER DEFAULT 0,
                word_count_final INTEGER DEFAULT 0,
                polish_status TEXT DEFAULT 'draft',
                foreshadow_added TEXT DEFAULT '[]',
                continuity_check TEXT DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            /* === V2 索引 === */
            CREATE INDEX IF NOT EXISTS idx_v2_ideas_project ON v2_ideas(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_projects_project ON v2_projects(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_world_project ON v2_world_buildings(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_chars_project ON v2_characters(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_story_project ON v2_story_systems(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_power_project ON v2_power_systems(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_factions_project ON v2_factions(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_timeline_project ON v2_timelines(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_volumes_project ON v2_volumes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_plot_project ON v2_plot_nodes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_chapters_project ON v2_chapter_plans(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_scenes_project ON v2_scenes(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_foreshadow_project ON v2_foreshadowings(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_knowledge_project ON v2_knowledge_states(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_ai_gen_project ON v2_ai_generations(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_consistency_project ON v2_consistency_reports(project_id);
            CREATE INDEX IF NOT EXISTS idx_v2_drafts_project ON v2_drafts(project_id);

            /* 18. 流水线状态 (持久化) */
            CREATE TABLE IF NOT EXISTS v2_pipeline_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                module_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                error TEXT DEFAULT '',
                consistency_score REAL DEFAULT 0,
                started_at TEXT DEFAULT '',
                completed_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, module_name)
            );
            CREATE INDEX IF NOT EXISTS idx_v2_pipeline_project ON v2_pipeline_states(project_id);
        """)
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
            ON CONFLICT(id) DO UPDATE SET
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
                history, doc_path, world_foreshadows, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                origin=excluded.origin, rules=excluded.rules, structure=excluded.structure,
                civilization=excluded.civilization, history=excluded.history,
                doc_path=excluded.doc_path, world_foreshadows=excluded.world_foreshadows,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('origin', {})), _j(data.get('rules', [])),
              _j(data.get('structure', {})), _j(data.get('civilization', {})),
              _j(data.get('history', [])), data.get('doc_path', ''),
              _j(data.get('world_foreshadows', [])), now, now))
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
            INSERT INTO v2_relation_maps (project_id, nodes, edges, role_groups)
            VALUES (?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                nodes=excluded.nodes, edges=excluded.edges, role_groups=excluded.role_groups
        """, (project_id, _j(data.get('nodes', [])), _j(data.get('edges', [])),
              _j(data.get('role_groups', {}))))
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


# ========== 故事体系 CRUD ==========

def save_story(project_id, data):
    """保存故事体系"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_story_systems (project_id, summary, conflict_layers, theme,
                volume_cliffhangers, volumes_detail, total_plot_events, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                summary=excluded.summary, conflict_layers=excluded.conflict_layers,
                theme=excluded.theme, volume_cliffhangers=excluded.volume_cliffhangers,
                volumes_detail=excluded.volumes_detail, total_plot_events=excluded.total_plot_events,
                updated_at=excluded.updated_at
        """, (project_id, data.get('summary', ''), _j(data.get('conflict_layers', [])),
              data.get('theme', ''), _j(data.get('volume_cliffhangers', [])),
              _j(data.get('volumes_detail', [])), _j(data.get('total_plot_events', [])),
              now, now))
        conn.commit()
        conn.close()


def get_story(project_id):
    """获取故事体系"""
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_story_systems WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['conflict_layers'] = _jl(d.get('conflict_layers', '[]'))
    d['volume_cliffhangers'] = _jl(d.get('volume_cliffhangers', '[]'))
    d['volumes_detail'] = _jl(d.get('volumes_detail', '[]'))
    d['total_plot_events'] = _jl(d.get('total_plot_events', '[]'))
    return d


# ========== 力量/势力/时间线 CRUD ==========

def save_power_system(project_id, data):
    """保存力量体系"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_power_systems (project_id, tiers, combat_categories,
                growth_method, limits, bottlenecks, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                tiers=excluded.tiers, combat_categories=excluded.combat_categories,
                growth_method=excluded.growth_method, limits=excluded.limits,
                bottlenecks=excluded.bottlenecks, updated_at=excluded.updated_at
        """, (project_id, _j(data.get('tiers', [])), _j(data.get('combat_categories', [])),
              data.get('growth_method', ''), _j(data.get('limits', [])),
              _j(data.get('bottlenecks', [])), now, now))
        conn.commit()
        conn.close()


def get_power_system(project_id):
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_power_systems WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['tiers'] = _jl(d.get('tiers', '[]'))
    d['combat_categories'] = _jl(d.get('combat_categories', '[]'))
    d['limits'] = _jl(d.get('limits', '[]'))
    d['bottlenecks'] = _jl(d.get('bottlenecks', '[]'))
    return d


def save_faction(project_id, faction_id, data):
    """保存势力"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_factions (project_id, faction_id, name, faction_type, territory,
                leader_char_id, military_strength, core_value, relations,
                protagonist_status, members, internal_conflicts, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, faction_id) DO UPDATE SET
                name=excluded.name, faction_type=excluded.faction_type,
                territory=excluded.territory, leader_char_id=excluded.leader_char_id,
                military_strength=excluded.military_strength, core_value=excluded.core_value,
                relations=excluded.relations, protagonist_status=excluded.protagonist_status,
                members=excluded.members, internal_conflicts=excluded.internal_conflicts,
                updated_at=excluded.updated_at
        """, (project_id, faction_id, data.get('name', ''), data.get('faction_type', ''),
              data.get('territory', ''), data.get('leader_char_id', ''),
              data.get('military_strength', ''), data.get('core_value', ''),
              _j(data.get('relations', [])), data.get('protagonist_status', ''),
              _j(data.get('members', [])), _j(data.get('internal_conflicts', [])),
              now, now))
        conn.commit()
        conn.close()


def get_factions(project_id):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_factions WHERE project_id=? ORDER BY id",
                          (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['relations'] = _jl(d.get('relations', '[]'))
        d['members'] = _jl(d.get('members', '[]'))
        d['internal_conflicts'] = _jl(d.get('internal_conflicts', '[]'))
        result.append(d)
    return result


def save_timeline(project_id, data):
    """保存时间线"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_timelines (project_id, events, consistency_status, created_at, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(project_id) DO UPDATE SET
                events=excluded.events, consistency_status=excluded.consistency_status,
                updated_at=excluded.updated_at
        """, (project_id, _j(data.get('events', [])), _j(data.get('consistency_status', {})),
              now, now))
        conn.commit()
        conn.close()


def get_timeline(project_id):
    with _v2_lock:
        conn = _v2_db()
        row = conn.execute("SELECT * FROM v2_timelines WHERE project_id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['events'] = _jl(d.get('events', '[]'))
    d['consistency_status'] = _jd(d.get('consistency_status', '{}'), {})
    return d


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


def save_plot_node(project_id, event_id, data):
    """保存剧情节点"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_plot_nodes (project_id, event_id, title, trigger, scene_location,
                characters, action_purpose, dialogue_points, climax, consequence,
                next_events, word_count_min, word_count_max, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, event_id) DO UPDATE SET
                title=excluded.title, trigger=excluded.trigger,
                scene_location=excluded.scene_location, characters=excluded.characters,
                action_purpose=excluded.action_purpose, dialogue_points=excluded.dialogue_points,
                climax=excluded.climax, consequence=excluded.consequence,
                next_events=excluded.next_events, word_count_min=excluded.word_count_min,
                word_count_max=excluded.word_count_max, updated_at=excluded.updated_at
        """, (project_id, event_id, data.get('title', ''), data.get('trigger', ''),
              data.get('scene_location', ''), _j(data.get('characters', [])),
              data.get('action_purpose', ''), _j(data.get('dialogue_points', [])),
              data.get('climax', ''), data.get('consequence', ''),
              _j(data.get('next_events', [])), data.get('word_count_min', 1500),
              data.get('word_count_max', 3000), now, now))
        conn.commit()
        conn.close()


def get_plot_nodes(project_id):
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_plot_nodes WHERE project_id=?  ORDER BY id",
                          (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['characters'] = _jl(d.get('characters', '[]'))
        d['dialogue_points'] = _jl(d.get('dialogue_points', '[]'))
        d['next_events'] = _jl(d.get('next_events', '[]'))
        result.append(d)
    return result


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
                scenes, knowledge_update, status, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, chapter_no) DO UPDATE SET
                title=excluded.title, target_words=excluded.target_words,
                plot_nodes_covered=excluded.plot_nodes_covered,
                timeline_events=excluded.timeline_events, hook_type=excluded.hook_type,
                cliffhanger=excluded.cliffhanger, protagonist_level=excluded.protagonist_level,
                locations=excluded.locations, dialogue_ratio=excluded.dialogue_ratio,
                pacing=excluded.pacing, foreshadows_to_add=excluded.foreshadows_to_add,
                foreshadows_to_recycle=excluded.foreshadows_to_recycle,
                emotion_curve=excluded.emotion_curve, scenes=excluded.scenes,
                knowledge_update=excluded.knowledge_update, status=excluded.status,
                updated_at=excluded.updated_at
        """, (project_id, chapter_no, data.get('title', ''),
              data.get('target_words', 2000), _j(data.get('plot_nodes_covered', [])),
              _j(data.get('timeline_events', [])), data.get('hook_type', ''),
              data.get('cliffhanger', ''), data.get('protagonist_level', ''),
              _j(data.get('locations', [])), data.get('dialogue_ratio', 0.4),
              data.get('pacing', 'normal'), _j(data.get('foreshadows_to_add', [])),
              _j(data.get('foreshadows_to_recycle', [])), _j(data.get('emotion_curve', [])),
              _j(data.get('scenes', [])), _j(data.get('knowledge_update', {})),
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


def save_scene(project_id, scene_id, data):
    """保存场景"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_scenes (project_id, scene_id, chapter_no, setting, plot_purpose,
                core_conflict, combat_strategy, foreshadow_integration, atmosphere,
                reader_reaction, expected_emotion, scene_hooks, word_count_actual,
                content_path, state_diff, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, scene_id) DO UPDATE SET
                chapter_no=excluded.chapter_no, setting=excluded.setting,
                plot_purpose=excluded.plot_purpose, core_conflict=excluded.core_conflict,
                combat_strategy=excluded.combat_strategy,
                foreshadow_integration=excluded.foreshadow_integration,
                atmosphere=excluded.atmosphere, reader_reaction=excluded.reader_reaction,
                expected_emotion=excluded.expected_emotion, scene_hooks=excluded.scene_hooks,
                word_count_actual=excluded.word_count_actual, content_path=excluded.content_path,
                state_diff=excluded.state_diff, updated_at=excluded.updated_at
        """, (project_id, scene_id, data.get('chapter_no', ''),
              _j(data.get('setting', {})), data.get('plot_purpose', ''),
              data.get('core_conflict', ''), data.get('combat_strategy', ''),
              data.get('foreshadow_integration', ''), data.get('atmosphere', ''),
              data.get('reader_reaction', ''), _j(data.get('expected_emotion', {})),
              _j(data.get('scene_hooks', {})), data.get('word_count_actual', 0),
              data.get('content_path', ''), _j(data.get('state_diff', {})),
              now, now))
        conn.commit()
        conn.close()


def get_scenes(project_id, chapter_no=None):
    with _v2_lock:
        conn = _v2_db()
        if chapter_no:
            rows = conn.execute("SELECT * FROM v2_scenes WHERE project_id=? AND chapter_no=? ORDER BY id",
                              (project_id, chapter_no)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM v2_scenes WHERE project_id=?  ORDER BY id",
                              (project_id,)).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['setting'] = _jd(d.get('setting', '{}'), {})
        d['expected_emotion'] = _jd(d.get('expected_emotion', '{}'), {})
        d['scene_hooks'] = _jd(d.get('scene_hooks', '{}'), {})
        d['state_diff'] = _jd(d.get('state_diff', '{}'), {})
        result.append(d)
    return result


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
            rows = conn.execute("SELECT * FROM v2_foreshadowings WHERE project_id=? AND status? ORDER BY id",
                              (project_id, status)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM v2_foreshadowings WHERE project_id=?  ORDER BY id",
                              (project_id,)).fetchall()
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
    """保存或更新流水线模块状态"""
    with _v2_lock:
        conn = _v2_db()
        now = _v2_now()
        conn.execute("""
            INSERT INTO v2_pipeline_states (project_id, module_name, status, retry_count,
                error, consistency_score, started_at, completed_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(project_id, module_name) DO UPDATE SET
                status=excluded.status, retry_count=excluded.retry_count,
                error=excluded.error, consistency_score=excluded.consistency_score,
                started_at=excluded.started_at, completed_at=excluded.completed_at,
                updated_at=excluded.updated_at
        """, (project_id, module_name, data.get('status', 'pending'),
              data.get('retry_count', 0), data.get('error', ''),
              data.get('consistency_score', 0), data.get('started_at', ''),
              data.get('completed_at', ''), now))
        conn.commit()
        conn.close()


def get_pipeline_state(project_id):
    """获取项目所有流水线模块状态"""
    with _v2_lock:
        conn = _v2_db()
        rows = conn.execute("SELECT * FROM v2_pipeline_states WHERE project_id=?", (project_id,)).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def delete_project_v2(project_id):
    """级联删除项目所有V2数据"""
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
