# 用户指令记忆

本文件记录了用户的指令、偏好和教导，用于在未来的交互中提供参考。

## 格式

### 用户指令条目
用户指令条目应遵循以下格式：

[用户指令摘要]
- Date: [YYYY-MM-DD]
- Context: [提及的场景或时间]
- Instructions:
  - [用户教导或指示的内容，逐行描述]

### 项目知识条目
Agent 在任务执行过程中发现的条目应遵循以下格式：

[项目知识摘要]
- Date: [YYYY-MM-DD]
- Context: Agent 在执行 [具体任务描述] 时发现
- Category: [运维部署|构建方法|测试方法|排错调试|工作流协作|环境配置]
- Instructions:
  - [具体的知识点，逐行描述]

## 去重策略
- 添加新条目前，检查是否存在相似或相同的指令
- 若发现重复，跳过新条目或与已有条目合并
- 合并时，更新上下文或日期信息
- 这有助于避免冗余条目，保持记忆文件整洁

## 条目

### Docker 部署规范
- Date: 2026-07-02
- Context: 用户要求将项目迁移到 Docker 环境，今后新项目都用 Docker 管理
- Category: 运维部署
- Instructions:
  - 所有项目使用 Docker Compose 管理
  - 项目存放路径：`/home/ubuntu/<项目名>-docker/`
  - 所有项目共用主机 port 80，通过不同 URL 路径区分（如 `/fanqie/`、`/other/`）
  - 数据持久化使用 Docker Volume
  - 容器设置 `restart: unless-stopped`

### Docker 镜像拉取
- Date: 2026-07-02
- Context: 服务器无法访问 Docker Hub，需要使用镜像加速
- Category: 环境配置
- Instructions:
  - 使用 DaoCloud 镜像：`docker.m.daocloud.io/library/<image>`
  - 拉取后 tag 为官方名称：`docker tag docker.m.daocloud.io/library/<image> <image>`
  - 已缓存镜像：`nginx:alpine`、`python:3.11-slim`

### 服务器环境
- Date: 2026-07-02
- Context: 腾讯云 VPS 部署环境
- Category: 运维部署
- Instructions:
  - 服务器 IP：`140.143.210.177`，用户名 `ubuntu`，系统 Ubuntu 22.04
  - Docker 已安装（v29.6.1），Docker Compose v5.2.0
  - 旧服务已停止：systemd `fanqie-content`、系统 Nginx（避免端口冲突）
