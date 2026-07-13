"""Database wrapper module - delegates to novel_creator.database"""
import json
import sqlite3
import os
import time
import threading

from app.config import DB_PATH

_db_lock = threading.RLock()


class NovelDB:
    """Database wrapper for project, chapter, outline, step-summary, and generation-status operations."""

    def get_db(self):
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _now(self):
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def _safe_json(self, val, default=None):
        if isinstance(val, (dict, list)):
            return json.dumps(val, ensure_ascii=False)
        if isinstance(val, str):
            return val
        return str(default or '')

    def init_db(self):
        with _db_lock:
            conn = self.get_db()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT DEFAULT '',
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
                    chapter_hook TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime')),
                    deleted_at TEXT DEFAULT NULL,
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
                    updated_at TEXT DEFAULT (datetime('now','localtime')),
                    deleted_at TEXT DEFAULT NULL
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
                    updated_at TEXT DEFAULT (datetime('now','localtime')),
                    deleted_at TEXT DEFAULT NULL
                );
                CREATE TABLE IF NOT EXISTS step_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    summary_json TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime')),
                    deleted_at TEXT DEFAULT NULL,
                    UNIQUE(project_id, step)
                );
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
            conn.commit()
            conn.close()

    # ========== Project CRUD ==========

    def save_project(self, project_id, name, step, data, tags='', category='', metadata=None, is_archived=0):
        data_str = self._safe_json(data)
        meta_str = self._safe_json(metadata or {})
        with _db_lock:
            conn = self.get_db()
            now = self._now()
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

    def list_projects(self):
        with _db_lock:
            conn = self.get_db()
            rows = conn.execute("SELECT * FROM projects WHERE is_archived=0 AND deleted_at IS NULL ORDER BY updated_at DESC").fetchall()
            conn.close()
        return [dict(r) for r in rows]

    def get_project(self, project_id):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM projects WHERE id=? AND deleted_at IS NULL", (project_id,)).fetchone()
            conn.close()
        if not row:
            return None
        d = dict(row)
        try:
            d['data_json'] = json.loads(d.get('data_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            d['data_json'] = {}
        return d

    def delete_project_cascade(self, project_id):
        with _db_lock:
            conn = self.get_db()
            for table in ['projects', 'chapters', 'outlines', 'step_summaries', 'generation_status', 'outline_generation_status']:
                conn.execute(f"DELETE FROM {table} WHERE project_id=?", (project_id,))
            conn.commit()
            conn.close()

    # ========== Chapter CRUD ==========

    def save_chapter(self, project_id, chapter_number, title, content='', word_count=0, status='pending', version=1, error_message='', metadata=None):
        meta_str = self._safe_json(metadata or {})
        with _db_lock:
            conn = self.get_db()
            now = self._now()
            conn.execute("""
                INSERT INTO chapters (project_id, chapter_number, title, content, word_count, status, version, error_message, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                    title=excluded.title, content=excluded.content, word_count=excluded.word_count,
                    status=excluded.status, version=excluded.version, error_message=excluded.error_message,
                    metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
            """, (project_id, chapter_number, title, content, word_count, status, version, error_message, meta_str, now))
            conn.commit()
            conn.close()

    def get_chapter(self, project_id, chapter_number):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM chapters WHERE project_id=? AND chapter_number=?", (project_id, chapter_number)).fetchone()
            conn.close()
        return dict(row) if row else None

    def get_all_chapters(self, project_id):
        with _db_lock:
            conn = self.get_db()
            rows = conn.execute("SELECT * FROM chapters WHERE project_id=? ORDER BY chapter_number", (project_id,)).fetchall()
            conn.close()
        return [dict(r) for r in rows]

    def delete_chapter(self, project_id, chapter_number):
        with _db_lock:
            conn = self.get_db()
            conn.execute("DELETE FROM chapters WHERE project_id=? AND chapter_number=?", (project_id, chapter_number))
            conn.commit()
            conn.close()

    def get_chapter_count(self, project_id):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT COUNT(*) as cnt FROM chapters WHERE project_id=?", (project_id,)).fetchone()
            conn.close()
        return {'total': row['cnt'] if row else 0}

    def get_pending_chapters(self, project_id, total):
        with _db_lock:
            conn = self.get_db()
            rows = conn.execute("SELECT * FROM chapters WHERE project_id=? AND status='pending' ORDER BY chapter_number", (project_id,)).fetchall()
            conn.close()
        return [dict(r) for r in rows]

    # ========== Generation Status ==========

    def get_generation_status(self, project_id):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM generation_status WHERE project_id=?", (project_id,)).fetchone()
            conn.close()
        if not row:
            return {'is_running': 0, 'is_paused': 0, 'total_chapters': 0, 'completed_chapters': 0, 'failed_chapters': 0, 'current_chapter': 0}
        return dict(row)

    def start_generation(self, project_id, total_chapters, config):
        config_str = self._safe_json(config, {})
        with _db_lock:
            conn = self.get_db()
            conn.execute("""
                INSERT INTO generation_status (project_id, total_chapters, is_running, is_paused, config, started_at, updated_at)
                VALUES (?, ?, 1, 0, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    total_chapters=excluded.total_chapters, is_running=1, is_paused=0,
                    config=excluded.config, started_at=excluded.started_at, updated_at=excluded.updated_at,
                    completed_chapters=0, failed_chapters=0, current_chapter=0
            """, (project_id, total_chapters, config_str, self._now(), self._now()))
            conn.commit()
            conn.close()

    def pause_generation(self, project_id):
        with _db_lock:
            conn = self.get_db()
            conn.execute("UPDATE generation_status SET is_paused=1, updated_at=? WHERE project_id=?", (self._now(), project_id))
            conn.commit()
            conn.close()

    def stop_generation(self, project_id):
        with _db_lock:
            conn = self.get_db()
            conn.execute("UPDATE generation_status SET is_running=0, is_paused=0, updated_at=? WHERE project_id=?", (self._now(), project_id))
            conn.commit()
            conn.close()

    def update_generation_progress(self, project_id, current, completed, failed):
        with _db_lock:
            conn = self.get_db()
            conn.execute("""
                UPDATE generation_status SET current_chapter=?, completed_chapters=?, failed_chapters=?, updated_at=?
                WHERE project_id=?
            """, (current, completed, failed, self._now(), project_id))
            conn.commit()
            conn.close()

    # ========== Step Summaries ==========

    def save_step_summary(self, project_id, step, summary_json):
        summary_str = self._safe_json(summary_json)
        with _db_lock:
            conn = self.get_db()
            conn.execute("""
                INSERT INTO step_summaries (project_id, step, summary_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(project_id, step) DO UPDATE SET
                    summary_json=excluded.summary_json, updated_at=excluded.updated_at
            """, (project_id, step, summary_str, self._now()))
            conn.commit()
            conn.close()

    def get_step_summary(self, project_id, step):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM step_summaries WHERE project_id=? AND step=?", (project_id, step)).fetchone()
            conn.close()
        if not row:
            return None
        d = dict(row)
        try:
            d['summary_json'] = json.loads(d.get('summary_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            d['summary_json'] = {}
        return d

    def get_all_step_summaries(self, project_id):
        with _db_lock:
            conn = self.get_db()
            rows = conn.execute("SELECT * FROM step_summaries WHERE project_id=? ORDER BY id", (project_id,)).fetchall()
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

    # ========== Outline CRUD ==========

    def save_outline(self, project_id, chapter_number, title='', summary='', scenes='[]', characters='[]',
                     key_points='[]', emotion='', goal='', technique_focus='', book_overview='',
                     acts='[]', importance=0, status='pending', error_message='', metadata=None):
        scenes_str = self._safe_json(scenes, [])
        chars_str = self._safe_json(characters, [])
        kp_str = self._safe_json(key_points, [])
        acts_str = self._safe_json(acts, [])
        meta_str = self._safe_json(metadata or {})
        with _db_lock:
            conn = self.get_db()
            now = self._now()
            conn.execute("""
                INSERT INTO outlines (project_id, chapter_number, title, summary, scenes, characters,
                    key_points, emotion, goal, technique_focus, book_overview, acts, importance,
                    status, error_message, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, chapter_number) DO UPDATE SET
                    title=excluded.title, summary=excluded.summary, scenes=excluded.scenes,
                    characters=excluded.characters, key_points=excluded.key_points,
                    emotion=excluded.emotion, goal=excluded.goal, technique_focus=excluded.technique_focus,
                    book_overview=excluded.book_overview, acts=excluded.acts,
                    importance=excluded.importance, status=excluded.status,
                    error_message=excluded.error_message, metadata_json=excluded.metadata_json,
                    updated_at=excluded.updated_at
            """, (project_id, chapter_number, title, summary, scenes_str, chars_str, kp_str,
                  emotion, goal, technique_focus, book_overview, acts_str, importance,
                  status, error_message, meta_str, now))
            conn.commit()
            conn.close()

    def get_outline(self, project_id, chapter_number):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM outlines WHERE project_id=? AND chapter_number=?", (project_id, chapter_number)).fetchone()
            conn.close()
        return dict(row) if row else None

    def get_all_outlines(self, project_id):
        with _db_lock:
            conn = self.get_db()
            rows = conn.execute("SELECT * FROM outlines WHERE project_id=? ORDER BY chapter_number", (project_id,)).fetchall()
            conn.close()
        return [dict(r) for r in rows]

    def delete_outline(self, project_id, chapter_number):
        with _db_lock:
            conn = self.get_db()
            conn.execute("DELETE FROM outlines WHERE project_id=? AND chapter_number=?", (project_id, chapter_number))
            conn.commit()
            conn.close()

    def get_outline_generation_status(self, project_id):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM outline_generation_status WHERE project_id=?", (project_id,)).fetchone()
            conn.close()
        if not row:
            return {'is_running': 0, 'is_paused': 0, 'total_chapters': 0, 'completed_chapters': 0, 'failed_chapters': 0, 'current_chapter': 0}
        return dict(row)

    def start_outline_generation(self, project_id, total, config):
        config_str = self._safe_json(config, {})
        with _db_lock:
            conn = self.get_db()
            conn.execute("""
                INSERT INTO outline_generation_status (project_id, total_chapters, is_running, is_paused, config, started_at, updated_at)
                VALUES (?, ?, 1, 0, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    total_chapters=excluded.total_chapters, is_running=1, is_paused=0,
                    config=excluded.config, started_at=excluded.started_at, updated_at=excluded.updated_at,
                    completed_chapters=0, failed_chapters=0, current_chapter=0
            """, (project_id, total, config_str, self._now(), self._now()))
            conn.commit()
            conn.close()

    def pause_outline_generation(self, project_id):
        with _db_lock:
            conn = self.get_db()
            conn.execute("UPDATE outline_generation_status SET is_paused=1, updated_at=? WHERE project_id=?", (self._now(), project_id))
            conn.commit()
            conn.close()

    def stop_outline_generation(self, project_id):
        with _db_lock:
            conn = self.get_db()
            conn.execute("UPDATE outline_generation_status SET is_running=0, is_paused=0, updated_at=? WHERE project_id=?", (self._now(), project_id))
            conn.commit()
            conn.close()

    def update_outline_generation_progress(self, project_id, current, completed, failed):
        with _db_lock:
            conn = self.get_db()
            conn.execute("""
                UPDATE outline_generation_status SET current_chapter=?, completed_chapters=?, failed_chapters=?, updated_at=?
                WHERE project_id=?
            """, (current, completed, failed, self._now(), project_id))
            conn.commit()
            conn.close()


novel_db = NovelDB()
