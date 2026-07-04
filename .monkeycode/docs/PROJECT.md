# AI创作平台 - 项目文档

> 访问地址：`http://140.143.210.177/fanqie/`

---

## 一、项目概览

一个功能完整的AI辅助创作平台，支持：

- **小说下载**：搜索、目录抓取、批量下载、持久化存储
- **AI创作**：灵感→世界观→角色→总纲→细纲→章节正文，完整的小说创作工作流
- **章节管理**：编辑、保存、断点续传、单章操作（查看/润色/对比）
- **项目管理**：保存/加载/删除项目，数据全部持久化到SQLite
- **章节持久化**：每章生成完毕立即保存到数据库，刷新后可恢复
- **大纲持久化**：总纲和细纲自动保存，下次可继续创作
- **步骤摘要联动**：自动生成世界观/角色/大纲的联动上下文
- **进度实时追踪**：生成状态实时保存，暂停/继续/恢复全支持
- **风格分析**：基于参考文本生成风格特征，驱动全创作流程
- **网文技法**：AI检测、文风修复、黄金三章分析、评分等

---

## 二、技术栈

### 当前架构 (v3.0)

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + TypeScript + Pinia + Vue Router |
| 后端 | Python 3.11 + FastAPI + Uvicorn + Pydantic |
| 数据库 | SQLite + WAL 模式 |
| 部署 | Docker Compose (frontend Nginx + backend Python) |
| 反向代理 | Nginx (SPA 路由 + API 代理) |

### 旧版兼容 (v2.0)

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 CDN + 原生 HTML/JS（单文件SPA） |
| 后端 | Python 3.11 HTTP Server（无框架） |
| 部署 | Docker Compose (单 backend + Nginx) |

---

## 三、项目结构

```
deploy/
├── docker-compose.yml          # Docker Compose 编排（v3.0）
├── backend_v2/                 # FastAPI 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI 入口 + 路由注册 + 中间件
│       ├── config.py           # 环境变量配置
│       ├── database.py         # 数据库初始化
│       ├── models/
│       │   └── schemas.py      # Pydantic 请求/响应模型（58个）
│       ├── api/                # API 路由模块（8个文件）
│       │   ├── projects.py     # 项目管理 CRUD
│       │   ├── chapters.py     # 章节管理 + 生成控制
│       │   ├── outlines.py     # 大纲管理 + 生成控制
│       │   ├── step_summaries.py # 步骤摘要
│       │   ├── novel.py        # AI 小说生成
│       │   ├── craft.py        # 网文技法
│       │   ├── download.py     # 小说下载
│       │   └── ai.py           # AI 工具
│       └── services/
│           ├── novel_generator.py  # NovelGenerator 包装
│           └── download_service.py # 下载会话管理
├── frontend/                   # Vue 3 前端工程
│   ├── Dockerfile              # 多阶段构建(Vite build + Nginx serve)
│   ├── nginx.conf              # SPA 路由 + API 代理
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.ts             # createApp + Pinia + Router
│       ├── App.vue             # 根组件 + 淡蓝主题
│       ├── router/index.ts     # Vue Router
│       ├── api/                # API 客户端封装
│       │   ├── client.ts       # fetch 封装 + 超时 + SSE
│       │   ├── project.ts      # 项目 CRUD
│       │   ├── chapter.ts      # 章节管理
│       │   ├── outline.ts      # 大纲管理
│       │   ├── novel.ts        # 小说创作
│       │   └── download.ts     # 下载
│       ├── stores/             # Pinia 状态管理
│       │   ├── settings.ts     # 模型配置
│       │   ├── project.ts      # 当前项目
│       │   └── download.ts     # 下载会话
│       ├── components/         # 通用组件
│       │   ├── AppHeader.vue   # 头部
│       │   ├── TabBar.vue      # 标签导航
│       │   ├── ModalBase.vue   # 模态框
│       │   └── ModelConfig.vue # 模型配置
│       └── views/              # 页面组件
│           ├── Download.vue    # 下载
│           ├── Create.vue      # AI 创作
│           └── Craft.vue       # 网文技法
├── novel_creator/              # AI 小说创作核心模块
│   ├── database.py             # SQLite + WAL + schema 迁移
│   ├── generator.py            # NovelGenerator 生成器
│   ├── prompts.py              # Novel 流程 prompt
│   ├── craft_prompts.py        # 网文技法 prompt
│   └── ai_client.py            # OpenAI 兼容客户端
└── legacy/                     # 旧版归档（参考用）
    ├── server-v2.py            # 旧版后端
    ├── index-v2.html           # 旧版前端
    ├── docker-compose.yml      # 旧版编排
    └── ...                     # 其他旧版文件
```
deploy/
├── docker-compose.v2.yml      # 前后端分离编排（推荐）
├── docker-compose.yml          # 旧版编排（兼容）
├── backend_v2/                 # FastAPI 后端
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI 入口 + 路由注册 + 中间件
│       ├── config.py           # 环境变量配置
│       ├── database.py         # 数据库初始化
│       ├── models/
│       │   └── schemas.py      # Pydantic 请求/响应模型（58个）
│       ├── api/                # API 路由模块（按业务分类）
│       │   ├── projects.py     # POST /api/projects/{save,list,load,delete}
│       │   ├── chapters.py     # POST /api/chapters/* + /api/chapters/generation/*
│       │   ├── outlines.py     # POST /api/outline/* + /api/outline/generation/*
│       │   ├── step_summaries.py # POST /api/step-summary/{save,get}
│       │   ├── novel.py        # POST /api/novel/* (inspiration/worldbuilding/characters/outline/book-overview/chapter)
│       │   ├── craft.py        # POST /api/novel/craft/*
│       │   ├── download.py     # GET /api/search|directory|content|download/*
│       │   └── ai.py           # POST /api/ai/{analyze,generate} + /api/analyze-style|generate-style
│       └── services/
│           ├── novel_generator.py  # NovelGenerator + ResponseModelDict
│           └── download_service.py # Session管理后台线程
├── frontend/                   # Vue 3 前端工程
│   ├── Dockerfile              # 多阶段构建(Vite build + Nginx serve)
│   ├── nginx.conf              # SPA 路由 + API 代理
│   ├── package.json            # vue/vite/pinia/vue-router
│   ├── vite.config.ts          # base: /fanqie/, dev proxy
│   ├── index.html
│   └── src/
│       ├── main.ts             # createApp + Pinia + Router
│       ├── App.vue             # 根组件 + 全局样式 + 淡蓝主题
│       ├── router/index.ts     # Vue Router 路由配置
│       ├── api/                # API 客户端封装
│       │   ├── client.ts       # fetch 封装 + 超时控制 + SSE
│       │   ├── project.ts      # 项目 CRUD API
│       │   ├── chapter.ts      # 章节管理 API
│       │   ├── outline.ts      # 大纲管理 API
│       │   ├── novel.ts        # 小说创作 API
│       │   └── download.ts     # 下载 API
│       ├── stores/             # Pinia 状态管理
│       │   ├── settings.ts     # 模型配置 + localStorage
│       │   ├── project.ts      # 当前项目 + 项目列表
│       │   └── download.ts     # 下载会话管理
│       ├── components/         # 通用组件
│       │   ├── AppHeader.vue   # 头部标题+设置
│       │   ├── TabBar.vue      # 三标签导航
│       │   ├── ModalBase.vue   # 模态框基础组件
│       │   └── ModelConfig.vue # 模型配置弹窗
│       └── views/              # 页面级组件
│           ├── Download.vue    # 下载页面
│           ├── Create.vue      # AI 创作页面
│           └── Craft.vue       # 网文技法页面
├── novel_creator/              # AI 小说创作核心模块
│   ├── database.py             # SQLite + WAL + schema 迁移
│   ├── generator.py            # NovelGenerator 生成器类
│   ├── prompts.py              # Novel 流程 prompt 模板
│   ├── craft_prompts.py        # 网文技法 prompt 模板
│   └── ai_client.py            # OpenAI 兼容 HTTP 客户端
├── index-v2.html               # 旧版单文件前端（兼容保留）
├── server-v2.py                # 旧版后端（兼容保留）
└── nginx.conf                  # 旧版 Nginx 配置
```

---

## 四、数据库设计

### 4.1 表结构

#### `projects` — 主项目表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | 项目唯一ID |
| name | TEXT | 项目名称 |
| step | INTEGER | 当前创作步骤(0-10) |
| data_json | TEXT | 完整项目数据(JSON) |
| tags | TEXT | 标签(逗号分隔) |
| category | TEXT | 分类 |
| metadata_json | TEXT | 扩展元数据(JSON) |
| is_archived | INTEGER | 是否归档(0/1) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### `chapters` — 章节表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| project_id | TEXT | 所属项目ID |
| chapter_number | INTEGER | 章节号 |
| title | TEXT | 章节标题 |
| content | TEXT | 章节正文 |
| word_count | INTEGER | 字数 |
| status | TEXT | 状态: pending/done/error |
| version | INTEGER | 版本号(每次编辑+1) |
| error_message | TEXT | 错误信息 |
| metadata_json | TEXT | 扩展元数据(JSON) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |
| **UNIQUE** | | (project_id, chapter_number) |

#### `outlines` — 大纲表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| project_id | TEXT | 所属项目ID |
| chapter_number | INTEGER | 章节号(0=总纲) |
| title | TEXT | 章节标题 |
| summary | TEXT | 章节概要 |
| scenes | TEXT | 场景(JSON数组) |
| characters | TEXT | 角色(JSON数组) |
| key_points | TEXT | 关键节点(JSON数组) |
| emotion | TEXT | 情绪走向 |
| goal | TEXT | 章节目标 |
| technique_focus | TEXT | 技法重点 |
| book_overview | TEXT | 全书总纲(仅chapter_number=0) |
| acts | TEXT | 幕结构(JSON数组) |
| importance | INTEGER | 重要程度(0-10) |
| status | TEXT | 状态 |
| metadata_json | TEXT | 扩展元数据 |
| **UNIQUE** | | (project_id, chapter_number) |

#### `step_summaries` — 步骤摘要表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增ID |
| project_id | TEXT | 所属项目ID |
| step | TEXT | 步骤标识 |
| summary_json | TEXT | 摘要数据(JSON) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |
| **UNIQUE** | | (project_id, step) |

#### `generation_status` — 章节生成状态表
| 字段 | 类型 | 说明 |
|------|------|------|
| project_id | TEXT PK | 项目ID |
| total_chapters | INTEGER | 总章节数 |
| completed_chapters | INTEGER | 已完成数 |
| failed_chapters | INTEGER | 失败数 |
| current_chapter | INTEGER | 当前章节 |
| is_running | INTEGER | 是否运行中 |
| is_paused | INTEGER | 是否暂停 |
| config | TEXT | 配置(JSON) |
| started_at | TEXT | 开始时间 |
| updated_at | TEXT | 更新时间 |

#### `outline_generation_status` — 大纲生成状态表
> 结构同 `generation_status`

### 4.2 索引

| 名称 | 作用 |
|------|------|
| idx_projects_updated | 项目列表按更新时间排序 |
| idx_projects_archived | 归档筛选 |
| idx_chapters_project | 按项目查章节 |
| idx_chapters_status | 按项目+状态查章节 |
| idx_outlines_project | 按项目查大纲 |
| idx_outlines_status | 按项目+状态查大纲 |
| idx_generation_status_project | 生成状态查询 |
| idx_outline_generation_status_project | 大纲生成状态查询 |
| idx_step_summaries_project | 步骤摘要查询 |

### 4.3 Schema 迁移

数据库使用 `PRAGMA user_version` 追踪schema版本，启动时自动执行迁移：

| 版本 | 变更 |
|------|------|
| v1 | 初始表结构 |
| v2 | 添加索引 + projects扩展字段(chapters.version, outlines.importance等) |

---

## 五、API 参考

> 所有API均通过 Nginx 反代 `/fanqie/api/` → `/api/`

### 5.1 项目管理

| 端点 | 方法 | 请求体 | 说明 |
|------|------|--------|------|
| /api/projects/save | POST | {id?, name, step, data, tags?, category?, metadata?} | 保存/更新项目 |
| /api/projects/list | POST | {} | 列出项目摘要 |
| /api/projects/load | POST | {id} | 加载完整项目 |
| /api/projects/delete | POST | {id} | 级联删除项目 |

### 5.2 章节管理

| 端点 | 方法 | 请求体关键字段 | 说明 |
|------|------|----------------|------|
| /api/chapters/save | POST | {projectId, chapterNumber, title, content, status, metadata?} | 保存章节(自动递增version) |
| /api/chapters/get | POST | {projectId, chapterNumber} | 获取单章 |
| /api/chapters/delete | POST | {projectId, chapterNumber} | 删除单章 |
| /api/chapters/regenerate | POST | {projectId, chapterNumber} | 重新生成(删除后重新生成) |
| /api/chapters/status | POST | {projectId} | 获取生成状态 |
| /api/chapters/generation/start | POST | {projectId, totalChapters, ...} | 开始批量生成 |
| /api/chapters/generation/pause | POST | {projectId} | 暂停 |
| /api/chapters/generation/stop | POST | {projectId} | 停止 |
| /api/chapters/generation/update | POST | {projectId, currentChapter, ...} | 更新进度 |

### 5.3 大纲管理

> 同上结构，前缀为 `/api/outline/`

### 5.4 步骤摘要

| 端点 | 方法 | 请求体 | 说明 |
|------|------|--------|------|
| /api/step-summary/save | POST | {projectId, step, summary} | 保存步骤摘要 |
| /api/step-summary/get | POST | {projectId, step?} | 获取(全部或单步) |

### 5.5 小说创作

| 端点 | 说明 |
|------|------|
| /api/novel/inspiration/title | 生成标题灵感 |
| /api/novel/inspiration/description | 生成简介灵感 |
| /api/novel/inspiration/theme | 生成主题灵感 |
| /api/novel/inspiration/genre | 生成类型灵感 |
| /api/novel/worldbuilding | 生成世界观 |
| /api/novel/characters | 生成角色 |
| /api/novel/outline | 生成大纲 |
| /api/novel/book-overview | 生成全书总纲 |
| /api/novel/chapter-outline | 生成章节细纲 |
| /api/novel/chapter | 生成章节正文(支持stream) |
| /api/novel/analyze-style | 分析文风 |
| /api/novel/generate-style | 生成风格模板 |

### 5.6 网文技法

| 端点 | 说明 |
|------|------|
| /api/novel/craft/detect-ai | AI检测 |
| /api/novel/craft/fix-ai | AI文风修复 |
| /api/novel/craft/golden-three | 黄金三章分析 |
| /api/novel/craft/hooks | 钩子分析 |
| /api/novel/craft/satisfaction | 爽点分析 |
| /api/novel/craft/quality-score | 质量评分 |
| /api/novel/craft/chapter | 技法化章节生成 |
| /api/novel/craft/titles | 标题生成 |
| /api/novel/craft/descriptions | 描述生成 |
| /api/novel/craft/report | 综合报告 |

### 5.7 其他

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/health | GET | 健康检查 |
| /api/search | GET | 搜索小说 |
| /api/directory | GET | 获取目录 |
| /api/content | GET | 获取章节内容 |
| /api/download/start | GET | 开始下载 |
| /api/download/status | GET | 下载状态 |
| /api/download/pause | GET | 暂停下载 |
| /api/download/resume | GET | 恢复下载 |
| /api/download/file | GET | 下载文件 |
| /api/downloads/list | GET | 已下载列表 |
| /api/downloads/content | GET | 已下载内容 |
| /api/ai/analyze | POST | AI分析 |
| /api/ai/generate | POST | AI生成 |

---

## 六、部署指南

### 6.1 环境要求

- Docker + Docker Compose
- Ubuntu 22.04

### 6.2 快速部署

```bash
# 1. 创建项目目录
mkdir -p ~/fanqie-docker && cd ~/fanqie-docker

# 2. 放置文件（通过scp或git）
# - docker-compose.yml
# - Dockerfile
# - nginx.conf
# - server-v2.py
# - index-v2.html
# - novel_creator/ (整个目录)

# 3. 启动
docker compose up -d --build

# 4. 验证
curl http://localhost/fanqie/api/health
```

### 6.3 更新与部署

每次代码修改后的部署流程：

```bash
# 1. 提交代码
git add -A && git commit -m "本次变更描述" && git push origin master

# 2. 部署到服务器
scp deploy/index-v2.html ubuntu@140.143.210.177:/tmp/
ssh ubuntu@140.143.210.177 "sudo cp /tmp/index-v2.html /home/ubuntu/fanqie-docker/index-v2.html && docker compose -f /home/ubuntu/fanqie-docker/docker-compose.yml restart web"
```

### 6.4 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| PORT | 8000 | 后端HTTP端口 |
| CONTENT_API | http://101.35.133.34:5000/... | 小说内容API |
| SEARCH_API | https://novel.snssdk.com/... | 搜索API |
| AI_TIMEOUT | 600 | AI调用超时(秒) |
| SESSION_TTL | 86400 | 下载session过期时间(秒) |
| HTTP_TIMEOUT | 20 | HTTP请求超时(秒) |
| MAX_BODY_SIZE | 52428800 | 最大POST body(50MB) |

---

## 七、数据流转

### 7.1 创作流程

```
灵感(Inspiration) → 世界观(World) → 角色(Characters) → 
总纲(Book Overview) → 细纲(Chapter Outline) → 章节正文(Chapter)
     ↓                    ↓              ↓
  saveStepSummary    saveStepSummary  saveStepSummary
     ↓                    ↓              ↓
  step_summaries     step_summaries   step_summaries
                                            ↓
                                    总纲生成时自动读取
                                    三步摘要作为上下文
```

### 7.2 项目保存

```
用户操作 → 前端保存到 dbChapters/dbOutlines (响应式状态)
        → 自动调用 API 保存到 SQLite (debounce 800ms)
        → 项目整体通过 /api/projects/save 保存到 projects 表
```

### 7.3 断点续传

```
章节生成中 → 每章完成后立即 saveChapterToDb(status='done')
         → 中断后重新生成时 → 跳过 status='done' 的章节
         → 从第一个未完成章节继续
```

---

## 八、运维

### 8.1 数据库备份

```bash
docker exec fanqie-backend sqlite3 /app/fanqie.db ".backup /app/backup_$(date +%Y%m%d).db"
```

### 8.2 查看日志

```bash
docker logs fanqie-backend --tail 100
docker logs fanqie-web --tail 100
```

### 8.3 重启服务

```bash
cd ~/fanqie-docker && docker compose restart
```

### 8.4 更新部署

```bash
cd ~/fanqie-docker
docker compose build --no-cache backend
docker compose up -d
```

---

## 九、常见问题

| 问题 | 解决方案 |
|------|---------|
| 白屏 | Ctrl+Shift+R 强制刷新 |
| 端口不通 | 检查 `docker ps` 和 `nginx.conf` 配置 |
| 数据库锁定 | SQLite WAL 模式，极少出现；重启容器即可 |
| AI 生成超时 | 调整 `AI_TIMEOUT` 环境变量 |
| 项目数据丢失 | SQLite 持久化到容器内 `/app/fanqie.db`，确保容器不删除 |

## 十、UI 设计

### 10.1 主题风格

- **主色调**：淡蓝色系（#4a90d9 → #6bb6ff）
- **背景**：#f5f8fc（淡蓝灰）
- **卡片**：白色背景 + 轻投影
- **布局**：最大宽度 900px，卡片间距 18px，圆角 12px
- **字体**：系统无衬线字体，标题 16px，正文 13-14px

### 10.2 界面结构

- **Header**：淡蓝色渐变，标题 + 副标题 + 模型配置按钮
- **Tabs**：下载 / 创作 / 技法 三个标签页
- **卡片**：每个功能区域独立卡片，内边距 24px

---

## 十一、版本历史

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-04 | v2.0 | 主题改为淡蓝色系，优化布局至900px宽屏 |
| 2026-07-04 | v2.0 | 章节持久化、大纲持久化、断点续传 |
| 2026-07-04 | v2.0 | 暂停/继续生成、进度追踪、步骤摘要联动 |
| 2026-07-04 | v1.0 | 初始版本发布 |

---

## 十二、架构设计决策

1. **SQLite 而非 MySQL/PostgreSQL**：单用户场景，零运维，WAL模式支持并发读写
2. **单文件前端**：无需构建工具，直接部署，加载即运行
3. **HTTP Server 而非 Flask/FastAPI**：最小依赖，镜像体积小
4. **JSON-in-SQLite**：projects.data_json 存储完整项目数据，schema变更无需ALTER TABLE
5. **流式传输**：SSE方式支持AI生成实时预览
