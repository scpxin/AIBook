#!/bin/bash
set -e

# 配置
DB_PATH="${DATABASE_PATH:-/app/data/fanqie.db}"
BACKUP_DIR="${BACKUP_DIR:-/app/data/backups}"

# 显示用法
if [ $# -lt 1 ]; then
    echo "用法：$0 <备份文件名>"
    echo ""
    echo "可用的备份文件:"
    ls -lh "$BACKUP_DIR"/fanqie_*.db.gz 2>/dev/null | awk '{print "  " $9}'
    exit 1
fi

BACKUP_FILE="$1"

# 如果不是完整路径，在备份目录查找
if [[ ! "$BACKUP_FILE" = /* ]]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# 检查备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误：备份文件不存在：$BACKUP_FILE"
    exit 1
fi

# 解压并恢复
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始恢复数据库..."
echo "源文件：$BACKUP_FILE"
echo "目标：$DB_PATH"

# 创建目标目录
mkdir -p "$(dirname "$DB_PATH")"

# 解压备份
if [[ "$BACKUP_FILE" = *.gz ]]; then
    TEMP_DB=$(mktemp)
    gunzip -c "$BACKUP_FILE" > "$TEMP_DB"
    mv "$TEMP_DB" "$DB_PATH"
else
    cp "$BACKUP_FILE" "$DB_PATH"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 恢复完成"
echo ""
echo "数据库信息:"
sqlite3 "$DB_PATH" "SELECT '表数量：' || count(*) FROM sqlite_master WHERE type='table';"
