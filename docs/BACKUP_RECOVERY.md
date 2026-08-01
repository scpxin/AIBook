# 数据库备份与恢复指南

## 概述

本文档说明如何备份和恢复番茄小说应用的 SQLite 数据库。

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_PATH` | `/app/data/fanqie.db` | 数据库文件路径 |
| `BACKUP_DIR` | `/app/data/backups` | 备份文件存储目录 |
| `MAX_BACKUPS` | `7` | 保留的备份数量 |

## 备份数据库

### 自动备份（推荐）

在 Kubernetes 或 Docker 环境中，建议设置定时任务自动执行备份：

```bash
# Crontab 示例：每天凌晨 2 点备份
0 2 * * * /workspace/scripts/backup.sh >> /var/log/backup.log 2>&1
```

### 手动备份

```bash
# 执行备份
./scripts/backup.sh

# 查看备份文件
ls -lh /app/data/backups/
```

输出示例：
```
[2026-01-30 02:00:01] 开始备份数据库：/app/data/fanqie.db
[2026-01-30 02:00:02] 备份完成：/app/data/backups/fanqie_20260130_020001.db.gz
[2026-01-30 02:00:02] 已清理旧备份，保留最近 7 个

当前备份列表:
fanqie_20260130_020001.db.gz 1.2M
fanqie_20260129_020001.db.gz 1.1M
fanqie_20260128_020001.db.gz 1.1M
```

## 恢复数据库

### 列出可用备份

```bash
./scripts/restore.sh
```

### 从备份恢复

```bash
# 从指定备份恢复
./scripts/restore.sh fanqie_20260130_020001.db.gz

# 恢复成功输出示例:
# [2026-01-30 10:00:01] 开始恢复数据库...
# 源文件：/app/data/backups/fanqie_20260130_020001.db.gz
# 目标：/app/data/fanqie.db
# [2026-01-30 10:00:02] 恢复完成
# 
# 数据库信息:
# 表数量：12
```

### 验证恢复

```bash
# 检查数据库完整性
sqlite3 /app/data/fanqie.db "PRAGMA integrity_check;"

# 预期输出: ok
```

## Docker 环境中的备份

### 在容器内执行

```bash
# 进入容器
docker exec -it fanqie-app /bin/bash

# 执行备份
./scripts/backup.sh

# 退出容器
exit

# 将备份文件复制到宿主机
docker cp fanqie-app:/app/data/backups ./backups
```

### 从宿主机执行

```bash
docker exec fanqie-app ./scripts/backup.sh
docker cp fanqie-app:/app/data/backups ./backups
```

## Kubernetes 环境中的备份

### 使用 CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fanqie-backup
spec:
  schedule: "0 2 * * *"  # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: fanqie-app:latest
            command:
            - /bin/bash
            - /app/scripts/backup.sh
            env:
            - name: DB_PATH
              value: /app/data/fanqie.db
            - name: BACKUP_DIR
              value: /app/data/backups
          restartPolicy: OnFailure
          volumeMounts:
          - name: data
            mountPath: /app/data
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: fanqie-data-pvc
```

### 使用 PV 存储备份

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fanqie-backups
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: nfs-storage
```

## 注意事项

1. **备份一致性**: 脚本使用文件复制方式备份，确保在低峰期执行
2. **备份保留策略**: 默认保留 7 个备份，可通过 `MAX_BACKUPS` 环境变量调整
3. **存储空间**: 定期监控备份目录大小，避免磁盘空间耗尽
4. **恢复测试**: 建议定期在测试环境验证备份可恢复性
5. **安全传输**: 跨环境传输备份文件时使用加密通道 (SCP/SFTP)

## 故障排查

### 备份失败

```bash
# 检查数据库文件是否存在
ls -la /app/data/fanqie.db

# 检查备份目录权限
ls -ld /app/data/backups

# 手动执行备份查看详细错误
bash -x ./scripts/backup.sh
```

### 恢复失败

```bash
# 检查备份文件完整性
gunzip -t fanqie_*.db.gz

# 检查数据库文件是否被占用
lsof /app/data/fanqie.db

# 停止应用后恢复
docker stop fanqie-app
./scripts/restore.sh fanqie_20260130_020001.db.gz
docker start fanqie-app
```

## 相关文档

- [部署指南](docs/deployment.md)
- [运维手册](docs/operations.md)
