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
