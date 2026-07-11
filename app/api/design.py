"""V2 设计层 API — M1-M5 五个设计模块的REST端点"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.design_service import (
    IdeaService, ProjectService, WorldService,
    CharacterService, StoryService,
)
from app.services.novel_generator import parse_style_profile
from app.utils.errors import safe_error as _safe_error
from app.models.v2_schemas import (
    IdeaGenerateRequest, IdeaScoreRequest, IdeaUpgradeRequest,
    IdeaAnalyzeRisksRequest, ProjectAnalyzeRequest,
    ProjectCheckCompatibilityRequest,
    WorldOriginRequest, WorldRulesRequest, WorldStructureRequest,
    WorldCivilizationRequest, WorldHistoryRequest,
    WorldCheckConsistencyRequest, WorldSaveRequest,
    CharacterProtagonistRequest, CharacterSupportingRequest,
    CharacterAntagonistsRequest, CharacterRelationsRequest,
    CharacterCheckConsistencyRequest,
    StoryMasterRequest as StoryMasterServiceRequest, StoryVolumesRequest,
    StoryCheckConsistencyRequest,
)

logger = logging.getLogger('novel_creator.api.v2.design')

router = APIRouter(prefix="/api/v2", tags=["V2设计层"])


def _get_style(style_profile) -> Optional[dict]:
    """解析风格参数"""
    if style_profile is None:
        return None
    if isinstance(style_profile, dict):
        return style_profile
    return parse_style_profile(style_profile)


# ========== M1: 灵感 ==========

@router.post("/ideas/generate")
def idea_generate(payload: IdeaGenerateRequest):
    """POST /api/v2/ideas/generate — 发散生成N个创意"""
    result, err = IdeaService.generate(
        project_id=payload.project_id,
        user_input=payload.user_input,
        genre_hint=payload.genre_hint,
        style_profile=_get_style(payload.style_profile),
        count=payload.count,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/ideas/score")
def idea_score(payload: IdeaScoreRequest):
    """POST /api/v2/ideas/score — 创意评分"""
    result, err = IdeaService.score(payload.project_id, payload.ideas)
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/ideas/upgrade")
def idea_upgrade(payload: IdeaUpgradeRequest):
    """POST /api/v2/ideas/upgrade — TOP3创意升级"""
    result, err = IdeaService.upgrade(payload.project_id, payload.ideas)
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/ideas/analyze-risks")
def idea_analyze_risks(payload: IdeaAnalyzeRisksRequest):
    """POST /api/v2/ideas/analyze-risks — 风险分析"""
    result, err = IdeaService.analyze_risks(payload.project_id, payload.concept, **(payload.extra or {}))
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


# ========== M2: 项目定位 ==========

@router.post("/projects/analyze-batch")
def project_analyze_batch(payload: ProjectAnalyzeRequest):
    """POST /api/v2/projects/analyze-batch — 分批项目策划(每批4维度)"""
    if payload.batch_index < 0 or payload.batch_index > 2:
        raise HTTPException(400, "batch_index必须在0-2之间")
    result, err = ProjectService.analyze_batch(
        project_id=payload.project_id,
        idea=payload.idea,
        platform=payload.platform,
        batch_index=payload.batch_index,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/projects/analyze")
def project_analyze(payload: ProjectAnalyzeRequest):
    """POST /api/v2/projects/analyze — 12维度项目策划"""
    result, err = ProjectService.analyze(
        project_id=payload.project_id,
        idea=payload.idea,
        platform=payload.platform,
        style_profile=None,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return _adapt_novel_position(result)


def _adapt_novel_position(data: dict) -> dict:
    """将后端snake_case嵌套格式转为前端camelCase扁平格式"""
    if not isinstance(data, dict):
        return data
    key_map = {
        'target_audience': 'targetAudience',
        'core_hook': 'coreHook',
        'novelty_angle': 'noveltyAngle',
        'emotional_resonance': 'emotionalResonance',
        'update_strategy': 'updateStrategy',
        'title_direction': 'titleDirection',
        'cover_concept': 'coverConcept',
        'opener_strategy': 'openerStrategy',
        'main_conflict': 'mainConflict',
        'subplot_count': 'subplotCount',
        'climax_pattern': 'climaxPattern',
        'ending_direction': 'endingDirection',
    }
    adapted = {}
    for key, val in data.items():
        new_key = key_map.get(key, key)
        if isinstance(val, dict) and 'content' in val:
            adapted[new_key] = val['content']
        else:
            adapted[new_key] = val
    return adapted


@router.post("/projects/check-compatibility")
def project_check_compatibility(payload: ProjectCheckCompatibilityRequest):
    """POST /api/v2/projects/check-compatibility — 平台兼容性"""
    result, err = ProjectService.check_compatibility(
        payload.project_id,
        payload.idea,
        payload.platform,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


# ========== M3: 世界观 ==========

@router.post("/world/origin")
def world_origin(payload: WorldOriginRequest):
    """POST /api/v2/world/origin — 世界本源设计"""
    result, err = WorldService.design_origin(
        payload.project_id, payload.idea,
        payload.genre, _get_style(payload.style_profile),
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/rules")
def world_rules(payload: WorldRulesRequest):
    """POST /api/v2/world/rules — 世界规则设计"""
    result, err = WorldService.design_rules(
        payload.project_id, payload.origin or {},
        payload.power_system,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/structure")
def world_structure(payload: WorldStructureRequest):
    """POST /api/v2/world/structure — 世界结构设计"""
    result, err = WorldService.design_structure(
        payload.project_id, payload.origin or {},
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/civilization")
def world_civilization(payload: WorldCivilizationRequest):
    """POST /api/v2/world/civilization — 文明体系设计"""
    result, err = WorldService.design_civilization(
        payload.project_id, payload.structure or {},
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/history")
def world_history(payload: WorldHistoryRequest):
    """POST /api/v2/world/history — 历史时间线设计"""
    result, err = WorldService.design_history(
        payload.project_id, payload.structure or {},
        payload.civilization or {},
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/check-consistency")
def world_check_consistency(payload: WorldCheckConsistencyRequest):
    """POST /api/v2/world/check-consistency — 世界一致性"""
    result, err = WorldService.check_consistency(
        payload.project_id, payload.world_data,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/world/save")
def world_save(payload: WorldSaveRequest):
    """POST /api/v2/world/save — 完整世界观保存"""
    result, err = WorldService.save_world(
        payload.project_id, payload.world_data,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


# ========== M4: 角色系统 ==========

@router.post("/characters/protagonist")
def char_protagonist(payload: CharacterProtagonistRequest):
    """POST /api/v2/characters/protagonist — 主角九维档案"""
    result, err = CharacterService.generate_protagonist(
        payload.project_id,
        payload.world_rules or {},
        payload.story_concept,
        _get_style(payload.style_profile),
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/characters/supporting")
def char_supporting(payload: CharacterSupportingRequest):
    """POST /api/v2/characters/supporting — 配角设计"""
    result, err = CharacterService.generate_supporting(
        payload.project_id, payload.protagonist or {},
        payload.count,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/characters/antagonists")
def char_antagonists(payload: CharacterAntagonistsRequest):
    """POST /api/v2/characters/antagonists — 反派体系"""
    result, err = CharacterService.generate_antagonists(
        payload.project_id, payload.protagonist or {},
        payload.world or {},
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/characters/relations")
def char_relations(payload: CharacterRelationsRequest):
    """POST /api/v2/characters/relations — 关系网络"""
    result, err = CharacterService.generate_relations(
        payload.project_id, payload.characters,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/characters/check-consistency")
def char_check_consistency(payload: CharacterCheckConsistencyRequest):
    """POST /api/v2/characters/check-consistency — 角色一致性"""
    result, err = CharacterService.check_consistency(
        payload.project_id, payload.characters,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


# ========== M5: 故事体系 ==========

@router.post("/story/master")
def story_master(payload: StoryMasterServiceRequest):
    """POST /api/v2/story/master — 总纲设计"""
    result, err = StoryService.generate_master(
        payload.project_id,
        payload.protagonist or {},
        payload.world or {},
        payload.characters or [],
        _get_style(payload.style_profile),
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/story/volumes")
def story_volumes(payload: StoryVolumesRequest):
    """POST /api/v2/story/volumes — 卷纲生成"""
    result, err = StoryService.generate_volumes(
        payload.project_id, payload.master_story or {},
        payload.volume_count,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result


@router.post("/story/check-consistency")
def story_check_consistency(payload: StoryCheckConsistencyRequest):
    """POST /api/v2/story/check-consistency — 故事一致性"""
    result, err = StoryService.check_consistency(
        payload.project_id, payload.story_data,
        payload.characters,
    )
    if err:
        raise HTTPException(400, _safe_error(err))
    return result
