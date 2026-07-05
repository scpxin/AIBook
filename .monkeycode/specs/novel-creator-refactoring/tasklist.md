# 需求实施计划 — AI创作平台18模块重构

> **参考文档**: DETAILED_SPEC.md (2101行) + REFACTORING_REPORT.md (1257行)
> **目标**: 将现有5步向导式创作流程重构为18模块完整流水线,从 "灵感→世界观→角色→大纲→章节" 升级为完整的设计/结构/规划/执行/完善五层架构

---

## 数据库层扩展

- [x] 1. 扩展 SQLite 数据库 schema
  - 新增 `world_buildings` 表: 世界观(世界本源/规则/结构/文明/历史/伏笔)
  - 新增 `characters` 表: 角色(九维档案/成长路线/关系/状态)
  - 新增 `story_systems` 表: 故事体系(总纲/冲突/主题/卷纲/事件)
  - 新增 `power_systems` 表: 力量体系(等级/战斗分类/限制/瓶颈)
  - 新增 `factions` 表: 势力(名称/领土/首领/关系/内部冲突)
  - 新增 `timelines` 表: 时间线(世界+剧情事件统一)
  - 新增 `volumes` 表: 卷纲(卷名/字数/章数/关键事件/钩子)
  - 新增 `plot_nodes` 表: 具体事件(触发/场景/对白/结果)
  - 新增 `chapters_2` 表: 章节扩展(场景划分/情绪曲线/知识更新)
  - 新增 `scenes` 表: 场景设计(骨架/氛围/战斗/钩子)
  - 新增 `foreshadowings` 表: 伏笔(类型/触发/回收/状态)
  - 新增 `knowledge_states` 表: 知识库(角色位置/等级/关系值/状态)
  - 新增 `ai_generations` 表: AI生成日志(prompt/response/token)
  - 修改 `novel_creator/database.py`: 添加新表的CRUD方法
  - 保持旧表(chapters/outlines/projects/step_summaries)不变以兼容旧API
  - 启用 WAL 模式 + 添加相应索引

- [x] 2. 创建数据库迁移 script
  - 编写 `migrate.py`: 检测旧库并ALTER TABLE添加新表
  - 添加幂等性检查(IF NOT EXISTS)
  - 支持回滚

- [x]* 3. 数据库 schema 单元测试
  - 测试新表创建和CRUD操作
  - 测试旧表兼容性(读写chapters/outlines/projects不变)
  - 测试WAL模式下并发读取

- [x] 4. 检查点 — 确保数据库层测试全部通过
  - 确保所有数据库测试通过,如有疑问请询问用户

---

## 后端 — 设计层API

- [ ] 5. 创建灵感生成API
  - POST `/api/v2/ideas/generate` — 发散生成N个创意
  - POST `/api/v2/ideas/score` — 创意评分(创新性/商业性/可持续性/差异化/难度)
  - POST `/api/v2/ideas/upgrade` — 创意TOP3升级(增加矛盾/设计限制)
  - POST `/api/v2/ideas/analyze-risks` — 风险分析
  - POST `/api/v2/ideas/save` — 保存灵感记录
  - 存储到 `ai_generations` 表(entity_type="idea")
  - 实现IdeaService调用NovelGenerator + 评分逻辑

- [ ] 6. 创建项目定位API
  - POST `/api/v2/projects/analyze` — 12维度项目策划
  - POST `/api/v2/projects/check-compatibility` — 平台×灵感兼容性检查
  - POST `/api/v2/projects/derive-fields` — 衍生字段计算
  - 扩展现有projects表或新建project_details表存储12维度
  - ProjectService加载平台预设 + 调用NovelGenerator

- [ ] 7. 创建世界观构建API
  - POST `/api/v2/world/origin` — 世界本源设计
  - POST `/api/v2/world/rules` — 世界规则设计(每条规则6要素)
  - POST `/api/v2/world/structure` — 世界结构设计(层级+地点)
  - POST `/api/v2/world/civilization` — 文明体系设计(8维度)
  - POST `/api/v2/world/history` — 历史时间线设计
  - POST `/api/v2/world/check-consistency` — 世界一致性检查
  - POST `/api/v2/world/save` — 完整世界观保存
  - WorldService串行调用5步 → 组合为完整文档
  - 存储到world_buildings表(doc_path保存Markdown文件)

- [ ] 8. 创建角色系统API
  - POST `/api/v2/characters/protagonist` — 主角九维档案生成
  - POST `/api/v2/characters/supporting` — 配角设计
  - POST `/api/v2/characters/antagonists` — 反派体系设计
  - POST `/api/v2/characters/relations` — 关系网络生成
  - POST `/api/v2/characters/check-consistency` — 角色一致性检查
  - POST `/api/v2/characters/save` — 保存角色
  - CharacterService引用world.rules约束能力设计
  - 存储到characters表 + 文件Markdown

- [ ] 9. 创建故事体系API
  - POST `/api/v2/story/master` — 总纲设计(冲突/主题/事件集)
  - POST `/api/v2/story/volumes` — 每卷卷纲生成
  - POST `/api/v2/story/check-consistency` — 故事一致性
  - StoryService引用protagonist.growth_route对齐剧情节点
  - 存储到story_systems表

- [ ] 10. 检查点 — 确保设计层API测试全部通过
  - 确保所有测试通过,如有疑问请询问用户

---

## 后端 — 结构层API

- [ ] 11. 创建力量体系API
  - POST `/api/v2/power-system/generate` — 完整力量体系设计(等级/战斗/升级/限制)
  - POST `/api/v2/power-system/save` — 保存力量体系
  - PowerService引用world.rules + characters.abilities
  - 存储到power_systems表

- [ ] 12. 创建势力体系API
  - POST `/api/v2/factions/generate` — 5-8势力设计
  - POST `/api/v2/factions/save` — 保存势力
  - FactionService引用world.civilization + characters.affiliation
  - 存储到factions表

- [ ] 13. 创建时间线API
  - POST `/api/v2/timeline/build` — 整合世界历史 + 剧情事件
  - POST `/api/v2/timeline/save` — 保存时间线
  - TimelineService合并world.history + story.plot_events
  - 存储到timelines表

- [ ] 14. 创建全书大纲API
  - POST `/api/v2/outline/master` — 全书大纲(起承转合/卷结构)
  - POST `/api/v2/outline/save` — 保存全书大纲
  - 这是原有outline概念的扩展版,非替代

- [ ] 15. 检查点 — 确保结构层API测试全部通过
  - 确保所有测试通过,如有疑问请询问用户

---

## 后端 — 规划层API

- [ ] 16. 创建卷纲API
  - POST `/api/v2/volumes/generate` — 单卷详细设计
  - POST `/api/v2/volumes/save` — 保存卷纲
  - VolumeService组合V1-V3所有上游数据
  - 存储到volumes表

- [ ] 17. 创建剧情节点API
  - POST `/api/v2/plot-nodes/generate` — 事件具体化(场景/对白/转折点)
  - POST `/api/v2/plot-nodes/save` — 保存剧情节点
  - PlotNodeService引用location_index + characters + power_system
  - 存储到plot_nodes表

- [ ] 18. 创建章节规划API
  - POST `/api/v2/chapters/plan` — 章节分配(事件→章 + 钩子分配)
  - POST `/api/v2/chapters/plan-save` — 保存章节规划
  - ChapterPlanService按字数和节奏分配
  - 存储到chapters_2表

- [ ] 19. 创建章节细纲API
  - POST `/api/v2/chapters/outline` — 逐章展开(场景/情绪曲线/知识库)
  - POST `/api/v2/chapters/outline-save` — 保存细纲
  - ChapterOutlineService按foreshadow.plan埋/收伏笔
  - 更新chapters_2表

- [ ] 20. 检查点 — 确保规划层API测试全部通过
  - 确保所有测试通过,如有疑问请询问用户

---

## 后端 — 执行层API

- [ ] 21. 创建场景设计API
  - POST `/api/v2/scenes/design` — 场景骨架生成(时间/环境/冲突/战斗/氛围)
  - POST `/api/v2/scenes/save` — 保存场景
  - SceneService引用location_details + foreshadow_plan + power_system
  - 存储到scenes表

- [ ] 22. 创建正文生成API (流式)
  - POST `/api/v2/draft/generate` — 流式正文生成(分段:开场/发展/高潮/结尾)
  - POST `/api/v2/draft/save` — 保存正文
  - DraftService引用scene_skeleton + characters + foreshadow + constraints
  - 支持续写(continuation模式,以上一段结尾为接口)
  - 生成后自动触发content parsing → knowledge update → consistency check

- [ ] 23. 创建润色API
  - POST `/api/v2/polish` — 三阶段润色(语言/节奏/查重)
  - PolishService引用style + foreshadow_protected
  - 返回change_summary + similarity报告

- [ ] 24. 创建内容解析API
  - POST `/api/v2/content/parse` — 已写章节解析(场景/对白/动作切分)
  - ContentParser提取status_change → 触发knowledge update

- [ ] 25. 创建知识库API
  - POST `/api/v2/knowledge/update` — 增量更新知识库
  - GET `/api/v2/knowledge/snapshot` — 获取当前知识库快照
  - GET `/api/v2/knowledge/foreshadows` — 获取活跃伏笔列表
  - KnowledgeService管理累积状态 + 伏笔跟踪
  - 存储到knowledge_states + foreshadowings表

- [ ] 26. 创建一致性检查API
  - POST `/api/v2/consistency/check` — 9项自动校验
  - GET `/api/v2/consistency/report` — 获取最近检查报告
  - ConsistencyService实现9维度校验 + 评分 + 修复建议

- [ ] 27. 检查点 — 确保执行层API测试全部通过
  - 确保所有测试通过,如有疑问请询问用户

---

## 后端 — 应用层编排

- [x] 28. 创建流水线编排引擎
  - 实现 `PipelineService`: 管理18模块的编排顺序
  - 状态机: pending → generating → done / failed
  - 支持断点续传(从任意模块继续)
  - 支持单模块重跑
  - POST `/api/v2/pipeline/start` — 启动/恢复流水线
  - GET `/api/v2/pipeline/status` — 获取流水线状态
  - GET `/api/v2/pipeline/result/{module}` 获取模块结果
  - POST `/api/v2/pipeline/rerun/{module}` 重跑指定模块

- [ ] 29. 重构主路由结构
  - 保留旧路由(api/*.py)不修改(向后兼容)
  - 新增 api/v2/ 目录: 按模块分组路由
  - main.py同时注册 /api/ 和 /api/v2/
  - 统一错误处理 + 日志格式

- [ ] 30. 检查点 — 确保全部后端测试通过
  - 确保所有测试通过

---

## 前端 — 类型定义与API层

- [ ] 31. 创建 V2 类型定义
  - `src/types/idea.ts` — Idea / IdeaCandidate 类型
  - `src/types/world.ts` — WorldBuilding / WorldRule / WorldLayer 类型
  - `src types/character.ts` — Character / CharacterAppearance / Personality / Ability 类型
  - `src/types/story.ts` — StorySystem / Volume 类型
  - `src/types/power.ts` — PowerSystem / PowerTier 类型
  - `src/types/faction.ts` — Faction 类型
  - `src/types/timeline.ts` — TimelineEvent 类型
  - `src/types/volume.ts` — Volume 类型
  - `src/types/plot.ts` — PlotNode 类型
  - `src/types/chapter.ts` — ChapterPlan / ChapterOutline / Scene 类型
  - `src/types/scene.ts` — SceneSkeleton 类型
  - `src/types/draft.ts` — Draft 类型
  - `src/types/foreshadow.ts` — Foreshadowing 类型
  - `src/types/knowledge.ts` — KnowledgeState 类型
  - `src/types/consistency.ts` — ConsistencyReport 类型
  - `src/types/pipeline.ts` — PipelineStatus / ModuleResult 类型
  - 所有类型遵循后端Pydantic模型,使用camelCase

- [ ] 32. 创建 V2 API 服务层
  - `src/api/idea.ts` — 灵感API(5个函数)
  - `src/api/world.ts` — 世界观API(6个函数)
  - `src/api/character.ts` — 角色API(6个函数)
  - `src/api/story.ts` — 故事API(3个函数)
  - `src/api/power.ts` — 力量体系API(2个函数)
  - `src/api/faction.ts` — 势力API(2个函数)
  - `src/api/timeline.ts` — 时间线API(2个函数)
  - `src/api/outline2.ts` — 全书大纲API
  - `src/api/volume.ts` — 卷纲API
  - `src/api/plot.ts` — 剧情节点API
  - `src/api/chapter2.ts` — 章节规划/细纲API
  - `src/api/scene.ts` — 场景设计API
  - `src/api/draft.ts` — 正文生成API(流式)
  - `src/api/polish.ts` — 润色API
  - `src/api/content.ts` — 内容解析API
  - `src/api/knowledge.ts` — 知识库API
  - `src/api/consistency.ts` — 一致性API
  - `src/api/pipeline.ts` — 流水线API
  - 所有API使用已有的client.ts(apiGet/apiPost/apiPostLong/apiStream)
  - 路由前缀 `/api/v2/`

- [ ]* 33. V2 API 单元测试
  - Mock API客户端测试每个接口函数
  - 验证请求参数格式和响应类型解析
  - 验证流式ReadableStream消费

- [ ] 34. 检查点 — 确保前端API层全部可用
  - 确保所有V2 API模块正确导出并可导入,如有疑问请询问用户

---

## 前端 — 状态管理

- [ ] 35. 创建 Pipeline Store
  - `src/stores/pipeline.ts`: 流水线状态管理
  - State: currentModule, status, results{}, errorLog
  - Actions: startPipeline, resumePipeline, rerunModule, getStatus
  - 管理整个创作流水线的状态机

- [ ] 36. 创建 Idea Store
  - `src/stores/idea.ts`: 灵感状态管理
  - State: ideas[], selectedIdea, scores, upgradeVersions, risks
  - Actions: generate, score, upgrade, select, analyzeRisks, save

- [ ] 37. 创建 World Store
  - `src/stores/world.ts`: 世界观状态管理
  - State: origin, rules[], layers[], civilization, history, docPath
  - Actions: generateOrigin, generateRules, generateStructure, generateCivilization, generateHistory, checkConsistency, save

- [ ] 38. 创建 Character Store
  - `src/stores/character.ts`: 角色状态管理
  - State: protagonist, supporting[], antagonists[], relationMap
  - Actions: generateProtagonist, generateSupporting, generateAntagonists, buildRelationMap, checkConsistency, save

- [ ] 39. 创建 Story Store
  - `src/stores/story.ts`: 故事体系状态管理
  - State: summary, conflictLayers, theme, volumes[]
  - Actions: generateMaster, generateVolumes, checkConsistency, save

- [ ] 40. 创建 Planning Store
  - `src/stores/planning.ts`: 规划层状态管理(volumes/nodes/chapters/scenes)
  - State: volumes[], plotNodes[], chapterPlans[], chapterOutlines[], scenes[]
  - Actions: generateVolume, generatePlotNodes, planChapters, outlineChapters, designScenes
  - 管理从卷纲到章节细纲的完整规划数据

- [ ] 41. 创建 Execution Store
  - `src/stores/execution.ts`: 执行层状态管理(生成/解析/润色)
  - State: currentDraft, polishResult, parseResult, consistencyReport
  - Actions: generateDraft(stream), polish, parseContent, checkConsistency
  - 管理写作执行的实时状态

- [ ] 42. 创建 Knowledge Store
  - `src/stores/knowledge.ts`: 知识库状态管理
  - State: characterStates, worldState, foreshadows[], history[]
  - Actions: loadSnapshot, updateKnowledge, resolveForeshadow
  - 管理累积的写作状态(角色位置/等级/关系值等)

- [ ] 43. 扩展项目Store — 集成新旧流程
  - 修改 `src/stores/project.ts`: 添加V2项目支持
  - 保留旧load/save/list/remove(兼容旧API)
  - 添加saveV2(保存流水线状态以支持断点续传)
  - 添加关联: project → pipeline

- [ ] 44. 检查点 — 确保所有 Store 正确连接
  - 确保所有 Store 的 Actions 正确调用对应 API,如有疑问请询问用户

---

## 前端 — UI组件

- [ ] 45. 重构 App.vue — 创建V2布局架构
  - 保留旧导航(Craft/Download)不变
  - 新增"创作v2"入口视图
  - 使用ViewRouter: 根据step切换到不同模块视图
  - 侧边栏: 18模块进度面板(已完成/进行中/未解锁)
  - 主内容区: 当前模块的专属视图
  - 顶部: 项目名/保存按钮/流水线控制(暂停/续传)

- [ ] 46. 创建 IdeaView — 灵感生成视图
  - 输入区: 一句话描述 + 类型倾向 + 参考作品
  - 生成区: 展示候选创意卡片(含评分)
  - 升级区: 展示TOP3的两个升级版本
  - 确认区: 选中后显示风险分析 + 确认按钮
  - 调用 IdeaStore 方法

- [ ] 47. 创建 ProjectView — 项目定位视图
  - 平台选择(番茄/起点/七猫/自定义)
  - 12维度展示(每维度可折叠展开)
  - 兼容性检查结果可视化
  - 编辑维度 → 重新生成单个维度
  - 确认 → 触发衍生字段计算

- [ ] 48. 创建 WorldView — 世界观构建视图
  - 5步标签页: 本源/规则/结构/文明/历史
  - 世界本源: 世界类型 + 起源故事 + 隐藏真相
  - 世界规则: 规则卡片列表(6要素展示,可编辑)
  - 世界结构: 层级树形图 + 地点索引
  - 文明体系: 8维度网格卡片
  - 历史时间线: 横向时间轴可视化
  - 一致性检查按钮 + 结果展示

- [ ] 49. 创建 CharacterView — 角色系统视图
  - 主角面板: 九维档案表单(分5个标签页)
  - 配角列表: 卡片网格(点击展开详情)
  - 反派面板: 层级反派体系
  - 关系网络: 节点-边关系图(使用SVG渲染或第三方库)
  - 一致性检查: 高亮冲突

- [ ] 50. 创建 StoryView — 故事体系视图
  - 总纲展示(一句话+冲突+主题)
  - 卷纲预览(卡片列表,每卷显示摘要+钩子)
  - 事件时间线(全部plot_events可视化)
  - 编辑模式: 可手动调整事件位置

- [ ] 51. 创建 PlanningView — 规划层视图
  - 4步流程: 卷纲 → 剧情节点 → 章节规划 → 章节细纲
  - 每步有专属子视图(标签页)
  - 卷纲: 卷列表(每卷详细状态)
  - 剧情节点: 节点卡片(含场景/角色/对白要点)
  - 章节规划: 章列表(含字数/节奏/钩子类型)
  - 章节细纲: 逐章展开(场景/情绪曲线/知识库)

- [ ] 52. 创建 WritingView — 执行层视图
  - 左侧: 章节选择器(含进度标识)
  - 中间: 章节细纲(从Knowledge Store读取当前状态)
  - 右侧: 实时工具面板
    - 知识库面板(当前角色位置/等级/关系)
    - 伏笔面板(待收/已收列表)
    - 一致性面板(最近检查报告)
  - 底部: 流式生成输出区(实时显示生成内容)
  - 工具栏: 润色/重写/对比/解析按钮

- [ ] 53. 创建辅助组件
  - `ModuleProgressSidebar.vue` — 18模块进度侧边栏
  - `KnowledgePanel.vue` — 知识库实时状态面板
  - `ForeshadowPanel.vue` — 伏笔跟踪面板
  - `ConsistencyPanel.vue` — 一致性检查报告面板
  - `EmotionCurveChart.vue` — 情绪曲线可视化(简单折线图)
  - `WorldMapTree.vue` — 世界层级树形组件
  - `RelationGraph.vue` — 角色关系图组件
  - `TimelineChart.vue` — 时间线可视化组件
  - `StreamingOutput.vue` — 流式生成内容展示组件
  - `ModuleResultCard.vue` — 模块结果展示卡片

- [ ] 54. 检查点 — 确保前端构建通过
  - 确保 `npm run build` 成功,无TS类型错误,如有疑问请询问用户

---

## 前端 — 路由与集成

- [ ] 55. 更新路由配置
  - 保留原有路由 `/create` `/craft` `/download`
  - 新增: `/create-v2` → CreateV2View (18模块流水线)
  - `/create-v2/:module` → 路由到特定模块
  - `/create-v2/writing/:chapterId` → 写作界面
  - 根路径仍redirect到`/download`

- [ ] 56. 创建 CreateV2 主视图
  - `src/views/CreateV2.vue`: 18模块流水线主容器
  - 根据 currentModule 动态加载子视图
  - 管理模块间导航(上一步/下一步/跳到指定模块)
  - 处理流水线启动/恢复逻辑
  - 显示全局进度(已完成模块数/总数)

- [ ] 57. 集成旧API兼容层
  - 确保旧Create.vue(5步向导)仍可正常运行
  - 项目列表/下载/Craft视图不受V2影响
  - 旧项目可被V2导入(读取data_json并映射到新schema)
  
- [ ]* 58. 前端E2E测试
  - 测试从灵感到正文生成的基本流水线
  - 测试断点续传功能
  - 测试知识库实时更新
  - 测试一致性检查反馈

- [ ] 59. 检查点 — 确保前端-后端联调成功
  - 确保前端V2页面能正确调用后端V2 API,如有疑问请询问用户

---

## 工程化与优化

- [ ] 60. 添加流式API超时处理
  - V2 draft/polish流式接口确保600s超时
  - Nginx proxy_read_timeout保持600s
  - 前端apiStream自动重试1次

- [ ] 61. 添加错误处理与重试机制
  - PipelineService: 单模块失败后支持从该模块重试
  - 网络断开: 自动重连 + 本地缓存
  - AI返回格式错误: prompt修复 + 重试

- [ ] 62. 添加 V2 API 文档
  - 使用FastAPI原生Swagger(/docs)自动生成
  - 确保所有V2端点有Pydantic模型和描述

- [ ] 63. 性能优化
  - AI生成结果缓存(相同prompt+参数→直接返回缓存)
  - 前端模块懒加载(dynamic import Vuex store)
  - 大文本(split: 分批渲染/虚拟滚动)
  - SQLite查询优化(新索引)

- [ ] 64. 最终检查点 — 全链路验证
  - 完整运行: 灵感 → 项目 → 世界观 → 角色 → 故事 → 力量 → 势力 → 时间线 → 大纲 → 卷纲 → 节点 → 章节规划 → 细纲 → 场景 → 正文 → 润色 → 解析 → 知识库 → 一致性
  - 验证旧Create/Craft/Download功能不受影响
  - 验证Docker部署流程正常工作
