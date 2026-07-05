"""V2 结构层+规划层 API — M6-M13 REST端点"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.structure_service import (
    PowerSystemService, FactionService, TimelineService,
    MasterOutlineService, VolumeService, PlotNodeService,
    ChapterPlanService, ChapterOutlineService,
)

logger = logging.getLogger('novel_creator.api.v2.structure')

router = APIRouter(prefix="/api/v2", tags=["V2结构层+规划层"])


# ========== M6: 力量体系 ==========

@router.post("/power-system/generate")
async def power_generate(payload: dict):
    """POST /api/v2/power-system/generate — 完整力量体系"""
    result, err = PowerSystemService.generate(
        payload.get('project_id', ''),
        payload.get('world_rules', {}),
        payload.get('character_abilities'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/power-system/save")
async def power_save(payload: dict):
    """POST /api/v2/power-system/save"""
    result, err = PowerSystemService.save(
        payload.get('project_id', ''), payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M7: 势力体系 ==========

@router.post("/factions/generate")
async def factions_generate(payload: dict):
    """POST /api/v2/factions/generate"""
    result, err = FactionService.generate(
        payload.get('project_id', ''),
        payload.get('civilization', {}),
        payload.get('characters'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/factions/save")
async def factions_save(payload: dict):
    """POST /api/v2/factions/save"""
    result, err = FactionService.save(
        payload.get('project_id', ''), payload.get('factions', []),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M8: 时间线 ==========

@router.post("/timeline/build")
async def timeline_build(payload: dict):
    """POST /api/v2/timeline/build"""
    result, err = TimelineService.build(
        payload.get('project_id', ''),
        payload.get('world_history', {}),
        payload.get('story_events', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/timeline/save")
async def timeline_save(payload: dict):
    """POST /api/v2/timeline/save"""
    result, err = TimelineService.save(
        payload.get('project_id', ''), payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M9: 全书大纲 ==========

@router.post("/outline/master")
async def outline_master(payload: dict):
    """POST /api/v2/outline/master"""
    result, err = MasterOutlineService.generate(
        payload.get('project_id', ''),
        payload.get('story_system', {}),
        payload.get('volumes'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/outline/save")
async def outline_save(payload: dict):
    """POST /api/v2/outline/save"""
    result, err = MasterOutlineService.save(
        payload.get('project_id', ''), payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M10: 卷纲 ==========

@router.post("/volumes/generate")
async def volumes_generate(payload: dict):
    """POST /api/v2/volumes/generate"""
    result, err = VolumeService.generate(
        payload.get('project_id', ''),
        payload.get('volume_no', 1),
        payload.get('master_outline', {}),
        payload.get('world'),
        payload.get('characters'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/volumes/save")
async def volumes_save(payload: dict):
    """POST /api/v2/volumes/save"""
    result, err = VolumeService.save(
        payload.get('project_id', ''),
        payload.get('volume_no', 1),
        payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M11: 剧情节点 ==========

@router.post("/plot-nodes/generate")
async def plot_nodes_generate(payload: dict):
    """POST /api/v2/plot-nodes/generate"""
    result, err = PlotNodeService.generate(
        payload.get('project_id', ''),
        payload.get('chapter_plan', {}),
        payload.get('master_outline', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/plot-nodes/save")
async def plot_nodes_save(payload: dict):
    """POST /api/v2/plot-nodes/save"""
    result, err = PlotNodeService.save(
        payload.get('project_id', ''),
        payload.get('event_id', ''),
        payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M12: 章节规划 ==========

@router.post("/chapters/plan")
async def chapters_plan(payload: dict):
    """POST /api/v2/chapters/plan"""
    result, err = ChapterPlanService.plan(
        payload.get('project_id', ''),
        payload.get('master_outline', {}),
        payload.get('plot_events', []),
        payload.get('target_wordcount', 2000),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/chapters/plan-save")
async def chapters_plan_save(payload: dict):
    """POST /api/v2/chapters/plan-save"""
    result, err = ChapterPlanService.save(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M13: 章节细纲 ==========

@router.post("/chapters/outline")
async def chapters_outline_generate(payload: dict):
    """POST /api/v2/chapters/outline"""
    result, err = ChapterOutlineService.generate(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('chapter_plan', {}),
        payload.get('foreshadow_plan'),
        payload.get('knowledge_state'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/chapters/outline-save")
async def chapters_outline_save(payload: dict):
    """POST /api/v2/chapters/outline-save"""
    result, err = ChapterOutlineService.save(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result
