# Fanqie Novel Creator V2

AI 番茄小说创作平台 - 前后端分离的小说生成系统，支持从选题到成稿的全流程AI辅助创作。

## 功能特性

- **全流程创作流水线**：18个创意模块，从灵感到成稿
- **AI智能生成**：集成 LongCat-2.0 模型，自动生成世界观、角色、大纲、正文
- **V2数据架构**：全新数据模型，支持渐进式创作与模块化管理
- **实时状态追踪**：流水线可视化进度，模块独立保存与读取
- **模板系统**：预设创作模板，一键复用优质结构
- **知识管理**：一致性检查、伏笔追踪、情感曲线分析

## 项目结构

```
fanqie-v2/
├── app/                          # FastAPI 后端
│   ├── api/
│   │   ├── pipeline.py           # V2 流水线核心API（19模块保存/读取）
│   │   ├── projects.py           # 项目管理API（列表、创建、软删除）
│   │   ├── design.py             # 设计模块AI生成
│   │   ├── structure.py          # 结构模块AI生成
│   │   ├── execution.py          # 执行模块AI生成
│   │   ├── settings.py           # 系统设置
│   │   ├── template.py           # 模板管理
│   │   ├── generation_template.py # 生成模板
│   │   └── download.py           # 下载服务
│   ├── services/
│   │   ├── design_service.py     # 设计服务（含fallback数据）
│   │   ├── structure_service.py  # 结构设计服务（逐卷生成）
│   │   ├── execution_service.py  # 执行服务
│   │   ├── pipeline.py           # 流水线调度
│   │   ├── novel_generator.py    # 小说生成器
│   │   ├── template_service.py   # 模板服务
│   │   ├── validation.py         # 验证服务
│   │   ├── settings_service.py   # 设置服务
│   │   ├── download_service.py   # 下载服务
│   │   └── service_utils.py      # 服务工具
│   ├── models/
│   │   ├── schemas.py            # 数据模型（Pydantic）
│   │   └── v2_schemas.py         # V2专用模型
│   ├── utils/
│   │   └── errors.py             # 错误处理
│   ├── main.py                   # FastAPI 入口
│   └── config.py                 # 配置
├── novel_creator/                # 核心创作引擎
│   ├── database_v2.py            # V2数据库操作（SQLite）
│   ├── database.py               # V1数据库操作
│   ├── ai_client.py              # AI客户端（LongCat-2.0）
│   ├── generator.py              # 内容生成器
│   ├── prompts.py                # Prompt模板
│   ├── craft_prompts.py         # 写作技巧Prompt
│   └── migrate.py                # 数据库迁移
├── frontend/                     # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/                # 页面视图
│   │   │   ├── IdeaView.vue      # 灵感/选题
│   │   │   ├── WorldView.vue     # 世界观
│   │   │   ├── CharacterView.vue # 角色
│   │   │   ├── StoryArchitectureView.vue # 故事架构
│   │   │   ├── FactionsView.vue  # 势力
│   │   │   ├── PowerSystemView.vue # 力量体系
│   │   │   ├── PlanningView.vue  # 规划（卷纲/章纲）
│   │   │   ├── OutlineView.vue   # 大纲
│   │   │   ├── SceneDesignView.vue # 场景设计
│   │   │   ├── WritingView.vue   # 写作（正文生成）
│   │   │   ├── ContentView.vue   # 内容视图
│   │   │   ├── Download.vue      # 下载
│   │   │   ├── ExportView.vue    # 导出
│   │   │   ├── CreateV2.vue      # V2创建页
│   │   │   ├── ModulesOverview.vue # 模块总览
│   │   │   ├── ProjectView.vue   # 项目详情
│   │   │   └── TimelineView.vue  # 时间线
│   │   ├── stores/               # Pinia 状态管理
│   │   │   ├── pipeline.ts       # 流水线数据读写
│   │   │   ├── idea.ts           # 灵感store
│   │   │   ├── world.ts          # 世界观store
│   │   │   ├── character.ts      # 角色store
│   │   │   ├── story.ts          # 故事store
│   │   │   ├── planning.ts       # 规划store
│   │   │   ├── execution.ts      # 执行store
│   │   │   ├── knowledge.ts      # 知识store
│   │   │   ├── generation.ts     # 生成store
│   │   │   ├── settings.ts       # 设置store
│   │   │   ├── project.ts        # 项目store
│   │   │   ├── download.ts       # 下载store
│   │   │   └── toast.ts          # 通知store
│   │   ├── components/           # 公共组件
│   │   │   ├── Modal.vue         # 模态框
│   │   │   ├── ToastContainer.vue # 通知容器
│   │   │   ├── ModuleProgressSidebar.vue # 侧边进度栏
│   │   │   ├── StreamingOutput.vue # 流式输出
│   │   │   ├── RelationGraph.vue # 关系图谱
│   │   │   ├── TimelineChart.vue # 时间线图表
│   │   │   ├── EmotionCurveChart.vue # 情感曲线图表
│   │   │   ├── WorldMapTree.vue  # 世界观树
│   │   │   ├── ForeshadowPanel.vue # 伏笔面板
│   │   │   ├── KnowledgePanel.vue # 知识面板
│   │   │   ├── GenerationStatusBar.vue # 生成状态栏
│   │   │   ├── ModelSelect.vue   # 模型选择
│   │   │   ├── ConsistencyPanel.vue # 一致性面板
│   │   │   └── ...
│   │   ├── api/                  # API客户端
│   │   │   ├── client.ts         # HTTP客户端
│   │   │   ├── v2.ts             # V2 API
│   │   │   ├── project.ts        # 项目API
│   │   │   ├── outline.ts        # 大纲API
│   │   │   ├── chapter.ts        # 章节API
│   │   │   └── ...
│   │   ├── composables/
│   │   │   └── useGeneration.ts  # 生成逻辑复用
│   │   ├── router/
│   │   │   └── index.ts          # 前端路由
│   │   ├── types/
│   │   │   └── v2.ts             # V2类型定义
│   │   ├── App.vue               # 根组件
│   │   ├── main.ts               # 入口
│   │   └── styles/
│   │       └── main.css          # 全局样式
│   ├── dist/                     # 构建产物
│   ├── index.html                # HTML入口
│   ├── package.json              # 依赖
│   ├── vite.config.ts            # Vite配置
│   └── tsconfig.json             # TypeScript配置
├── requirements.txt              # Python依赖
├── Dockerfile                    # 后端Docker镜像
├── docker-compose.yml            # Docker编排
├── docker-compose.yml
└── package.json
```

## 18模块创作流水线

| 序号 | 模块 | 说明 | 专用表 |
|------|------|------|--------|
| M1 | idea | 灵感/选题 | v2_ideas |
| M2 | project | 项目定位 | v2_pipeline_states |
| M3 | world | 世界观构建 | v2_world_buildings |
| M4 | characters | 角色设计 | v2_characters |
| M5 | story_architecture | 故事架构 | v2_pipeline_states |
| M6 | outline | 大纲 | v2_pipeline_states |
| M7 | power_system | 力量体系 | v2_power_systems |
| M8 | factions | 势力 | v2_factions |
| M9 | volumes | 卷纲 | v2_volumes |
| M10 | chapter_plan | 章节规划 | v2_chapter_plans |
| M11 | chapter_outline | 章节细纲 | v2_pipeline_states |
| M12 | plot_nodes | 剧情节点 | v2_plot_nodes |
| M13 | scene_design | 场景设计 | v2_scenes |
| M14 | draft_generation | 正文生成 | v2_drafts |
| M15 | content_parsing | 内容解析 | v2_pipeline_states |
| M16 | polish | 润色 | v2_pipeline_states |
| M17 | knowledge_update | 知识库 | v2_knowledge_states |
| M18 | consistency_check | 一致性检查 | v2_consistency_reports |

## API 接口

### 核心流水线
- `POST /api/v2/pipeline/{projectId}/data/{moduleName}` - 保存模块数据
- `GET /api/v2/pipeline/{projectId}/data/{moduleName}` - 读取模块数据
- `GET /api/v2/pipeline/{projectId}/status` - 流水线状态
- `GET /api/v2/projects/list` - 项目列表
- `DELETE /api/v2/pipeline/{projectId}?confirm=true` - 删除项目

### AI生成
- `POST /api/v2/structure/generate-world` - 生成世界观
- `POST /api/v2/structure/generate-characters` - 生成角色
- `POST /api/v2/design/generate-project` - 分析项目定位
- `POST /api/v2/execution/generate-draft` - 生成正文

### 模板
- `GET /api/v2/templates/` - 模板列表
- `POST /api/v2/templates/` - 创建模板
- `POST /api/v2/generation-templates/match` - 匹配模板

## 部署

### Docker Compose

```bash
# 构建前端
cd frontend && npm install && npm run build

# 启动服务
docker-compose up -d
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| PORT | 后端端口 | 8000 |
| DB_PATH | 数据库路径 | /app/data/fanqie.db |
| AI_TIMEOUT | AI请求超时 | 600s |
| AI_ENDPOINT | AI API地址 | LongCat |
| AI_API_KEY | AI API Key | - |
| AI_MODEL | AI模型名 | LongCat-2.0 |

### 服务器部署

```bash
# SSH连接
ssh ubuntu@140.143.210.177

# 进入项目
cd /home/ubuntu/fanqie-v2

# 更新代码
git pull origin master

# 重启容器
docker-compose down && docker-compose up -d --build
```

## 技术栈

- **后端**: Python 3.11 / FastAPI / SQLite / Uvicorn
- **前端**: Vue 3 / Vite / Pinia / TypeScript / Element Plus
- **AI**: LongCat-2.0 对话模型
- **部署**: Docker / Docker Compose / Nginx

## 数据库

SQLite 双数据库架构：
- `fanqie.db` - V1遗留数据
- V2 使用独立表结构（`v2_*` 前缀表）

运行 `database_v2..init_db_v2()` 自动创建所有V2表。

## License

MIT
