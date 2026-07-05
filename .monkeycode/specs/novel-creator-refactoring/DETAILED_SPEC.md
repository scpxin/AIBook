# AI小说创作平台 — 模块级详细设计规范

> **本文档的用途**: 开发者按照本文档实现每个模块，模块之间自动串联。  
> **核心原则**: 每个模块有明确的「输入契约」「处理步骤」「输出契约」「下游绑定」四要素。  
> **模块间连接**: 每个模块的输出中包含下游模块所需的全部引用（ID、路径、关键字段），下游模块通过引用直接获取上游数据。

---

## 系统全景数据流

```
用户输入
  │
  ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块1: 灵感 (Idea)                                            │
│   输入: 用户一句话描述                                         │
│   输出: { idea_id, core_concept, selling_points[],            │
│           target_audience, risks[], sustainability_score }     │
│   下游绑定: → 模块2 引用 idea_id                              │
└──┬───────────────────────────────────────────────────────────┘
   │ idea_id + core_concept + selling_points + target_audience
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块2: 项目定位 (Project)                                      │
│   输入: idea_id 的全部输出 + 用户平台选择                       │
│   输出: { project_id, type, subtype, tags[], platform,         │
│           total_words, chapter_words, pace, style,            │
│           content_boundary, update_plan, risk_analysis }       │
│   下游绑定: → 模块3 引用 project_id + platform + pace         │
└──┬───────────────────────────────────────────────────────────┘
   │ project_id + type + pace + style + content_boundary + total_words
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块3: 世界观 (World Bible)                                    │
│   输入: project_id + type + pace + content_boundary           │
│   输出: { world_id, origin, rules[], structure, civilization, │
│           history_timeline[], hidden_truth, doc_path }        │
│   下游绑定: → 模块4 引用 world_id + rules + structure         │
│             → 模块8 引用 history_timeline                      │
└──┬───────────────────────────────────────────────────────────┘
   │ world_id + origin + rules + civilization + structure + history
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块4: 人物系统 (Character Bible)                               │
│   输入: world_id + project_id + idea_core                     │
│   输出: { characters[], relations[], factions[],              │
│           character_doc_paths{}, state_snapshot }             │
│   下游绑定: → 模块5 引用 character_ids[] + relations          │
│             → 模块6 引用 power_system_id (来自角色能力)        │
│             → 模块7 引用 faction_ids[]                        │
└──┬───────────────────────────────────────────────────────────┘
   │ character_ids[] + character_arcs + main_character_id + theme_from_arc
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块5: 故事系统 (Story System)                                  │
│   输入: character_ids[] + arcs + world_id + idea_core         │
│   输出: { story_id, theme, core_question, core_conflict,      │
│           main_plot, sub_plots[], conflict_loop,              │
│           reward_loop, world_escalation[] }                   │
│   下游绑定: → 模块9 引用 story_id + main_plot + escalation    │
└──┬───────────────────────────────────────────────────────────┘
   │ story_id + main_plot + act_structure + escalation + total_words
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块9: 全书大纲 (Master Outline)                                │
│   输入: story_id + main_plot + world_escalation + total_words │
│   输出: { outline_id, acts[], opening, ending_plan,           │
│           foreshadowing_plan, volume_count }                  │
│   下游绑定: → 模块10 引用 outline_id + act_boundaries         │
└──┬───────────────────────────────────────────────────────────┘
   │ outline_id + volume_count + volume_boundaries + act_targets
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块10: 卷纲 (Volume Outline)                                   │
│   输入: outline_id + volume_number + act_info                  │
│   输出: { volume_id, beats[], chapter_targets,                │
│           volume_conflict, climax, bridge_to_next }           │
│   下游绑定: → 模块11 引用 volume_id + beats                   │
└──┬───────────────────────────────────────────────────────────┘
   │ volume_id + beat_ids[] + beat_chapter_ranges
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块11: 剧情节点 (Story Beat)                                   │
│   输入: volume_id + beat_range + characters + conflict        │
│   输出: { beat_id, type, trigger, goal, obstacle,             │
│           state_change, result, new_question,                 │
│           chapter_range:[start,end] }                         │
│   下游绑定: → 模块12 引用 beat_id + chapter_range             │
└──┬───────────────────────────────────────────────────────────┘
   │ beat_ids[] + chapter_ranges + state_changes[]
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块12: 章节规划 (Chapter Plan)                                  │
│   输入: beat_ids[] + chapter_range + character_states         │
│   输出: { chapter_id, goal, conflict, hook, state_change,    │
│           word_count_target, scene_count_est }                │
│   下游绑定: → 模块13 引用 chapter_id + goal + conflict        │
└──┬───────────────────────────────────────────────────────────┘
   │ chapter_id + goal + conflict + scene_count_est + character_states
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块13: 章节细纲 (Chapter Outline)                               │
│   输入: chapter_id + goal + conflict + character_states       │
│   输出: { chapter_id, scenes[], opening, progression,         │
│           climax, hook, state_updates }                       │
│   下游绑定: → 模块14 引用 chapter_id + scenes[] 的完整定义     │
└──┬───────────────────────────────────────────────────────────┘
   │ chapter_id + scenes[] (每个 scene: goal/conflict/outcome/hook/characters)
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块14: 场景设计 (Scene Design)                                  │
│   输入: scene_definition + full_context (world/character/knowledge) │
│   输出: { scene_id, content_path, word_count, used_chars[],   │
│           state_diff, new_foreshadow_ids }                    │
│   下游绑定: → 模块15 引用 scene_ids[] + merged_chapter_plan    │
└──┬───────────────────────────────────────────────────────────┘
   │ scene_ids[] + chapter_id + merged_content_path
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块15: 正文生成 (Draft)                                        │
│   输入: scene_ids[] 顺序 + knowledge_snapshot                 │
│   输出: { chapter_id, draft_path, actual_words,               │
           summary, used_foreshadow_ids[] }                     │
│   下游绑定: → 模块16 引用 draft_path + chapter_id             │
└──┬───────────────────────────────────────────────────────────┘
   │ chapter_id + draft_path + used_foreshadow_ids
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块16: 润色 (Polish)                                           │
│   输入: draft_path + style + character_profiles               │
│   输出: { polished_path, polish_log, change_summary }        │
│   下游绑定: → 模块17 引用 polished_path + chapter_id          │
└──┬───────────────────────────────────────────────────────────┘
   │ chapter_id + polished_path
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块17: 一致性检查 (Consistency Check)                           │
│   输入: polished_path + all_knowledge + chapter_id            │
│   输出: { report_path, issues[], need_rewrite,                │
│           knowledge_gaps[] }                                  │
│   下游绑定: → 若 issues>0, 回模块15 指定 rewrite_sections     │
│             → 若通过, → 模块18                                 │
└──┬───────────────────────────────────────────────────────────┘
   │ chapter_id + passed=true
   ▼
┌──────────────────────────────────────────────────────────────┐
│ 模块18: 知识库更新 (Knowledge Update)                            │
│   输入: chapter_id + polished_path + previous_knowledge       │
│   输出: { knowledge_snapshot, updated_foreshadowings,         │
│           updated_characters, updated_world_state }           │
│   下游绑定: → 作为下一轮的模块12输入                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 设计层 (Design Layer)


---

## 模块1: 灵感 (Idea)

### 1.1 输入契约

| 输入字段 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| user_input | string | 是 | 用户原始想法,如"我想写一本主角死后能获得死者能力的小说" |
| genre_hint | string | 否 | 类型倾向,如"都市高武" |
| reference_works | string[] | 否 | 参考作品名称,如["诡秘之主","死亡回档"] |
| generate_count | int | 否 | 生成创意数量,默认8个 |

### 1.2 AI执行步骤

```
Step 1: IdeaAgent 发散生成 (1次调用, 生成N个创意)
  prompt模板:
    你是一位网文创意策划师。根据以下输入,生成 {count} 个小说核心创意(High Concept)。
    每个创意必须:
    1. 用一句话概括核心卖点
    2. 说明"和已有作品最大的区别"
    3. 包含"金手指"定义
    4. 预估可持续性(能写多少万字)
    
    用户输入: {user_input}
    类型倾向: {genre_hint}
    参考作品分析: {reference_works_分析}
    
    输出JSON格式: [ {concept, hook, differentiation, sustainability_estimate} ]

Step 2: 创意评分 (对每个创意打分)
  评分维度:
    - 创新性 (1-10): 是否真正有新规则/新矛盾
    - 商业性 (1-10): 对标爆款题材,读者是否买账
    - 可持续性 (1-10): 是否能支撑200万字+
    - 差异化 (1-10): 和同类作品的区分度
    - 难度 (1-10): 写作难度(低分=容易崩)

Step 3: 创意升级 (选取TOP3, 进一步优化)
  prompt模板:
    以下是一个小说创意, 请从"增加矛盾层次"和"设计能力限制"两个方向各升级一版:
    原始创意: {concept}
    升级要求:
    - 增加能力限制: 如果不限制,后期战力崩
    - 增加矛盾层次: 表面矛盾之外,设计隐藏矛盾
    输出JSON: { version_a, version_b }

Step 4: 用户选择 + 风险分析 (选择后触发)
  用户选定创意后, AI自动分析:
    - 风险1: 能力是否会导致后期升级困难
    - 风险2: 世界观能否支撑目标字数
    - 风险3: 是否存在同质化爆款(红海风险)
    - 优化建议: 针对每个风险给出修改方案
```

### 1.3 输出契约

```json
{
  "idea_id": "uuid",
  "user_input": "我想写一本主角死后能获得死者能力的小说",
  "candidates": [
    {
      "candidate_id": "c1",
      "concept": "主角每死亡一次,继承死者的一项永久能力,但会随机失去一段记忆",
      "hook": "如果必须不断死亡才能变强,代价是遗忘一切,你会不会继续",
      "differentiation": "传统死亡回档:死亡可重来;本书:死亡不可逆,但能力永久叠加,代价是失忆",
      "innovation_score": 9,
      "commercial_score": 8,
      "sustainability_score": 8,
      "differentiation_score": 9,
      "difficulty_score": 6,
      "total_score": 8.0,
      "upgrades": {
        "version_a": "加入'记忆碎片'机制:失去的记忆偶尔闪回,成为伏笔",
        "version_b": "加入'能力冲突'机制:同时持有相克能力会反噬"
      }
    }
  ],
  "selected": {
    "candidate_id": "c1",
    "upgrade_version": "version_a",
    "final_concept": "主角每死亡一项,继承死者的一项永久能力,但会随机失去一段记忆。失去的记忆化为碎片,偶尔成为关键伏笔。",
    "core_selling_points": [
      "死亡即成长:每次死亡都有即时反馈",
      "能力组合无限:N种死者=N种能力组合",
      "记忆碎片伏笔:遗忘本身成为剧情推动力",
      "高随机性:读者无法预测下次获得什么"
    ],
    "target_audience": {
      "age_range": "18-35",
      "gender": "male_dominant",
      "preferences": ["系统流","无限流","热血","升级打脸"],
      "platform_fit": ["番茄","起点"]
    },
    "risks": [
      {
        "risk": "能力叠加后期战力膨胀",
        "mitigation": "设计能力上限/相克机制/能量槽限制",
        "priority": "high"
      },
      {
        "risk": "失忆桥段重复度过高",
        "mitigation": "记忆碎片化为谜题/记忆交易/记忆掠夺",
        "priority": "medium"
      },
      {
        "risk": "死亡场景重复",
        "mitigation": "设计死亡竞技场/契约式死亡/死亡任务",
        "priority": "medium"
      }
    ],
    "sustainability_estimate": "200-400万字",
    "suggested_keywords": ["死亡","能力继承","无限成长","悬疑","副本"]
  },
  "status": "selected",
  "created_at": "2026-07-05T10:00:00Z"
}
```

### 1.4 下游绑定

```
→ 模块2 (Project) 直接使用:
    - idea_id
    - final_concept → project.idea_core
    - core_selling_points → project.selling_points
    - target_audience → project_target_audience
    - risks → project_risk_analysis
    - sustainability_estimate → project_total_words 范围参考

存储方式:
  - 整条 idea 记录存入 SQLite ideas 表
  - 步骤1-3的完整 prompt+response 存入 ai_generations 表(entity_type="idea")
```


---

## 模块2: 项目定位 (Project)

### 2.1 输入契约

| 输入字段 | 类型 | 来源 | 说明 |
|---------|------|------|------|
| idea_id | UUID | 模块1输出 | 关联灵感 |
| idea.object | JSON | 模块1输出 | 灵感的全部字段 |
| platform_choice | string | 用户选择 | 目标平台: tomato/qidian/qimao/custom |
| custom_params | JSON | 用户可选 | 自定义参数覆盖 |

### 2.2 AI执行步骤

```
Step 1: 平台规则加载
  根据 platform_choice 加载平台参数预设:
    番茄小说: { pace: "极快", chapter_words: 2000, daily_words: 6000, 
               first_3_chapters: "必须有爆点", style: "轻松爽快" }
    起点:     { pace: "中快", chapter_words: 3000, daily_words: 4000,
               first_3_chapters: "钩子+世界观展示", style: "可深沉" }
    七猫:     { pace: "快", chapter_words: 2500, daily_words: 8000,
               first_3_chapters: "前三章定生死", style: "脑洞大开" }

Step 2: 12维度项目策划 (1次AI调用)
  prompt模板:
    你是一位网文总编。根据以下灵感创意和目标平台,制定完整的项目策划书。
    
    === 输入 ===
    核心创意: {idea.final_concept}
    核心卖点: {idea.core_selling_points}
    目标读者: {idea.target_audience}
    平台: {platform_choice} (平台规则: {platform_rules})
    
    === 需要输出的12个维度 ===
    
    1. 项目简介(一句话)
    2. 小说定位: type(主类型)+subtype(子类型)+tags(标签数组)
    3. 平台定位: 目标平台+更新策略+章节长度
    4. 用户定位: 年龄段+爽点偏好+阅读场景
    5. 商业定位: 第一卖点+第二卖点+第三卖点+差异化
    6. 风格定位: 语言风格+情绪基调+叙事方式+文风参照
    7. 节奏定位: 
       - 开局节奏(前3章): [事件1→事件2→事件3]
       - 短期节奏(前10章): 每章的钩子和爽点
       - 中期节奏(每卷): 卷首引子→卷中发展→卷末高潮
       - 长期节奏(全书): 世界升级节点[城市→国家→大陆→世界→宇宙]
    8. 创新定位: 和同类作品的5个核心差异点
    9. 内容边界: 绝不写入的设定/剧情(至少5条)
    10. 字数规划: 总字数+卷数+每卷章数分配
    11. 更新计划: 每日更新字数+每章用时预估
    12. 风险分析: 设定风险+商业风险+剧情风险+优化建议(每类≥2条)
    
    输出JSON格式,严格符合以下结构:
    { projectoverview, novel_position, platform, audience, commercial, style,
      pace, innovation, content_boundary, wordcount, update_plan, risks }

Step 3: 兼容性检查
  AI检查以下冲突:
    - 平台要求 VS 灵感设定是否冲突(如番茄要快节奏但灵感设定是慢热悬疑)
    - 字数规划 VS 节奏分配是否合理
    - 卖点是否真的差异化(检查已有爆款对比)

Step 4: 用户确认/修改
  展示策划书,用户可:
    - 直接确认
    - 修改某个维度后重新生成
    - 完全重来(回到Step1)

Step 5: 生成关联字段 (确认后自动执行)
  计算衍生字段:
    - volume_fragments = 根据总字数/节奏自动生成卷数建议
    - foreshadowing_templates = 根据卖点生成伏笔模板列表
    - character_seed = 根据剧情需要生成初始角色需求清单
```

### 2.3 输出契约

```json
{
  "project_id": "uuid",
  "idea_id": "uuid → 关联模块1",
  "status": "active",
  "confirmed": true,
  
  "project_overview": "都市高武无限成长小说:主角通过死亡继承能力,探索世界真相。",
  
  "novel_position": {
    "type": "都市高武",
    "subtype": "系统/死亡成长",
    "tags": ["都市高武","死亡","能力继承","无限成长","悬疑","副本"],
    "logline": "「如果必须不断死亡才能变强,你会不会继续?」"
  },
  
  "platform": {
    "target_platform": "番茄小说",
    "update_strategy": "每日6000字,三章更新",
    "chapter_words": 2000,
    "first_3_chapter_requirements": "爆点开局,快速建立金手指,前三章完成第一次死亡+能力觉醒"
  },
  
  "audience": {
    "age_range": "18-35",
    "gender_ratio": "男85%女15%",
    "preferences": ["升级打脸","热血","系统流","无限流"],
    "reading_scene": "通勤/睡前碎片阅读",
    "triggers": ["死亡即变强","随时有新能力","悬念不断"]
  },
  
  "commercial": {
    "primary_sell": "死亡即成长:每次死亡都是爽点",
    "secondary_sells": ["无限能力组合","记忆碎片悬疑","副本节奏感"],
    "differentiation": "死亡不可逆(区别于回档流),但失去记忆成为新推动力"
  },
  
  "style": {
    "language": "简洁有力,短句多,对白驱动",
    "emotional_tone": "紧张刺激中带黑色幽默",
    "narrative": "第三人称主角视角",
    "reference_authors": ["乌贼","远瞳","裴屠狗"],
    "taboo_words": ["冗长环境描写","内心独白超过3句","连续2页无对白"]
  },
  
  "pace": {
    "opening": ["第1章:死亡与觉醒","第2章:第一次使用能力","第3章:发现世界异常"],
    "first_10_chapters": ["引入→能力展示→第一个副本→第一个朋友→第一次危机→解决→升级→新敌→新悬念→阶段小结"],
    "volume_pace": "每卷30章,前5章建立→中20章发展高潮→后5章收尾+钩子",
    "world_escalation": [
      {"volume":1,"scope":"城市","trigger":"发现本地组织"},
      {"volume":3,"scope":"全国","trigger":"副本全国开放"},
      {"volume":5,"scope":"国际","trigger":"外国势力介入"},
      {"volume":7,"scope":"世界真相","trigger":"突破到世界核心"},
      {"volume":9,"scope":"宇宙终极","trigger":"揭开死亡真相"}
    ]
  },
  
  "innovation": [
    "1. 死亡不可逆:区别于回档流,每次死亡都是永久损失",
    "2. 记忆碎片:遗忘不仅是代价,还是伏笔",
    "3. 能力相克:同时持有过多能力会反噬",
    "4. 死亡交易所:他人可以交易主角的死亡机会",
    "5. 终极代价:最终能力需要杀死最重要的人"
  ],
  
  "content_boundary": [
    "绝不写后宫(影响主线节奏)",
    "绝不写无脑反派(每个敌人有动机)",
    "绝不写突然出现的救场角色",
    "绝不写时间穿越(和死亡不可逆冲突)",
    "绝不写主角圣母化(可成长但不违背初心)"
  ],
  
  "wordcount": {
    "total": 3000000,
    "volumes": 10,
    "distribution": [
      {"volume":1,"target_words":250000,"chapters":125},
      {"volume":2,"target_words":280000,"chapters":140},
      {"volume":3,"target_words":300000,"chapters":150},
      {"volume":4,"target_words":320000,"chapters":160},
      {"volume":5,"target_words":350000,"chapters":175},
      {"volume":6,"target_words":380000,"chapters":190},
      {"volume":7,"target_words":400000,"chapters":200},
      {"volume":8,"target_words":350000,"chapters":175},
      {"volume":9,"target_words":280000,"chapters":140},
      {"volume":10,"target_words":190000,"chapters":95}
    ]
  },
  
  "update_plan": {
    "daily_words": 6000,
    "chapters_per_day": 3,
    "writing_hours_per_chapter": 2,
    "rest_day": "每周日"
  },
  
  "risks": [
    {"category":"设置风险","risk":"能力叠加后期膨胀","mitigation":"设计能力槽限制+属性相克","severity":"high"},
    {"category":"商业风险","risk":"番茄对智斗要求高于打斗","mitigation":"增加智斗+心理博弈","severity":"medium"},
    {"category":"剧情风险","risk":"记忆碎片桥段重复","mitigation":"设计5种不同的记忆闪回模式","severity":"medium"}
  ],
  
  "derived_fields": {
    "volume_fragments": 10,
    "suggested_volume_titles": ["觉醒之卷","学院之卷","...卷"],
    "foreshadowing_templates": [
      {"id":"TPL-001","type":"道具","example":"第2章的坠饰→第86章开启遗迹"},
      {"id":"TPL-002","type":"对话伏笔","example":"导师的无心之语→后期真相"}
    ],
    "character_seed_needs": [
      {"role":"主角","name":"待定","must_have":["金手指","成长弧核心"]},
      {"role":"女主","name":"待定","must_have":["独立能力","不拖后腿"]},
      {"role":"宿敌","name":"待定","must_have":["正义立场","和主角非私仇"]},
      {"role":"智者","name":"待定","must_have":["信息差","关键时刻指引"]}
    ]
  }
}
```

### 2.4 下游绑定

```
→ 模块3 (World Bible) 直接使用:
    - project_id
    - novel_position.type → 决定世界类型选项(都市高武≠修仙)
    - pace.world_escalation → 世界观的规模和层数参考
    - content_boundary → 世界观中禁止的设计
    - derived_fields.character_seed_needs → 角色设计方向

→ 模块4 (Characters) 直接使用:
    - derived_fields.character_seed_needs → 角色需求清单
    - commercial.differentiation → 角色差异化依据

→ 模块5 (Story) 等后续模块通过 project_id 关联
```


---

## 模块3: 世界观 (World Bible)

### 3.1 输入契约

| 输入字段 | 类型 | 来源 | 说明 |
|---------|------|------|------|
| project_id | UUID | 模块2 | 关联项目 |
| project.world_escalation | JSON | 模块2 | 世界升级路线→决定世界观层数 |
| project.content_boundary | string[] | 模块2 | 禁止内容 |
| project.novel_position.type | string | 模块2 | 类型决定世界范式 |
| project.derived_fields.foreshadowing_templates | JSON | 模块2 | 伏笔模板→世界观设计依据 |

### 3.2 AI执行步骤

```
Step 0: 加载前置数据
  从数据库取:
    - idea记录(获取核心创意中的"规则改变"部分)
    - project记录(全部12维度)
  构建基础prompt上下文

Step 1: 世界本源设计 (Origin)
  prompt模板:
    你是世界观设计师。根据以下信息,设计"世界本源":
    
    === 约束 ===
    核心创意: {idea.final_concept}
    类型: {project.type}({project.subtype})
    内容边界: {project.content_boundary}
    
    === 设计要求 ===
    回答以下问题:
    1. 这个世界是什么?(平行世界/现实延伸/模拟世界/神创...)
    2. 为什么会有{idea.core_concept中的规则改变}?
    3. 这个改变的源头是什么?(外星科技/上古遗迹/宇宙规则/高维存在...)
    4. 这个世界的终极秘密是什么?(后期要揭露的隐藏真相)
    
    输出JSON:
    {
      "world_type": "现实延伸+高维干涉",
      "origin_story": "世界规则的核心叙述...",
      "rule_change_source": "规则改变的解释...",
      "hidden_truth": "读者后期才会知道的终极真相...",
      "truth_reveal_timing": "第几卷揭露",
      "world_rules": [
        {"rule": "xxx", "why": "xxx", "what_if_broken": "xxx"}
      ]
    }

Step 2: 世界规则设计 (Rules) ─ 核心!
  输入: Step1的输出 + idea.output.final_concept
  prompt模板:
    基于世界本源:{origin.world_type},设计不可违反的世界规则。
    
    === 已知 ===
    核心设定: {idea.final_concept}
    金手指: {idea.core_selling_points[0]}
    风险缓解: {project.risks中high severity的mitigation}
    
    === 设计原则 ===
    每条规则必须有:
    1. 规则名(四个字以内)
    2. 规则描述(一句话)
    3. 为什么不能违反(底层逻辑)
    4. 如果违反会怎样(后果)
    5. 这条规则对剧情的推动作用
    6. 是否有例外(例外就是伏笔)
    
    输出JSON: { rules: [{name, description, why, consequence, plot_use, exception}] }
    
    === AI自动校验 ===
    生成后立即检查:
    - 规则之间是否存在矛盾?
    - 金手指是否绕过了某条规则?
    - 规则是否能支撑{project.wordcount.total}万字的剧情?

Step 3: 世界结构设计 (Structure)
  输入: Step1+Step2 的输出
  prompt模板:
    基于世界规则{rules.length}条,设计世界的物理/空间结构。
    
    === 设计要求 ===
    根据world_escalation: {project.pace.world_escalation}
    设计层级结构(从大到小):
    
    最高层: 宇宙级/多元宇宙/神国
       ↓
    大世界: 灵界/仙界/上界
       ↓
    主世界: 主角所在世界
       ↓
    区域层: 国家/州省/宗门领地
       ↓
    城市层: 主角日常活动范围
       ↓
    具体地点: 学院/副本入口/黑市/遗迹...
    
    每个层级需要:
    - 层级名称
    - 和上下层的关系(如何上下流动)
    - 当前已知的地点列表
    - 这一层的规则特殊性
    
    输出JSON: { layers: [{level, name, parent_level, connections, locations, local_rules}] }

Step 4: 文明体系设计 (Civilization)
  输入: Step3的输出
  prompt模板:
    基于世界结构{structure.layers.length}层,设计主世界的文明体系。
    
    === 必须回答 ===
    政治: 有没有国家?政体?和主角的关系?
    经济: 货币体系?主角如何赚钱?
    教育: 有没有学院?和主线什么关系?
    宗教: 有没有信仰?神是真是假?
    军事: 有没有军队?主角是否加入?
    法律: 副本中杀人合法吗?副本外呢?
    传媒: 信息如何传播?有没有直播/排行榜?
    阶级: 觉醒者和平民的差距?
    
    输出JSON:
    {
      "politics": {...}, "economy": {...}, "education": {...},
      "religion": {...}, "military": {...}, "law": {...},
      "media": {...}, "class": {...}
    }

Step 5: 历史时间线 (History)
  输入: Step1(隐藏真相) + Step4(文明)
  prompt模板:
    基于隐藏_truth:{origin.hidden_truth}和文明体系,
    设计从创世到"故事开始"时刻的完整历史。
    
    === 时间线结构 ===
    远古时代(万年前): 创世/规则建立
      ↓
    上古时代(千年前): 繁荣/大战/衰落
      ↓
    近代(百年前): 规则改变/灵气复苏/副本降临
      ↓
    现代(故事开始时): 当前世界状态
    
    每个时代包含:
    - 时代名称+时间范围
    - 3-5个关键事件
    - 每个事件: {when, what, who, why, consequence, modern_impact}
    - 是否留下遗迹/神器/伏笔(→ foreshadowing_templates)
    
    特别注意: 
    - 隐藏真相必须有3个"误导性传说"(读者以为的真相)
    - 每个误导必须有对应的"真相碎片"埋点

Step 6: 世界一致性检查
  AI自动检查:
    - 世界规则 VS 金手指是否兼容
    - 升级路线 VS 世界层级是否匹配
    - 隐藏真相 VS 近期事件是否有逻辑漏洞
    - 文明体系 VS 阅读平台是否匹配(番茄不需要太复杂)

Step 7: 生成世界观文档
  将Step1-5的输出组合为完整的Markdown文档
  保存到文件系统: /projects/{project_id}/world_bible/README.md
  
  同时生成:
    - 每层规则的"速查表" (→ 给后续模块引用)
    - 重要地点索引 (→ 场景设计引用)
    - 世界观中的伏笔清单 (→ 伏笔管理模块)
```

### 3.3 输出契约

```json
{
  "world_id": "uuid",
  "project_id": "uuid → 关联模块2",
  "doc_path": "/projects/{project_id}/world_bible/",
  
  "origin": {
    "world_type": "现实延伸+高维干涉",
    "origin_story": "地球被高维存在'系统'选中,规则被改写...",
    "rule_change_source": "系统核心在地球地心,释放改写能量",
    "hidden_truth": "系统不是恩赐,是一场宇宙级实验,所有'玩家'都是样本",
    "truth_reveal_volume": 8,
    "world_rules": [
      {
        "rule": "死亡继承",
        "description": "杀死他人可永久获得对方一项能力",
        "why": "系统规则第3条,高维能量守恒的产物",
        "consequence": "滥用会导致系统强制清除",
        "plot_use": "解释了能力来源,同时制造'可持续杀人'的道德困境",
        "exception": "自愿赠予不触发继承(伏笔:如何处理亲密之人)"
      }
    ]
  },
  
  "rules": {
    "core_rules": [
      {"name":"死亡继承","desc":"...","why":"...","consequence":"...","plot_use":"...","exception":"..."},
      {"name":"记忆代价","desc":"...","why":"...","consequence":"...","plot_use":"...","exception":"..."},
      {"name":"能力冲突","desc":"...","why":"...","consequence":"...","plot_use":"...","exception":"..."},
      {"name":"系统清除","desc":"...","why":"...","consequence":"...","plot_use":"...","exception":"..."}
    ],
    "derived_rules": ["不能...","必须...","禁止..."],
    "rules_foreshadow_links": ["规则'系统清除'的例外→隐藏真相"]
  },
  
  "structure": {
    "layers": [
      {
        "level": 1, "name": "高维宇宙",
        "parent": null,
        "connections": "不可直接到达",
        "locations": ["系统核心"],
        "local_rules": "物理法则不同"
      },
      {
        "level": 2, "name": "副本世界",
        "parent": 1,
        "connections": "通过副本入口传送",
        "locations": ["新手副本","进阶副本","深渊副本"],
        "local_rules": "副本内死亡真实死亡(除非有复活道具)"
      },
      {
        "level": 3, "name": "主世界-地球",
        "parent": 2,
        "connections": "现实世界,副本入口随机出现",
        "locations": ["华夏国","灯塔国","欧盟区"],
        "local_rules": "副本外禁止能力使用"
      },
      {
        "level": 4, "name": "华夏国-江南省",
        "parent": 3,
        "connections": "主角活动区域V1-V3",
        " locations": ["江城(主城)","青云学院","江城副本区","黑市"],
        "local_rules": "学院内可使用能力训练"
      }
    ],
    "location_index": [
      {"id":"LOC-001","name":"江城","layer":4,"type":"城市","current_owner":"城主府","importance":"high"},
      {"id":"LOC-002","name":"青云学院","layer":4,"type":"学院","current_owner":"学院议会","importance":"high"}
    ]
  },
  
  "civilization": {
    "politics": {"has_country":true,"system":"觉醒者议会制","protagonist_relation":"后期加入"},
    "economy": {"currency":"信用点+灵石","protagonist_income方式":"副本产出+黑市"},
    "education": {"has_academy":true,"name":"青云学院","relation":"V1主场"},
    "religion": {"has_religion":true,"name":"系统教会","truth":"教主知道部分真相"},
    "military": {"has_army":true,"name":"觉醒者特战队","protagonist_join_chapter":15},
    "law": {"副本内":"弱肉强食","副本外":"能力犯罪重罚"},
    "media": {"platform":"觉醒者APP","features":["排行榜","悬赏","直播"]},
    "class": {"tiers":["S级觉醒者","A级","B级","C级","平民"]}
  },
  
  "history": {
    "timeline": [
      {
        "era":"创世神话","year":"万年前",
        "events":[
          {"when":"万年前","what":"系统降临","who":"高维存在","why":"实验","consequence":"规则改写","modern_impact":"灵气出现","foreshadow_id":"FS-001"}
        ],
        "misleading_lore":["神创造世界","系统是为了帮助人类"],
        "truth_fragments":["系统日志碎片001"]
      },
      {
        "era":"近代复苏","year":"10年前",
        "events":[
          {"when":"10年前","what":"副本首次出现","who":"未知","why":"测试阶段","consequence":"第一批觉醒者出现","modern_impact":"社会重组"}
        ]
      },
      {
        "era":"故事元年","year":"现代",
        "events":[
          {"when":"3月前","what":"江城大副本降临","who":"系统","why":"第二测试阶段","consequence":"主角所在城市被标记","modern_impact":"主角命运的起点"}
        ]
      }
    ]
  },
  
  "world_foreshadows": [
    {"id":"FS-W-001","source":"rule.exception","trigger":"'自愿赠现'的定义","payoff":"第30章发现系统漏洞"},
    {"id":"FS-W-002","source":"history.truth_fragments","trigger":"系统日志碎片","payoff":"第8卷揭露系统真相"}
  ]
}
```

### 3.4 下游绑定

```
→ 模块4 (Characters) 直接使用:
    - world_id
    - structure.location_index → 角色出生地/活动范围
    - civilization.class → 角色初始阶级
    - world_rules → 角色能力的规则约束(不能违反)
    - origin.hidden_truth → 哪些角色知道真相(设计信息差)
    - history.timeline → 角色年龄对应的历史事件(背景故事)

→ 模块5 (Story) 直接使用:
    - world_rules → 冲突必须基于规则
    - world_escalation → 和story.world_escalation对齐

→ 模块8 (Timeline) 直接使用:
    - history.timeline → 时间线表的基础数据

→ 模块14-15 (Scene/Draft) 后续间接引用:
    - location_index → 场景设置选择
    - local_rules → 场景中允许/禁止的行为
```


---

## 模块4: 人物系统 (Character Bible)

### 4.1 输入契约

| 输入字段 | 类型 | 来源 | 说明 |
|---------|------|------|------|
| project_id | UUID | 模块2 | 关联项目 |
| world_id | UUID | 模块3 | 关联世界观 |
| character_seed_needs | JSON | 模块2.derived_fields | 角色需求清单 |
| world.location_index | JSON | 模块3 | 地点列表(用于出生地) |
| world.rules | JSON | 模块3 | 规则列表(用于能力约束) |
| civilization.class | JSON | 模块3 | 阶级体系 |
| idea.final_concept | string | 模块1 | 核心创意(主角能力来源) |
| content_boundary | string[] | 模块2 | 角色设计边界 |

### 4.2 AI执行步骤

```
Step 1: 主角设计 (最详细, 1次长调用)
  prompt模板:
    你是角色设计师。设计一本{project.type}小说的主角。
    
    === 输入 ===
    核心创意: {idea.final_concept}
    金手指: {idea.core_selling_points[0]}
    项目风格: {project.style}
    目标读者偏好: {project.audience.preferences}
    世界观规则: {world.rules}(主角能力不能违反这些规则)
    内容边界: {project.content_boundary}(不能写在角色上)
    可持续性: 需要支撑{project.wordcount.total}万字的成长
    
    === 输出主角九维档案 ===
    
    1. 基础档案:
       name, age, gender, birthday, height, weight,
       identity(当前身份), race, affiliation, birthplace(从world.location_index选)
    
    2. 外貌系统:
       hair, eyes, skin, build, clothing_style, 
       signature_action(标志性动作), signature_item(标志性物品),
       distinctiveness(一眼记住的点)
    
    3. 性格系统(不是"善良",而是心理模型):
       values(核心价值观), bottom_line(底线),
       strengths(≥3个), weaknesses(≥3个,weakness就是冲突来源),
       fears(最大恐惧,剧情推动力), obsession(执念,主线动力),
       speaking_style(说话方式), behavior_traits(行为特点)
    
    4. 能力系统(详细):
       current_level: "未觉醒" / "觉醒一阶" ...
       abilities: [
         {
           "name": "死亡继承",
           "type": "主动/被动",
           "effect": "杀死他人永久获得一项能力",
           "limit": "一天最多触发3次",
           "cost": "失去一段随机记忆",
           "growth_path": "通过死亡次数升级",
           "synergies": ["能力A+能力B=组合效果"]
         }
       ],
       resources: ["初始资金","初始装备"...],
       growth_potential: "理论上能到什么程度"
    
    5. 成长系统(十万字一个阶段, 必须完整):
       growth_route: [
         {"stage": 1, "name": "觉醒者", "volume": "1", "chapter_range":"1-125", 
          "description": "初步认知能力,第一次死亡,第一次获得能力",
          "personality_change": "从普通人到能力者的心理转变",
          "power_level": "F级"},
         {"stage": 2, "name": "精英猎手", "volume": "2", ...},
         {"stage": 3, "name": "城市强者", "volume": "4", ...},
         ...至少8个阶段,覆盖全书
       ]
    
    6. 关系系统(初始):
       initial_relations: [
         {"with": "待定(父亲)", "relation": "父子", "trust": 70, "conflict": "隐藏"},
         {"with": "待定(导师)", "relation": "师徒", "trust": 60, "conflict": null}
       ]
    
    7. 心理系统:
       initial_mood: "平静"
       trauma: null
       current_stress: 20
       secrets: ["能力的真正来源","每天晚上听到低语"]
       mental_state: "初期坚强,有轻微焦虑"
    
    8. 初始状态:
       current_state: {"level":"未觉醒", "location":"江城", "wealth":5000, "equipment":[]...}
    
    9. 人物日志模板(占位):
       log_entries: []

Step 2: 配角设计(依赖主角)
  输入: 主角完整档案
  prompt模板:
    基于主角档案, 设计{max_supporting_roles}个核心配角。
    每个配角必须:
    1. 和主角有至少一个关系维度(友/敌/亲/师/恋)
    2. 有自己的目标和冲突(不是主角的工具人)
    3. 和主角的能力体系产生化学反应(配合/克制/互补)
    
    分类设计:
    - 搭档(1-2人): 主角最信任的人,和主角能力互补
    - 导师(1人): 前期指引,有隐藏身份
    - 宿敌(1人): 非私仇,立场对立
    - 女主(0-1人): 独立能力,不拖后腿(如果content_boundary不禁止)
    - 势力代表(2-3人): 各大势力的关键人物
    
    每个配角同样九维,但详细度降为70%

Step 3: 反派设计
  输入: 主角 + 世界观 + 故事风险
  prompt模板:
    设计全书反派体系(至少5个层级):
    
    第一卷反派: 具体的、有动机的、可以被打败的
      - 和主角的直接冲突是什么?
      - 反派的立场是否有合理之处?(不做无脑反派)
    
    卷级反派(每卷一个大反派): 
      - 和主角的冲突升级路径
    
    幕後黑手(多人):
      - 各自隐瞒的秘密
      - 之间的利益冲突
    
    最终反派(vol8-10出现):
      - 和隐藏真相的关系
    
    每个反派: 九维档案 + 和主角的关系演化路径

Step 4: 人物关系网络生成
  输入: 所有角色档案
  prompt模板:
    根据以下角色, 设计完整的关系网络。
    每条关系: source, target, type, trust_now, trust_max, plot_uses
    特别注意:
    - 至少3对"隐藏关系"(表面A实际B)
    - 至少1个"双面间谍"
    - 关系的演化路径要配合growth_route
    
    生成关系图数据: nodes[], edges[]

Step 5: 一致性检查
  AI检查:
    - 主角的能力是否违反world.rules
    - 关系中是否有矛盾(同时是朋友又是死敌但未解释)
    - 角色的年龄和历史事件是否冲突(出生于10年前但经历了20年前的事件?)
    - 角色数量是否适合平台(番茄不需要太多角色)
    - 男女角色比例是否符合受众

Step 6: 生成角色文档
  每个角色一个Markdown文件保存到:
    /projects/{project_id}/characters/{role_type}/{name}.md
  
  同时生成:
    - /characters/README.md (角色总览)
    - /characters/relationship_map.md (关系图)
    - /characters/state_summary.md (动态状态总表)
```

### 4.3 输出契约

```json
{
  "character_registry": {
    "project_id": "uuid",
    "total_characters": 15,
    "protagonist_id": "char_001",
    "characters": [
      {
        "id": "char_001",
        "role_type": "protagonist",
        "name": "苏默",
        "doc_path": "/projects/{pid}/characters/protagonist/苏默.md",
        
        "profile": {
          "age": 18, "gender": "男", "race": "人类-觉醒者",
          "identity": "江城一中学生", "occupation": "学生→副本猎人",
          "affiliation": "平民→觉醒者协会",
          "birthplace": "LOC-001 江城"
        },
        
        "appearance": {
          "hair": "黑色短发,略显凌乱",
          "eyes": "深褐色,使用后变为金色(能力激活时)",
          "build": "偏瘦但结实", "height": 175,
          "clothing_style": "深色系休闲装,便于行动",
          "signature_action": "思考时用手指轻敲太阳穴",
          "signature_item": "母亲的遗物·一枚旧怀表(停在他出生时间)",
          "distinctiveness": "使用能力时瞳孔会出现金色齿轮纹"
        },
        
        "personality": {
          "values": ["自由至上","保护弱者","绝不背叛朋友"],
          "bottom_line": "不主动伤害无辜,但可以被威胁",
          "strengths": ["观察力极强","记忆力好(反衬失忆代价)","冷静分析"],
          "weaknesses": ["过度保护同伴导致决策失误","对失去记忆的恐惧","对'父亲之死'的心结"],
          "fears": ["彻底失忆忘记自己是谁","同伴因自己而死","变成只知道杀戮的机器"],
          "obsession": "找到父亲死亡的真相",
          "speaking_style": "简洁直接,偶尔冷幽默,不轻易承诺但一诺千金",
          "behavior_traits": ["先观察后行动","经常忘记吃饭","对善意保持警惕"]
        },
        
        "abilities": {
          "core_ability": {
            "name": "死亡继承",
            "type": "被动+主动",
            "trigger": "杀死智慧生命后自动激活",
            "effect": "永久获得死者生前一项能力(随机)",
            "cost": "随机失去一段记忆(几小时到几天不等)",
            "limits": [
              "每天最多触发3次",
              "不能选择获得哪项能力(完全随机)",
              "失去的记忆不可恢复(除非特殊方式)",
              "同时持有超过10项能力会精神不稳定"
            ],
            "synergies": [
              "能力A+死亡继承概率=提高下一次获得概率",
              "记忆相关能力+失忆=形成对抗"
            ]
          },
          "current_level": "觉醒一阶(仅死亡继承)",
          "skill_tree_template": "...",
          "resources": ["学生证","5000信用点","旧怀表"],
          "growth_potential": "理论无上限,但精神负担线性增长"
        },
        
        "growth_route": [
          {"stage":1,"name":"懵懂觉醒者","volume":"1","chapters":"1-125",
           "personality":"从恐惧到接受,第一次主动使用能力",
           "power_level":"F级","key_events":["第一次死亡","第一次获得能力","加入学院"]},
          {"stage":2,"name":"精英猎手","volume":"2","chapters":"126-265",
           "personality":"开始享受力量的危险信号,同时失忆频率增加",
           "power_level":"E级","key_events":["第一次主动杀死敌人","第一次重要失忆"]},
          ...共8个阶段
        ],
        
        "initial_relations": [
          {"with":"char_002","relation":"父亲(已故)","trust":100,"conflict":"死因不明"},
          {"with":"char_003","relation":"学院导师","trust":70,"conflict":null},
          {"with":"char_005","relation":"第一个朋友","trust":60,"conflict":null},
          {"with":"char_008","relation":"第一卷反派","trust":0,"conflict":"利益冲突→杀父仇人"}
        ],
        
        "initial_psychology": {
          "mood": "表面平静,内心焦虑",
          "trauma": "六岁时目睹父亲'意外'死亡",
          "stress_level": 40,
          "secrets": ["父亲可能不是普通人","经常梦到死亡场景","怀疑系统在监视自己"],
          "mental_state": "坚强但孤独,对世界保持警惕"
        },
        
        "initial_state": {
          "level": "觉醒一阶", "hp": "100%", 
          "location": "LOC-001 江城 家中",
          "wealth": 5000, "equipment": ["校服","旧怀表"],
          "current_abilities": ["死亡继承"],
          "lost_memories_count": 0,
          "location_coordinates": {"lat":0,"lng":0}
        },
        
        "log_summary": "尚未开始"
      }
    ],
    
    "relation_map": {
      "nodes": [{"id":"char_001","label":"苏默","group":"protagonist"}, ...],
      "edges": [
        {"from":"char_001","to":"char_002","relation":"父子","trust":100},
        ...
      ]
    },
    
    "role_groups": {
      "protagonist": ["char_001"],
      "partner": ["char_005", "char_006"],
      "mentor": ["char_003"],
      "rival": ["char_004"],
      "antagonist_v1": ["char_008"],
      "factions": ["char_009","char_010","char_011"]
    }
  }
}
```

### 4.4 下游绑定

```
→ 模块5 (Story System) 直接使用:
    - protagonist_id → 故事主线围绕此人展开
    - protagonist.growth_route → 主线剧情的关键节点
    - character_ids[] → 所有参与剧情的角色
    - relation_map → 关系变化驱动支线
    - protagonist.abilities.limits → 冲突设计依据(限制=冲突)

→ 模块6 (Power System) 直接使用:
    - protagonist.abilities.core_ability → 力量体系基础
    - characters[].abilities → 全员能力列表
    - world.rules → 力量体系的规则约束

→ 模块7 (Factions) 直接使用:
    - characters[].profile.affiliation → 势力归属
    - role_groups.factions → 势力核心人物列表
    - faction_leaders → 各势力首领角色ID

→ 模块12-13 (Chapter Plan/Outline) 后续引用:
    - character.growth_route → 章节需要覆盖的成长阶段
    - character.initial_state → 写作起始状态(知识库初值)

→ 模块14-15 (Scene/Draft) 后续引用:
    - character.appearance → 描写依据
    - character.personality → 对白和行为依据
    - character.speaking_style → 对白风格
```


---

## 模块5: 故事体系 (Story System)

### 5.1 输入契约

| 输入字段 | 类型 | 来源 | 说明 |
|---------|------|------|------|
| project_id | UUID | 模块2 | 关联项目 |
| protagonist | JSON | 模块4 | 主角完整档案 |
| protagonist.growth_route | JSON | 模块4 | 成长阶段→剧情节点 |
| characters.relation_map | JSON | 模块4 | 关系网络→支线依据 |
| world.hidden_truth | string | 模块3 | 终极真相→全书主线 |
| world.world_escalation | JSON | 模块3 | 世界升级→剧情升级 |
| world.foreshadows | JSON | 模块3 | 世界观伏笔→剧情回收 |
| innovation.items | string[] | 模块2 | 创新点→剧情差异化 |
| content_boundary | string[] | 模块2 | 禁止内容 |

### 5.2 AI执行步骤

```
Step 1: 总纲设计 (1次长调用)
  prompt模板:
    设计全书故事总纲。遵循{innovation}创新点。
    
    === 输入 ===
    主角: {protagonist.profile.name}, 目标: {protagonist.obsession}
    成长阶段: {protagonist.growth_route}
    世界升级: {world.world_escalation}
    隐藏真相: {world.hidden_truth}
    
    === 输出要求 ===
    1. 一句话总纲: "一个[身份]为了[目标],通过[方法],最终[结果]。"
    2. 核心冲突: 人vs[什么](至少3层冲突)
    3. 核心主题: 故事要表达的核心价值观
    4. 全书钩子: 每卷一个"不得不看下一卷"的悬念
    
    === 成长型剧情事件集(至少15个) ===
    每个事件: {id, name, volume, chapter_min, chapter_max, description, key_characters[], 
               type(关键节点/转折点/日常补充/支线/伏笔埋设/伏笔回收)}
    
    输出JSON:
    {
      "summary": "...",
      "conflict_layers": ["人vs命运","人vs系统","人vs自我"],
      "theme": "xxx",
      "volume_cliffhangers": [...],
      "plot_events": [...数组长度≥15]
    }

Step 2: 每卷卷纲 (分10次调用或1次批量)
  输入: 总纲 + 卷字数 + 卷升级范围
  对每卷:
    prompt模板:
      设计第{volume_number}卷的故事。
      - 字数: {volume.target_words}
      - 章数: {volume.chapters}
      - 阶段: {growth_route[volume_number].name}
      - 范围: {world_escalation[volume_number]}
      
      输出:
      1. 卷引子(一句话): "这一卷,[谁]将[做什么]。"
      2. 卷核心冲突 + 解决方法
      3. 5-8个关键事件(从总纲plot_events中选)
      4. 主角在这一卷的: 起点能力 → 终点能力 / 起点信任 → 终点信任 / 收获/失去
      5. 卷末钩子(必须强烈)
      6. 反派进度(反派在这卷做了什么)
      7. 伏笔: 埋下哪些 / 回收哪些
```

### 5.3 输出契约

```json
{
  "story_id": "uuid",
  
  "summary": "一个普通学生为了找到父亲死亡真相,通过不断死亡获得能力,最终揭开系统是宇宙实验的真相,打破系统束缚。",
  
  "conflict_layers": [
    {"layer":1,"type":"生存","description":"不断副本求生,不被杀死也不发疯"},
    {"layer":2,"type":"真相","description":"调查父亲之死,接近系统真相"},
    {"layer":3,"type":"抉择","description":"最终选择:打破系统(失去所有能力)还是接受系统(掌控力量)"}
  ],
  
  "theme": "记忆即人性:当失去所有记忆,你还是你吗?",
  
  "volume_cliffhangers": [
    {"volume":1,"hook":"能力觉醒的关键时刻,系统突然发来一条信息:'实验体#0721,欢迎入局'"},
    {"volume":2,"hook":"苏默发现了父亲的'意外现场'留有觉醒者的痕迹"}
  ],

  "volumes_detail": [
    {"volume_no":1,"summary":"主角初入副本,觉醒能力,加入学院",
     "key_events":["EVT-001","EVT-002"],"cliffhanger":"'实验体#0721,欢迎入局'"},
    {"volume_no":2,"summary":"发现父亲死亡线索,深入调查,危机升级",
     "key_events":["EVT-003"], "cliffhanger":"父亲的秘密"}
  ],
  
  "total_plot_events": [
    {"id":"EVT-001","name":"能力第一次觉醒","volume":1,"chapter":5,"type":"关键节点",
     "characters":["char_001","char_003"],"result":"获得第一个能力"},
    {"id":"EVT-002","name":"第一次重要失忆","volume":1,"chapter":20,"type":"转折点",
     "characters":["char_001","char_005"],"result":"忘记char_005的名字,关系倒退"},
    {"id":"EVT-003","name":"父亲之死线索","volume":2,"chapter":150,"type":"伏笔回收",
     "characters":["char_001","char_008"],"result":"发现父亲不是普通死亡"},
    ...更多事件
  ]
}
```

### 5.4 下游绑定

```
→ 模块6 (Power System) 引用: story.conflict_layers → 冲突能力需求
→ 模块7 (Factions) 引用: story.volume_cliffhangers → 势力冲突
→ 模块9 (Volume Fragments) 引用: story.volumes_detail → 每卷展开(包含summary/key_events/cliffhanger)
→ 模块11 (Chapter Plan) 引用: story.plot_events → 事件分配到章
→ 模块16 (Polish) 引用: story.theme → 润色围绕主题
```


---

## 模块6: 力量体系 (Power System)

### 6.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| world.rules | 模块3 | 必须遵守的规则 |
| protagonist.abilities | 模块4 | 主角能力模板 |
| characters[].abilities | 模块4 | 全员能力 |
| story.conflict_layers | 模块5 | 冲突对能力的需求 |

### 6.2 AI执行步骤

```
Step 1: 设计力量体系全貌 (1次调用)
  标准模板:
    prompt模板:
      基于{world.rules}设计完整力量体系。
      
      必须回答:
      1. 等级体系(至少10级): 
         等级名,每级的标志/特征,战力范围
         和主角growth_route对应
      2. 力量来源(为什么有高有低):
         天赋/修炼方式/突破条件
      3. 战斗体系(攻击/防御/辅助/规则类):
         每个大类的细分
      4. 升级机制:
         如何升级?瓶颈在哪?怎么突破?
      5. 限制(最重要!):
         力量的代价/限制/副作用
         (避免"全能"无敌设定)
      6. 等级对应年龄/身份:
         社会中不同等级的地位
```

### 6.3 输出契约

```json
{
  "power_system": {
    "tiers": [
      {"level":1,"name":"未觉醒","desc":"普通人","req":"无","population_pct":"85%"},
      {"level":2,"name":"觉醒一阶","desc":"初步感知能量","req":"首次副本通关","pct":"8%"},
      {"level":5,"name":"精英","desc":"能力稳定","req":"100次副本+精神阈值","pct":"2%"},
      {"level":8,"name":"霸主","desc":"多人无敌","req":"特殊机缘+心魔","pct":"0.01%"},
      {"level":10,"name":"传说","desc":"最高等级","req":"打破系统限制","pct":"0%"}
    ],
    "combat_categories": ["元素系","强化系","精神系","规则类","辅助系"],
    "growth_method": "副本契炼+参悟规则",
    "limits": ["精力有限","能力相克","精神过载","规则惩罚"],
    "bottlenecks": [
      {"level":2→5,"name":"凝练瓶颈","sol":"收集50种不同能力"},
      {"level":5→8,"name":"心魔瓶颈","sol":"面对最深的恐惧(记忆恢复)"}
    ]
  }
}
```

### 6.4 下游绑定

```
→ 模块14 场景设计: power_system.combat_categories → 战斗描写方式
→ 模块15 正文生成: power_system.limits → 战斗不能无代价
→ 模块9 卷纲: power_system.tiers → 提升节奏对齐
```

---

## 模块7: 势力体系 (Faction System)

### 7.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| world.civilization | 模块3 | 政治结构 |
| characters[].profile.affiliation | 模块4 | 初始阵营 |
| story.conflict_layers | 模块5 | 势力冲突依据 |

### 7.2 AI执行步骤

```
Step 1: 设计各势力 (1次调用)
  标准模板:
    基于{world.civilization}设计{5-8}个主要势力。
    每个势力: name, type, territory(LOC index), leader(character_id), 
    military_strength, core_value, relations{合作/中立/敌对}, 
    protagonist_current_status, character_members[], internal_conflicts
```

### 7.3 输出契约

```json
{
  "factions": [
    {
      "id": "FAC-001", "name": "觉醒者协会", 
      "leader": "char_009", "tier": 2,
      "relations": [{"fac":"FAC-002","type":"敌对"}],
      "members": ["char_003", "char_009"],
      "current_relations": {"protagonist": "友好,正式成员"}
    }
  ]
}
```

### 7.4 下游绑定

```
→ 模块14 场景设计: factions[].territory → 势力范围→场景选择
→ 模块15 正文生成: factions[].relations → 角色冲突来源
```

---

## 模块8: 时间线 (Timeline)

### 8.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| world.history.timeline | 模块3 | 历史事件 |
| story.plot_events | 模块5 | 剧情事件 |
| protagonist.growth_route | 模块4 | 成长阶段 |

### 8.2 AI执行步骤

```
Step 1: 整合世界+故事时间线 (1次调用)
  标准模板:
    基于{world.history.timeline}和{story.plot_events},整合主线+分支时间线。
    每个事件: {id, era, type, chapter_ref, involved_characters, 
    status(基础/预设计划/已完成)}, display_color, notes
```

### 8.3 输出契约

```json
{
  "timeline": {
    "events": [
      {"id":"TL-001","era":"近代","type":"世界观","chapter":null,"characters":[],"status":"基础"},
      {"id":"TL-002","era":"故事元年","type":"关键节点","chapter":5,"characters":["char_001"],"color":"#1890ff"},
      {"id":"TL-003","era":"故事元年","type":"日常","chapter":10,"characters":["char_001","char_005"],"color":"#52c41a"}
    ],
    "consistency": {"contradictions": [], "orphans": []}
  }
}
```

### 8.4 下游绑定

```
→ 模块11 章节规划: timeline.events → 分配到章
→ 模块18 一致性检查: timeline → 校验事件时序
```

---

## 模块9: 卷纲 (Volume Fragments)

### 9.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| project.wordcount.volumes | 模块2 | 卷数字数 |
| world.world_escalation | 模块3 | 世界升级 |
| protagonist.growth_route | 模块4 | 每卷成长 |
| story.volumes_detail | 模块5 | 每卷摘要(含key_events/cliffhanger) |
| story.volume_cliffhangers | 模块5 | 每卷引子(卷首引导语) |
| story.total_plot_events | 模块5 | 全部剧情事件池(按volume过滤) |
| story.theme | 模块5 | 核心主题 |
| power_system.tiers | 模块6 | 每卷等级上限 |

### 9.2 AI执行步骤

```
Step 1: 每卷详细设计 (分10次或1次批量)
  标准模板:
    基于{story.volume[v]}设计第{v}卷完整内容。
    巻名,巻主人公状态,包含章节,本卷核心冲突,关键事件{EVT-ids},
    伏笔本卷埋/本卷收,卷末钩子,写作要点
    一致性检查: 能力/关系/字数是否合理
```

### 9.3 输出契约

```json
{
  "volumes": [
    {
      "volume_no": 1,
      "name": "能力觉醒",
      "chapters": 125,
      "target_words": 250000,
      "protagonist_start_state": {"level": "觉醒一阶", "location": "LOC-001"},
      "protagonist_end_state": {"level": "觉醒二阶", "location": "LOC-002"},
      "key_events": ["EVT-001", "EVT-002"],
      "volume_foreshadows": [{"type":"埋设","desc":"系统消息'}", "chap":5,"recycle_vol":3}],
      "cliffhanger": "'实验体#0721,欢迎入局' - 第125章最后一句",
      "consistency": {"power_rationality":true,"wordcount":true,"relationships":true}
    }
  ]
}
```

### 9.4 下游绑定

```
→ 模块10 剧情节点: volume.key_events → 事件细化
→ 模块11 章节规划: volume.chapters → 章节分配
```

---

## 模块10: 剧情节点 (Plot Nodes)

### 10.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| story.plot_events | 模块5 | 全部事件 |
| volumes[].key_events | 模块9 | 每卷事件 |
| characters.relation_map | 模块4 | 角色关系 |
| world.location_index | 模块3 | 地点列表 |
| power_system | 模块6 | 力量等级 |
| factions | 模块7 | 势力关系 |

### 10.2 AI执行步骤

```
Step 1: 每个关键事件具体化 (1次批量调用)
  标准模板:
    选取以下事件 {event_ids},对每个事件设计具体方案:
    背景铺垫,发生原因,场景选择(LOC index),涉及角色(character_ids),
    对白要点,动作描写,事件转折点,结果,导致后续,字数范围
```

### 10.3 输出契约

```json
{
  "plot_nodes": [
    {
      "event_id": "EVT-001",
      "title": "能力第一次觉醒",
      "trigger": "第一次副本中被杀死,系统激活",
      "scene": "LOC-002 新手副本",
      "characters": ["char_001"],
      "action_purpose": "建立金手指,让读者第一次感受爽感",
      "dialogue_points": ["'这是...?","'我没死?","多了什么...'"],
      "climax": "反杀,获得第一个能力",
      "consequence": "意识到自己可以变强,走上主动变强之路",
      "next_events": ["EVT-002", "EVT-005"],
      "word_count_range": [1500, 3000]
    }
  ]
}
```

### 10.4 下游绑定

```
→ 模块12 章节细纲: plot_nodes → 每个节点展开为细纲
→ 模块14 场景设计: plot_nodes[].scene → 场景选择依据
```


---

## 模块11: 章节规划 (Chapter Plan)

### 11.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| volume.chapters | 模块9 | 本卷总章数 |
| volume.target_words | 模块9 | 本卷总字数 |
| volume.key_events | 模块9 | 关键事件列表 |
| plot_nodes[] | 模块10 | 每个事件具体设计 |
| timeline.events | 模块8 | 预设计划事件 |
| project.platform | 模块2 | 平台规则 |
| protagonist.current_state | 模块4 | 当前状态(每章刷新) |

### 11.2 AI执行步骤

```
Step 1: 章节分配大列表 (1次调用/每卷)
  prompt模板:
    为第{volume.volume_no}卷设计{chapter_count}章的规划。
    己知音级信息: {platform_rules}
    需要覆盖: {key_events},{timeline_events}
    要求: 每章{chapter_target_words}字(±10%),每3章一个小钩子,每5章一个大钩子
    
    输出: [{chapter_no,title,plot_nodes_covered,target_words,hook_type,cliffhanger,
    protagonist_level_start,location_ids,dialogue_ratio,pacing}]
    dialogue_ratio: 对白占比(轻松章节>50%,打斗章节30%)
    pacing: "缓/正常/快/爆"
```

### 11.3 输出契约

```json
{
  "volume_no": 1,
  "chapters": [
    {
      "global_chapter_no": 1,
      "chapter_no": "1-1",
      "title": "死者复生",
      "plot_nodes_covered": ["EVT-001"],
      "target_words": 2000,
      "hook_type": "小钩子",
      "cliffhanger": null,
      "protagonist_level": "未觉醒→觉醒一阶",
      "locations": ["LOC-001", "LOC-002"],
      "dialogue_ratio": 0.4,
      "pacing": "快",
      "key_events": ["进入副本","死亡","觉醒"],
      "foreshadows_to_add": ["系统的提示音"],
      "foreshadows_to_recycle": []
    }
  ]
}
```

### 11.4 下游绑定

```
→ 模块12 章节细纲: chapter_plan → 逐章展开
→ 模块13 场景设计: chapter.locations → 场景上下文
```

---

## 模块12: 章节细纲 (Chapter Outline)

### 12.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| chapter_plan.cover | 模块11 | 本章覆盖范围 |
| timeline.events | 模块8 | 主线事件 |
| plot_nodes[].scene | 模块10 | 事件场景 |
| character.log | 模块4 | 角色状态 |
| foreshadow.plan | 模块9 (volume_foreshadows) | 本章按计划需埋/收的伏笔清单 |
| world_foreshadows | 模块3 | 全局伏笔列表(∩本章相关) |

### 12.2 AI执行步骤

```
Step 1: 逐章生成细纲 (1次调用/每章)
  prompt模板:
    基于章节规划展开: 章节标题,本章字数目标
    展开为完整细纲: 开场白钩子,场景1(引子)→场景2(发展)→...→场景N(钩子),
    每小节:字数范围,节奏,场景地点,出场人物,剧情作用,情绪曲线位置,核心情绪,
    本章知识库状态({知识库字段}),写作要点(特别注意)
    一致性:人设/能力/关系,剧情是否连贯,伏笔埋/收是否正确,情绪曲线形状
```

### 12.3 输出契约

```json
{
  "chapter": {
    "chapter_no": "1-1",
    "target_words": 2000,
    "scenes": [
      {
        "scene_no": 1,
        "location": "LOC-001 主角卧室",
        "characters": ["char_001"],
        "plot": "主角从噩梦中惊醒",
        "word_range": [300, 400],
        "pacing": "缓",
        "emotion_curve_position": "低点→爬升",
        "emotions": ["不安", "困惑"],
        "action_beats": ["醒来","看表(怀表闪了一下)","出门"],
        "sensory_details": ["潮湿的空气","钟表滴答声"],
        "knowledge_update": {"protagonist.location": "LOC-001", "protagonist.mood": "焦虑"},
        "writing_tips": "开局要简短有代入感,怀表闪光为伏笔"
      }
    ],
    "consistency": {"character_voices_ok": true, "power_consistent": true,
                    "plot_coherent": true, "foreshadow_balanced": true},
    "foreshadows": ["埋:怀表闪光→第86章","收:无"],
    "status": "planned"
  }
}
```

### 12.4 下游绑定

```
→ 模块14 场景设计: chapter.scenes[] → 每场景展开
→ 模块15 正文生成: chapter → 直接生成依据
→ 模块17 知识库更新: chapter.knowledge_update → 更新知识库
```

---

## 模块13: 内容解析 (Content Parser)

### 13.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| chapter_plan | 模块11 | 章节列表 |
| character | 模块4 | 角色模块 |
| world | 模块3 | 世界观 |
| foreshadow_active_list | 模块12累积(经M9→M10→M11→M12链路) | 截至上章已埋未收的伏笔ID列表 |
| writing_constraints | 模块3+4+6+7拼接 | 规则/能力/关系/时序静态约束 |
| config_template | 模块10 | 解析配置 |

### 13.2 AI执行步骤

```
Step 1: 文本预处理 (AI辅助解析)
  输入: 用户已写章节正文
  
  1. 场景/对白/动作切分
  2. 关键信息提取(世界观/人物/剧情/情绪/节奏)
  
  prompt模板:
    解析以下章节, 提取: 当前状态(角色,地点,时间),进行事件,
    已消耗字数,情绪小结
    
    输出: {summary_text, events, status_change, word_count_actual}

Step 2: 状态同步
  解析结果 → module17 知识库更新
  character当前状态更新
  时间线新增事件
```

### 13.3 输出契约

```json
{
  "chapter_no": "1-1",
  "parsed_data": {
    "events": ["事件1"],
    "status_change": {"char_001": {"location": "LOC-003", "mood": "紧张"}},
    "word_count_actual": 1950,
    "emotion_summary": "从不安到冷静为主,结尾有提升"
  }
}
```

### 13.4 下游绑定

```
→ 模块17 知识库更新: parsed_data.status_change → 更新
→ 模块11/12: 作为写作进度记录
```

---

## 模块14: 场景设计 (Scene Design)

### 14.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| scene.chapter | 模块12 | 场景上下文 |
| location | 模块3 | 地点设定 |
| characters | 模块4 | 出场角色能力/性格 |
| power_system | 模块6 | 打斗描写依据 |
| emotion_curve | 模块12 | 情绪曲线位置 |
| foreshadow_plan | 模块12 | 本章要埋/收的伏笔清单(与M12.foreshadows输出一致) |
| chapter_pacing | 模块11 | 本章节奏("缓/正常/快/爆") |

### 14.2 AI执行步骤

```
Step 1: 场景骨架生成 (1次调用)
  prompt模板:
    基于{scene.location}的{scene.characters}输入场景骨架:
    场景概述时间/地点/环境,剧情推进目标,场景核心冲突,
    战斗策略(根据 power_system.combat_categories, 重策略不单暴力),
    前钩后钩(承上启下),场景氛围(幽默/紧张...),伏笔植入,预期阅读反应
    
    输入: 场景起始情绪{scene.emotion_curve_position}, 场景目的{scene.plot}
    输出: 场景骨架JSON
    
Step 2: 情绪计算
  基于前场景结束情绪+当前场景目的+emotion_curve位置 → 计算当前情绪值
```

### 14.3 输出契约

```json
{
  "scene_skeleton": {
    "scene_id": "scene-1-1-1",
    "setting": {"time":"深夜","location":"废墟工厂","environment":"月光,生锈金属"},
    "plot_purpose": "主角第一次使用能力觉醒后的对战",
    "core_conflict": "主角(刚觉醒) VS 副本一阶怪物",
    "combat_strategy": "利用环境偷袭,避免正面硬拼",
    "foreshadow_integration": "战斗中隐约听到系统提示音",
    "atmosphere": "紧张+好奇",
    "reader_reaction": "惊喜于能力组合+悬念系统提示"
  },
  "expected_emotion": {"before": "焦虑","middle":"紧张","after":"兴奋+期待"}

  "scene_hooks": {
    "before": ["承接:主角不安的情绪"],
    "after": ["钩子:发现怪物似曾相识"]
  }
}
```

### 14.4 下游绑定

```
→ 模块15 正文生成: scene_skeleton → 描写框架
→ 模块16 润色: atmosphere + emotion → 润色方向
```


---

## 模块15: 正文生成 (Draft Generation) ─ 核心

### 15.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| scene_skeleton | 模块14 | 场景骨架 |
| character(personality,speaking_style) | 模块4 | 对白+行为依据 |
| foreshadow_to_add | 模块12 | 本章要埋的伏笔 |
| location_details | 模块3 | 环境描写参考 |
| power_system(combat_categories) | 模块6 | 打斗描写依据 |
| target_words | 模块12 | 本章字数目标 |
| writing_constraints | 模块3+4+6+7拼接 | 所有约束规则(能力限制/关系/规则/边界) |
| foreshadow_plan | 模块12 | 本章要埋/收的伏笔清单 |

### 15.2 AI执行步骤

```
Step 1: 场景开头生成 (1次调用)
  prompt模板:
    续写{scene.previous_scene.location}衔接{scene.location},参考{scene_skeleton},
    场景氛围:{atmosphere},必须回收:{foreshadows}中的伏笔,
    本次字数:{target_words},出场角色:{characters},
    特别要求: 氛围适度{style.taboo_words},对白占比{dialogue_ratio},情绪:{emotion_curve}
    
    开头: {previous_scene.ending_text}
    返回: Markdown正文

Step 2: 情绪渲染强化 (continuation模式)
  Step1完成 → 以最后一段为接口继续生成
  分段策略: [{opening:0-200}, {development:200-1500}, {climax:1500-1800}, {ending:1800-2000}]

Step 3: 压缩润色 (每个完整场景后)
  生成完毕后 → 检查 → 压缩10%-15%:
    1. 删除重复描写
    2. 简化冗余对白
    3. 删除违反内容边界元素

Step 4: 场景组装 + 衔接检查
  拼接分段 → 检查衔接: 时间线连续,角色一致,情绪过渡自然
```

### 15.3 输出契约

```json
{
  "draft": {
    "chapter_no": "1-1",
    "scene_id": "scene-1-1-1",
    "content": "深夜,月光穿过破碎的玻璃窗洒在生锈的钢铁走廊上...",
    "word_count_raw": 2100,
    "word_count_final": 1950,
    "foreshadow_added": ["怀表停下那一刻,远处传来低语"],
    "transition_ok": true,
    "continuation_point": "最后200字(衔接下一场景)"
  }
}
```

### 15.4 下游绑定

```
→ 模块13 内容解析: 生成正文 → 解析更新状态
→ 模块16 润色: draft → 进一步润色
→ 模块17 知识库更新: draft中提取知识更新
→ 模块18 一致性检查: 检查生成内容是否符合所有约束
输出到: project(章节正文), AI日志, 相关统计数据
```

---

## 模块16: 润色 (Polish)

### 16.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| characters.speaking_style | 模块4 | 对白风格 |
| power_system.tiers | 模块6 | 力量描述边界 |
| world.rules | 模块3 | 设定描写边界 |
| style.language | 模块2 | 语言风格 |
| content_boundary | 模块2 | 禁止内容 |
| foreshadow_protected | 模块12 | 本章伏笔的关键句/关键字(润色不可删改) |

### 16.2 AI执行步骤

```
Step 1: 语言润色 (1次调用)
  prompt模板:
    润色以下段落, 目标: 1)消除翻译腔 2)增强画面感 3)控制对白银河 4)优化标点节奏
    特别要求: 保留原意+情节+情绪,仅提升文字质量,保持{style.language}风格
    
  prompt: 分三阶段:
    - 第一阶段: 仅改语言(标点/用词/节奏)
    - 第二阶段: 删冗余/加细节描写
    - 第三阶段: 节奏调整(切割长句/合短句)

Step 2: 节奏调节
  输入: 润色后正文 + 平台+场景氛围
  按章节切分 → 控制每分钟信息量:
    紧张场景: 短句多,信息密
    日常场景: 可稍缓
  
Step 3: 风格统一 + 查重
  全文润色完毕 → 统一: 称号统一, 能力名统一, 说话方式统一
  查重: 3章内是否有类似桥段 → 标记修改
```

### 16.3 输出契约

```json
{
  "polished": {
    "chapter_no": "1-1",
    "content": "润色后的正文",
    "word_count_before": 1950,
    "word_count_after": 1850,
    "changes": [
      {"type":"语言润色","count":23},
      {"type":"节奏调节","count":5},
      {"type":"统一调整","count":2}
    ],
    "similarity": {"max": 0.08, "with_chapter": null}
  }
}
```

### 16.4 下游绑定

```
→ 模块13 内容解析: 最终正文 → 再次解析
→ 模块17 知识库更新: 提取知识更新
→ 模块18 一致性检查: 全方位检查
最终输出: fanqie_novel 章节内容表
```

---

## 模块17: 知识库更新 (Knowledge Base Update)

### 17.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| parsed_chapter | 模块13 | 已写章节解析结果(包含status_change) |
| previous_knowledge | 数据库读取 | 截至上章的知识库快照(已编码M3/M4/M8累积状态) |

### 17.2 AI执行步骤

```
Step 1: 增量更新 (自动)
  输入: 本次写作产生的 status_change
  处理流程:
    1. 检测变更字段 (character.X / world.X / plot.X)
    2. 追加变更到知识库
    3. 对比前后版本 → 生成 change_log
    
  更新内容:
    - characters char_XXX 字段: level递增 / location变化 / mood变化
    - world 字段: 地点解锁 / 势力关系变化
    - plot 字段: 事件标记为已完成/已伏笔已回收
    - timeline 字段: 设置 status 已完成

Step 2: 回收钩子
  检测: foreshadows(待回收) == 已写入正文 → 标记为"已回收":
    → 高亮显示在界面上

Step 3: 一致性验证
  step1+2 更新后 → 调用 module18 校验一致性
```

### 17.3 输出契约

```json
{
  "knowledge_update": {
    "chapter_no": "1-1",
    "changes": [
      {"entity":"char_001","field":"level","old":"未觉醒","new":"觉醒一阶"},
      {"entity":"char_001","field":"location","old":"LOC-001","new":"LOC-002"},
      {"entity":"plot","field":"EVT-001","old":"预设","new":"已完成"}
    ],
    "foreshadows_resolved": [],
    "consistency_status": "ok"
  }
}
```

### 17.4 下游绑定

```
→ 模块18 一致性检查: 触发校验(自动,不可绕过)
→ 模块12(下章规划时): 提供知识库快照作为下章初始状态
→ 模块15(下章生成时): 提供累积状态快照
输出到: fanqie_novel 知识库表
```

---

## 模块18: 一致性检查 (Consistency Check)

### 18.1 输入契约

| 输入字段 | 来源 | 说明 |
|---------|------|------|
| world.rules | 模块3 | 规则边界 |
| characters | 模块4 | 人设边界 |
| power_system.limits | 模块6 | 力量限制 |
| factions | 模块7 | 势力边界 |
| timeline | 模块8 | 时序约束 |
| knowledge_base | 模块17 | 当前状态 |
| content_boundary | 模块2 | 内容边界 |

### 18.2 AI执行步骤

```
Step 1: 自动校验规则集 (每次写作后自动执行)
  1. 等级校验: 角色等级是否超过本卷上限
  2. 能力校验: 新能力是否违背 world.rules
  3. 关系校验: 关系值更新是否符合交互逻辑
  4. 队伍校验: 队伍成员位置是否合理
  5. 时序校验: 当前事件是否在前置事件之后
  6. 伏笔校验: 是否有超时未收的伏笔(>50章)
  7. 商业校验: 内容是否违反 content_boundary
  8. 风格校验: 对白是否符合 speaking_style
  9. 逻辑校验: 是否存在因果/动机不合理

Step 2: 生成修复建议
  → 如果校验发现错误/矛盾:
    按严重程度分类: [critical/medium/low]
    给出具体修复建议(精确到章/段)
    
Step 3: 一致性评分
  综合评分 = Σ(各检查项通过率 × 权重)
  weight: level=0.15, ability=0.20, relation=0.15, timeline=0.15,
         foreshadow=0.15, commercial=0.10, style=0.10
```

### 18.3 输出契约

```json
{
  "consistency_report": {
    "check_id": "uuid",
    "checked_at": "2026-07-05T10:00:00Z",
    "chapter_range": "1-1",
    
    "items": [
      {"rule":"ability.violation","status":"ok","detail":"能力使用不违背rule#死亡继承"},
      {"rule":"foreshadow.timeout","status":"warning","detail":"FS-W-002超过50章未回收"},
      {"rule":"character.voice","status":"ok","detail":"char_001 对白符合speaking_style"}
    ],
    
    "score": 0.92,
    "summary": "1项重要警告,细节:FS-W-002超时",
    
    "fixes": [
      {"item":"foreshadow.timeout","priority":"medium","suggestion":"在第40-50章节插入回收场景"}
    ]
  }
}
```

### 18.4 下游绑定

```
→ 弹框警告用户(如果有critical/medium问题)
→ 写入 knowledge_base.consistency_status
→ 如果 score < 0.7 → 暂停写作,让用户修复
如果 score ≥ 0.7 → 继续下一章
最终输出: fanqie_novel 一致性检查日志
```

---

## 模块依赖关系全景表

```
[规划链 — 静态DAG,无环]

模块1(灵感) → 模块2(项目) → 模块3(世界观)
                         ↘ 模块4(人物)
                         ↘ 模块5(故事)
                              ↓
模块6(力量体系) ← 模块3+模块4+模块5
模块7(势力体系) ← 模块3+模块4+模块5
模块8(时间线) ← 模块3+模块5

模块9(卷纲) ← 模块2+模块3+模块4+模块5+模块6
模块10(剧情节点) ← 模块5+模块9+模块4+模块3+模块6+模块7
模块11(章节规划) ← 模块9+模块10+模块8+模块2+模块4
模块12(章节细纲) ← 模块11+模块9+模块8+模块10+模块3+模块4

[执行链 — 运行时迭代闭环]

  ┌──────────────────────────────────────────┐
  │                                          │
  ▼                                          │
模块15(正文生成) → 模块13(内容解析) → 模块17(知识库更新) → 模块18(一致性检查)
       ↑                                              │
       └────────── score<0.7 返回重修 ─────────────────┘
       │
       └─ score≥0.7 → 模块16(润色) → 章节输出

[闭环完成后,知识库状态作为下一章M12的输入,开启新一轮循环]
```

