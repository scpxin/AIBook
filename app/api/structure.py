"""V2 结构层+规划层 API — M6-M13 REST端点"""
import logging

from fastapi import APIRouter, HTTPException

from app.utils.errors import safe_error as _safe_error, categorize_error as _categorize_error
from app.models.v2_schemas import (
    PowerSystemGenerateRequest, PowerSystemSaveRequest,
    FactionsGenerateRequest, FactionsSaveRequest,
    TimelineBuildRequest, TimelineSaveRequest,
    OutlineMasterRequest, OutlineSaveRequest,
    VolumeGenerateRequest, VolumeGenerateBatchRequest, VolumeSaveRequest,
    PlotNodesGenerateRequest, PlotNodesSaveRequest,
    ChaptersPlanRequest, ChaptersPlanSaveRequest,
    ChaptersOutlineRequest, ChaptersOutlineBatchRequest, ChaptersOutlineSaveRequest,
)
from app.services.structure_service import (
    PowerSystemService, FactionService, TimelineService,
    MasterOutlineService, VolumeService, PlotNodeService,
    ChapterPlanService, ChapterOutlineService,
)

logger = logging.getLogger('novel_creator.api.v2.structure')

router = APIRouter(prefix="/api/v2", tags=["V2结构层+规划层"])


# ========== M6: 力量体系 ==========

@router.post("/power-system/generate")
def power_generate(payload: PowerSystemGenerateRequest):
    """POST /api/v2/power-system/generate — 完整力量体系"""
    result, err = PowerSystemService.generate(
        payload.project_id,
        payload.world_rules,
        payload.character_abilities,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/power-system/save")
def power_save(payload: PowerSystemSaveRequest):
    """POST /api/v2/power-system/save"""
    result, err = PowerSystemService.save(
        payload.project_id, payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M7: 势力体系 ==========

@router.post("/factions/generate")
def factions_generate(payload: FactionsGenerateRequest):
    """POST /api/v2/factions/generate"""
    result, err = FactionService.generate(
        payload.project_id,
        payload.civilization,
        payload.characters,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/factions/save")
def factions_save(payload: FactionsSaveRequest):
    """POST /api/v2/factions/save"""
    result, err = FactionService.save(
        payload.project_id, payload.factions,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M8: 时间线 ==========

@router.post("/timeline/build")
def timeline_build(payload: TimelineBuildRequest):
    """POST /api/v2/timeline/build"""
    result, err = TimelineService.build(
        payload.project_id,
        payload.world_history,
        payload.story_events,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/timeline/save")
def timeline_save(payload: TimelineSaveRequest):
    """POST /api/v2/timeline/save"""
    result, err = TimelineService.save(
        payload.project_id, payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M9: 全书大纲 ==========

@router.post("/outline/master")
def outline_master(payload: OutlineMasterRequest):
    """POST /api/v2/outline/master"""
    result, err = MasterOutlineService.generate(
        payload.project_id,
        payload.story_system,
        payload.volumes,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    if isinstance(result, dict):
        if 'outline_content' in result and len(result) <= 2:
            inner = result['outline_content']
            if isinstance(inner, dict):
                return inner
        if 'master_outline' in result and len(result) <= 2:
            inner = result['master_outline']
            if isinstance(inner, dict):
                return inner
    return result


@router.post("/outline/save")
def outline_save(payload: OutlineSaveRequest):
    """POST /api/v2/outline/save"""
    result, err = MasterOutlineService.save(
        payload.project_id, payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M10: 卷纲 ==========

@router.post("/volumes/generate")
def story_volumes(payload: VolumeGenerateRequest):
    """POST /api/v2/volumes/generate — 卷纲生成"""
    result, err = VolumeService.generate_batch(
        payload.project_id,
        payload.volume_no if payload.volume_no is not None else 3,
        payload.master_outline,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    if isinstance(result, list):
        return {"volumes": result}
    return result


@router.post("/volumes/generate-batch")
def volumes_generate_batch(payload: VolumeGenerateBatchRequest):
    """POST /api/v2/volumes/generate-batch — 批量生成多卷"""
    result, err = VolumeService.generate_batch(
        payload.project_id,
        payload.count,
        payload.master_outline,
        payload.world,
        payload.characters,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/volumes/save")
def volumes_save(payload: VolumeSaveRequest):
    """POST /api/v2/volumes/save"""
    result, err = VolumeService.save(
        payload.project_id,
        payload.volume_no,
        payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M11: 剧情节点 ==========

@router.post("/plot-nodes/generate")
def plot_nodes_generate(payload: PlotNodesGenerateRequest):
    """POST /api/v2/plot-nodes/generate"""
    result, err = PlotNodeService.generate(
        payload.project_id,
        payload.chapter_plan,
        payload.master_outline,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/plot-nodes/save")
def plot_nodes_save(payload: PlotNodesSaveRequest):
    """POST /api/v2/plot-nodes/save"""
    result, err = PlotNodeService.save(
        payload.project_id,
        payload.event_id,
        payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M12: 章节规划 ==========

@router.post("/chapters/plan")
def chapters_plan(payload: ChaptersPlanRequest):
    """POST /api/v2/chapters/plan"""
    result, err = ChapterPlanService.plan(
        payload.project_id,
        payload.master_outline,
        payload.plot_events,
        payload.target_wordcount,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    if isinstance(result, dict) and 'chapter_plan' in result and len(result) <= 2:
        inner = result['chapter_plan']
        if isinstance(inner, dict):
            return inner
    return result


@router.post("/chapters/plan-save")
def chapters_plan_save(payload: ChaptersPlanSaveRequest):
    """POST /api/v2/chapters/plan-save"""
    result, err = ChapterPlanService.save(
        payload.project_id,
        payload.chapter_no,
        payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M13: 章节细纲 ==========

@router.post("/chapters/outline")
def chapters_outline_generate(payload: ChaptersOutlineRequest):
    """POST /api/v2/chapters/outline"""
    result, err = ChapterOutlineService.generate(
        payload.project_id,
        payload.chapter_no,
        payload.chapter_plan,
        payload.foreshadow_plan,
        payload.knowledge_state,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/chapters/outline-batch")
def chapters_outline_batch(payload: ChaptersOutlineBatchRequest):
    """POST /api/v2/chapters/outline-batch — 批量生成章纲"""
    result, err = ChapterOutlineService.generate_batch(
        payload.project_id,
        payload.total_chapters,
        payload.chapter_plan,
        payload.foreshadow_plan,
        payload.knowledge_state,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/chapters/outline-save")
def chapters_outline_save(payload: ChaptersOutlineSaveRequest):
    """POST /api/v2/chapters/outline-save"""
    result, err = ChapterOutlineService.save(
        payload.project_id,
        payload.chapter_no,
        payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result
