# AI创作平台

基于 Docker 前后端分离架构的小说下载与 AI 小说创作平台，支持风格分析驱动的全流程创作。

## 架构

```
┌─────────────────────────────────────────────────────┐
│ Docker Compose                                       │
│  ┌──────────────────┐     ┌──────────────────────┐  │
│  │ frontend (Nginx) │────▶│ backend (FastAPI)    │  │
│  │ Vue 3 + Vite     │     │ Python 3.11          │  │
│  │ Port 80          │     │ Port 8000            │  │
│  └──────────────────┘     └──────────────────────┘  │
│         │                          │                │
│         ▼                          ▼                │
│  /fanqie/api/* proxy          SQLite + WAL          │
└─────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| 后端 | Python 3.11 + FastAPI + Uvicorn + Pydantic |
| 数据库 | SQLite + WAL 模式 |
| 部署 | Docker Compose (frontend Nginx + backend Python) |

## 在线访问

```
http://140.143.210.177/fanqie/
```

## 功能概览

### 小说下载
- 搜索小说（支持书名、作者、链接）
- 查看章节目录
- 下载整本小说到服务器（支持暂停/继续）
- 下载内容持久化存储

### AI 创作
- **灵感生成**：AI 生成书名、简介、主题、类型选项
- **世界观构建**：自动生成时间背景、空间环境、世界规则
- **角色生成**：批量生成角色和组织（含性格、背景、关系）
- **大纲生成**：自动生成章节大纲
- **章节生成**：根据大纲逐章生成正文（支持流式输出）
- **风格分析**：分析任意文本的写作风格
- **风格仿写**：根据分析结果仿写新内容

### 数据持久化
- **项目保存**：项目信息保存到 SQLite，支持加载/删除
- **章节持久化**：每章生成完毕立即保存到数据库，刷新后可恢复
- **大纲持久化**：总纲和细纲自动保存，下次可继续创作
- **步骤摘要联动**：自动生成世界观/角色/大纲的联动上下文
- **进度实时追踪**：生成状态实时保存，暂停/继续/恢复全支持
- **断点续传**：中断后重新生成时跳过已完成章节

### 网文技法
- AI 检测与文风修复
- 黄金三章分析
- 钩子分析、爽点分析
- 质量评分
- 技法化章节生成

## 快速开始

### 前置要求

- Docker 29+
- Docker Compose v5+

### 启动服务

```bash
git clone https://github.com/scpxin/AIBook.git
cd AIBook/deploy
docker compose -f docker-compose.v2.yml up -d
```

服务启动后访问 `http://<服务器IP>/fanqie/`

### 配置 AI 模型

1. 点击右上角设置图标
2. 添加大模型配置（支持所有 OpenAI 兼容 API）
3. 常用预设：
   - 智谱 GLM-4-Flash（免费）
   - DeepSeek V3
   - 通义千问 Turbo

## 项目结构

```
AIBook/
├── deploy/
│   ├── docker-compose.v2.yml      # Docker Compose 编排
│   ├── docker-compose.yml          # 旧版编排（兼容）
│   ├── backend_v2/                 # FastAPI 后端
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py             # FastAPI 入口
│   │       ├── config.py           # 环境变量配置
│   │       ├── database.py         # 数据库初始化
│   │       ├── models/
│   │       │   └── schemas.py      # Pydantic 请求/响应模型
│   │       ├── api/                # API 路由模块
│   │       │   ├── projects.py     # 项目管理
│   │       │   ├── chapters.py     # 章节管理
│   │       │   ├── outlines.py     # 大纲管理
│   │       │   ├── step_summaries.py # 步骤摘要
│   │       │   ├── novel.py        # AI 生成
│   │       │   ├── craft.py        # 网文技法
│   │       │   ├── download.py     # 小说下载
│   │       │   └── ai.py           # AI 工具
│   │       └── services/
│   │           ├── novel_generator.py
│   │           └── download_service.py
│   ├── frontend/                   # Vue 3 前端
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.ts             # 应用入口
│   │       ├── App.vue             # 根组件
│   │       ├── router/             # Vue Router 路由
│   │       ├── stores/             # Pinia 状态管理
│   │       ├── api/                # API 客户端封装
│   │       ├── components/         # 通用组件
│   │       └── views/              # 页面组件
│   ├── novel_creator/              # AI 小说创作模块
│   │   ├── database.py             # SQLite 数据库操作
│   │   ├── generator.py            # AI 生成器
│   │   ├── prompts.py              # Novel AI prompt 模板
│   │   ├── craft_prompts.py        # 网文技法 prompt 模板
│   │   └── ai_client.py            # OpenAI 兼容 API 客户端
│   ├── index-v2.html               # 旧版前端（兼容）
│   ├── server-v2.py                # 旧版后端（兼容）
│   └── nginx.conf                  # 旧版 Nginx 配置
├── .monkeycode/
│   ├── docs/                       # 项目文档
│   └── specs/                      # 功能规格文档
└── README.md                       # 本文件
```

## API 接口

> 所有API请求通过前端 Nginx 代理 `/fanqie/api/` → `/api/`

### 项目管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/projects/save` | POST | 保存/更新项目 |
| `/api/projects/list` | POST | 列出项目摘要 |
| `/api/projects/load` | POST | 加载完整项目 |
| `/api/projects/delete` | POST | 级联删除项目 |

### 章节管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chapters/save` | POST | 保存章节（自动递增版本） |
| `/api/chapters/get` | POST | 获取单章 |
| `/api/chapters/delete` | POST | 删除单章 |
| `/api/chapters/regenerate` | POST | 重新生成 |
| `/api/chapters/status` | POST | 获取生成状态 |
| `/api/chapters/generation/start` | POST | 开始批量生成 |
| `/api/chapters/generation/pause` | POST | 暂停 |
| `/api/chapters/generation/stop` | POST | 停止 |
| `/api/chapters/generation/update` | POST | 更新进度 |

### 大纲管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/outline/save` | POST | 保存大纲 |
| `/api/outline/get` | POST | 获取大纲 |
| `/api/outline/delete` | POST | 删除大纲 |
| `/api/outline/generation/start` | POST | 开始大纲生成 |
| `/api/outline/generation/pause` | POST | 暂停 |
| `/api/outline/generation/stop` | POST | 停止 |

### 步骤摘要

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/step-summary/save` | POST | 保存步骤摘要 |
| `/api/step-summary/get` | POST | 获取步骤摘要 |

### AI 创作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/novel/inspiration/{title,description,theme,genre}` | POST | 灵感生成 |
| `/api/novel/worldbuilding` | POST | 构建世界观 |
| `/api/novel/characters` | POST | 生成角色 |
| `/api/novel/outline` | POST | 生成大纲 |
| `/api/novel/book-overview` | POST | 生成全书总纲（支持stream） |
| `/api/novel/chapter-outline` | POST | 生成章节细纲（支持stream） |
| `/api/novel/chapter` | POST | 生成章节正文 |
| `/api/novel/chapter/polish` | POST | 润色章节 |
| `/api/novel/chapter/summarize` | POST | 章节摘要 |

### 风格分析与网文技法

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/analyze-style` | POST | 风格分析 |
| `/api/generate-style` | POST | 风格仿写 |
| `/api/novel/craft/chapter` | POST | 技法化章节生成 |
| `/api/novel/craft/titles` | POST | 标题生成 |
| `/api/novel/craft/descriptions` | POST | 描述生成 |
| `/api/novel/craft/report` | POST | 综合报告 |

### 小说下载

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/search` | GET | 搜索小说 |
| `/api/directory` | GET | 获取章节目录 |
| `/api/content` | GET | 获取章节内容 |
| `/api/download/start` | GET | 开始下载 |
| `/api/download/status` | GET | 查询下载进度 |
| `/api/download/pause` | GET | 暂停下载 |
| `/api/download/resume` | GET | 继续下载 |
| `/api/download/file` | GET | 下载文件 |
| `/api/downloads/list` | GET | 获取已下载书籍列表 |

### AI 通用

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/ai/analyze` | POST | AI 分析 |
| `/api/ai/generate` | POST | AI 生成 |
| `/api/ai/test-connection` | POST | 模型连接测试 |
| `/api/health` | GET | 健康检查 |

## 前端开发

```bash
cd frontend
npm install
npm run dev    # 开发服务器，热更新，代理 /api → localhost:8000
npm run build  # 生产构建 到 dist/
```

## 后端开发

```bash
cd backend_v2
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看自动生成的 OpenAPI 文档。

## 数据库设计

| 表名 | 说明 |
|------|------|
| `projects` | 主项目表（含 data_json 完整数据） |
| `chapters` | 章节表（支持版本管理） |
| `outlines` | 大纲表（总纲+细纲） |
| `step_summaries` | 步骤摘要表（联动上下文） |
| `generation_status` | 章节生成状态表 |
| `outline_generation_status` | 大纲生成状态表 |

数据库使用 SQLite + WAL 模式，支持自动 schema 迁移。

## Docker 部署

### 常用命令

```bash
# 启动
docker compose -f docker-compose.v2.yml up -d

# 查看日志
docker compose -f docker-compose.v2.yml logs -f

# 重启
docker compose -f docker-compose.v2.yml restart

# 停止
docker compose -f docker-compose.v2.yml down

# 更新代码后重建
docker compose -f docker-compose.v2.yml down
docker compose -f docker-compose.v2.yml up -d --build
```

### 服务架构

```
用户 → Nginx (80) ─┬─ /fanqie/ → Vue SPA
                   └─ /fanqie/api/ → FastAPI (8000) → SQLite
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 8000 | 后端 HTTP 端口 |
| DB_PATH | /app/data/fanqie.db | 数据库路径 |
| CONTENT_API | http://101.35.133.34:5000/... | 小说内容 API |
| SEARCH_API | https://novel.snssdk.com/... | 搜索 API |
| AI_TIMEOUT | 600 | AI 调用超时（秒） |
| SESSION_TTL | 86400 | 下载 session 过期时间（秒） |
| HTTP_TIMEOUT | 20 | HTTP 请求超时（秒） |
| MAX_BODY_SIZE | 52428800 | 最大 POST body（50MB） |

## 版本历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-05 | v3.0 | 前后端分离，FastAPI后端+Vue3前端工程化 |
| 2026-07-04 | v2.0 | 淡蓝色主题，布局优化，数据持久化 |
| 2026-07-04 | v1.0 | 初始版本发布 |

## 许可证

GPL-3.0
