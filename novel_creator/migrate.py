"""数据库迁移脚本 — 检测旧库并添加V2表

用法:
    python migrate.py              # 执行迁移(幂等)
    python migrate.py --check      # 仅检查,不执行
    python migrate.py --rollback   # 删除所有V2表(危险)

退出码:
    0 — 成功 / 已是最新
    1 — 迁移失败
"""
import argparse
import os
import sqlite3
import sys

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'))
V2_TABLE_PREFIX = 'v2_'


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_existing_v2_tables(conn):
    """获取已存在的V2表"""
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
        (f'{V2_TABLE_PREFIX}%',)
    )
    return {row[0] for row in cur.fetchall()}


def check_only(args):
    """仅检查,不执行迁移"""
    conn = get_connection()
    v2_tables = get_existing_v2_tables(conn)
    conn.close()

    if v2_tables:
        print(f'[OK] 数据库已是最新: {len(v2_tables)} 张V2表已存在')
        return 0
    else:
        print('[INFO] 未检测到V2表,需要执行迁移')
        return 0


def run_migration(args):
    """执行迁移"""
    if not os.path.exists(DB_PATH):
        print(f'[ERROR] 数据库文件不存在: {DB_PATH}')
        return 1

    try:
        # 确保能正确导入 novel_creator 模块
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        if _script_dir not in sys.path:
            sys.path.insert(0, _script_dir)
        from database_v2 import init_db_v2

        conn = get_connection()
        before_tables = get_existing_v2_tables(conn)
        conn.close()

        # 执行初始化(幂等)
        init_db_v2()

        conn = get_connection()
        after_tables = get_existing_v2_tables(conn)
        conn.close()

        new_count = len(after_tables) - len(before_tables)
        print(f'[OK] 迁移完成: {len(after_tables)} 张V2表存在 (新增 {new_count})')
        return 0

    except Exception as e:
        print(f'[ERROR] 迁移失败: {e}')
        import traceback
        traceback.print_exc()
        return 1


def rollback(args):
    """删除所有V2表(危险操作)"""
    if not args.force:
        print('[WARN] 此操作将删除所有V2数据表! 使用 --force 确认')
        return 1

    conn = get_connection()
    v2_tables = get_existing_v2_tables(conn)

    if not v2_tables:
        print('[INFO] 未找到V2表,无需回滚')
        conn.close()
        return 0

    print(f'[INFO] 将删除 {len(v2_tables)} 张V2表...')

    cur = conn.cursor()
    for table in sorted(v2_tables, reverse=True):
        try:
            cur.execute(f'DROP TABLE IF EXISTS {table}')
            print(f'  已删除: {table}')
        except Exception as e:
            print(f'  删除失败 {table}: {e}')

    conn.commit()
    conn.close()
    print(f'[OK] 回滚完成,删除了 {len(v2_tables)} 张表')
    return 0


def main():
    parser = argparse.ArgumentParser(description='数据库迁移工具 - V2 18模块创作流水线')
    parser.add_argument('--check', action='store_true', help='仅检查不执行')
    parser.add_argument('--rollback', action='store_true', help='删除所有V2表')
    parser.add_argument('--force', action='store_true', help='强制执行(配合--rollback)')
    parser.add_argument('--db-path', help='自定义数据库路径')

    args = parser.parse_args()

    if args.db_path:
        global DB_PATH
        DB_PATH = args.db_path

    if args.rollback:
        return rollback(args)
    elif args.check:
        return check_only(args)
    else:
        return run_migration(args)


if __name__ == '__main__':
    sys.exit(main())
