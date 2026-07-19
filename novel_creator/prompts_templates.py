"""Prompt 模板常量 - 所有 AI 生成提示词模板
从 prompts.py 拆分，保持向后兼容。
"""

WORLD_BUILDING = """你是一位专业的世界观构建师。为小说《{title}》构建完整的世界观设定。

主题：{theme}
类型：{genre}
简介：{description}

请输出严格的JSON格式，包含以下4个字段，每个字段300-500字：
- time_period: 时间背景与社会状态
- location: 空间环境与地理特征
- atmosphere: 感官体验与情感基调
- rules: 世界规则与社会结构

根据类型有不同指导原则：
- 现代都市/言情：当代社会，聚焦具体城市
- 历史/古代：明确朝代，时代特征
- 玄幻/仙侠：修炼文明，门派势力
- 科幻：未来时期，科技水平

只输出JSON，不要其他内容。"""


WORLD_BUILDING_STYLE = """你是网文世界观构建大师。请严格仿照以下参考风格，为小说《{title}》构建世界观。

=== 参考风格特征 ===
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 描写风格：{description_style}
- 情感浓度：{emotional_intensity}
- 世界观特征：{world_features}
- 世界观铺设风格：{world_building_style}
- 升级/推进机制：{upgrade_mechanism}

=== 参考风格总结 ===
{overall_summary}

=== 创作基础 ===
类型：{genre}
子类型：{sub_genres}
主题：{theme}
副主题：{sub_themes}
核心驱动：{core_drive}
主角原型：{protagonist_archetype}

请输出严格的JSON格式，包含以下4个字段，每个字段300-500字：
- time_period: 时间背景与社会状态，必须体现参考风格的叙事节奏和语言基调
- location: 空间环境与地理特征，描写风格与参考风格一致
- atmosphere: 感官体验与情感基调，保持参考风格的情感浓度
- rules: 世界规则与社会结构，融入参考风格的升级机制和世界观特征

世界观必须与核心驱动和主角成长模式匹配，铺设方式遵循参考风格的世界观揭示方式。
只输出JSON，不要其他内容。"""


CHARACTERS_BATCH_GENERATION = """你是一位专业的小说角色设计师。请根据以下世界观和设定，生成{count}个角色和组织实体。

故事核心设定：{novel_description}

世界观：
- 时间：{time_period}
- 地点：{location}
- 氛围：{atmosphere}
- 规则：{rules}

主题：{theme}
类型：{genre}
要求：{requirements}

请输出严格的JSON数组格式，每个元素为角色或组织对象。

角色对象格式：
- name: 姓名
- age: 年龄
- gender: 性别
- is_organization: false
- role_type: protagonist(主角)/supporting(配角)/antagonist(反派)
- personality: 100-200字性格描述
- background: 100-200字背景故事
- appearance: 50-100字外貌描述
- traits: ["特长1", "特长2"]

组织对象格式：
- name: 组织名称
- is_organization: true
- organization_type: 门派/家族/公司/组织等
- organization_purpose: 组织目标
- power_level: 70-95
- location: 所在位置
- motto: 口号
- color: 主题色(十六进制如#FF5733)

只输出JSON数组，不要其他内容。"""


CHARACTERS_BATCH_GENERATION_STYLE = """你是网文角色设计大师。严格仿照以下参考风格，生成{count}个角色和组织实体。

=== 参考风格特征 ===
- 主角原型：{protagonist_archetype}
- 成长模式：{character_growth_pattern}
- 人物关系模式：{relationship_dynamics}
- 语言基调：{tone}
- 情感浓度：{emotional_intensity}
- 对话风格：{dialogue_style}

=== 参考风格总结 ===
{overall_summary}

=== 创作要求 ===
世界观：
- 时间：{time_period}
- 地点：{location}
- 氛围：{atmosphere}
- 规则：{rules}

主题：{theme}
类型：{genre}
子类型：{sub_genres}
核心矛盾：{main_conflict}
要求：{requirements}

请输出严格的JSON数组格式，每个元素为角色或组织对象。

角色参照参考风格的人设原型和成长模式：
- 主角必须符合"{protagonist_archetype}"原型，成长遵循"{character_growth_pattern}"模式
- 角色语言习惯与参考风格的对话风格一致
- 人物关系参照参考风格的"{relationship_dynamics}"设计

角色对象格式：
- name: 姓名
- age: 年龄
- gender: 性别
- is_organization: false
- role_type: protagonist(主角)/supporting(配角)/antagonist(反派)
- personality: 100-200字性格描述，体现{tone}的基调
- background: 100-200字背景故事
- appearance: 50-100字外貌描述
- traits: ["特长1", "特长2"]，与升级机制{upgrade_mechanism}相关

组织对象格式：
- name: 组织名称
- is_organization: true
- organization_type: 门派/家族/公司/组织等
- organization_purpose: 组织目标
- power_level: 70-95
- location: 所在位置
- motto: 口号
- color: 主题色(十六进制如#FF5733)

只输出JSON数组，不要其他内容。"""


# ========== 总纲（结构化蓝图）==========

BOOK_OVERVIEW_CREATE = """你是一位专业的小说总架构师。请根据以下前序创作信息，为小说撰写全书结构化总纲。

## 创作基础

### 灵感设定
书名：{title}
类型：{genre}
主题：{theme}
叙事视角：{narrative_perspective}
作品简介：{inspiration_desc}

### 角色信息
{characters_info}

### 世界观摘要
{world_summary}

请输出严格JSON格式，包含以下6个维度：

1. core_conflict: 核心叙事引擎
    - central_conflict: 核心冲突（一句话）
    - central_question: 全书悬念问题
    - thematic_statement: 主题表达

2. acts: 幕结构设计（3-5幕），每幕包含：
    - act_number: 幕序号
    - name: 幕名称（如"起·废柴觉醒"）
    - chapter_range: "1-5"格式的章节范围
    - goal: 本幕核心目标
    - key_turning_point: 本幕关键转折事件
    - emotional_tone: 本幕情感基调

3. character_arcs: 角色成长轨迹，每个角色包含：
    - name: 角色名
    - arc_type: 成长类型（如"逆袭成长""黑化堕落"）
     - milestones: [{{chapter: 5, change: "转变描述"}}, ...]

4. subplots: 支线规划，每条支线包含：
    - name: 支线名称
    - involved_chapters: [3, 8, 14] 涉及的章节列表
    - resolution_chapter: 收束章节

5. foreshadowing: 伏笔时间线，每个伏笔包含：
    - planted_chapter: 埋设章节
    - payoff_chapter: 回收章节
    - hint: 伏笔暗示内容
    - reveal: 揭示内容

6. pacing: 节奏分布，每段包含：
    - chapters: "1-3" 章节范围
    - rhythm: 节奏描述（如"慢热铺垫""爆发高潮"）
    - satisfaction_type: 爽点类型

只输出严格JSON，不输出其他内容。"""


BOOK_OVERVIEW_CREATE_STYLE = """你是网文总架构师。严格仿照以下参考风格，为小说撰写全书结构化总纲。

## 参考风格特征

- 故事框架：{story_framework}
- 核心驱动：{core_drive}
- 主线矛盾：{main_conflict}
- 叙事节奏：{pacing}
- 情感浓度：{emotional_intensity}
- 爽点类型：{satisfaction_type}
- 爽点循环：{satisfaction_pattern}
- 情绪节奏：{emotional_beats}
- 钩子设计：{hook_design}
- 衔接模式：{transition_style}
- 伏笔运用：{foreshadowing_style}
- 写作手法：{writing_techniques}

### 参考风格总结
{overall_summary}

## 创作基础

### 灵感设定
书名：{title}
类型：{genre}
子类型：{sub_genres}
主题：{theme}
叙事视角：{narrative_perspective}
副主题：{sub_themes}
作品简介：{inspiration_desc}

### 角色信息
{characters_info}

### 世界观摘要
{world_summary}

请输出严格JSON格式，包含以下6个维度：

1. core_conflict: 核心叙事引擎
   - central_conflict: 核心冲突（一句话）
   - central_question: 全书悬念问题
   - thematic_statement: 主题表达

2. acts: 幕结构设计（3-5幕），每幕严格遵循参考风格的爽点循环模式（{satisfaction_pattern}），每幕包含：
   - act_number: 幕序号
   - name: 幕名称
   - chapter_range: "1-5"格式的章节范围
   - goal: 本幕核心目标
   - key_turning_point: 本幕关键转折事件（参照{hook_design}设计钩子）
   - emotional_tone: 本幕情感基调（参照{emotional_beats}）

3. character_arcs: 角色成长轨迹，每个角色包含：
   - name: 角色名
   - arc_type: 成长类型
    - milestones: [{{chapter: 5, change: "转变描述"}}, ...]（milestone必须对应到具体章节）

4. subplots: 支线规划，每条支线包含：
   - name: 支线名称
   - involved_chapters: [3, 8, 14] 涉及的章节列表
   - resolution_chapter: 收束章节

5. foreshadowing: 伏笔时间线（参照{foreshadowing_style}），每个伏笔包含：
   - planted_chapter: 埋设章节
   - payoff_chapter: 回收章节
   - hint: 伏笔暗示内容
   - reveal: 揭示内容

6. pacing: 节奏分布，每段包含：
   - chapters: "1-3" 章节范围
   - rhythm: 节奏描述（参照{pacing}）
   - satisfaction_type: 爽点类型（参照{satisfaction_type}）

只输出严格JSON，不输出其他内容。"""


# ========== 章节细纲（局部上下文注入）==========

CHAPTER_OUTLINE_DETAIL = """你是小说《{project_title}》的大纲设计师。请为第{chapter_number}章撰写详细大纲。
{degradation_warning}
## 全书总纲
{book_overview_json}

## 世界观设定
{world_summary}

## 本章局部上下文

### 所属幕信息
{act_context}

### 本章触发的角色转变
{character_milestones}

### 当前活跃支线
{active_subplots}

### 伏笔管理
- 本章需要埋设的伏笔：{foreshadow_to_plant}
- 本章需要回收的伏笔：{foreshadow_to_payoff}

### 本章节奏要求
{pacing_requirement}

### 前一章衔接
- 前一章标题：{prev_chapter_title}
- 前一章结尾：{prev_chapter_tail}

## 创作基础
类型：{genre}
叙事视角：{narrative_perspective}

## 角色信息
{characters_info}

## 本章位置
这是第{chapter_number}章（共{total_chapters}章），{my_position}

请输出：
- title: 章节标题（吸引人，符合类型风格）
- summary: 200-300字章节概要，包含本章节的核心事件和情节推进
- scenes: ["场景1描述", "场景2描述", ...]
- characters: ["出场角色1", "出场角色2", ...]
- key_points: ["关键情节1", "关键情节2", ...]
- emotion: 本章节情感基调
- goal: 本章节在整体故事中的目标（对应总纲中的哪个节点）
- technique_focus: 本章节重点运用的写作技法
- chapter_hook: 章尾钩子（引导读者继续阅读的悬念）

只输出严格JSON格式。"""


CHAPTER_OUTLINE_DETAIL_STYLE = """你是小说《{project_title}》的网文大纲师。请为第{chapter_number}章撰写详细大纲。
{degradation_warning}
## 全书总纲
{book_overview_json}

## 世界观设定
{world_summary}

## 本章局部上下文

### 所属幕信息
{act_context}

### 本章触发的角色转变
{character_milestones}

### 当前活跃支线
{active_subplots}

### 伏笔管理
- 本章需要埋设的伏笔：{foreshadow_to_plant}
- 本章需要回收的伏笔：{foreshadow_to_payoff}

### 本章节奏要求
{pacing_requirement}

### 前一章衔接
- 前一章标题：{prev_chapter_title}
- 前一章结尾：{prev_chapter_tail}

## 参考风格特征
- 故事框架：{story_framework}
- 爽点循环：{satisfaction_pattern}
- 钩子设计：{hook_design}
- 衔接模式：{transition_style}
- 伏笔运用：{foreshadowing_style}
- 写作手法：{writing_techniques}
- 叙事节奏：{pacing}
- 情绪节奏：{emotional_beats}

## 创作基础
类型：{genre}
叙事视角：{narrative_perspective}

## 角色信息
{characters_info}

## 本章位置
这是第{chapter_number}章（共{total_chapters}章），{my_position}

必须遵循：
1. 严格遵循所属幕的目标和情感基调
2. 角色转变必须在本章中自然体现
3. 支线推进必须与主线交织
4. 伏笔埋设/回收必须自然融入情节
5. 章节末尾设计钩子（参照{hook_design}），引导读者继续阅读
6. 体现参考风格的「{transition_style}」衔接模式
7. 本章情感节奏参照局部上下文中的节奏要求

请输出：
- title: 章节标题（吸引人，符合类型风格，带钩子感）
- summary: 200-300字章节概要，体现参考风格的节奏和叙事手法
- scenes: ["场景1描述", "场景2描述", ...]
- characters: ["出场角色1", "出场角色2", ...]
- key_points: ["关键情节1", "关键情节2", ...]
- emotion: 本章节情感基调，参照局部上下文
- goal: 本章节在整体故事中的目标（对应总纲中的哪个节点）
- technique_focus: 本章节重点运用的写作技法，从参考风格中选取
- chapter_hook: 章尾钩子（引导读者继续阅读的悬念）

只输出严格JSON格式。"""


OUTLINE_CREATE = """你是一位专业的小说大纲设计师。请根据以下信息，为小说设计{chapter_count}章的详细大纲。

书名：{title}
类型：{genre}
主题：{theme}
叙事视角：{narrative_perspective}

=== 世界观设定（大纲必须符合此设定） ===
{world_summary}

角色信息：
{characters_info}

请输出严格的JSON数组格式，每个元素为一章的大纲：
- chapter_number: 章节序号
- title: 章节标题
- summary: 200-300字章节概要
- scenes: ["场景1", "场景2"]
- characters: ["出场角色1", "出场角色2"]
- key_points: ["关键情节1", "关键情节2"]
- emotion: 本章节情感基调
- goal: 本章节在整体故事中的目标

只输出JSON数组，不要其他内容。"""


OUTLINE_CREATE_STYLE = """你是网文大纲设计大师。严格仿照以下参考风格，为小说设计{chapter_count}章的详细大纲。

=== 参考风格特征 ===
- 故事框架：{story_framework}
- 核心驱动：{core_drive}
- 主线矛盾：{main_conflict}
- 叙事节奏：{pacing}
- 情感浓度：{emotional_intensity}
- 爽点类型：{satisfaction_type}
- 爽点循环：{satisfaction_pattern}
- 情绪节奏：{emotional_beats}
- 钩子设计：{hook_design}
- 衔接模式：{transition_style}
- 伏笔运用：{foreshadowing_style}
- 写作手法：{writing_techniques}

=== 参考风格总结 ===
{overall_summary}

=== 创作基础 ===
书名：{title}
类型：{genre}
子类型：{sub_genres}
主题：{theme}
叙事视角：{narrative_perspective}
核心主题：{theme}
副主题：{sub_themes}

=== 世界观设定（大纲必须符合此设定） ===
{world_summary}

角色信息：
{characters_info}

请输出严格的JSON数组格式，每个元素为一章的大纲：
- chapter_number: 章节序号
- title: 章节标题
- summary: 200-300字章节概要，体现参考风格的节奏和叙事手法
- scenes: ["场景1", "场景2"]
- characters: ["出场角色1", "出场角色2"]
- key_points: ["关键情节1", "关键情节2"]
- emotion: 本章节情感基调，参照参考情绪节奏
- goal: 本章节在整体故事中的目标
- technique_focus: 本章节重点运用的写作技法，从参考风格中选取

大纲必须严格遵循：
1. 故事推进遵循参考风格的爽点循环模式（{satisfaction_pattern}）
2. 章节间衔接使用参考风格的过渡模式（{transition_style}）
3. 章尾钩子参照参考风格的钩子设计（{hook_design}）
4. 整体节奏匹配参考风格的{pacing}
5. 交替运用参考风格中的写作手法：{writing_techniques}

只输出JSON数组，不要其他内容。"""


CHAPTER_GENERATION_NEXT = """你是小说《{project_title}》的作者，专注于{genre}类型。

撰写第{chapter_number}章《{chapter_title}》的完整正文。
- 目标字数：{target_word_count}字
- 叙事视角：{narrative_perspective}

=== 本章细纲（核心依据，所有情节必须严格据此展开） ===
{chapter_outline}

=== 世界观设定（正文必须符合此设定） ===
{world_summary}

=== 衔接锚点（上一章结尾内容） ===
{continuation_point}

=== 上一章已完成剧情（禁止重复！） ===
{previous_chapter_summary}

=== 上一章结尾章钩（衔接关键情节，本章必须接续这些设定） ===
{prev_chapter_hook}

=== 本章角色 ===
{chapter_characters}

=== 伏笔提醒 ===
{foreshadow_reminders}
{first_chapter_note}

输出规范：直接输出小说正文，从故事场景或动作开始。不要写"第X章"标题，直接开始正文。"""


CHAPTER_GENERATION_NEXT_STYLE = """你是小说《{project_title}》的作者，深谙{genre}类型网文写作技法。

撰写第{chapter_number}章《{chapter_title}》的完整正文。
- 目标字数：{target_word_count}字
- 叙事视角：{narrative_perspective}

=== 必须遵循的写作风格 ===
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 句式特点：{sentence_structure}
- 对话风格：{dialogue_style}
- 描写风格：{description_style}
- 情感浓度：{emotional_intensity}

=== 本章必须运用的写作技法 ===
{writing_techniques}

=== 钩子和悬念设计 ===
- 开篇钩子类型：{hook_design}
- 本章爽点模式：{satisfaction_pattern}
- 爽点类型：{satisfaction_type}
- 章尾衔接模式：{transition_style}

=== 情绪节奏 ===
- 本章情感基调：{emotional_beats}
- 伏笔运用：{foreshadowing_style}

=== 参考风格总结 ===
{overall_summary}

=== 本章细纲（核心依据，所有情节必须严格据此展开） ===
{chapter_outline}

=== 世界观设定（正文必须符合此设定） ===
{world_summary}

=== 衔接锚点（上一章结尾内容） ===
{continuation_point}

=== 上一章已完成剧情（禁止重复！） ===
{previous_chapter_summary}

=== 上一章结尾章钩（衔接关键情节，本章必须接续这些设定） ===
{prev_chapter_hook}

=== 本章角色 ===
{chapter_characters}

=== 伏笔提醒 ===
{foreshadow_reminders}

=== 本章重点技法 ===
{technique_focus}
{first_chapter_note}

写作要求：
1. 严格使用参考风格的语言基调、句式特点和描写风格
2. 对话口语化，60%以上不加对话标签
3. 用动作和细节展示情绪，避免直接心理描写
4. 开篇前3句必须有信息差或冲突钩子
5. 爽点循环遵循：铺垫→释放→至少1个反应层→衔接新钩子
6. 章尾留悬念，驱动读者追读下一章
7. 段落长短交替，节奏与参考风格一致

输出规范：直接输出小说正文，从故事场景或动作开始。不要写"第X章"标题，直接开始正文。
重要：本章目标{target_word_count}字，本次是开篇部分，写800-1500字引出情节即可，后续会自动续写完成全章。"""


CHAPTER_CONTINUATION = """你是小说《{project_title}》的作者，深谙{genre}类型网文写作技法。

你正在撰写第{chapter_number}章《{chapter_title}》，这是本章的续写部分。

=== 本章已写内容（承接最后一段继续，不要重复！） ===
{progress_content}

=== 本章大纲 ===
{chapter_outline}

=== 上一章结尾章钩（续写时需保持这些设定的连贯性） ===
{prev_chapter_hook}

=== 字数要求 ===
本章总目标约 {target_word_count} 字，当前已写约 {progress_chars} 字。
本次需要续写约 {segment_chars} 字。
⚠️ 未完待续：本章尚未写完，你必须在达到目标字数后才能结束。
{style_section}
=== 写作要求 ===
1. 承接上文最后一段的情感与节奏，自然过渡
2. 继续推进本章核心冲突，发展悬念
3. 不要重复上文已有的情节、对话或描写
4. 不要在正文中间强行收尾或总结
5. 不要写章节标题、不要写"第X章"
6. 每次续写内容要充实，避免过于简短
7. 本章未达目标字数前不要写"未完待续"等结束语

输出规范：直接续写正文，从被打断的情节处自然继续。"""


CHAPTER_CONTINUATION_STYLE = """=== 风格约束（续写必须与开篇风格一致） ===
- 语言基调：{tone}
- 节奏控制：{pacing}
- 句式特征：{sentence_structure}
- 对话风格：{dialogue_style}
- 描写手法：{description_style}
- 情感强度：{emotional_intensity}
- 写作技法：{writing_techniques}
- 氛围营造：{foreshadowing_style}
{overall_summary}

=== 上一章结尾章钩（续写时需保持这些设定的连贯性） ===
{prev_chapter_hook}"""


PLOT_ANALYSIS = """你是一位专业的小说编辑。请分析以下章节内容。

第{chapter_number}章《{title}》

{content}

请输出严格的JSON格式分析结果：
- hooks: 剧情钩子分析(悬念/情感/冲突/认知)
- foreshadowing: 伏笔分析
- conflict: 冲突分析(类型/各方/强度)
- emotional_arc: 情感曲线描述
- plot_points: ["关键情节点1", "关键情节点2"]
- pacing: 节奏评分(1-100)
- engagement: 吸引力评分(1-100)
- coherence: 连贯性评分(1-100)
- overall: 综合评分(1-100)
- suggestions: ["改进建议1", "改进建议2"]

只输出JSON，不要其他内容。"""


INSPIRATION_TITLE = """你是一位富有创意的小说策划。请根据以下信息，生成6个书名建议。

{style_section}用户输入：{user_input}

请输出严格的JSON数组格式，每个元素为一个书名(2-10字)。
只输出JSON数组，不要其他内容。"""


INSPIRATION_TITLE_STYLE = """你是一位网文小说策划专家。请严格仿照以下风格特征，为这部小说生成6个书名建议。

=== 参考风格 ===
- 叙事视角：{narrative_perspective}
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 情感浓度：{emotional_intensity}
- 独特特点：{unique_quirks}

=== 风格总结 ===
{overall_summary}

{user_input_section}请输出严格的JSON数组格式，每个元素为一个书名(2-10字)。
书名必须体现上述风格的基调与节奏感，避免与该风格不搭的书名。
只输出JSON数组，不要其他内容。"""


INSPIRATION_DESCRIPTION = """你是一位富有创意的小说策划。请根据以下信息，生成6个简介选项。

{style_section}书名：{title}
用户输入：{user_input}

每个简介50-100字，体现不同风格方向。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_DESCRIPTION_STYLE = """你是网文简介策划大师。请严格仿照以下风格，为小说《{title}》生成3个仿写简介选项。

=== 参考风格 ===
- 叙事视角：{narrative_perspective}
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 对话风格：{dialogue_style}
- 描写风格：{description_style}
- 句式特点：{sentence_structure}
- 情感浓度：{emotional_intensity}

=== 风格总结 ===
{overall_summary}

简介必须满足：
1. 使用与该风格一致的叙事口吻和句式节奏
2. 保持该风格的情感浓度和信息密度
3. 每个简介80-120字，悬念留白，不提供完整信息
4. 体现不同故事方向，但都符合该风格的调性

{user_input_section}请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_THEME = """你是一位富有创意的小说策划。请根据以下信息，生成6个主题选项。

{style_section}书名：{title}
简介：{description}
{user_input_section}
每个主题50-150字，体现不同主题方向。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_THEME_STYLE = """你是一位网文主题策划。请基于以下风格特征，生成3个主题选项。

=== 参考风格 ===
- 语言基调：{tone}
- 情感浓度：{emotional_intensity}
- 描写风格：{description_style}
- 独特特点：{unique_quirks}

=== 风格总结 ===
{overall_summary}

书名：{title}
简介：{description}

每个主题50-150字，必须与该风格的情感基调和叙事特点一致。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_GENRE = """你是一位富有创意的小说策划。请根据以下信息，生成6个类型标签。

书名：{title}
简介：{description}{user_input_section}
每个类型标签2-4字。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_GENRE_STYLE = """你是一位网文类型分析专家。基于以下风格特征，生成6个最匹配的类型标签。

=== 参考风格 ===
- 叙事视角：{narrative_perspective}
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 情感浓度：{emotional_intensity}
- 描写风格：{description_style}
- 句式特点：{sentence_structure}

=== 风格总结 ===
{overall_summary}

书名：{title}
简介：{description}

每个类型标签2-4字，必须与该风格实际匹配（不要给出与风格不符的类型）。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


STYLE_ANALYSIS = """你是网文深度拆解专家。请对以下小说内容进行全方位结构化分析。

{content}

请输出严格的JSON格式分析结果。注意：使用扁平JSON对象，不要嵌套分组。以下是所有需要的字段：

- narrative_perspective: 叙事视角(第一人称/第三人称限知/第三人称全知等)
- tone: 语言风格基调(幽默/严肃/轻松/沉重/诙谐/热血等)
- pacing: 叙事节奏(紧凑/舒缓/张弛有度/快慢交替等)
- dialogue_style: 对话风格描述(口语化/简洁/犀利/含蓄等)
- description_style: 描写风格(细腻白描/写意留白/感官轰炸等)
- vocabulary_level: 词汇特点(通俗/文雅/网络化/古风等)
- sentence_structure: 句式特点(短句为主/长短交替/排比递进等)
- emotional_intensity: 情感浓度(浓烈/克制/爆发式/渐进式等)
- unique_quirks: ["独特写作特点1", "独特写作特点2"]
- genre: 最匹配的类型标签(如:玄幻/都市/言情/悬疑/历史/科幻/末世/无限流等)
- sub_genres: ["子类型1", "子类型2"] 如: 系统流/无敌流/虐心/甜宠等
- theme: 核心主题(一句话描述，如"废柴逆袭走上巅峰")
- sub_themes: ["副主题1", "副主题2"] 如: 复仇/成长/守护/寻宝等
- plot_structure: 整体脉络(200字内，描述从开局到当前的故事框架、核心驱动、主要矛盾演进)
- story_framework: 故事框架类型(升级流/复仇线/日常单元/多线交织/蜕变成长/混合等)
- core_drive: 核心叙事引擎(一句话，如"主角通过系统任务不断升级")
- main_conflict: 主线矛盾(一句话)
- upgrade_mechanism: 升级/推进机制(境界等级/关系变化/财富积累等)
- writing_techniques: ["技法1", "技法2"] 如: 钩子开篇/爽点循环/信息差/延迟揭示/对比锚点/一笔两用/跨章回扣/身体反应替代心理描写
- hook_design: 钩子设计模式(悬念钩/冲突钩/反差钩/信息差钩等)
- satisfaction_type: 爽点类型(装逼打脸/逆袭反转/获得机缘/信息差碾压/情感满足/扮猪吃虎)
- satisfaction_pattern: 爽点循环模式(铺垫→释放→反应→衔接 的具体描述)
- emotional_beats: 情绪节奏(爽/虐/甜/燃等情绪的交替周期)
- foreshadowing_style: 伏笔运用风格(草蛇灰线/明暗交织/一环扣一环等)
- transition_style: 衔接过渡模式(打完小的来大的/胜利发现隐患/身份暴露反转等)
- protagonist_archetype: 主角人设原型(废柴逆袭/天才妖孽/重生者/穿越者/系统等)
- character_growth_pattern: 成长模式(隐忍爆发/稳中求进/跌宕起伏等)
- relationship_dynamics: 人物关系模式(如: 强强对抗/救赎/追妻/团宠等)
- world_building_style: 世界观铺设风格(信息倾泻/随事件揭示/对话透露等)
- world_features: 世界观特征描述(100字内)
- overall_summary: 200字整体风格总结，综合以上所有维度的仿写指导
- key_lessons: ["核心教训1", "核心教训2", "核心教训3"]

只输出一个扁平JSON对象，不要嵌套。不要使用分组名称作为key。

示例格式（扁平对象，非嵌套）：
narrative_perspective: 第一人称, tone: 轻松幽默, pacing: 紧凑, emotional_intensity: 克制, overall_summary: 200字总结, ...

只输出JSON，不要其他内容。"""

CHAPTER_POLISH = """你是专业小说编辑，深谙{genre}类型网文的写作技法。

请对以下章节进行润色优化。

=== 章节信息 ===
第{chapter_number}章《{chapter_title}》

=== 章节大纲 ===
{chapter_outline}

=== 润色重点 ===
{polish_focus}

=== 参考风格 ===（如有）
- 语言基调：{tone}
- 叙事节奏：{pacing}
- 句式特点：{sentence_structure}
- 描写风格：{description_style}

=== 原文 ===
{original_content}

=== 润色要求 ===
1. 保持原文核心情节和主线不变
2. 优化语言表达：让对话更生动、描写更细腻
3. 增强画面感和代入感
4. 去除重复啰嗦的表述
5. 丰富人物情感层次，增加心理暗描写
6. 章尾悬念更有钩子力
7. 不要添加原文不存在的新情节
8. 保持章节字数与原文基本一致（±10%以内）
9. 直接输出润色后正文，不要写"润色版"等说明文字"""
