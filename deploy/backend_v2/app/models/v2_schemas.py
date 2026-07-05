"""V2 Pydantic 请求模型 — 为V2 API提供类型安全验证"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class IdeaConfirmRequest(BaseModel):
    idea_id: str
    version: int = 1


class CompatibilityCheckRequest(BaseModel):
    platform: str = Field(..., description="目标平台: fanqie/qidian/qimao/custom")


class ModuleStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="模块状态: pending/generating/done/failed/locked")
    error: Optional[str] = None
    consistency_score: Optional[float] = None


class PipelineGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1, description="用户输入创意描述")
    genre_hint: Optional[str] = None
    platform: Optional[str] = "fanqie"


class DraftGenerateRequest(BaseModel):
    chapter_no: str = Field(..., description="章节编号")
    scene_skeleton: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = 3000


class PolishRequest(BaseModel):
    content: str = Field(..., min_length=1, description="需要润色的内容")
    focus: Optional[str] = None


class ContentParseRequest(BaseModel):
    chapter_no: str
    content: str = Field(..., min_length=1, description="需要解析的正文内容")


class KnowledgeUpdateRequest(BaseModel):
    chapter_no: str
    parse_result: Dict[str, Any]


class ConsistencyCheckRequest(BaseModel):
    chapter_no: str = "1"
    content: Optional[str] = None
    character_states: Optional[Dict[str, Any]] = None
    world_state: Optional[Dict[str, Any]] = None


class ProjectPositionRequest(BaseModel):
    idea: str
    platform: str = "fanqie"


class WorldBuildRequest(BaseModel):
    origin: Optional[Dict[str, Any]] = None
    rules: Optional[List[Dict[str, Any]]] = None


class StoryMasterRequest(BaseModel):
    protagonist: Optional[Dict[str, Any]] = None
    world: Optional[Dict[str, Any]] = None
    characters: Optional[List[str]] = None
