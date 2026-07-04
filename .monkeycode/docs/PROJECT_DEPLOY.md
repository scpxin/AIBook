# 项目部署指南

## 服务器信息

- **IP**: `140.143.210.177`
- **OS**: Ubuntu 22.04
- **用户**: `ubuntu`
- **SSH**: `sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@140.143.210.177`
- **访问地址**: `http://140.143.210.177/fanqie/`

---

## 文件结构（工作区 vs 服务器）

### 工作区（本地编辑）

```
/workspace/deploy/
├── docker-compose.yml          # Docker 编排（定义 bind mount 映射）
├── Dockerfile                  # 后端镜像构建
├── index-v2.html               # 前端（Vue 3 单文件应用）
├── nginx.conf                  # Nginx 配置
└── novel_creator/              # Python 模块（后端业务逻辑）
    ├── __init__.py
    ├── ai_client.py            # OpenAI 兼容 API 客户端
    ├── generator.py            # AI 生成核心（灵感/世界观/角色/大纲/章节）
    ├── prompts.py              # 全部 prompt 模板（含风格感知版）
    └── craft_prompts.py        # 网文技法 prompt 模板
```

### 服务器（运行时）

```
/home/ubuntu/fanqie-docker/     # Docker Compose 项目目录（bind mount 源）
├── docker-compose.yml
├── Dockerfile
├── index-v2.html               # ★ bind mount → nginx 容器
├── nginx.conf                  # ★ bind mount → nginx 容器
└── novel_creator/              # 构建时 COPY 到 backend 镜像
    ├── *.py
```

---

## 容器内部路径

| 容器 | 路径 | 来源 |
|------|------|------|
| `fanqie-backend` | `/app/server-v2.py` | Dockerfile COPY |
| `fanqie-backend` | `/app/novel_creator/*.py` | Dockerfile COPY |
| `fanqie-backend` | `/app/downloads/` | named volume |
| `fanqie-web` | `/usr/share/nginx/html/index.html` | bind mount `./index-v2.html` |
| `fanqie-web` | `/etc/nginx/conf.d/default.conf` | bind mount `./nginx.conf` |

---

## 部署流程

### 前端修改（index-v2.html / nginx.conf）

```bash
# 1. 编辑 /workspace/deploy/index-v2.html
# 2. 复制到 compose 目录（bind mount 源）
sshpass -p 'Tencent123c' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  /workspace/deploy/index-v2.html \
  ubuntu@140.143.210.177:/home/ubuntu/fanqie-docker/index-v2.html

# 3. 重启 web 容器（bind mount 是实时同步的，但保险起见重启）
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "cd /home/ubuntu/fanqie-docker && docker compose restart web"
```

**关键点**：`docker-compose.yml` 中 `web` 服务的 volumes 配置为：
```yaml
volumes:
  - ./index-v2.html:/usr/share/nginx/html/index.html:ro
  - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
```
所以**必须**把文件放到 `/home/ubuntu/fanqie-docker/` 目录，不是 `/tmp/`！

### 后端修改（novel_creator/*.py）

```bash
# 1. 编辑 /workspace/deploy/novel_creator/ 中的文件
# 2. 复制到服务器临时目录
sshpass -p 'Tencent123c' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  /workspace/deploy/novel_creator/generator.py \
  /workspace/deploy/novel_creator/prompts.py \
  /workspace/deploy/novel_creator/craft_prompts.py \
  ubuntu@140.143.210.177:/tmp/novel_creator/

# 3. docker cp 到运行中的容器
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "docker cp /tmp/novel_creator/generator.py fanqie-backend:/app/novel_creator/generator.py && \
  docker cp /tmp/novel_creator/prompts.py fanqie-backend:/app/novel_creator/prompts.py && \
  docker cp /tmp/novel_creator/craft_prompts.py fanqie-backend:/app/novel_creator/craft_prompts.py"

# 4. 重启 backend
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
```

**关键点**：backend 的 Python 文件是构建时 COPY 到镜像的，运行时用 `docker cp` 覆盖。

### 后端修改（server-v2.py）

```bash
# 1. 编辑 /workspace/deploy/server-v2.py
# 2. 复制到服务器
sshpass -p 'Tencent123c' scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  /workspace/deploy/server-v2.py \
  ubuntu@140.143.210.177:/tmp/server-v2.py

# 3. docker cp 到容器
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "docker cp /tmp/server-v2.py fanqie-backend:/app/server-v2.py"

# 4. 重启 backend
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
```

---

## 快速部署脚本

将以下脚本保存为 `/workspace/deploy/sync.sh`：

```bash
#!/bin/bash
set -e
HOST="ubuntu@140.143.210.177"
PASS="Tencent123c"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SCP="sshpass -p '$PASS' scp $SSH_OPTS"
SSH="sshpass -p '$PASS' ssh $SSH_OPTS $HOST"

case "$1" in
  frontend)
    $SCP /workspace/deploy/index-v2.html $HOST:/home/ubuntu/fanqie-docker/index-v2.html
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart web"
    echo "Frontend deployed."
    ;;
  backend)
    $SCP /workspace/deploy/novel_creator/generator.py \
         /workspace/deploy/novel_creator/prompts.py \
         /workspace/deploy/novel_creator/craft_prompts.py \
         $HOST:/tmp/novel_creator/
    $SSH "docker cp /tmp/novel_creator/generator.py fanqie-backend:/app/novel_creator/generator.py && \
          docker cp /tmp/novel_creator/prompts.py fanqie-backend:/app/novel_creator/prompts.py && \
          docker cp /tmp/novel_creator/craft_prompts.py fanqie-backend:/app/novel_creator/craft_prompts.py"
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
    echo "Backend modules deployed."
    ;;
  server)
    $SCP /workspace/deploy/server-v2.py $HOST:/tmp/server-v2.py
    $SSH "docker cp /tmp/server-v2.py fanqie-backend:/app/server-v2.py"
    $SSH "cd /home/ubuntu/fanqie-docker && docker compose restart backend"
    echo "Server script deployed."
    ;;
  all)
    $0 frontend
    $0 backend
    $0 server
    ;;
  *)
    echo "Usage: $0 {frontend|backend|server|all}"
    exit 1
    ;;
esac
```

---

## 常见错误排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 改了前端但页面没变 | 文件没放到 compose 目录 | 确认复制到 `/home/ubuntu/fanqie-docker/index-v2.html` |
| 改了后端但行为没变 | `docker cp` 后没重启 | 执行 `docker compose restart backend` |
| 容器内文件被覆盖 | 重启后 bind mount 重新挂载 | bind mount 是实时的，不需要担心 |
| 502 Bad Gateway | backend 未启动或健康检查失败 | `docker logs fanqie-backend` 查看错误 |

---

## 验证部署

```bash
# 检查容器状态
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "cd /home/ubuntu/fanqie-docker && docker compose ps"

# 检查后端日志
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "docker logs fanqie-backend --tail 10"

# 检查前端是否包含新代码
sshpass -p 'Tencent123c' ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  ubuntu@140.143.210.177 "docker exec fanqie-web grep -c 'customPrompt' /usr/share/nginx/html/index.html"
```
