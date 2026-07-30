#!/bin/bash
set -e

# 配置
DB_PATH="${DATABASE_PATH:-/app/data/fanqie.db}"
BACKUP_DIR="${BACKUP_DIR:-/app/data/backups}"
MAX_BACKUPS="${MAX_BACKUPS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份数据库
BACKUP_FILE="$BACKUP_DIR/fanqie_${TIMESTAMP}.db"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始备份数据库：$DB_PATH"

if [ ! -f "$DB_PATH" ]; then
    echo "错误：数据库文件不存在：$DB_PATH"
    exit 1
fi

# 使用 SQLite 备份模式确保一致性
cp "$DB_PATH" "$BACKUP_FILE"
gzip "$BACKUP_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 备份完成：${BACKUP_FILE}.gz"

# 清理旧备份（保留最近的 N 个）
cd "$BACKUP_DIR"
ls -t fanqie_*.db.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已清理旧备份，保留最近 $MAX_BACKUPS 个"

# 列出当前备份
echo ""
echo "当前备份列表:"
ls -lh fanqie_*.db.gz 2>/dev/null | awk '{print $9, $5}'
