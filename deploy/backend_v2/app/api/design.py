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

logger = logging.getLogger('novel_creator.api.v2.design')

router = APIRouter(prefix="/api/v2", tags=["V2设计层"])


def _get_style(style_profile) -> Optional[dict]:
    """解析风格参数"""
    return parse_style_profile(style_profile)


# ========== M1: 灵感 ==========

@router.post("/ideas/generate")
async def idea_generate(payload: dict):
    """POST /api/v2/ideas/generate — 发散生成N个创意"""
    project_id = payload.get('project_id')
    user_input = payload.get('user_input', '')
    if not project_id:
        raise HTTPException(400, "project_id required")

    result, err = IdeaService.generate(
        project_id=project_id,
        user_input=user_input,
        genre_hint=payload.get('genre_hint', ''),
        style_profile=_get_style(payload.get('style_profile')),
        count=payload.get('count', 5),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/ideas/score")
async def idea_score(payload: dict):
    """POST /api/v2/ideas/score — 创意评分"""
    project_id = payload.get('project_id')
    ideas = payload.get('ideas', [])
    if not project_id or not ideas:
        raise HTTPException(400, "project_id and ideas required")

    result, err = IdeaService.score(project_id, ideas)
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/ideas/upgrade")
async def idea_upgrade(payload: dict):
    """POST /api/v2/ideas/upgrade — TOP3创意升级"""
    project_id = payload.get('project_id')
    ideas = payload.get('ideas', [])
    if not project_id or not ideas:
        raise HTTPException(400, "project_id and ideas required")

    result, err = IdeaService.upgrade(project_id, ideas)
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/ideas/analyze-risks")
async def idea_analyze_risks(payload: dict):
    """POST /api/v2/ideas/analyze-risks — 风险分析"""
    project_id = payload.get('project_id')
    concept = payload.get('concept', '')
    if not project_id or not concept:
        raise HTTPException(400, "project_id and concept required")

    result, err = IdeaService.analyze_risks(project_id, concept, **payload.get('extra', {}))
    if err:
        raise HTTPException(500, err)
    return result


# ========== M2: 项目定位 ==========

@router.post("/projects/analyze")
async def project_analyze(payload: dict):
    """POST /api/v2/projects/analyze — 12维度项目策划"""
    project_id = payload.get('project_id')
    idea = payload.get('idea', '')
    if not project_id or not idea:
        raise HTTPException(400, "project_id and idea required")

    result, err = ProjectService.analyze(
        project_id=project_id,
        idea=idea,
        platform=payload.get('platform', 'tomato'),
        style_profile=_get_style(payload.get('style_profile')),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/projects/check-compatibility")
async def project_check_compatibility(payload: dict):
    """POST /api/v2/projects/check-compatibility — 平台兼容性"""
    project_id = payload.get('project_id')
    result, err = ProjectService.check_compatibility(
        project_id,
        payload.get('idea', ''),
        payload.get('platform', 'tomato'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/projects/derive-fields")
async def project_derive_fields(payload: dict):
    """POST /api/v2/projects/derive-fields — 衍生字段计算"""
    project_id = payload.get('project_id')
    result, err = ProjectService.derive_fields(project_id, payload.get('project_data', {}))
    if err:
        raise HTTPException(500, err)
    return result


# ========== M3: 世界观 ==========

@router.post("/world/origin")
async def world_origin(payload: dict):
    """POST /api/v2/world/origin — 世界本源设计"""
    project_id = payload.get('project_id')
    result, err = WorldService.design_origin(
        project_id, payload.get('idea', ''),
        payload.get('genre', ''), _get_style(payload.get('style_profile')),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/rules")
async def world_rules(payload: dict):
    """POST /api/v2/world/rules — 世界规则设计"""
    project_id = payload.get('project_id')
    result, err = WorldService.design_rules(
        project_id, payload.get('origin', {}),
        payload.get('power_system'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/structure")
async def world_structure(payload: dict):
    """POST /api/v2/world/structure — 世界结构设计"""
    project_id = payload.get('project_id')
    result, err = WorldService.design_structure(
        project_id, payload.get('origin', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/civilization")
async def world_civilization(payload: dict):
    """POST /api/v2/world/civilization — 文明体系设计"""
    project_id = payload.get('project_id')
    result, err = WorldService.design_civilization(
        project_id, payload.get('structure', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/history")
async def world_history(payload: dict):
    """POST /api/v2/world/history — 历史时间线设计"""
    project_id = payload.get('project_id')
    result, err = WorldService.design_history(
        project_id, payload.get('structure', {}),
        payload.get('civilization', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/check-consistency")
async def world_check_consistency(payload: dict):
    """POST /api/v2/world/check-consistency — 世界一致性"""
    project_id = payload.get('project_id')
    result, err = WorldService.check_consistency(
        project_id, payload.get('world_data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/world/save")
async def world_save(payload: dict):
    """POST /api/v2/world/save — 完整世界观保存"""
    project_id = payload.get('project_id')
    result, err = WorldService.save_world(
        project_id, payload.get('world_data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M4: 角色系统 ==========

@router.post("/characters/protagonist")
async def char_protagonist(payload: dict):
    """POST /api/v2/characters/protagonist — 主角九维档案"""
    project_id = payload.get('project_id')
    result, err = CharacterService.generate_protagonist(
        project_id,
        payload.get('world_rules', {}),
        payload.get('story_concept', ''),
        _get_style(payload.get('style_profile')),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/characters/supporting")
async def char_supporting(payload: dict):
    """POST /api/v2/characters/supporting — 配角设计"""
    project_id = payload.get('project_id')
    result, err = CharacterService.generate_supporting(
        project_id, payload.get('protagonist', {}),
        payload.get('count', 5),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/characters/antagonists")
async def char_antagonists(payload: dict):
    """POST /api/v2/characters/antagonists — 反派体系"""
    project_id = payload.get('project_id')
    result, err = CharacterService.generate_antagonists(
        project_id, payload.get('protagonist', {}),
        payload.get('world', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/characters/relations")
async def char_relations(payload: dict):
    """POST /api/v2/characters/relations — 关系网络"""
    project_id = payload.get('project_id')
    result, err = CharacterService.generate_relations(
        project_id, payload.get('characters', []),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/characters/check-consistency")
async def char_check_consistency(payload: dict):
    """POST /api/v2/characters/check-consistency — 角色一致性"""
    project_id = payload.get('project_id')
    result, err = CharacterService.check_consistency(
        project_id, payload.get('characters', []),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M5: 故事体系 ==========

@router.post("/story/master")
async def story_master(payload: dict):
    """POST /api/v2/story/master — 总纲设计"""
    project_id = payload.get('project_id')
    result, err = StoryService.generate_master(
        project_id,
        payload.get('protagonist', {}),
        payload.get('world', {}),
        payload.get('characters', []),
        _get_style(payload.get('style_profile')),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/story/volumes")
async def story_volumes(payload: dict):
    """POST /api/v2/story/volumes — 卷纲生成"""
    project_id = payload.get('project_id')
    result, err = StoryService.generate_volumes(
        project_id, payload.get('master_story', {}),
        payload.get('volume_count', 5),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/story/check-consistency")
async def story_check_consistency(payload: dict):
    """POST /api/v2/story/check-consistency — 故事一致性"""
    project_id = payload.get('project_id')
    result, err = StoryService.check_consistency(
        project_id, payload.get('story_data', {}),
        payload.get('characters', []),
    )
    if err:
        raise HTTPException(500, err)
    return result
