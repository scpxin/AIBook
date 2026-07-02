"""小说创作 Prompt 模板 - 提取自 MuMuAINovel 项目"""
import json


def format_prompt(template, **kwargs):
    return template.format(**kwargs)


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


CHARACTERS_BATCH_GENERATION = """你是一位专业的小说角色设计师。请根据以下世界观和设定，生成{count}个角色和组织实体。

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


OUTLINE_CREATE = """你是一位专业的小说大纲设计师。请根据以下信息，为小说设计{chapter_count}章的详细大纲。

书名：{title}
类型：{genre}
主题：{theme}
叙事视角：{narrative_perspective}

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


CHAPTER_GENERATION_NEXT = """你是小说《{project_title}》的作者，专注于{genre}类型。

撰写第{chapter_number}章《{chapter_title}》的完整正文。
- 目标字数：{target_word_count}字
- 叙事视角：{narrative_perspective}

=== 本章大纲 ===
{chapter_outline}

=== 衔接锚点（上一章结尾内容） ===
{continuation_point}

=== 上一章已完成剧情（禁止重复！） ===
{previous_chapter_summary}

=== 本章角色 ===
{chapter_characters}

=== 伏笔提醒 ===
{foreshadow_reminders}

输出规范：直接输出小说正文，从故事场景或动作开始。不要写"第X章"标题，直接开始正文。"""


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


INSPIRATION_TITLE = """你是一位富有创意的小说策划。请根据用户输入，生成6个书名建议。

用户输入：{user_input}

请输出严格的JSON数组格式，每个元素为一个书名(2-10字)。
只输出JSON数组，不要其他内容。"""


INSPIRATION_DESCRIPTION = """你是一位富有创意的小说策划。请根据以下信息，生成6个简介选项。

书名：{title}
用户输入：{user_input}

每个简介50-100字，体现不同风格方向。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_THEME = """你是一位富有创意的小说策划。请根据以下信息，生成6个主题选项。

书名：{title}
简介：{description}

每个主题50-150字，体现不同主题方向。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


INSPIRATION_GENRE = """你是一位富有创意的小说策划。请根据以下信息，生成6个类型标签。

书名：{title}
简介：{description}
描述：{description}

每个类型标签2-4字。
请输出严格的JSON数组格式。
只输出JSON数组，不要其他内容。"""


STYLE_ANALYSIS = """你是一位专业的文学分析师。请分析以下小说内容的写作风格。

{content}

请输出严格的JSON格式分析结果：
- narrative_perspective: 叙事视角(第一人称/第三人称限知/第三人称全知等)
- tone: 语言风格基调(幽默/严肃/轻松/沉重等)
- pacing: 叙事节奏(紧凑/舒缓/张弛有度等)
- dialogue_style: 对话风格描述
- description_style: 描写风格描述
- vocabulary_level: 词汇特点
- sentence_structure: 句式特点
- emotional_intensity: 情感浓度
- unique_quirks: ["独特写作特点1", "独特写作特点2"]
- overall_summary: 200字整体风格总结

只输出JSON，不要其他内容。"""


def parse_json_response(text):
    """从AI响应中解析JSON"""
    if not text:
        return None

    text = text.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从markdown代码块中提取
    if "```" in text:
        import re
        blocks = re.findall(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        for block in blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue

    # 尝试找到第一个 { 或 [ 到最后一个 } 或 ]
    import re
    json_match = re.search(r"[\{[\].*[\}\]]", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return None
