# 模块重组进度报告

> 19 模块 → 13 模块重构，统一数据访问层 DataBridge
> 最后更新: 2026-07-20

---

## 总体进度

| 阶段 | 内容 | 状态 | 提交 |
|------|------|------|------|
| 1 | DataBridge 基础层 | 已完成 | `90d1cd0` |
| 2 | DataBridge 写入层 | 已完成 | `5127865` |
| 3 | DataBridge 读取层 | 已完成 | `f702423` |
| 4 | DB Schema 迁移 | 已完成 | `6ab6193` |
| 5 | Pipeline 模块重定义 | 未开始 | - |
| 6-7 | Service 去写 + 功能合并 | 未开始 | - |
| 8-9 | API 层适配 + main.py 集成 | 未开始 | - |
| 10 | 前端适配 | 未开始 | - |
| 11-12 | 测试改造 + 验证推送 | 未开始 | - |

---

## 已完成详情

### 阶段1: DataBridge 基础层 (`90d1cd0`)

- 新建 `novel_creator/data_bridge.py`，DataBridge 类骨架
- `_conn()` / `close()` — 请求级 threading.local() 连接复用
- 工具函数: `_j()`, `_jl()`, `_deserialize_row()`, `_now()`
- 14 测试通过

### 阶段2: DataBridge 写入层 (`5127865`)

- `WRITE_MAP` 分发映射 (13 个模块)
- 13 个 `_write_*` 方法覆盖全模块
- `write()` 分发入口 + `_write_generic()` no-op 兜底
- `v2_relation_maps` 补 `updated_at` 列
- 35 测试通过

### 阶段3: DataBridge 读取层 (`f702423`)

- `READ_MAP` 分发映射 (12 个模块, polish 无 read)
- `read(project_id, module, chapter_no=None)` 分发
- `read_all(project_id, chapter_no=None)` 全文读取
- 13 个 `_read_*` 方法 (5 个列表型返回 `[]`，7 个单体型返回 dict/None)
- `v2_outlines` 表 DDL (opening/rising_actions/subplots/midpoint_turn/climax/ending/chapters/emotional_curve)
- 58 测试通过

### 阶段4: DB Schema 迁移 (`6ab6193`)

**新增列:**

| 表 | 新增列 | 来源模块 |
|----|--------|----------|
| `v2_world_buildings` | `power_system TEXT`, `factions TEXT` | 力量体系 + 势力 → 世界观 |
| `v2_story_systems` | `timeline_events TEXT`, `timeline_consistency TEXT` | 时间线 → 故事架构 |
| `v2_chapter_plans` | `scene_designs TEXT` | 场景设计 → 章节规划 |

**废弃表标记 (5 张):**
- `v2_power_systems` → v2_world_buildings.power_system
- `v2_factions` → v2_world_buildings.factions
- `v2_timelines` → v2_story_systems.timeline_*
- `v2_scenes` → v2_chapter_plans.scene_designs
- `v2_plot_nodes` → 删除 (无前端视图)

**迁移机制:** `V2_SCHEMA_MIGRATIONS` 列表 + `init_db_v2()` 自动执行 ALTER TABLE（幂等）

- DataBridge `_write_world` 增加 power_system/factions 列
- DataBridge `_write_architecture` 增加 timeline_events/timeline_consistency 列
- DataBridge `_write_chapter_plan` 增加 scene_designs 列
- 123 测试通过

---

## 待实施详情

### 阶段5: Pipeline 模块重定义 (save_map→DataBridge)

目标: 将 pipeline.py 中 19 模块定义简化为 13 模块。

**模块变更:**

| 序号 | 新模块名 | 原模块 | 变更 |
|------|----------|--------|------|
| M1 | idea | idea | - |
| M2 | project | project | - |
| M3 | world | world + power_system + factions | 力量+势力合并 |
| M4 | characters | characters | - |
| M5 | architecture | story_architecture + timeline | 时间线合并 |
| M6 | outline | outline | - |
| M7 | volumes | volumes | - |
| M8 | chapter_plan | chapter_plan + chapter_outline | 合并 |
| M9 | draft | draft_generation | 重命名 |
| M10 | parse | content_parsing + knowledge_update | 内容解析+知识库合并 |
| M11 | polish | polish | - |
| M12 | consistency | consistency_check | 重命名 |
| M13 | relation_map | (relation_map) | 角色关系网独立路由 |

**需要做的事:**
1. `pipeline.py`: PIPELINE_MODULES 从 19 条减到 13 条
2. `pipeline.py`: MODULE_ORDER 重排
3. `save_pipeline_state()` 改为调用 `DataBridge.write()` 写 v2_pipeline_states
4. `get_pipeline_state()` 改为调用 `DataBridge.read()`
5. pipeline.py import 从 database_v2 改为 data_bridge
6. 删除原 19 模块中废弃的定义 (power_system/factions/timeline/scene_design/plot_nodes/knowledge_update)

**数据层写入口变更:**
- `save_pipeline_state(project_id, module_name, **fields)` → `DataBridge.write(project_id, "pipeline", {...})` (需新增 _write_pipeline)
- `get_pipeline_state(project_id, module_name)` → `DataBridge.read(project_id, "pipeline")`

### 阶段6-7: Service 去写 + 功能合并

目标: 所有 Service 层不再直接调用 database_v2.save_*()，统一走 DataBridge.write()。

**需要变更的文件和函数:**
1. `design_service.py`: IdeaService/ProjectService/WorldService/CharacterService/StoryArchitectureService 的 save 方法
2. `structure_service.py`: PowerSystemService.save → 写入 world.power_system; FactionService.save → 写入 world.factions; TimelineService.save → 写入 architecture.timeline_*
3. `planning_service.py`: VolumeService/ChapterPlanService/OutlineService 的 save 方法
4. `execution_service.py`: SceneService → 写入 chapter_plan.scene_designs; DraftService; ParseService; PolishService
5. `refinement_service.py`: KnowledgeService → 合并到 parse; ConsistencyService

**运行 `python3 -m ruff check` 确保无 lint 错误**

**运行 `python3 -m pytest tests/ -q` 确保 123+ 测试通过**

### 阶段8-9: API 层适配 + main.py 集成

目标: API 路由适配 13 模块结构。

**新增路由:**
- `/api/v2/architecture/*` — 替代原 /api/v2/story-architecture/*
- `/api/v2/outline/generate` — 大纲生成端点

**删除路由 (6 个):**
- `/api/v2/power-system/*`
- `/api/v2/factions/*`
- `/api/v2/timeline/*`
- `/api/v2/scene/*`
- `/api/v2/knowledge/*`
- `/api/v2/plot-nodes/*`

**main.py 集成:**
- 在 FastAPI lifespan 中调用 `DataBridge.close()` 清理连接
- 中间件中按请求创建/关闭 DataBridge 连接

### 阶段10: 前端适配

目标: 前端视图映射到 13 模块。

**需要变更的文件:**
- `frontend/src/views/CreateV2.vue`: 13 模块视图映射更新
- WorldView: 新增力量体系子面板 + 势力子面板
- ArchitectureView: 替代 StoryArchitectureView + 时间线面板
- PlanningView: 含场景设计子面板
- ContentView: 合并 knowledge_update 分支

### 阶段11-12: 测试改造 + 验证推送

目标: 最终测试验证和代码清理。

**测试验证:**
- 运行 `python3 -m pytest tests/ -q` 确保全部通过
- 运行 `python3 -m ruff check . --ignore=B904` 检查全局
- 运行 `python3 -m pytest tests/ -q --cov=novel_creator --cov=app` 检查覆盖率

**代码清理:**
- 删除 database_v2.py 中已废弃的 CRUD 函数 (标注 deprecation warning)
- 清理未使用的 import

---

## 技术决策记录

### 存储策略
| 策略 | 适用模块 |
|------|----------|
| 全量 UPSERT | idea, project, outline, consistency |
| 读-改-写 (merged dict) | world, architecture |
| DELETE + INSERT | volumes, chapter_plan |
| 按名 UPSERT | characters (char_id 联合键) |
| 按章 UPSERT | draft (project_id + chapter_no) |

### 架构约定
- DataBridge 使用 `threading.local()` 实现请求级连接复用
- 所有 JSON 列通过 `_j()` / `_jl()` 统一序列化/反序列化
- `_deserialize_row()` 自动检测并反序列化 JSON 列
- `_write_polish` 为 no-op（润色仅返回展示，不写 DB）
- WRITE_MAP 包含 `relation_map` 独立路由，不与 characters 耦合

### 数据库
- SQLite WAL 模式，`/workspace/novel_creator/data_bridge.py` 新建
- concurrent read-friendly via WAL journal
- 4 张旧表保留但标记 DEPRECATED，5 张表新增列
