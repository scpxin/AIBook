# 模块重组进度报告

> 19 模块 → 13 模块重构，统一数据访问层 DataBridge
> 最后更新: 2026-07-21
> 测试: 123 passed, lint: 仅预存 E402 (非阻塞)

---

## 总体进度

| 阶段 | 内容 | 状态 | 提交 |
|------|------|------|------|
| 1 | DataBridge 基础层 | 已完成 | `90d1cd0` |
| 2 | DataBridge 写入层 | 已完成 | `5127865` |
| 3 | DataBridge 读取层 | 已完成 | `f702423` |
| 4 | DB Schema 迁移 | 已完成 | `6ab6193` |
| 5 | Pipeline 模块重定义 | 已完成 | `782d730` |
| 6-7 | Service 去写 + 功能合并 | 已完成 | `eafdf10` |
| 8-9 | API 层适配 + main.py 集成 | 已完成 (基础) | `25fc2d8` |
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

### 阶段5: Pipeline 模块重定义 (`782d730`)

**已完成:**
- `PIPELINE_MODULES`: 19 → 13 条目，层重设计 (design/structure/planning/execution)
- `MODULE_ORDER`: 13 模块拓扑排序
- `LEGACY_MODULE_MAP`: 11 条旧→新映射 (兼容已有数据)
- 所有 `database_v2` 调用替换为 `DataBridge` 内部函数
  - `get_pipeline_state` → `_get_pipeline_state` (DataBridge._conn())
  - `save_pipeline_state` → `_save_pipeline_state` (DataBridge._conn())
- `set_module_status` → 使用 DataBridge 连接而非 _v2_db
- `_unlock_dependents_db` → `_unlock_dependents`
- `get_executionlayer_state` → 4 模块 (draft/parse/polish/consistency)
- `is_execution_loop_complete` → 检查 draft + consistency

**13 模块架构:**

| # | 模块名 | 显示名 | 层 | 依赖 |
|---|--------|--------|-----|------|
| M1 | idea | 灵感 | design | - |
| M2 | project | 项目定位 | design | idea |
| M3 | world | 世界观体系 | design | project |
| M4 | characters | 人物系统 | design | project, world |
| M5 | architecture | 故事架构 | design | characters |
| M6 | relation_map | 角色关系网 | design | characters (并行) |
| M7 | outline | 全书大纲 | structure | architecture (并行) |
| M8 | volumes | 卷纲 | planning | architecture |
| M9 | chapter_plan | 章节规划 | planning | volumes, architecture |
| M10 | draft | 正文生成 | execution | chapter_plan (迭代) |
| M11 | parse | 内容解析 | execution | draft (迭代) |
| M12 | polish | 润色 | execution | draft (迭代) |
| M13 | consistency | 一致性检查 | execution | parse, polish (迭代) |

### 阶段6-7: Service 去写 + 功能合并 (`eafdf10`)

**design_service.py (8处 → DataBridge):**

| 原调用 | 新调用 |
|--------|--------|
| `save_idea(project_id, {...})` | `DataBridge.write(project_id, "idea", {...})` |
| `save_project_detail(project_id, {...})` | `DataBridge.write(project_id, "project", {...})` |
| `save_world(project_id, {...})` | `DataBridge.write(project_id, "world", {...})` |
| `save_character(project_id, char_id, {...})` | `DataBridge.write(project_id, "characters", [{char_id: ..., ...}])` |
| `save_relation_map(project_id, result)` | `DataBridge.write(project_id, "relation_map", result)` |
| `save_story(project_id, {...})` | `DataBridge.write(project_id, "architecture", {...})` |
| `save_volume(project_id, vol_no, {...})` | `DataBridge.write(project_id, "volumes", [...])` |

**structure_service.py (14处 → DataBridge，含合并):**

| 原调用 | 新调用 | 合并方向 |
|--------|--------|----------|
| `save_power_system(project_id, {...})` | `DataBridge.write(project_id, "world", {"power_system": {...}})` | power → world |
| `save_faction(project_id, fid, f)` | `DataBridge.write(project_id, "world", {"factions": [...]})` | factions → world |
| `save_timeline(project_id, result)` | `DataBridge.write(project_id, "architecture", {"timeline_*": ...})` | timeline → architecture |
| `save_story(project_id, {...})` | `DataBridge.write(project_id, "architecture", {...})` | - |
| `save_volume(project_id, no, vol)` | `DataBridge.write(project_id, "volumes", [...])` | - |
| `save_plot_node(...)` | no-op (logger.warning) | 已废弃 |
| `save_chapter_plan(project_id, ch_no, ch)` | `DataBridge.write(project_id, "chapter_plan", [...])` | - |
| `get_story(project_id)` → `save_story` | `DataBridge.read/write(project_id, "architecture", ...)` | - |

**execution_service.py (11处 → DataBridge，含合并):**

| 原调用 | 新调用 | 合并方向 |
|--------|--------|----------|
| `save_scene(project_id, sid, scene)` | `DataBridge.write(project_id, "chapter_plan", [{"scene_designs": [...]}])` | scene → chapter_plan |
| `save_draft(project_id, ch, data)` | `DataBridge.write(project_id, "draft", {ch: data})` | - |
| `save_knowledge_state(project_id, {...})` | `DataBridge.write(project_id, "parse", {...})` | knowledge → parse |
| `get_knowledge_state(project_id)` | `DataBridge.read(project_id, "parse")` | knowledge → parse |
| `save_consistency_report(project_id, {...})` | `DataBridge.write(project_id, "consistency", {...})` | - |
| `get_world(project_id)` | `DataBridge.read(project_id, "world")` | - |
| `get_all_characters(project_id)` | `DataBridge.read(project_id, "characters")` | - |

**保留 database_v2 调用 (3处):**
- `get_foreshadows()` — 专用伏笔查询
- `get_ai_generations()` — AI 生成日志查询
- `settings_service.py` — 全局设置表（非项目数据）

### 阶段8-9: main.py 集成 (`25fc2d8`)

- 添加 `@app.on_event("shutdown")` 调用 `DataBridge.close()` 清理连接

---

## 待实施详情

### 阶段10: 前端适配

**需要变更:**
- `frontend/src/views/CreateV2.vue`: 13 模块视图映射更新
- WorldView: 新增力量体系子面板 + 势力子面板
- ArchitectureView: 替代 StoryArchitectureView + 时间线面板
- PlanningView: 含场景设计子面板
- ContentView: 合并 knowledge_update 分支

### 阶段11-12: 测试改造 + 验证推送

- API 路由适配 (新增 `/api/v2/architecture/*`, `/api/v2/outline/generate`, 删除 6 个废弃端点)
- 前端构建验证
- 运行 `python3 -m pytest tests/ -q` 确保全部通过
- 运行 `python3 -m ruff check . --ignore=B904,E402,E741` 全局检查

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
