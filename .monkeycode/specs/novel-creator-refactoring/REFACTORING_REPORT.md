# AI小说创作平台 — 流程重构方案报告

> **版本**: v1.0  
> **日期**: 2026-07-05  
> **用途**: 作为项目流程重构的完整技术方案  
> **目标**: 将现有的"灵感→大纲→章节→正文"简单流水线，升级为分层化、模块化、AI Agent 协作的专业创作系统

---

## 第一部分：系统架构总览

### 1.1 架构分层模型

```
┌─────────────────────────────────────────────────────────────────┐
│                      展示层 (Frontend)                           │
│  Vue 3 + Vite + TypeScript + Pinia + Vue Router                 │
│  Tab: 灵感 | 项目 | 世界观 | 人物 | 故事 | 大纲 | 写作 | 下载    │
└────────────────────────────────┬────────────────────────────────┘
                                 │ REST API
┌────────────────────────────────┴────────────────────────────────┐
│                       API 网关层 (Nginx)                         │
│  /fanqie/ → /fanqie/api/* → backend:8000/api/*                  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────┐
│                   应用服务层 (FastAPI Backend)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │ 项目管理  │ │ 世界观   │ │ 人物系统  │ │ 故事系统  │ │ 写作   ││
│  │ Router   │ │ Router   │ │ Router   │ │ Router   │ │ Router ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘│
│       │             │            │             │            │      │
│  ┌────┴─────────────┴────────────┴─────────────┴────────────┴───┐│
│  │               AI Agent 编排引擎 (AgentOrchestrator)           ││
│  │  灵感Agent | 策划Agent | 世界观Agent | 人物Agent | 编剧Agent  ││
│  │  | 写作Agent | 审查Agent | 润色Agent | 知识更新Agent          ││
│  └─────────────────────────┬───────────────────────────────────┘│
│                            │                                     │
│  ┌─────────────────────────┴───────────────────────────────────┐│
│  │               AI Client (统一大模型调用封装)                   ││
│  │  同步 | 流式 | 函数调用 | 多模型切换                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┴────────────────────────────────┐
│                      数据持久层                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐│
│  │ SQLite   │ │ 文件系统  │ │ Session  │ │ 内存缓存              ││
│  │ 结构化数据│ │ Markdown │ │ Store    │ │ (流式/生成状态)       ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 创作流水线分层

```
设计层 (Design Layer) ──────── 解决"为什么要写"和"写什么"
  │
  ├── 模块1: 灵感 (Idea)
  ├── 模块2: 项目定位 (Project)
  ├── 模块3: 世界观 (World Bible)
  ├── 模块4: 人物系统 (Character Bible)
  ├── 模块5: 故事系统 (Story System)
  │
  ▼
结构层 (Structure Layer) ──── 解决"怎么组织"
  │
  ├── 模块6: 力量体系 (Power System)
  ├── 模块7: 势力体系 (Faction System)
  ├── 模块8: 时间线 (Timeline)
  ├── 模块9: 全书大纲 (Master Outline)
  │
  ▼
规划层 (Planning Layer) ──── 解决"怎么写"
  │
  ├── 模块10: 卷纲 (Volume Outline)
  ├── 模块11: 剧情节点 (Story Beat)
  ├── 模块12: 章节规划 (Chapter Plan)
  ├── 模块13: 章节细纲 (Chapter Outline)
  │
  ▼
执行层 (Writing Layer) ──── 解决"写出来"
  │
  ├── 模块14: 场景设计 (Scene Design)
  ├── 模块15: 正文生成 (Draft)
  │
  ▼
完善层 (Polish Layer) ──── 解决"写好"
  │
  ├── 模块16: 润色 (Polish)
  ├── 模块17: 一致性检查 (Consistency Check)
  └── 模块18: 知识库更新 (Knowledge Update)
```

### 1.3 核心设计原则

| 原则 | 说明 |
|------|------|
| **数据与文档分离** | 结构化数据存 SQLite，长文本/Markdown 存文件系统 |
| **状态驱动** | 每个模块有明确的状态机，不允许跳跃式创作 |
| **单线程写入** | 同一时刻只有一个 AI Agent 在写入，避免冲突 |
| **引用而非复制** | 后续模块通过 ID 引用前置模块，不复制内容 |
| **增量更新** | 已生成的内容可通过 Agent 增量修改，而非重新生成 |
| **版本可追溯** | 所有 AI 生成内容保留版本历史 |

---

## 第二部分：数据库设计

### 2.1 数据库选型

| 存储类型 | 技术 | 用途 |
|---------|------|------|
| 结构化数据 | SQLite (WAL模式) | 项目、人物、章节、伏笔等结构化记录 |
| 长文本/Markdown | 文件系统 | 世界观文档、章节正文、细纲等 |
| 运行时状态 | 内存 (Python Dict) | 流式生成状态、任务队列 |
| 会话缓存 | Pinia Store | UI 端临时状态、编辑草稿 |

### 2.2 ER 关系图

```
projects (1) ──── (N) world_buildings
projects (1) ──── (N) characters
projects (1) ──── (N) story_systems
projects (1) ──── (N) power_systems
projects (1) ──── (N) factions
projects (1) ──── (N) timelines
projects (1) ──── (N) master_outlines
projects (1) ──── (N) volumes
projects (1) ──── (N) chapters
projects (1) ──── (N) scenes
projects (1) ──── (N) foreshadowings
projects (1) ──── (N) knowledge_states
projects (1) ──── (N) generation_tasks
projects (1) ──── (N) ai_generations (版本历史)
```

### 2.3 完整表结构

#### 2.3.1 projects（项目主表）

```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,                    -- UUID
    name TEXT NOT NULL,                     -- 项目名
    status INTEGER NOT NULL DEFAULT 0,       -- 状态机: 0=创建中,1=灵感,2=项目定位,3=世界观,4=人物,5=故事,6=大纲,7=卷纲,8=章节规划,9=细纲,10=写作中,11=已完成
    
    -- 灵感阶段核心字段
    idea_core TEXT,                         -- 核心创意(一句话)
    idea_selling_points TEXT,               -- 卖点列表(JSON Array)
    idea_innovation TEXT,                   -- 创新点
    idea_target_audience TEXT,              -- 目标读者(JSON: {age, preferences})
    idea_sustainability INTEGER,            -- 可持续性评分 1-5
    idea_risks TEXT,                        -- 风险分析(JSON Array)
    
    -- 项目定位核心字段
    project_type TEXT,                      -- 类型: 都市/修仙/科幻/末日/无限流...
    project_subtype TEXT,                   -- 子类型: 高武/系统/神豪/校园...
    project_tags TEXT,                      -- 标签(JSON Array)
    project_platform TEXT,                  -- 目标平台: 番茄/起点/七猫...
    project_total_words INTEGER,            -- 目标总字数
    project_chapter_length INTEGER,         -- 每章字数
    project_daily_update INTEGER,           -- 每日更新字数
    project_style TEXT,                     -- 风格: 轻松/热血/黑暗/治愈...
    project_pace TEXT,                      -- 节奏: 极快/快/中/慢
    project_content_boundary TEXT,          -- 内容边界(不能写什么)
    
    -- 写作阶段状态
    current_volume INTEGER DEFAULT 0,       -- 当前卷号
    current_chapter INTEGER DEFAULT 0,      -- 当前章节号
    current_stage INTEGER DEFAULT 0,        -- 当前流水线阶段
    
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_updated ON projects(updated_at DESC);
```

#### 2.3.2 world_buildings（世界观表）

```sql
CREATE TABLE world_buildings (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 世界本源
    origin_type TEXT,                       -- 世界类型: 现实/平行/模拟/神创/科技/梦境...
    origin_description TEXT,                -- 世界本源描述(Markdown,存文件路径)
    
    -- 世界规则
    rules TEXT,                             -- 世界规则(JSON Array of {rule, description, importance})
    
    -- 世界结构
    structure TEXT,                         -- 世界结构(JSON: 层级关系)
    map_description TEXT,                   -- 地图描述
    
    -- 文明体系
    civilization TEXT,                      -- 文明体系(JSON: {nations, economy, education, religion...})
    
    -- 历史演化
    history_timeline TEXT,                  -- 历史时间线(JSON Array of {era, event, year})
    
    -- 隐藏真相
    hidden_truth TEXT,                      -- 隐藏真相(Markdown)
    
    -- 文档路径 (长文本存储)
    doc_path TEXT,                          -- 02_世界观/ 目录路径
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_world_project ON world_buildings(project_id);
```

#### 2.3.3 characters（人物表）

```sql
CREATE TABLE characters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 基础档案
    name TEXT NOT NULL,
    role_type TEXT NOT NULL,                -- 主角/配角/反派/NPC/龙套
    age INTEGER,
    gender TEXT,
    birthday TEXT,
    height TEXT,
    weight TEXT,
    identity TEXT,                          -- 身份
    occupation TEXT,                        -- 职业
    race TEXT,                              -- 种族
    affiliation TEXT,                       -- 所属势力(faction_id)
    birthplace TEXT,                        -- 出生地
    
    -- 外貌系统
    appearance TEXT,                        -- 外貌(JSON: {hair, eyes, skin, build, clothing_style, signature_item})
    
    -- 性格系统
    personality TEXT,                       -- 性格(JSON: {values, bottom_line, strengths, weaknesses, fears, obsession, speaking_style, behavior_traits})
    
    -- 能力系统
    abilities TEXT,                         -- 能力(JSON: {level, skills, equipment, resources, special_abilities, limitations, side_effects, growth_direction})
    
    -- 成长系统
    growth_route TEXT,                      -- 成长路线(JSON Array of {stage, name, volume_range, description})
    
    -- 关系系统 (指向其他 character IDs)
    relationships TEXT,                     -- 关系(JSON Array of {character_id, relation_type, current_value, future_note})
    
    -- 心理系统
    psychology TEXT,                        -- 心理(JSON: {current_mood, trauma, stress_level, secrets, obsession, mental_state})
    
    -- 动态状态
    current_state TEXT,                     -- 当前状态(JSON: {level, hp, equipment, location, wealth, stamina})
    
    -- 人物日志摘要 (详细日志存文件)
    log_summary TEXT,                       -- 最新事件摘要
    log_doc_path TEXT,                      -- 人物日志文件路径
    
    -- 排序
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_char_project ON characters(project_id);
CREATE INDEX idx_char_type ON characters(project_id, role_type);
CREATE INDEX idx_char_name ON characters(project_id, name);
```

#### 2.3.4 story_systems（故事系统表）

```sql
CREATE TABLE story_systems (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    theme TEXT,                             -- 主题(一句话)
    core_question TEXT,                     -- 核心问题
    core_conflict TEXT,                     -- 核心冲突
    main_plot TEXT,                         -- 主线(一句话)
    sub_plots TEXT,                         -- 支线(JSON Array of {name, description, start_volume, end_volume})
    character_arc TEXT,                     -- 人物成长弧(JSON Array of {stage, volume, description})
    conflict_loop TEXT,                     -- 冲突循环(JSON: {pattern, description})
    reward_loop TEXT,                       -- 爽点循环(JSON: {pattern, intervals})
    world_escalation TEXT,                  -- 世界升级(JSON Array of {stage, scope, trigger})
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_story_project ON story_systems(project_id);
```

#### 2.3.5 master_outlines（全书大纲表）

```sql
CREATE TABLE master_outlines (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    opening TEXT,                           -- 小说开局(Markdown,存文件路径)
    act_structure TEXT,                     -- 五幕结构(JSON Array of {act_number, name, description, volume_range})
    world_escalation TEXT,                  -- 世界升级路线(JSON Array)
    character_growth TEXT,                  -- 人物成长路线(JSON Array)
    foreshadowing_plan TEXT,                -- 伏笔规划(引用 foreshadowings 表)
    ending_plan TEXT,                       -- 结局规划(JSON: {type, description})
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_outline_project ON master_outlines(project_id);
```

#### 2.3.6 volumes（卷表）

```sql
CREATE TABLE volumes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    volume_number INTEGER NOT NULL,
    
    -- 卷基本信息
    title TEXT,                             -- 卷名
    position TEXT,                          -- 本卷定位(在整本书中的作用)
    goal TEXT,                              -- 本卷目标
    theme TEXT,                             -- 本卷主题
    target_words INTEGER,                   -- 目标字数
    chapter_count INTEGER,                  -- 章节数量
    
    -- 剧情结构
    opening TEXT,                           -- 开端
    conflict TEXT,                          -- 核心冲突
    midpoint_twist TEXT,                    -- 中期转折
    climax TEXT,                            -- 高潮
    ending TEXT,                            -- 收尾
    next_volume_bridge TEXT,                -- 下一卷接口(钩子)
    
    -- 本卷状态
    status INTEGER DEFAULT 0,               -- 0=未开始,1=设计中,2=写作中,3=已完成
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_volume_project ON volumes(project_id);
CREATE INDEX idx_volume_number ON volumes(project_id, volume_number);
```

#### 2.3.7 story_beats（剧情节点表）

```sql
CREATE TABLE story_beats (
    id TEXT PRIMARY KEY,
    volume_id TEXT NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    beat_number INTEGER NOT NULL,           -- Beat序号
    
    name TEXT NOT NULL,                     -- Beat名称
    beat_type TEXT NOT NULL,                -- info/relationship/power/status/conflict/world
    
    trigger_event TEXT,                     -- 触发事件
    goal TEXT,                              -- 目标
    obstacle TEXT,                          -- 阻碍
    state_change TEXT,                      -- 状态变化(从X到Y)
    result TEXT,                            -- 结果
    new_question TEXT,                      -- 新问题
    
    -- 章节映射
    start_chapter INTEGER,                  -- 起始章节
    end_chapter INTEGER,                    -- 结束章节
    
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_beat_volume ON story_beats(volume_id);
CREATE INDEX idx_beat_number ON story_beats(volume_id, beat_number);
```

#### 2.3.8 chapters（章节表）

```sql
CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    volume_id TEXT REFERENCES volumes(id),
    chapter_number INTEGER NOT NULL,
    
    title TEXT,                             -- 章节标题
    status INTEGER DEFAULT 0,               -- 0=未开始,1=规划中,2=细纲中,3=写作中,4=已完成,5=润色中,6=已发布
    
    -- 章节规划核心字段
    goal TEXT,                              -- 章节目标
    conflict TEXT,                          -- 冲突
    progress_content TEXT,                  -- 推进内容
    mini_climax TEXT,                       -- 小高潮
    hook TEXT,                              -- 章节钩子
    state_change TEXT,                      -- 状态变化(JSON)
    
    -- 关联Beat
    beat_id TEXT REFERENCES story_beats(id),
    
    -- 统计数据
    target_words INTEGER DEFAULT 2000,
    actual_words INTEGER DEFAULT 0,
    
    -- 文件路径 (长文本)
    outline_path TEXT,                      -- 章节细纲文件路径
    draft_path TEXT,                        -- 正文文件路径
    polished_path TEXT,                     -- 润色后文件路径
    
    -- 版本控制
    version INTEGER DEFAULT 1,
    generated_at TIMESTAMP,
    polished_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chapter_project ON chapters(project_id);
CREATE INDEX idx_chapter_volume ON chapters(volume_id);
CREATE INDEX idx_chapter_number ON chapters(project_id, chapter_number);
CREATE INDEX idx_chapter_status ON chapters(status);
```

#### 2.3.9 scenes（场景表）

```sql
CREATE TABLE scenes (
    id TEXT PRIMARY KEY,
    chapter_id TEXT NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    scene_number INTEGER NOT NULL,
    
    title TEXT,
    setting TEXT,                           -- 场景设置(时间地点氛围)
    characters_present TEXT,                -- 出场人物(JSON Array of character_ids)
    goal TEXT,                              -- 场景目标
    conflict TEXT,                          -- 场景冲突
    outcome TEXT,                           -- 场景结果
    hook TEXT,                              -- 场景钩子
    
    target_words INTEGER DEFAULT 600,
    actual_words INTEGER DEFAULT 0,
    
    status INTEGER DEFAULT 0,               -- 0=未开始,1=写作中,2=已完成
    
    -- 文件
    content_path TEXT,                      -- 场景正文文件路径
    
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scene_chapter ON scenes(chapter_id);
CREATE INDEX idx_scene_number ON scenes(chapter_id, scene_number);
```

#### 2.3.10 foreshadowings（伏笔表）

```sql
CREATE TABLE foreshadowings (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    code TEXT NOT NULL,                     -- 编号: V1-001(第一卷第一个伏笔)
    volume_id TEXT REFERENCES volumes(id),
    
    setup_chapter INTEGER,                  -- 埋设章节
    setup_scene TEXT,                       -- 埋设位置描述
    content TEXT,                           -- 伏笔内容
    
    payoff_chapter INTEGER,                 -- 回收章节(可能跨卷)
    payoff_scene TEXT,                      -- 回收位置描述
    payoff_content TEXT,                    -- 回收内容
    
    status TEXT DEFAULT 'active',           -- active(未回收)/paid(已回收)/abandoned(废弃)
    importance TEXT DEFAULT 'normal',       -- critical/normal/minor
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_foreshadow_project ON foreshadowings(project_id);
CREATE INDEX idx_foreshadow_status ON foreshadowings(status);
CREATE INDEX idx_foreshadow_setup ON foreshadowings(setup_chapter);
```

#### 2.3.11 power_systems（力量体系表）

```sql
CREATE TABLE power_systems (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    name TEXT,                              -- 体系名称: 修炼/异能/科技...
    
    levels TEXT,                            -- 等级(JSON Array of {level, name, power_description, requirements})
    skills TEXT,                            -- 技能体系(JSON Array)
    resources TEXT,                         -- 资源/材料(JSON Array)
    breakthrough_method TEXT,               -- 突破方式
    lifespan_effect TEXT,                   -- 寿命影响
    limitations TEXT,                       -- 限制条件(JSON Array)
    side_effects TEXT,                      -- 副作用(JSON Array)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_power_project ON power_systems(project_id);
```

#### 2.3.12 factions（势力体系表）

```sql
CREATE TABLE factions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    name TEXT NOT NULL,
    headquarters TEXT,                      -- 总部
    philosophy TEXT,                        -- 理念/宗旨
    history TEXT,                           -- 历史(Markdown)
    leader TEXT,                            -- 首领(character_id)
    members TEXT,                           -- 成员(JSON Array of {character_id, position, power_level})
    allies TEXT,                            -- 盟友(JSON Array of faction_ids)
    enemies TEXT,                           -- 敌人(JSON Array of faction_ids)
    resources TEXT,                         -- 资源(JSON Array)
    power_level TEXT,                       -- 整体实力评级
    territory TEXT,                         -- 势力范围
    
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_faction_project ON factions(project_id);
```

#### 2.3.13 timelines（时间线表）

```sql
CREATE TABLE timelines (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    event_number INTEGER NOT NULL,          -- 序号
    era TEXT,                               -- 时代/时期
    year TEXT,                              -- 年份/时间点
    event TEXT NOT NULL,                    -- 事件描述
    event_type TEXT DEFAULT 'normal',       -- world/character/plot/world_beat
    related_characters TEXT,                -- 相关人物(JSON Array)
    related_locations TEXT,                 -- 相关地点(JSON Array)
    
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timeline_project ON timelines(project_id);
```

#### 2.3.14 knowledge_states（知识状态总表）

```sql
CREATE TABLE knowledge_states (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 最新状态快照 (每写完一章更新)
    last_chapter_number INTEGER DEFAULT 0,  -- 最后完成章节号
    last_updated TIMESTAMP,                  -- 最后更新时间
    
    -- 状态快照(JSON,包含完整当前状态)
    snapshot TEXT NOT NULL,
    /*
    snapshot 结构:
    {
        "characters": {
            "char_id_1": { "level": "筑基二层", "hp": "80%", "location": "学院", ... },
            ...
        },
        "world": {
            "current_state": "灵气复苏第三年",
            "public_awareness": true,
            "major_events": ["副本降临", "全球觉醒"]
        },
        "relationships": {
            "char1_char2": { "trust": 85, "status": "恋人" }
        },
        "inventory": {
            "char_id_1": ["青云剑", "回春丹×3"]
        },
        "pending_foreshadowings": ["V1-001", "V2-003"],
        "completed_foreshadowings": ["V1-002"]
    }
    */
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_project ON knowledge_states(project_id);
```

#### 2.3.15 generation_tasks（AI生成任务表）

```sql
CREATE TABLE generation_tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    task_type TEXT NOT NULL,                -- idea/project/world/character/story/outline/volume/beat/chapter/scene/draft/polish/consistency
    
    -- 目标引用
    target_type TEXT,                       -- project/volume/chapter/scene/character/faction...
    target_id TEXT,                         -- 目标实体ID
    
    -- 任务状态
    status INTEGER DEFAULT 0,               -- 0=待处理,1=处理中,2=已完成,3=失败,4=已取消
    priority INTEGER DEFAULT 5,             -- 1-10, 10最高
    
    -- 输入/输出
    input_data TEXT,                        -- 输入参数(JSON)
    output_data TEXT,                       -- 输出结果(JSON,包含生成内容的文件路径)
    error_message TEXT,                     -- 错误信息
    
    -- 重试
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- AI模型配置
    model_config TEXT,                      -- 使用的AI模型配置(JSON)
    
    -- 时间
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_task_project ON generation_tasks(project_id);
CREATE INDEX idx_task_status ON generation_tasks(status);
CREATE INDEX idx_task_type ON generation_tasks(project_id, task_type);
```

#### 2.3.16 ai_generations（AI生成版本历史表）

```sql
CREATE TABLE ai_generations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    entity_type TEXT NOT NULL,              -- chapter/scene/character/outline/...
    entity_id TEXT NOT NULL,                -- 对应实体ID
    version INTEGER NOT NULL,               -- 版本号
    
    -- 生成信息
    content_path TEXT,                      -- 生成内容文件路径
    content_preview TEXT,                   -- 预览文本(前200字)
    word_count INTEGER DEFAULT 0,
    
    -- 生成参数
    model_name TEXT,                        -- 模型名
    prompt_type TEXT,                       -- 使用的prompt类型
    prompt_hash TEXT,                       -- prompt的hash(用于去重)
    generation_params TEXT,                 -- 生成参数(JSON: temperature, max_tokens等)
    
    -- 用户反馈
    rating INTEGER,                         -- 用户评分1-5
    feedback TEXT,                          -- 用户反馈文本
    is_accepted BOOLEAN DEFAULT 0,          -- 是否被采纳
    
    -- 时间
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(entity_type, entity_id, version)
);

CREATE INDEX idx_gen_entity ON ai_generations(entity_type, entity_id);
CREATE INDEX idx_gen_project ON ai_generations(project_id);
```

#### 2.3.17 character_relations（人物关系表 — 可选展开）

```sql
CREATE TABLE character_relations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    source_id TEXT NOT NULL REFERENCES characters(id),
    target_id TEXT NOT NULL REFERENCES characters(id),
    
    relation_type TEXT NOT NULL,            -- parent/child/sibling/friend/rival/lover/master/apprentice/enemy/ally
    
    trust_level INTEGER DEFAULT 50,         -- -100 到 100
    status TEXT DEFAULT 'stable',           -- stable/improving/deteriorating
    current_note TEXT,                      -- 当前关系描述
    future_plan TEXT,                       -- 未来计划
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_id, target_id, relation_type)
);

CREATE INDEX idx_rel_source ON character_relations(source_id);
CREATE INDEX idx_rel_target ON character_relations(target_id);
```

### 2.4 存储策略矩阵

| 数据 | 位置 | 理由 |
|------|------|------|
| 项目元信息 | SQLite | 需要查询、排序、过滤 |
| 人物基础信息 | SQLite | 需要按类型/姓名查询 |
| 世界观结构(JSON) | SQLite | 结构化查询，规则检索 |
| 世界观详细描述 | 文件(.md) | 大文本，需要Markdown渲染 |
| 故事系统 | SQLite + 文件 | 结构字段存DB，详细文档存文件 |
| 大纲各层级 | SQLite + 文件 | 同上 |
| 章节细纲 | 文件(.md) | 大文本 |
| 场景正文 | 文件(.md) | 大文本 |
| 人物日志 | 文件(.md) | 频繁追加写入 |
| 知识状态快照 | SQLite (JSON) | 需要快速读取 |
| AI生成版本 | 文件(.md) + SQLite索引 | 需要历史对比 |
| 伏笔 | SQLite | 频繁查询和状态更新 |
| 时间线 | SQLite | 需要排序和过滤 |
| 势力 | SQLite + 文件 | 结构信息存DB |

---

## 第三部分：API 设计

### 3.1 RESTful API 概览

```
/api/novel/projects/*              — 项目管理
/api/novel/idea/*                  — 灵感模块
/api/novel/project/*               — 项目定位
/api/novel/world/*                 — 世界观
/api/novel/characters/*            — 人物系统
/api/novel/story/*                 — 故事系统
/api/novel/power/*                 — 力量体系
/api/novel/factions/*              — 势力体系
/api/novel/timeline/*              — 时间线
/api/novel/outline/*               — 全书大纲
/api/novel/volumes/*               — 卷纲
/api/novel/beats/*                 — 剧情节点
/api/novel/chapters/*              — 章节
/api/novel/scenes/*                — 场景
/api/novel/foreshadowings/*        — 伏笔
/api/novel/draft/*                 — 正文生成
/api/novel/knowledge/*             — 知识库
/api/novel/tasks/*                 — AI任务
/api/novel/generations/*           — 版本历史
```

### 3.2 核心API详细设计

#### 3.2.1 灵感模块

```
POST   /api/novel/idea/generate          — AI生成创意灵感(流式)
POST   /api/novel/idea/score             — AI评分创意
POST   /api/novel/idea/fuse              — AI融合多个创意
PUT    /api/novel/idea/select            — 用户选定灵感
GET    /api/novel/idea/history           — 获取灵感生成历史
```

#### 3.2.2 项目定位

```
POST   /api/novel/project/generate       — AI生成项目定位(流式)
POST   /api/novel/project/validate       — AI分析项目可行性
POST   /api/novel/project/risk-analysis  — AI风险分析
PUT    /api/novel/project/save           — 保存项目定位
GET    /api/novel/project/{id}           — 获取项目定位
```

#### 3.2.3 世界观

```
POST   /api/novel/world/generate         — AI生成世界观(流式,分步)
POST   /api/novel/world/expand           — AI扩展世界观某一层
POST   /api/novel/world/check            — AI检查世界观漏洞
PUT    /api/novel/world/save             — 保存世界观
GET    /api/novel/world/{project_id}     — 获取世界观
GET    /api/novel/world/{project_id}/doc — 获取世界观文档(Markdown)
```

#### 3.2.4 人物系统

```
POST   /api/novel/characters/generate    — AI生成角色
POST   /api/novel/characters/expand      — AI扩展角色设定
POST   /api/novel/characters/relation    — AI分析角色关系
PUT    /api/novel/characters/{id}        — 更新角色
GET    /api/novel/characters/{id}        — 获取角色详情
GET    /api/novel/characters/project/{pid} — 获取项目全部角色
DELETE /api/novel/characters/{id}        — 删除角色
POST   /api/novel/characters/{id}/log    — 追加角色日志
POST   /api/novel/characters/{id}/state  — 更新角色状态
```

#### 3.2.5 故事系统

```
POST   /api/novel/story/generate         — AI生成故事系统(流式)
POST   /api/novel/story/validate         — AI验证故事逻辑
PUT    /api/novel/story/save             — 保存故事系统
GET    /api/novel/story/{project_id}     — 获取故事系统
```

#### 3.2.6 大纲体系

```
POST   /api/novel/outline/generate       — AI生成全书大纲
PUT    /api/novel/outline/save           — 保存大纲

POST   /api/novel/volumes/generate       — AI生成卷纲
PUT    /api/novel/volumes/{id}           — 保存卷纲
GET    /api/novel/volumes/{volume_id}/beats — 获取卷内Beat列表

POST   /api/novel/beats/generate         — AI生成Beat
PUT    /api/novel/beats/{id}             — 保存Beat
```

#### 3.2.7 章节体系

```
POST   /api/novel/chapters/generate-plan — AI生成章节规划
POST   /api/novel/chapters/generate-outline — AI生成章节细纲(流式)
PUT    /api/novel/chapters/{id}/plan     — 保存章节规划
PUT    /api/novel/chapters/{id}/outline  — 保存章节细纲

POST   /api/novel/scenes/generate        — AI生成场景设计
PUT    /api/novel/scenes/{id}            — 保存场景
```

#### 3.2.8 正文生成

```
POST   /api/novel/draft/generate         — AI生成正文(流式)
POST   /api/novel/draft/regenerate       — AI重新生成(带修改意见)
POST   /api/novel/draft/polish           — AI润色(流式)
POST   /api/novel/draft/expand           — AI扩写
POST   /api/novel/draft/rewrite          — AI改写(指定段落)

GET    /api/novel/draft/{chapter_id}     — 获取最新正文
GET    /api/novel/draft/{chapter_id}/versions — 获取版本列表
```

#### 3.2.9 知识库与一致性

```
GET    /api/novel/knowledge/{project_id} — 获取当前知识状态
POST   /api/novel/knowledge/update      — AI更新知识状态
POST   /api/novel/knowledge/check       — AI一致性检查
GET    /api/novel/knowledge/foreshadowings — 获取活跃伏笔
```

#### 3.2.10 AI任务管理

```
POST   /api/novel/tasks/create           — 创建生成任务
GET    /api/novel/tasks/{project_id}     — 获取项目任务列表
PUT    /api/novel/tasks/{id}/status      — 更新任务状态
POST   /api/novel/tasks/{id}/cancel      — 取消任务
DELETE /api/novel/tasks/{id}             — 删除任务
```

### 3.3 通用请求/响应格式

```json
// AI生成请求通用格式
POST /api/novel/{module}/generate
{
    "project_id": "uuid",
    "model": {
        "endpoint": "...",
        "apiKey": "...",
        "model": "gpt-4"
    },
    "temperature": 0.7,
    "max_tokens": 8000,
    "stream": true,
    "params": { /* 模块特定参数 */ },
    "user_input": "用户的额外输入"
}

// 任务响应格式
{
    "task_id": "uuid",
    "status": "processing|completed|failed",
    "message": "正在生成中...",
    "estimated_seconds": 30
}

// 流式响应格式 (SSE)
data: {"type": "progress", "message": "正在生成世界观...", "percent": 30}
data: {"type": "content", "content": "..."}
data: {"type": "done", "result": {...}}
```

---

## 第四部分：AI Agent 设计

### 4.1 Agent 分类

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **IdeaAgent** | 创意生成与评分 | 用户意图 | Idea.md |
| **ProjectAgent** | 项目定位策划 | Idea | Project.md |
| **WorldAgent** | 世界观设计 | Idea + Project | World Bible |
| **CharacterAgent** | 角色设计与管理 | Idea + World | Character Profiles |
| **StoryAgent** | 故事系统设计 | Idea + Characters | Story System |
| **OutlineAgent** | 大纲生成 | Story + World | Master Outline |
| **VolumeAgent** | 卷纲生成 | Outline + Story | Volume Outline |
| **BeatAgent** | 剧情节点设计 | Volume Outline | Story Beats |
| **ChapterPlannerAgent** | 章节规划 | Beats + Volume | Chapter Plans |
| **SceneDesignerAgent** | 场景设计 | Chapter Plan | Scenes |
| **DraftWriterAgent** | 正文撰写 | Scenes + Knowledge | Draft |
| **PolishAgent** | 润色优化 | Draft + Character profiles | Polished text |
| **ConsistencyAgent** | 一致性检查 | All modules | Consistency report |
| **KnowledgeAgent** | 知识库更新 | Draft + Knowledge State | Updated Knowledge |
| **ForeshadowAgent** | 伏笔管理 | Story + Outline | Foreshadowing plan |
| **CritiqueAgent** | AI自审/评分 | Any generated content | Score + suggestions |

### 4.2 Agent 协作模式

```python
# AgentOrchestrator 核心逻辑
class AgentOrchestrator:
    """AI Agent 编排器 — 管理创作流水线"""
    
    async def execute_pipeline(self, project_id: str, target_stage: int):
        """执行流水线直到目标阶段"""
        project = await self.get_project(project_id)
        current_stage = project.status
        
        while current_stage <= target_stage:
            # 1. 创建生成任务
            task = await self.create_task(project_id, current_stage)
            
            # 2. 加载前置模块数据
            context = await self.load_context(project_id, current_stage)
            
            # 3. 选择并执行对应 Agent
            agent = self.get_agent_for_stage(current_stage)
            result = await agent.execute(context, task)
            
            # 4. 保存结果
            await self.save_result(project_id, current_stage, result)
            
            # 5. 更新项目状态
            await self.advance_stage(project_id)
            current_stage += 1
```

### 4.3 Agent Prompt 模板管理

| Agent | Prompt 模板 | 关键指令 |
|-------|------------|---------|
| IdeaAgent | `prompts/idea_generate.md` | 发散生成→评分→精选→升级 |
| ProjectAgent | `prompts/project_design.md` | 12维度策划→风险检查 |
| WorldAgent | `prompts/world_design.md` | 六层设计→漏洞检验 |
| CharacterAgent | `prompts/character_design.md` | 九维设计→关系网构建 |
| StoryAgent | `prompts/story_design.md` | 九模块设计→冲突循环 |
| DraftWriterAgent | `prompts/draft_write.md` | Beat→Chapter→Scene→正文 |

---

## 第五部分：状态管理与工作流引擎

### 5.1 项目状态机

```
[创建项目] → 0: Creating
                ↓
           1: Idea (灵感阶段)
                ↓ (用户确认灵感)
           2: Project (项目定位)
                ↓ (用户确认项目定位)
           3: World (世界观设计)
                ↓ (用户确认世界观)
           4: Character (人物系统)
                ↓ (用户确认人物)
           5: Story (故事系统)
                ↓ (用户确认故事)
           6: Outline (全书大纲)
                ↓ (用户确认大纲)
           7: Volume (卷纲设计)
                ↓ (用户确认卷纲)
           8: ChapterPlan (章节规划)
                ↓ (用户确认章节规划)
           9: OutlineDetail (细纲)
                ↓ (用户确认细纲)
           10: Writing (写作中) ← 此阶段可循环多章
                ↓ (所有章节完成)
           11: Completed (已完成)
```

### 5.2 章节状态机

```
0: NotStarted → 1: Planned (规划中)
                    ↓
               2: Outlined (细纲完成)
                    ↓
               3: Drafting (正文写作中)
                    ↓
               4: DraftDone (正文完成)
                    ↓
               5: Polishing (润色中)
                    ↓
               6: Polished (润色完成)
                    ↓
               7: ConsistencyCheck (一致性检查中)
                    ↓ (通过)
               8: Published (已发布/完成)
                    ↓ (未通过)
               3: Drafting (退回修改)
```

### 5.3 知识库更新触发点

| 触发事件 | 更新内容 | 操作 |
|---------|---------|------|
| 章节正文完成 | 人物状态、世界状态、装备、关系 | KnowledgeAgent 自动更新 |
| 人物属性修改 | 相关章节的一致性 | 触发 ConsistencyAgent |
| 世界观修改 | 后续章节内容 | 标记待检查章节 |
| 伏笔回收 | 伏笔状态更新 | 自动标记为 paid |
| 手动触发 | 全面一致性检查 | ConsistencyAgent 全量扫描 |

### 5.4 文件目录结构

```
/projects/{project_id}/
├── project.json                  -- 项目元信息 (从DB导出缓存)
├── projects.md                   -- 项目定位文档
├── idea.md                       -- 灵感文档
├── world_bible/                  -- 世界观文档
│   ├── 01_世界简介.md
│   ├── 02_世界本源.md
│   ├── 03_世界规则.md
│   ├── 04_世界结构.md
│   ├── 05_文明体系.md
│   ├── 06_历史时间线.md
│   ├── 07_地图设定.md
│   ├── 08_隐藏真相.md
│   └── README.md
├── characters/                   -- 人物文档
│   ├── 主角/
│   │   ├── 林夜.md
│   │   └── 林夜_log.md
│   ├── 配角/
│   ├── 反派/
│   ├── 人物关系图.md
│   └── 人物状态总表.md
├── story_system/                 -- 故事系统
│   ├── 01_主题.md
│   ├── 02_核心冲突.md
│   ├── 03_主线剧情.md
│   ├── 04_人物成长弧.md
│   ├── 05_冲突循环.md
│   ├── 06_爽点循环.md
│   └── 07_世界升级.md
├── power_system.md               -- 力量体系
├── factions/                     -- 势力体系
│   ├── 天剑宗.md
│   └── 帝国.md
├── timeline.md                   -- 时间线
├── outlines/                     -- 大纲文档
│   ├── master_outline.md         -- 全书大纲
│   └── volumes/
│       ├── volume_01/
│       │   ├── README.md         -- 卷纲
│       │   ├── beats.md          -- 剧情节点
│       │   ├── chapters.md       -- 章节规划
│       │   └── chapters/         -- 章节细纲
│       │       ├── ch_001.md
│       │       └── ch_002.md
│       └── volume_02/
├── drafts/                       -- 正文
│   ├── volume_01/
│   │   ├── ch_001/
│   │   │   ├── scene_01.md
│   │   │   ├── scene_02.md
│   │   │   ├── full.md           -- 合并后的完整章节
│   │   │   └── polished.md       -- 润色后
│   │   └── ch_002/
│   └── volume_02/
├── knowledge/                    -- 知识库快照
│   ├── latest.json               -- 最新状态快照
│   └── history/
│       ├── after_ch_001.json
│       └── after_ch_002.json
├── foreshadowings.md             -- 伏笔总表
├── generations/                  -- AI生成版本历史
│   ├── ch_001_v1.md
│   ├── ch_001_v2.md
│   └── ch_002_v1.md
└── consistency_reports/          -- 一致性检查报告
    └── report_ch_001.md
```

---

## 第六部分：改造实施计划

### 6.1 分阶段实施

#### Phase 1: 数据库重构 (2天)

| 任务 | 说明 |
|------|------|
| 创建新表结构 | 按本报告2.3节创建所有表 |
| 数据迁移脚本 | 将现有 `novel_data` JSON 字段拆分到新表 |
| 兼容层 | 旧API保持兼容，新API开始并行 |

#### Phase 2: 核心Agent实现 (3天)

| 任务 | 说明 |
|------|------|
| AgentOrchestrator | 任务编排引擎 |
| IdeaAgent | 灵感生成 |
| ProjectAgent | 项目定位 |
| WorldAgent | 世界观设计（最大模块） |
| CharacterAgent | 人物系统 |
| DraftWriterAgent | 正文写作 |

#### Phase 3: 前端页面重构 (3天)

| 任务 | 说明 |
|------|------|
| 灵感页面 | 多创意生成→评分→选择 |
| 项目定位页面 | 12维度展示和编辑 |
| 世界观页面 | 六层分步设计 |
| 人物页面 | 角色卡片+关系图+状态面板 |
| 大纲页面 | 全书→卷→Beat→章节 多层展示 |
| 写作页面 | 章节规划→细纲→正文→润色 流水线 |

#### Phase 4: 完善层实现 (2天)

| 任务 | 说明 |
|------|------|
| PolishAgent | 五轮润色 |
| ConsistencyAgent | 一致性检查 |
| KnowledgeAgent | 知识库自动更新 |
| ForeshadowAgent | 伏笔管理 |

#### Phase 5: 测试与优化 (2天)

| 任务 | 说明 |
|------|------|
| 端到端流程测试 | 从灵感到正文完整走通 |
| 性能优化 | 流式响应、并发控制 |
| 容错处理 | 中断恢复、重试、版本回退 |

### 6.2 兼容性策略

| 方面 | 策略 |
|------|------|
| 旧数据 | 保留 `project.data` JSON 字段，新表为空时从JSON读取 |
| 旧API | 继续支持至少3个月 |
| 新API | 按 `/api/v2/` 路径前缀 |
| 前端Tab | 现有Tab保留，新增Tab逐步展示新能力 |

---

## 第七部分：关键设计决策说明

### 7.1 为什么 SQLite 而不是 MySQL/PostgreSQL？

1. **零运维**: 当前环境是单台腾讯云服务器，SQLite 无需独立数据库服务
2. **便携性**: 整个项目可以打包带走，适合本地开发
3. **WAL模式**: 支持并发读+单写，满足当前需求
4. **数据量**: 单个项目最多几百MB，SQLite 完全可以胜任

### 7.2 为什么长文本存文件而不存数据库？

1. **版本对比**: 文件方便 diff 对比
2. **Markdown渲染**: 文件天然支持 Markdown 编辑器
3. **AI上下文**: AI 可以直接读取文件送入 prompt
4. **减少DB膨胀**: 大文本会导致 SQLite 性能下降

### 7.3 为什么不做实时协作（多用户）？

当前阶段是单用户创作工具，多用户协作会显著增加复杂度。未来可以通过以下方式扩展：
- 前端状态 → WebSocket 实时同步
- 后端状态 → PostgreSQL + Redis 替代 SQLite
- Agent → Celery + Redis 任务队列

### 7.4 评分体系设计

每个 AI 生成的内容都有自动评分机制：

```python
scoring_criteria = {
    "idea": {"innovation": 30, "commercial": 25, "sustainability": 25, "differentiation": 20},
    "world": {"completeness": 25, "consistency": 25, "originality": 25, "usability": 25},
    "character": {"depth": 25, "consistency": 25, "growth_potential": 25, "distinctiveness": 25},
    "story": {"conflict_strength": 25, "pacing": 25, "theme_depth": 25, "sustainability": 25},
    "draft": {"consistency": 30, "style_match": 25, "dialogue_quality": 25, "pace": 20}
}
```

### 7.5 流式响应设计

```python
# 所有长时间AI生成操作均使用流式响应
async def generate_with_stream(prompt, model_config):
    client = AIClient(**model_config)
    for chunk in client.generate_stream(prompt):
        yield f"data: {json.dumps(chunk)}\n\n"
        
# 前端使用 ReadableStream 逐块读取
const response = await fetch(url, { method: 'POST', body: JSON.stringify(data) });
const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk decoder.decode(value);
}
```

---

## 附录：现有系统 vs 新系统对比

| 维度 | 当前系统 | 新系统 |
|------|---------|--------|
| 数据模型 | 一个 `novel_data` JSON 字段存所有 | 17张结构化表 |
| AI调用 | 逐段生成，无全局上下文 | Agent 编排，全链路上下文 |
| 创作流程 | 灵感→大纲→大纲文本→章节→正文 | 18模块分层流水线 |
| 一致性 | 无保障，靠系统提示词约束 | 知识库+一致性Agent主动检查 |
| 版本管理 | 无 | 每次AI生成保存版本历史 |
| 中断恢复 | 不支持 | 任务队列+状态机，随时可恢复 |
| 伏笔管理 | 无 | 独立伏笔表+回收追踪 |
| 人物状态 | 无动态状态 | 实时状态快照+变更日志 |
| 字数控制 | 无 | 全局字数规划+章节级字数追踪 |
| 润色 | 单轮AI调用润色 | 五轮渐进式润色 |

---

*本报告作为项目重构的完整技术蓝图，后续开发按此方案执行。*
