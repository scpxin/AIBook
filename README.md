# AI创作平台

基于 Docker 部署的小说下载与 AI 小说创作平台，支持风格分析驱动的全流程创作。

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

## 界面预览

- **主题**：淡蓝色系（#4a90d9 → #6bb6ff）
- **布局**：最大宽度 900px，卡片式布局，简洁大方
- **技术**：Vue 3 CDN 单文件 SPA，无需构建

## 快速开始

### 前置要求

- Docker 29+
- Docker Compose v5+

### 启动服务

```bash
git clone https://github.com/scpxin/AIBook.git
cd AIBook/deploy
docker compose up -d --build
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
│   ├── docker-compose.yml      # Docker Compose 配置
│   ├── Dockerfile              # 后端镜像构建
│   ├── nginx.conf              # Nginx 反向代理配置
│   ├── server-v2.py            # Python 后端服务
│   ├── index-v2.html           # 前端单文件SPA（~1800行）
│   ├── novel_creator/          # AI 小说创作模块
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite 数据库模块
│   │   ├── generator.py        # 小说创作生成器
│   │   ├── prompts.py          # AI prompt 模板
│   │   ├── craft_prompts.py    # 网文技法 prompt 模板
│   │   └── ai_client.py        # OpenAI 兼容 API 客户端
│   └── check_db.py             # 数据库检查工具
├── .monkeycode/
│   ├── docs/                   # 项目文档
│   └── specs/                  # 功能规格文档
└── README.md                   # 本文件
```

## API 接口

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

### 步骤摘要

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/step-summary/save` | POST | 保存步骤摘要 |
| `/api/step-summary/get` | POST | 获取步骤摘要 |

### AI 创作

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/novel/inspiration/title` | POST | 生成书名建议 |
| `/api/novel/inspiration/description` | POST | 生成简介选项 |
| `/api/novel/inspiration/theme` | POST | 生成主题选项 |
| `/api/novel/inspiration/genre` | POST | 生成类型标签 |
| `/api/novel/worldbuilding` | POST | 构建世界观 |
| `/api/novel/characters` | POST | 生成角色 |
| `/api/novel/outline` | POST | 生成大纲 |
| `/api/novel/book-overview` | POST | 生成全书总纲 |
| `/api/novel/chapter-outline` | POST | 生成章节细纲 |
| `/api/novel/chapter` | POST | 生成章节正文（支持stream） |
| `/api/novel/analyze-style` | POST | 分析写作风格 |
| `/api/novel/generate-style` | POST | 风格仿写生成 |

### 网文技法

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/novel/craft/detect-ai` | POST | AI 检测 |
| `/api/novel/craft/fix-ai` | POST | AI 文风修复 |
| `/api/novel/craft/golden-three` | POST | 黄金三章分析 |
| `/api/novel/craft/hooks` | POST | 钩子分析 |
| `/api/novel/craft/satisfaction` | POST | 爽点分析 |
| `/api/novel/craft/quality-score` | POST | 质量评分 |
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
| `/api/downloads/content` | GET | 获取已下载书籍内容 |

### 其他

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/ai/analyze` | POST | AI 分析 |
| `/api/ai/generate` | POST | AI 生成 |

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
docker compose up -d

# 查看日志
docker compose logs -f

# 重启
docker compose restart

# 停止
docker compose down

# 更新代码后重建
docker compose down && docker compose up -d --build
```

### 服务架构

```
用户 → Nginx (80) → Python Backend (8000)
                              ↓
                     SQLite: /app/fanqie.db
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 8000 | 后端 HTTP 端口 |
| CONTENT_API | http://101.35.133.34:5000/... | 小说内容 API |
| SEARCH_API | https://novel.snssdk.com/... | 搜索 API |
| AI_TIMEOUT | 600 | AI 调用超时（秒） |
| SESSION_TTL | 86400 | 下载 session 过期时间（秒） |
| HTTP_TIMEOUT | 20 | HTTP 请求超时（秒） |
| MAX_BODY_SIZE | 52428800 | 最大 POST body（50MB） |

## 技术栈

- **前端**：Vue 3 CDN + 原生 HTML/JS（单文件 SPA）
- **后端**：Python 3.11 HTTP Server（无框架）
- **数据库**：SQLite + WAL 模式
- **部署**：Docker + Nginx 反向代理
- **AI**：OpenAI 兼容 API

## 版本历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-04 | v2.0 | 主题改为淡蓝色系，布局优化至 900px 宽屏 |
| 2026-07-04 | v2.0 | 章节/大纲/步骤摘要持久化，断点续传 |
| 2026-07-04 | v2.0 | 暂停/继续生成，进度实时追踪 |
| 2026-07-04 | v1.0 | 初始版本发布 |

## 许可证

GPL-3.0
