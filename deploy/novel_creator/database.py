"""SQLite 数据库模块 - 章节存储、大纲管理、步骤摘要、项目管理、生成状态管理"""
import sqlite3
import os
import time
import json
import threading

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'))
SCHEMA_VERSION = 2  # 当前 schema 版本号，用于迁移
_db_lock = threading.Lock()


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _ensure_columns(conn):
    """确保所有必需的列存在（幂等，可重复调用）"""
    cur = conn.cursor()
    # 获取 outlines 表的所有列
    cur.execute("PRAGMA table_info(outlines)")
    existing_cols = {row[1] for row in cur.fetchall()}
    # 检查并添加缺失的列
    if 'chapter_hook' not in existing_cols:
        try:
            cur.execute("ALTER TABLE outlines ADD COLUMN chapter_hook TEXT DEFAULT ''")
        except Exception:
            pass
    # 检查其他表...
    chapters_cols = {row[1] for row in cur.execute("PRAGMA table_info(chapters)").fetchall()}
    if 'version' not in chapters_cols:
        try:
            cur.execute("ALTER TABLE chapters ADD COLUMN version INTEGER DEFAULT 1")
        except Exception:
            pass
    if 'metadata_json' not in chapters_cols:
        try:
            cur.execute("ALTER TABLE chapters ADD COLUMN metadata_json TEXT DEFAULT '{}'")
        except Exception:
            pass
    conn.commit()


def _migrate(conn):
    """数据库 schema 迁移逻辑"""
    cur = conn.cursor()
    # 获取当前 schema 版本
    cur.execute("PRAGMA user_version")
    row = cur.fetchone()
    ver = row[0] if row else 0

    if ver < 2:
        # v2: 添加缺失索引、扩展字段
        cur.execute("CREATE INDEX IF NOT EXISTS idx_generation_status_project ON generation_status(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_outline_generation_status_project ON outline_generation_status(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived)")
        # 安全添加列（忽略已存在错误）
        for sql in [
            "ALTER TABLE projects ADD COLUMN category TEXT DEFAULT ''",
            "ALTER TABLE projects ADD COLUMN metadata_json TEXT DEFAULT '{}'",
            "ALTER TABLE projects ADD COLUMN is_archived INTEGER DEFAULT 0",
            "ALTER TABLE chapters ADD COLUMN version INTEGER DEFAULT 1",
            "ALTER TABLE chapters ADD COLUMN metadata_json TEXT DEFAULT '{}'",
            "ALTER TABLE outlines ADD COLUMN importance INTEGER DEFAULT 0",
            "ALTER TABLE outlines ADD COLUMN metadata_json TEXT DEFAULT '{}'",
            "ALTER TABLE outlines ADD COLUMN chapter_hook TEXT DEFAULT ''",
        ]:
            try:
                cur.execute(sql)
            except Exception:
                pass  # 列已存在则忽略
        cur.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
    # 无论版本如何，都确保列存在
    _ensure_columns(conn)


def init_db():
    """初始化数据库表（含迁移）"""
    with _db_lock:
        conn = get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT DEFAULT '未命名项目',
                step INTEGER DEFAULT 0,
                data_json TEXT DEFAULT '{}',
                tags TEXT DEFAULT '',
                category TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                is_archived INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS chapters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                word_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                version INTEGER DEFAULT 1,
                error_message TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, chapter_number)
            );

            CREATE TABLE IF NOT EXISTS outlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                chapter_number INTEGER NOT NULL,
                title TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                scenes TEXT DEFAULT '[]',
                characters TEXT DEFAULT '[]',
                key_points TEXT DEFAULT '[]',
                emotion TEXT DEFAULT '',
                goal TEXT DEFAULT '',
                technique_focus TEXT DEFAULT '',
                book_overview TEXT DEFAULT '',
                acts TEXT DEFAULT '[]',
                importance INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, chapter_number)
            );

            CREATE TABLE IF NOT EXISTS generation_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                total_chapters INTEGER DEFAULT 0,
                completed_chapters INTEGER DEFAULT 0,
                failed_chapters INTEGER DEFAULT 0,
                current_chapter INTEGER DEFAULT 0,
                is_running INTEGER DEFAULT 0,
                is_paused INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}',
                started_at TEXT,
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS outline_generation_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                total_chapters INTEGER DEFAULT 0,
                completed_chapters INTEGER DEFAULT 0,
                failed_chapters INTEGER DEFAULT 0,
                current_chapter INTEGER DEFAULT 0,
                is_running INTEGER DEFAULT 0,
                is_paused INTEGER DEFAULT 0,
                config TEXT DEFAULT '{}',
                started_at TEXT,
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS step_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                step TEXT NOT NULL,
                summary_json TEXT DEFAULT '{}',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                UNIQUE(project_id, step)
            );

            /* === 索引 === */
            CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at);
            CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived);
            CREATE INDEX IF NOT EXISTS idx_chapters_project ON chapters(project_id);
            CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(project_id, status);
            CREATE INDEX IF NOT EXISTS idx_outlines_project ON outlines(project_id);
            CREATE INDEX IF NOT EXISTS idx_outlines_status ON outlines(project_id, status);
            CREATE INDEX IF NOT EXISTS idx_generation_status_project ON generation_status(project_id);
            CREATE INDEX IF NOT EXISTS idx_outline_generation_status_project ON outline_generation_status(project_id);
            CREATE INDEX IF NOT EXISTS idx_step_summaries_project ON step_summaries(project_id);
        """)
        # 执行迁移
        _migrate(conn)
        conn.close()


def _now():
    return time.strftime('%Y-%m-%d %H:%M:%S')


# ========== 步骤摘要 CRUD ==========

def save_step_summary(project_id, step, summary_json):
    """保存或更新步骤摘要"""
    summary_str = json.dumps(summary_json, ensure_ascii=False) if isinstance(summary_json, dict) else summary_json
    with _db_lock:
        conn = get_db()
        conn.execute("""
            INSERT INTO step_summaries (project_id, step, summary_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, step) DO UPDATE SET
                summary_json=excluded.summary_json, updated_at=excluded.updated_at
        """, (project_id, step, summary_str, _now()))
        conn.commit()
        conn.close()


def get_step_summary(project_id, step):
    """获取单步摘要"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM step_summaries WHERE project_id=? AND step=?",
            (project_id, step)
        ).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d['summary_json'] = json.loads(d.get('summary_json', '{}'))
    except (json.JSONDecodeError, TypeError):
        d['summary_json'] = {}
    return d


def get_all_step_summaries(project_id):
    """获取项目所有步骤摘要"""
    with _db_lock:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM step_summaries WHERE project_id=? ORDER BY id",
            (project_id,)
        ).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        try:
            d['summary_json'] = json.loads(d.get('summary_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            d['summary_json'] = {}
        result.append(d)
    return result


def delete_project_step_summaries(project_id):
    """删除项目所有步骤摘要（建议用 delete_project_cascade 替代以级联删除所有数据）"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM step_summaries WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


# ========== 项目 CRUD ==========

def save_project(project_id, name, step, data, tags='', category='', metadata=None, is_archived=0):
    """保存或更新项目"""
    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = str(data)
    meta_str = json.dumps(metadata or {}, ensure_ascii=False)
    with _db_lock:
        conn = get_db()
        now = _now()
        conn.execute("""
            INSERT INTO projects (id, name, step, data_json, tags, category, metadata_json, is_archived, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, step=excluded.step, data_json=excluded.data_json,
                tags=excluded.tags, category=excluded.category, metadata_json=excluded.metadata_json,
                is_archived=excluded.is_archived, updated_at=excluded.updated_at
        """, (project_id, name, step, data_str, tags, category, meta_str, is_archived, now, now))
        conn.commit()
        conn.close()


def get_project(project_id):
    """获取项目详情"""
    with _db_lock:
        conn = get_db()
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d['data'] = json.loads(d.get('data_json', '{}'))
    except (json.JSONDecodeError, TypeError):
        d['data'] = {}
    d.pop('data_json', None)
    try:
        d['metadata'] = json.loads(d.get('metadata_json', '{}'))
    except (json.JSONDecodeError, TypeError):
        d['metadata'] = {}
    d.pop('metadata_json', None)
    return d


def list_projects(include_archived=False):
    """列出所有项目（摘要信息，不含 data 以节省带宽）"""
    with _db_lock:
        conn = get_db()
        sql = """
            SELECT id, name, step, tags, category, is_archived, created_at, updated_at, data_json
            FROM projects
        """
        if not include_archived:
            sql += " WHERE is_archived = 0"
        sql += " ORDER BY updated_at DESC"
        rows = conn.execute(sql).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        try:
            data = json.loads(d.get('data_json', '{}'))
        except:
            data = {}
        result.append({
            'id': d.get('id', ''),
            'name': d.get('name', '未命名'),
            'step': d.get('step', 0),
            'tags': d.get('tags', ''),
            'category': d.get('category', ''),
            'is_archived': bool(d.get('is_archived', 0)),
            'created_at': d.get('created_at', ''),
            'updated_at': d.get('updated_at', ''),
            'chapter_count': len(data.get('chapters', [])),
            'char_count': len(data.get('charactersRaw', [])) if isinstance(data.get('charactersRaw'), list) else (len(data.get('characters', '').split('\n')) if isinstance(data.get('characters', ''), str) and data.get('characters') else 0),
            'has_outline': bool(data.get('outline', [])),
            'title': data.get('title', ''),
        })
    return result


def delete_project_cascade(project_id):
    """删除项目及其所有关联数据"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        conn.execute("DELETE FROM step_summaries WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM chapters WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM generation_status WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM outlines WHERE project_id=?", (project_id,))
        conn.execute("DELETE FROM outline_generation_status WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


# ========== 章节 CRUD ==========

def save_chapter(project_id, chapter_number, title='', content='', status='done', error_message='', metadata=None):
    """保存或更新章节（自动递增 version）"""
    word_count = len(content) if content else 0
    meta_str = json.dumps(metadata or {}, ensure_ascii=False)
    with _db_lock:
        conn = get_db()
        # 获取当前版本号
        row = conn.execute("SELECT version FROM chapters WHERE project_id=? AND chapter_number=?",
                          (project_id, chapter_number)).fetchone()
        new_version = (row['version'] + 1) if row else 1
        conn.execute("""
            INSERT INTO chapters (project_id, chapter_number, title, content, word_count, status, version, error_message, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                title=excluded.title, content=excluded.content, word_count=excluded.word_count,
                status=excluded.status, version=excluded.version, error_message=excluded.error_message,
                metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
        """, (project_id, chapter_number, title, content, word_count, status, new_version, error_message, meta_str, _now()))
        conn.commit()
        conn.close()


def get_chapter(project_id, chapter_number):
    """获取单章"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM chapters WHERE project_id=? AND chapter_number=?",
            (project_id, chapter_number)
        ).fetchone()
        conn.close()
    return dict(row) if row else None


def get_all_chapters(project_id):
    """获取项目所有章节（按章节号排序）"""
    with _db_lock:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM chapters WHERE project_id=? ORDER BY chapter_number",
            (project_id,)
        ).fetchall()
        conn.close()
    return [dict(r) for r in rows]


def delete_chapter(project_id, chapter_number):
    """删除单章"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM chapters WHERE project_id=? AND chapter_number=?",
                     (project_id, chapter_number))
        conn.commit()
        conn.close()


def delete_project_chapters(project_id):
    """删除项目所有章节（建议用 delete_project_cascade 替代）"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM chapters WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


def get_chapter_count(project_id):
    """获取章节总数和已完成数"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as completed FROM chapters WHERE project_id=?",
            (project_id,)
        ).fetchone()
        conn.close()
    return {'total': row['total'] or 0, 'completed': row['completed'] or 0}


# ========== 大纲 CRUD ==========

def save_outline(project_id, chapter_number, title='', summary='', scenes=None, characters=None,
                 key_points=None, emotion='', goal='', technique_focus='', book_overview='',
                 chapter_hook='',
                 acts=None, importance=0, status='done', error_message='', metadata=None):
    """保存或更新大纲"""
    scenes_json = json.dumps(scenes or [], ensure_ascii=False)
    chars_json = json.dumps(characters or [], ensure_ascii=False)
    kp_json = json.dumps(key_points or [], ensure_ascii=False)
    acts_json = json.dumps(acts or [], ensure_ascii=False)
    meta_str = json.dumps(metadata or {}, ensure_ascii=False)
    with _db_lock:
        conn = get_db()
        conn.execute("""
            INSERT INTO outlines (project_id, chapter_number, title, summary, scenes, characters, key_points,
                emotion, goal, technique_focus, book_overview, chapter_hook, acts, importance, status, error_message, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                title=excluded.title, summary=excluded.summary, scenes=excluded.scenes,
                characters=excluded.characters, key_points=excluded.key_points,
                emotion=excluded.emotion, goal=excluded.goal, technique_focus=excluded.technique_focus,
                book_overview=excluded.book_overview, chapter_hook=excluded.chapter_hook, acts=excluded.acts, importance=excluded.importance,
                status=excluded.status, error_message=excluded.error_message, metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
        """, (project_id, chapter_number, title, summary, scenes_json, chars_json, kp_json,
              emotion, goal, technique_focus, book_overview, chapter_hook, acts_json, importance, status, error_message, meta_str, _now()))
        conn.commit()
        conn.close()


def get_outline(project_id, chapter_number):
    """获取单章大纲"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM outlines WHERE project_id=? AND chapter_number=?",
            (project_id, chapter_number)
        ).fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    d['scenes'] = json.loads(d.get('scenes', '[]'))
    d['characters'] = json.loads(d.get('characters', '[]'))
    d['key_points'] = json.loads(d.get('key_points', '[]'))
    d['acts'] = json.loads(d.get('acts', '[]'))
    return d


def get_all_outlines(project_id):
    """获取项目所有大纲"""
    with _db_lock:
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM outlines WHERE project_id=? ORDER BY chapter_number",
            (project_id,)
        ).fetchall()
        conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d['scenes'] = json.loads(d.get('scenes', '[]'))
        d['characters'] = json.loads(d.get('characters', '[]'))
        d['key_points'] = json.loads(d.get('key_points', '[]'))
        d['acts'] = json.loads(d.get('acts', '[]'))
        result.append(d)
    return result


def delete_outline(project_id, chapter_number):
    """删除单章大纲"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM outlines WHERE project_id=? AND chapter_number=?",
                     (project_id, chapter_number))
        conn.commit()
        conn.close()


def delete_project_outlines(project_id):
    """删除项目所有大纲（建议用 delete_project_cascade 替代）"""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM outlines WHERE project_id=?", (project_id,))
        conn.commit()
        conn.close()


def get_outline_count(project_id):
    """获取大纲总数和已完成数"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as completed FROM outlines WHERE project_id=?",
            (project_id,)
        ).fetchone()
        conn.close()
    return {'total': row['total'] or 0, 'completed': row['completed'] or 0}


# ========== 大纲生成状态管理 ==========

def get_outline_generation_status(project_id):
    """获取大纲生成状态"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM outline_generation_status WHERE project_id=?", (project_id,)
        ).fetchone()
        conn.close()
    if row:
        d = dict(row)
        d['is_running'] = bool(d['is_running'])
        d['is_paused'] = bool(d['is_paused'])
        return d
    return None


def start_outline_generation(project_id, total_chapters, config=None):
    """开始批量大纲生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("""
            INSERT INTO outline_generation_status (project_id, total_chapters, is_running, started_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                total_chapters=excluded.total_chapters, is_running=1, is_paused=0,
                current_chapter=0, completed_chapters=0, failed_chapters=0,
                started_at=excluded.started_at, updated_at=excluded.updated_at
        """, (project_id, total_chapters, _now(), _now()))
        if config:
            conn.execute("UPDATE outline_generation_status SET config=? WHERE project_id=?",
                         (config, project_id))
        conn.commit()
        conn.close()


def update_outline_generation_progress(project_id, current_chapter, completed=None, failed=None):
    """更新大纲生成进度"""
    with _db_lock:
        conn = get_db()
        sets = ["current_chapter=?", "updated_at=?"]
        params = [current_chapter, _now()]
        if completed is not None:
            sets.append("completed_chapters=?")
            params.append(completed)
        if failed is not None:
            sets.append("failed_chapters=?")
            params.append(failed)
        params.append(project_id)
        conn.execute(f"UPDATE outline_generation_status SET {', '.join(sets)} WHERE project_id=?", params)
        conn.commit()
        conn.close()


def pause_outline_generation(project_id):
    """暂停大纲生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE outline_generation_status SET is_paused=1, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


def resume_outline_generation(project_id):
    """恢复大纲生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE outline_generation_status SET is_paused=0, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


def stop_outline_generation(project_id):
    """停止大纲生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE outline_generation_status SET is_running=0, is_paused=0, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


# ========== 章节生成状态管理 ==========

def get_generation_status(project_id):
    """获取生成状态"""
    with _db_lock:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM generation_status WHERE project_id=?", (project_id,)
        ).fetchone()
        conn.close()
    if row:
        d = dict(row)
        d['is_running'] = bool(d['is_running'])
        d['is_paused'] = bool(d['is_paused'])
        return d
    return None


def start_generation(project_id, total_chapters, config=None):
    """开始批量生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("""
            INSERT INTO generation_status (project_id, total_chapters, is_running, started_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                total_chapters=excluded.total_chapters, is_running=1, is_paused=0,
                current_chapter=0, completed_chapters=0, failed_chapters=0,
                started_at=excluded.started_at, updated_at=excluded.updated_at
        """, (project_id, total_chapters, _now(), _now()))
        if config:
            conn.execute("UPDATE generation_status SET config=? WHERE project_id=?",
                         (config, project_id))
        conn.commit()
        conn.close()


def update_generation_progress(project_id, current_chapter, completed=None, failed=None):
    """更新生成进度"""
    with _db_lock:
        conn = get_db()
        sets = ["current_chapter=?", "updated_at=?"]
        params = [current_chapter, _now()]
        if completed is not None:
            sets.append("completed_chapters=?")
            params.append(completed)
        if failed is not None:
            sets.append("failed_chapters=?")
            params.append(failed)
        params.append(project_id)
        conn.execute(f"UPDATE generation_status SET {', '.join(sets)} WHERE project_id=?", params)
        conn.commit()
        conn.close()


def pause_generation(project_id):
    """暂停生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE generation_status SET is_paused=1, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


def resume_generation(project_id):
    """恢复生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE generation_status SET is_paused=0, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


def stop_generation(project_id):
    """停止生成"""
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE generation_status SET is_running=0, is_paused=0, updated_at=? WHERE project_id=?",
                     (_now(), project_id))
        conn.commit()
        conn.close()


def get_pending_chapters(project_id, total_chapters):
    """获取待生成的章节号列表"""
    with _db_lock:
        conn = get_db()
        rows = conn.execute(
            "SELECT chapter_number FROM chapters WHERE project_id=? AND status='done' ORDER BY chapter_number",
            (project_id,)
        ).fetchall()
        conn.close()
    done = set(r['chapter_number'] for r in rows)
    return [i for i in range(1, total_chapters + 1) if i not in done]
