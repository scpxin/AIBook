"""API Key 管理服务"""
import logging
import sqlite3
from datetime import datetime, timedelta

from app.models.api_key import APIKey, APIKeyCreate, APIKeyInDB
from app.utils.auth import generate_api_key, get_password_hash

logger = logging.getLogger(__name__)


class APIKeyService:
    """API Key 管理服务"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化 API Key 表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                key_hash TEXT NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                last_used_at TIMESTAMP,
                user_id INTEGER,
                permissions TEXT DEFAULT '["read"]'
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active)")
        conn.commit()
        conn.close()

    def create(self, data: APIKeyCreate, expires_days: int | None = None) -> APIKeyInDB:
        """创建新的 API Key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        raw_key = generate_api_key()
        key_hash = get_password_hash(raw_key)
        expires_at = datetime.utcnow() + timedelta(days=expires_days) if expires_days else None

        cursor.execute("""
            INSERT INTO api_keys (name, description, key_hash, expires_at, permissions)
            VALUES (?, ?, ?, ?, '["read"]')
        """, (data.name, data.description, key_hash, expires_at))

        key_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = cursor.fetchone()
        conn.close()

        api_key = APIKeyInDB(
            id=row[0],
            name=row[1],
            description=row[2],
            key_hash=row[3],
            is_active=bool(row[4]),
            created_at=row[5],
            expires_at=row[6],
            last_used_at=row[7],
            user_id=row[8],
            permissions=['read'],
        )

        # 返回时附带原始密钥 (仅显示一次)
        api_key.raw_key = raw_key  # type: ignore
        return api_key

    def get_by_id(self, key_id: int) -> APIKeyInDB | None:
        """根据 ID 获取 API Key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return APIKeyInDB(
            id=row[0],
            name=row[1],
            description=row[2],
            key_hash=row[3],
            is_active=bool(row[4]),
            created_at=row[5],
            expires_at=row[6],
            last_used_at=row[7],
            user_id=row[8],
            permissions=['read'],
        )

    def list_all(self, active_only: bool = False) -> list[APIKey]:
        """列出所有 API Key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM api_keys"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY created_at DESC"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [
            APIKey(
                id=row[0],
                name=row[1],
                description=row[2],
                key_hash=row[3][:8] + "..." + row[3][-8:],
                is_active=bool(row[4]),
                created_at=row[5],
                expires_at=row[6],
                last_used_at=row[7],
            )
            for row in rows
        ]

    def revoke(self, key_id: int) -> bool:
        """撤销 API Key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def update_last_used(self, key_hash: str):
        """更新最后使用时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE key_hash = ?",
            (key_hash,)
        )
        conn.commit()
        conn.close()


# 全局服务实例
_api_key_service: APIKeyService | None = None


def get_api_key_service(db_path: str) -> APIKeyService:
    """获取 API Key 服务实例"""
    global _api_key_service
    if not _api_key_service or _api_key_service.db_path != db_path:
        _api_key_service = APIKeyService(db_path)
    return _api_key_service
