# Docker 部署管理文档

> 本文档适用于腾讯云 Ubuntu 22.04 服务器上的 Docker 项目管理。

## 目录

- [一、架构概览](#一架构概览)
- [二、服务器环境](#二服务器环境)
- [三、项目目录结构](#三项目目录结构)
- [四、核心配置文件](#四核心配置文件)
- [五、日常操作命令](#五日常操作命令)
- [六、部署新服务](#六部署新服务)
- [七、数据管理](#七数据管理)
- [八、镜像管理](#八镜像管理)
- [九、网络与安全](#九网络与安全)
- [十、故障排查](#十故障排查)
- [十一、Docker 最佳实践](#十一docker-最佳实践)

---

## 一、架构概览

```
                        Internet
                           │
                           ▼
                 ┌─────────────────┐
                 │  腾讯云防火墙    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Host:80        │
                 │  Nginx 容器     │
                 │  (fanqie-web)   │
                 │  - 静态前端     │
                 │  - 反向代理     │
                 └────────┬────────┘
                          │ fanqie-net (内部网络)
                          ▼
                 ┌─────────────────┐
                 │  Host: --       │
                 │  Python 容器    │
                 │  (fanqie-backend)│
                 │  - API 服务     │
                 │  - 下载/AI逻辑  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Docker Volume  │
                 │  fanqie-downloads│
                 │  (持久化存储)   │
                 └─────────────────┘
```

### 设计原则

| 原则 | 说明 |
|------|------|
| **前后端分离** | Nginx 容器处理静态资源和 API 代理，Python 容器仅处理业务逻辑 |
| **数据持久化** | 用户下载内容通过 Docker Volume 持久化，容器重启不丢失 |
| **网络隔离** | 后端容器不暴露主机端口，仅通过内部网络访问 |
| **自动恢复** | `restart: unless-stopped` 确保容器异常退出后自动重启 |
| **健康检查** | 后端配置健康检查，前端等待后端健康后才启动 |

---

## 二、服务器环境

### Docker 信息

```
Docker 版本   : 29.6.1
Compose 版本  : v5.2.0
操作系统      : Ubuntu 22.04
服务器 IP     : 140.143.210.177
```

### 环境变量

```bash
# Docker 镜像加速（DaoCloud）
# 当无法访问 Docker Hub 时使用
export DOCKER_MIRROR="docker.m.daocloud.io/library"
```

### 目录规范

| 路径 | 用途 |
|------|------|
| `/home/ubuntu/<项目名>-docker/` | 项目根目录 |
| `/var/lib/docker/volumes/` | Docker Volume 存储位置 |
| `/etc/docker/daemon.json` | Docker  daemon 配置 |

---

## 三、项目目录结构

```
fanqie-docker/
├── docker-compose.yml      # Docker Compose 服务编排
├── Dockerfile              # 后端容器镜像构建文件
├── nginx.conf              # Nginx 反向代理 + 静态资源配置
├── server-v2.py            # Python 后端服务代码
├── index-v2.html           # 前端页面（单文件应用）
└── DOCKER.md               # 本文档
```

### 说明

- 每个项目独立一个目录，以 `-docker` 后缀命名
- 所有服务通过 `docker-compose.yml` 统一管理
- 前端 HTML 文件通过 Volume 挂载到 Nginx 容器（`ro` 只读）
- 后端代码通过 Dockerfile 构建为独立镜像

---

## 四、核心配置文件

### 4.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY server-v2.py .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["python3", "server-v2.py"]
```

**说明：**
- 使用 `python:3.11-slim` 基础镜像（体积小，约 50MB）
- `PYTHONUNBUFFERED=1` 确保日志实时输出到 stdout
- `PORT` 环境变量可通过 `docker-compose.yml` 覆盖

### 4.2 docker-compose.yml

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fanqie-backend
    environment:
      - PORT=8000
      - DOWNLOAD_DIR=/app/downloads
    volumes:
      - fanqie-downloads:/app/downloads
    restart: unless-stopped
    networks:
      - fanqie-net
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/search?q=test')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  web:
    image: nginx:alpine
    container_name: fanqie-web
    ports:
      - "80:80"
    volumes:
      - ./index-v2.html:/usr/share/nginx/html/index.html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - fanqie-net

volumes:
  fanqie-downloads:

networks:
  fanqie-net:
    driver: bridge
```

**配置说明：**

| 配置项 | 说明 |
|--------|------|
| `build.context: .` | 构建上下文为当前目录 |
| `container_name` | 容器名称，便于直接引用 |
| `environment` | 环境变量注入 |
| `volumes` | 数据持久化/文件挂载 |
| `restart: unless-stopped` | 手动停止外，其他情况自动重启 |
| `healthcheck` | 健康检查，确保服务可用 |
| `depends_on.condition` | 等待依赖服务健康后才启动 |
| `networks` | 自定义桥接网络，实现服务间隔离通信 |

### 4.3 nginx.conf

```nginx
server {
    listen 80;
    server_name _;

    # Root redirect
    location = / {
        return 302 /fanqie/;
    }

    # Redirect /fanqie to /fanqie/
    location = /fanqie {
        return 301 /fanqie/;
    }

    # Main app path
    location /fanqie/ {
        alias /usr/share/nginx/html/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # API proxy under /fanqie/
    location /fanqie/api/ {
        rewrite ^/fanqie(/.*)$ $1 break;
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }
}
```

**关键配置：**
- `proxy_pass http://backend:8000` — 使用 Docker 内部 DNS 服务发现
- `proxy_read_timeout 120s` — AI 请求耗时较长，设置为 120 秒
- `rewrite ^/fanqie(/.*)$ $1 break` — 去掉 URL 前缀后再转发给后端

---

## 五、日常操作命令

> 所有命令在项目目录下执行：`cd /home/ubuntu/fanqie-docker`

### 5.1 启动服务

```bash
# 构建镜像并启动（首次或代码变更后使用）
docker compose up -d --build

# 仅启动（不重新构建）
docker compose up -d

# 前台启动（查看实时日志）
docker compose up
```

### 5.2 停止服务

```bash
# 停止并删除容器（保留 Volume 数据）
docker compose down

# 停止并删除容器 + 镜像 + 网络
docker compose down --rmi all
```

### 5.3 查看状态

```bash
# 查看 Compose 项目中的容器状态
docker compose ps

# 查看所有容器（包括非 Compose 管理）
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看资源使用
docker stats --no-stream
```

### 5.4 查看日志

```bash
# 实时跟踪所有服务日志
docker compose logs -f

# 只看后端日志
docker compose logs -f backend

# 只看前端 Nginx 日志
docker compose logs -f web

# 最近 N 行日志
docker compose logs --tail 100

# 带时间戳
docker compose logs -f --timestamps
```

### 5.5 重启服务

```bash
# 全部重启
docker compose restart

# 重启单个服务
docker compose restart backend

# 优雅重启（零停机）
docker compose up -d --force-recreate backend
```

### 5.6 更新代码后重新部署

```bash
# 1. 上传新文件到服务器（通过 scp/sftp）
scp server-v2.py ubuntu@140.143.210.177:/home/ubuntu/fanqie-docker/

# 2. 在服务器项目目录下执行
cd /home/ubuntu/fanqie-docker
docker compose down
docker compose up -d --build

# 或者一行命令（仅重启+重建，不停机部署）
docker compose up -d --build --force-recreate
```

### 5.7 进入容器调试

```bash
# 进入后端容器（Python 环境）
docker exec -it fanqie-backend bash

# 进入前端容器（Alpine Linux，使用 sh）
docker exec -it fanqie-web sh

# 在容器内执行单条命令
docker exec fanqie-backend python3 -c "print('hello')"

# 查看容器内文件
docker exec fanqie-backend ls -la /app/downloads/
```

### 5.8 复制文件

```bash
# 从容器内复制文件到主机
docker cp fanqie-backend:/app/downloads/ ./backup/

# 从主机复制文件到容器内
docker cp ./new-server.py fanqie-backend:/app/server-v2.py
```

---

## 六、部署新服务

### 6.1 快速部署模板

```bash
# 1. 创建项目目录
mkdir -p /home/ubuntu/my-service-docker
cd /home/ubuntu/my-service-docker

# 2. 创建 Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY server.py .
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python3", "server.py"]
EOF

# 3. 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  backend:
    build: .
    container_name: my-service-backend
    volumes:
      - my-service-data:/app/data
    restart: unless-stopped
    networks:
      - my-service-net

  web:
    image: nginx:alpine
    container_name: my-service-web
    ports:
      - "8080:80"
    volumes:
      - ./index.html:/usr/share/nginx/html/index.html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - my-service-net

volumes:
  my-service-data:

networks:
  my-service-net:
    driver: bridge
EOF

# 4. 创建 nginx.conf（按需修改路径前缀和 API 路由）
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    location /my-service/ {
        alias /usr/share/nginx/html/;
        index index.html;
        try_files $uri $uri/ =404;
    }
    location /my-service/api/ {
        rewrite ^/my-service(/.*)$ $1 break;
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }
}
EOF

# 5. 启动
docker compose up -d --build
```

### 6.2 端口分配策略

| 项目 | 主机端口 | URL 路径 | 容器名 |
|------|----------|----------|--------|
| 番茄小说 | 80 | `/fanqie/` | fanqie-backend / fanqie-web |
| 新服务 A | 8080 | `/service-a/` | service-a-backend / service-a-web |
| 新服务 B | 8081 | `/service-b/` | service-b-backend / service-b-web |

### 6.3 多服务共用 80 端口

如果需要多个服务共用 80 端口，在主 Nginx 中添加 location 分发：

```nginx
 server {
    listen 80;
    server_name _;

    # 番茄小说
    location /fanqie/ {
        proxy_pass http://localhost:80/;
        # ... 保留原有 nginx.conf 中的配置
    }

    # 新服务 A
    location /service-a/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
    }
}
```

---

## 七、数据管理

### 7.1 Docker Volume 操作

```bash
# 列出所有 Volume
docker volume ls

# 查看详情
docker volume inspect fanqie-docker_fanqie-downloads

# 删除未使用的 Volume
docker volume prune
```

### 7.2 数据备份

```bash
# 备份整个 Volume 为 tar.gz
docker run --rm \
  -v fanqie-docker_fanqie-downloads:/data \
  -v /home/ubuntu/backups:/backup \
  alpine tar czf /backup/fanqie-downloads-$(date +%Y%m%d).tar.gz -C /data .

# 恢复备份
docker run --rm \
  -v fanqie-docker_fanqie-downloads:/data \
  -v /home/ubuntu/backups:/backup \
  alpine tar xzf /backup/fanqie-downloads-20260702.tar.gz -C /data
```

### 7.3 数据迁移

```bash
# 从旧位置迁移数据到新 Volume
# 假设旧数据在 /var/www/fanqie/downloads/
docker run --rm \
  -v fanqie-docker_fanqie-downloads:/dest \
  -v /var/www/fanqie/downloads:/src:ro \
  alpine cp -r /src/. /dest/
```

---

## 八、镜像管理

### 8.1 Docker Hub 镜像加速

> 当前服务器无法直接访问 `docker.io`，使用 DaoCloud 镜像加速。

```bash
# 拉取镜像
docker pull docker.m.daocloud.io/library/<镜像名>:<标签>

# 标记为官方名称（使 docker-compose 可直接使用）
docker tag docker.m.daocloud.io/library/<镜像名>:<标签> <镜像名>:<标签>
```

### 8.2 已缓存镜像

| 镜像 | 大小（约） | 用途 |
|------|-----------|------|
| `nginx:alpine` | 40 MB | 前端静态服务、反向代理 |
| `python:3.11-slim` | 50 MB | Python 后端服务 |

### 8.3 常用镜像拉取

```bash
# Web 服务器
docker pull docker.m.daocloud.io/library/nginx:alpine && \
  docker tag docker.m.daocloud.io/library/nginx:alpine nginx:alpine

# Python
docker pull docker.m.daocloud.io/library/python:3.11-slim && \
  docker tag docker.m.daocloud.io/library/python:3.11-slim python:3.11-slim

# Node.js
docker pull docker.m.daocloud.io/library/node:20-alpine && \
  docker tag docker.m.daocloud.io/library/node:20-alpine node:20-alpine

# Redis
docker pull docker.m.daocloud.io/library/redis:7-alpine && \
  docker tag docker.m.daocloud.io/library/redis:7-alpine redis:7-alpine

# MySQL
docker pull docker.m.daocloud.io/library/mysql:8 && \
  docker tag docker.m.daocloud.io/library/mysql:8 mysql:8
```

### 8.4 清理镜像

```bash
# 列出所有镜像
docker images

# 删除未使用的镜像
docker image prune -a

# 查看所有镜像占用空间
docker system df

# 深度清理（谨慎使用，会删除所有未使用的镜像、容器、网络、Volume）
docker system prune -a --volumes
```

---

## 九、网络与安全

### 9.1 Docker 网络

```bash
# 列出网络
docker network ls

# 查看网络详情
docker network inspect fanqie-docker_fanqie-net

# 网络隔离说明：
# - backend 容器仅连接 fanqie-net，不暴露主机端口
# - web 容器连接 fanqie-net + 暴露主机 80 端口
# - 外部无法直接访问 backend:8000，只能通过 web 容器代理
```

### 9.2 安全建议

1. **不要将敏感信息写入 Dockerfile** — 使用环境变量或 Docker Secret
2. **容器内不以 root 运行** — 在 Dockerfile 中添加非 root 用户
3. **限制容器资源** — 使用 `deploy.resources.limits` 限制 CPU/内存
4. **定期更新镜像** — 关注基础镜像的安全更新

```yaml
# 资源限制示例
services:
  backend:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## 十、故障排查

### 10.1 容器无法启动

```bash
# 查看日志
docker compose logs backend

# 常见原因：
# 1. 端口被占用 → 修改 ports 映射
# 2. Dockerfile 语法错误 → docker build 单独测试
# 3. 镜像拉取失败 → 检查网络/使用镜像加速
# 4. 健康检查不通过 → 检查 healthcheck 命令是否合理
```

### 10.2 端口冲突

```bash
# 检查端口占用
sudo ss -tlnp | grep :80
sudo lsof -i :80

# 解决方案：修改 docker-compose.yml
ports:
  - "8080:80"   # 将 80 改为其他端口
```

### 10.3 前端能访问但 API 报错

```bash
# 1. 检查后端日志
docker compose logs backend

# 2. 检查 Nginx 配置语法
docker exec fanqie-web nginx -t

# 3. 检查后端是否健康
docker inspect fanqie-backend --format='{{.State.Health.Status}}'

# 4. 测试内部网络连通性
docker exec fanqie-web wget -qO- http://backend:8000/api/search?q=test

# 5. 检查 proxy_pass 地址是否正确
docker exec fanqie-web cat /etc/nginx/conf.d/default.conf
```

### 10.4 构建失败

```bash
# 单独测试构建
docker build -t test-backend .

# 清理缓存后重新构建
docker compose build --no-cache

# 查看详细构建日志
docker compose up -d --build --progress=plain
```

### 10.5 磁盘空间不足

```bash
# 查看磁盘使用详情
docker system df -v

# 清理未使用的资源
docker system prune -a        # 删除未使用镜像、容器、网络
docker volume prune            # 删除未使用 Volume
docker builder prune -a        # 删除构建缓存
```

### 10.6 常用诊断命令

```bash
# 容器内进程
docker exec fanqie-backend ps aux

# 容器资源使用
docker stats fanqie-backend --no-stream

# 容器详细信息
docker inspect fanqie-backend

# 容器文件变更
docker diff fanqie-backend

# 实时事件监控
docker events --filter 'container=fanqie-backend'
```

---

## 十一、Docker 最佳实践

### 11.1 Dockerfile 最佳实践

```dockerfile
# 使用多阶段构建减小镜像体积
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local COPY . .
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["python3", "server.py"]
```

### 11.2 开发工作流

```bash
# 1. 本地开发修改代码
vim server-v2.py

# 2. 提交到 Git
git add . && git commit -m "update feature"

# 3. 推送到 GitHub
git push origin main

# 4. 在服务器拉取最新代码
ssh ubuntu@140.143.210.177
cd /home/ubuntu/fanqie-docker
docker compose down
git pull origin main  # 如果服务器上有 git repo
# 或 scp 上传新文件
docker compose up -d --build
```

### 11.3 监控建议

```bash
# 设置日志轮转（防止日志占满磁盘）
# 在 docker-compose.yml 中添加：
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 11.4 Compose 命令速查表

| 命令 | 用途 |
|------|------|
| `docker compose up -d` | 启动服务 |
| `docker compose up -d --build` | 构建并启动 |
| `docker compose down` | 停止并删除容器 |
| `docker compose down -v` | 停止并删除容器+Volume |
| `docker compose ps` | 查看服务状态 |
| `docker compose logs -f` | 实时日志 |
| `docker compose restart` | 重启所有服务 |
| `docker compose exec backend bash` | 进入容器 |
| `docker compose pull` | 拉取最新镜像 |
| `docker compose build --no-cache` | 无缓存构建 |
