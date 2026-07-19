"""Database wrapper module — V2 项目持久化"""
import json
import sqlite3
import threading
import time

from app.config import DB_PATH

_db_lock = threading.RLock()


class NovelDB:
    """项目数据的 SQLite 持久化封装"""

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
                CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at);
                CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived);
            """)
            conn.commit()
            conn.close()

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

    def get_project(self, project_id):
        with _db_lock:
            conn = self.get_db()
            row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            conn.close()
        if not row:
            return None
        d = dict(row)
        try:
            d['data_json'] = json.loads(d.get('data_json', '{}'))
        except (json.JSONDecodeError, TypeError):
            d['data_json'] = {}
        return d


novel_db = NovelDB()
