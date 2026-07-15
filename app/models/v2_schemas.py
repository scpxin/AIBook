"""V2 Pydantic 请求模型 — 为V2 API提供类型安全验证"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union


class CompatibilityCheckRequest(BaseModel):
    platform: str = Field(..., description="目标平台: fanqie/qidian/qimao/custom")


# ========== 设计层请求模型 ==========

class BaseV2Request(BaseModel):
    """所有V2请求基类"""
    project_id: str = Field(..., min_length=1, max_length=64, description="项目ID")

    @field_validator('project_id')
    @classmethod
    def validate_project_id(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('project_id 只能包含字母、数字、下划线、连字符')
        return v


class IdeaGenerateRequest(BaseV2Request):
    """M1: 灵感生成请求"""
    user_input: str = Field('', min_length=1, max_length=2000)
    genre_hint: str = Field('', max_length=100)
    count: int = Field(default=5, ge=1, le=10)
    style_profile: Optional[Dict[str, Any]] = None


class IdeaScoreRequest(BaseV2Request):
    """M1: 灵感评分请求"""
    ideas: List[Dict[str, Any]] = Field(..., min_length=1, max_length=10)


class IdeaUpgradeRequest(BaseV2Request):
    """M1: 灵感升级请求"""
    ideas: List[Dict[str, Any]] = Field(..., min_length=1, max_length=3)


class IdeaAnalyzeRisksRequest(BaseV2Request):
    """M1: 灵感风险分析请求"""
    concept: str = Field(..., min_length=1, max_length=500)
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProjectAnalyzeRequest(BaseV2Request):
    """M2: 项目定位分析请求"""
    idea: str = Field(..., min_length=1, max_length=2000)
    platform: str = Field('fanqie', max_length=50)
    batch_index: int = Field(0, ge=0, le=2)


class ProjectCheckCompatibilityRequest(BaseV2Request):
    """M2: 平台兼容性检查请求"""
    idea: str = Field('', max_length=2000)
    platform: str = Field('fanqie', max_length=50)


class ProjectDeriveFieldsRequest(BaseV2Request):
    """M2: 衍生字段生成请求"""
    project_data: Dict[str, Any] = Field(default_factory=dict)


class WorldOriginRequest(BaseV2Request):
    """M3: 世界观本源生成请求"""
    idea: str = Field('', max_length=2000)
    genre: str = Field('', max_length=100)
    style_profile: Optional[Dict[str, Any]] = None


class WorldRulesRequest(BaseV2Request):
    """M3: 世界观规则生成请求"""
    origin: Optional[Dict[str, Any]] = Field(default_factory=dict)
    power_system: Optional[Dict[str, Any]] = None


class WorldStructureRequest(BaseV2Request):
    """M3: 世界观结构生成请求"""
    origin: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorldCivilizationRequest(BaseV2Request):
    """M3: 世界观文明生成请求"""
    structure: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorldHistoryRequest(BaseV2Request):
    """M3: 世界观历史生成请求"""
    structure: Optional[Dict[str, Any]] = Field(default_factory=dict)
    civilization: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WorldCheckConsistencyRequest(BaseV2Request):
    """M3: 世界观一致性检查请求"""
    world_data: Dict[str, Any] = Field(default_factory=dict)


class WorldSaveRequest(BaseV2Request):
    """M3: 世界观保存请求"""
    world_data: Dict[str, Any] = Field(default_factory=dict)


class CharacterProtagonistRequest(BaseV2Request):
    """M4: 主角生成请求"""
    world_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    story_concept: str = Field('', max_length=1000)
    style_profile: Optional[Dict[str, Any]] = None


class CharacterSupportingRequest(BaseV2Request):
    """M4: 配角生成请求"""
    protagonist: Optional[Dict[str, Any]] = Field(default_factory=dict)
    count: int = Field(default=4, ge=1, le=20)


class CharacterAntagonistsRequest(BaseV2Request):
    """M4: 反派生成请求"""
    protagonist: Optional[Dict[str, Any]] = Field(default_factory=dict)
    world: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CharacterRelationsRequest(BaseV2Request):
    """M4: 角色关系生成请求"""
    characters: List[Dict[str, Any]] = Field(..., min_length=1)


class CharacterCheckConsistencyRequest(BaseV2Request):
    """M4: 角色一致性检查请求"""
    characters: List[Dict[str, Any]] = Field(default_factory=list)


class StoryMasterRequest(BaseV2Request):
    """M5: 故事总纲生成请求"""
    protagonist: Optional[Dict[str, Any]] = Field(default_factory=dict)
    world: Optional[Dict[str, Any]] = Field(default_factory=dict)
    characters: Optional[List[str]] = Field(default_factory=list)
    style_profile: Optional[Dict[str, Any]] = None


class StoryVolumesRequest(BaseV2Request):
    """M5: 卷纲生成请求"""
    master_story: Optional[Dict[str, Any]] = Field(default_factory=dict)
    volume_count: int = Field(default=3, ge=1, le=20)


class StoryCheckConsistencyRequest(BaseV2Request):
    """M5: 故事一致性检查请求"""
    story_data: Dict[str, Any] = Field(default_factory=dict)
    characters: List[Dict[str, Any]] = Field(default_factory=list)


# ========== 结构层请求模型 ==========

class PowerSystemGenerateRequest(BaseV2Request):
    """M6: 力量体系生成请求"""
    world_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)
    character_abilities: Optional[List[Dict[str, Any]]] = None


class PowerSystemSaveRequest(BaseV2Request):
    """M6: 力量体系保存请求"""
    data: Dict[str, Any] = Field(default_factory=dict)


class FactionsGenerateRequest(BaseV2Request):
    """M7: 势力生成请求"""
    civilization: Optional[Dict[str, Any]] = Field(default_factory=dict)
    characters: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class FactionsSaveRequest(BaseV2Request):
    """M7: 势力保存请求"""
    factions: List[Dict[str, Any]] = Field(default_factory=list)


class TimelineBuildRequest(BaseV2Request):
    """M8: 时间线构建请求"""
    world_history: Optional[Dict[str, Any]] = Field(default_factory=dict)
    story_events: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class TimelineSaveRequest(BaseV2Request):
    """M8: 时间线保存请求"""
    data: Dict[str, Any] = Field(default_factory=dict)


class OutlineMasterRequest(BaseV2Request):
    """M9: 全书大纲生成请求"""
    story_system: Optional[Dict[str, Any]] = Field(default_factory=dict)
    volumes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class OutlineSaveRequest(BaseV2Request):
    """M9: 全书大纲保存请求"""
    data: Dict[str, Any] = Field(default_factory=dict)


class VolumeGenerateRequest(BaseV2Request):
    """M10: 单卷生成请求"""
    volume_no: int = Field(..., ge=1, le=100)
    master_outline: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VolumeGenerateBatchRequest(BaseV2Request):
    """M10: 批量卷生成请求"""
    count: int = Field(..., ge=1, le=20)
    master_outline: Optional[Dict[str, Any]] = Field(default_factory=dict)
    world: Optional[Dict[str, Any]] = Field(default_factory=dict)
    characters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VolumeSaveRequest(BaseV2Request):
    """M10: 卷纲保存请求"""
    volume_no: int = Field(default=1, ge=1, le=100)
    data: Dict[str, Any] = Field(default_factory=dict)


class PlotNodesGenerateRequest(BaseV2Request):
    """M11: 剧情节点生成请求"""
    chapter_plan: Optional[Dict[str, Any]] = Field(default_factory=dict)
    master_outline: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PlotNodesSaveRequest(BaseV2Request):
    """M11: 剧情节点保存请求"""
    event_id: str = Field('', max_length=100)
    data: Dict[str, Any] = Field(default_factory=dict)


class ChaptersPlanRequest(BaseV2Request):
    """M12: 章节规划请求"""
    master_outline: Optional[Dict[str, Any]] = Field(default_factory=dict)
    plot_events: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    target_wordcount: int = Field(default=2000, ge=500, le=10000)


class ChaptersPlanSaveRequest(BaseV2Request):
    """M12: 章节规划保存请求"""
    chapter_no: str = Field(default='1', max_length=5)
    data: Dict[str, Any] = Field(default_factory=dict)


class ChaptersOutlineRequest(BaseV2Request):
    """M13: 章节细纲生成请求"""
    chapter_no: str = Field(..., max_length=5)
    chapter_plan: Optional[Dict[str, Any]] = Field(default_factory=dict)
    foreshadow_plan: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    knowledge_state: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChaptersOutlineBatchRequest(BaseV2Request):
    """M13: 批量章节细纲生成请求"""
    total_chapters: int = Field(..., ge=1)
    chapter_plan: Optional[Dict[str, Any]] = Field(default_factory=dict)
    foreshadow_plan: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    knowledge_state: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChaptersOutlineSaveRequest(BaseV2Request):
    """M13: 章节细纲保存请求"""
    chapter_no: str = Field(..., max_length=5)
    data: Dict[str, Any] = Field(default_factory=dict)


# ========== 执行层请求模型 ==========

class ScenesDesignRequest(BaseV2Request):
    """M14: 场景设计请求"""
    chapter_outline: Optional[Dict[str, Any]] = Field(default_factory=dict)
    foreshadow_plan: Optional[Any] = None
    power_system: Optional[Dict[str, Any]] = None
    characters: Optional[List[Dict[str, Any]]] = None


class ScenesSaveRequest(BaseV2Request):
    """M14: 场景保存请求"""
    scene_id: str = Field('', max_length=100)
    data: Dict[str, Any] = Field(default_factory=dict)


class DraftGenerateRequest(BaseV2Request):
    """M15: 正文生成请求"""
    chapter_no: str = Field(..., max_length=5)
    scene_skeleton: Optional[Dict[str, Any]] = Field(default_factory=dict)
    constraints: Optional[Dict[str, Any]] = None


class DraftSaveRequest(BaseV2Request):
    """M15: 正文保存请求"""
    chapter_no: str = Field(..., max_length=5)
    content: str = Field(default='', min_length=1, max_length=50000)


class PolishRequest(BaseV2Request):
    """M16: 润色请求"""
    content: str = Field(..., min_length=1, max_length=50000)
    focus: str = Field('整体优化', max_length=200)
    style_profile: Optional[Dict[str, Any]] = None
    foreshadow_protected: Optional[List[str]] = None


class ContentParseRequest(BaseV2Request):
    """M17: 内容解析请求"""
    chapter_no: str = Field(..., max_length=5)
    content: str = Field(..., min_length=1, max_length=50000)
    existing_characters: Optional[List[Dict[str, Any]]] = None


class KnowledgeUpdateRequest(BaseV2Request):
    """M18: 知识库更新请求"""
    chapter_no: str = Field(..., max_length=5)
    parse_result: Dict[str, Any] = Field(default_factory=dict)


class ConsistencyCheckRequest(BaseV2Request):
    """M19: 一致性检查请求"""
    chapter_no: str = Field("1", max_length=5)
    content: Optional[str] = Field(default=None, min_length=1, max_length=50000)
    knowledge_state: Optional[Dict[str, Any]] = None
    characters: Optional[List[Dict[str, Any]]] = None
    world: Optional[Dict[str, Any]] = None
    power_system: Optional[Dict[str, Any]] = None


# ========== 流水线请求模型 ==========

class PipelineGenerateRequest(BaseV2Request):
    """流水线生成请求"""
    user_input: str = Field('', min_length=1, max_length=2000)
    genre_hint: str = Field('', max_length=100)
    platform: str = Field('fanqie', max_length=50)


class SettingsModel(BaseModel):
    """单个模型配置"""
    id: str = Field(..., max_length=200)
    name: str = Field(..., min_length=1, max_length=200)
    endpoint: str = Field(..., min_length=1, max_length=500)
    apiKey: str = Field(..., min_length=1, max_length=500)
    model: str = Field(..., min_length=1, max_length=200)


class SettingsSaveModelsRequest(BaseModel):
    """保存模型配置请求 (全局设置，不需要 project_id)"""
    models: List[SettingsModel] = Field(default_factory=list, max_length=50)
    activeModelId: str = Field(default='', max_length=200)


class ModuleStatusUpdateRequest(BaseModel):
    """模块状态更新请求"""
    status: str = Field(..., pattern='^(pending|generating|done|failed|locked)$')
    error: Optional[str] = None
    consistency_score: Optional[float] = None


class IdeaConfirmRequest(BaseModel):
    """灵感确认请求"""
    idea_id: Optional[str] = None
    idea: Optional[str] = None
    version: int = Field(default=1, ge=1)


class TemplateCreateRequest(BaseModel):
    """创建灵感模板请求"""
    project_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = Field(default='💡', max_length=4)
    genre: str = Field(..., min_length=1, max_length=20)
    prompt: str = Field(..., min_length=10, max_length=2000)
    reference: Optional[str] = Field(default='', max_length=200)


class TemplateUpdateRequest(BaseModel):
    """更新灵感模板请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    icon: Optional[str] = Field(default=None, max_length=4)
    genre: Optional[str] = Field(default=None, min_length=1, max_length=20)
    prompt: Optional[str] = Field(default=None, min_length=10, max_length=2000)
    reference: Optional[str] = Field(default=None, max_length=200)
