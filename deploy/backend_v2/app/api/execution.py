"""V2 执行层 API — M14-M19 REST端点"""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.execution_service import (
    SceneService, DraftService, PolishService,
    ContentParserService, KnowledgeService, ConsistencyService,
)

logger = logging.getLogger('novel_creator.api.v2.execution')

router = APIRouter(prefix="/api/v2", tags=["V2执行层"])


# ========== 世界观一致性检查 ==========

@router.get("/world/{project_id}/consistency-check")
async def world_consistency_check(project_id: str):
    """GET /api/v2/world/{project_id}/consistency-check"""
    result, err = ConsistencyService.world_check(project_id)
    if err:
        raise HTTPException(500, err)
    return {"passed": True, "message": "世界观一致性检查通过", "data": result}


# ========== 角色一致性检查 ==========

@router.get("/character/{project_id}/consistency-check")
async def character_consistency_check(project_id: str):
    """GET /api/v2/character/{project_id}/consistency-check"""
    result, err = ConsistencyService.character_check(project_id)
    if err:
        raise HTTPException(500, err)
    return {"passed": True, "message": "角色一致性检查通过", "data": result}


# ========== 执行一致性检查 ==========

@router.post("/consistency/{project_id}/run")
async def run_consistency_check(project_id: str, payload: dict):
    """POST /api/v2/consistency/{project_id}/run"""
    result, err = ConsistencyService.check(
        project_id,
        str(payload.get('chapter_no', '1')),
        payload.get('content'),
        payload.get('knowledge_state'),
        payload.get('characters'),
        payload.get('world'),
        payload.get('power_system'),
    )
    if err:
        raise HTTPException(500, err)
    return {"success": True, "result": result}


# ========== M14: 场景设计 ==========

@router.post("/scenes/design")
async def scenes_design(payload: dict):
    """POST /api/v2/scenes/design"""
    result, err = SceneService.design(
        payload.get('project_id', ''),
        payload.get('chapter_outline', {}),
        payload.get('foreshadow_plan'),
        payload.get('power_system'),
        payload.get('characters'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.post("/scenes/save")
async def scenes_save(payload: dict):
    """POST /api/v2/scenes/save"""
    result, err = SceneService.save(
        payload.get('project_id', ''),
        payload.get('scene_id', ''),
        payload.get('data', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M15: 正文生成 (流式) ==========

@router.post("/draft/generate")
async def draft_generate(payload: dict):
    """POST /api/v2/draft/generate — 流式正文生成"""
    project_id = payload.get('project_id')
    if not project_id:
        raise HTTPException(400, "project_id required")

    def generate():
        for chunk in DraftService.generate_stream(
            project_id,
            str(payload.get('chapter_no', '')),
            payload.get('scene_skeleton', {}),
            payload.get('constraints'),
        ):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/draft/save")
async def draft_save(payload: dict):
    """POST /api/v2/draft/save"""
    result, err = DraftService.save(
        payload.get('project_id', ''),
        payload.get('chapter_no', ''),
        payload.get('content', ''),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M16: 润色 ==========

@router.post("/polish")
async def polish(payload: dict):
    """POST /api/v2/polish"""
    result, err = PolishService.polish(
        payload.get('project_id', ''),
        payload.get('content', ''),
        payload.get('style_profile'),
        payload.get('focus', '整体优化'),
        payload.get('foreshadow_protected'),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M17: 内容解析 ==========

@router.post("/content/parse")
async def content_parse(payload: dict):
    """POST /api/v2/content/parse"""
    result, err = ContentParserService.parse(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('content', ''),
        payload.get('existing_characters'),
    )
    if err:
        raise HTTPException(500, err)
    return result


# ========== M18: 知识库 ==========

@router.post("/knowledge/update")
async def knowledge_update(payload: dict):
    """POST /api/v2/knowledge/update"""
    result, err = KnowledgeService.update(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('parse_result', {}),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.get("/knowledge/snapshot")
async def knowledge_snapshot(project_id: str):
    """GET /api/v2/knowledge/snapshot?project_id=xxx"""
    result, err = KnowledgeService.snapshot(project_id)
    if err:
        raise HTTPException(500, err)
    return result


@router.get("/knowledge/foreshadows")
async def knowledge_foreshadows(project_id: str, status: str = None):
    """GET /api/v2/knowledge/foreshadows?project_id=xxx"""
    result, err = KnowledgeService.get_foreshadows(project_id, status)
    if err:
        raise HTTPException(500, err)
    return result


# ========== M19: 一致性检查 ==========

@router.post("/consistency/check")
async def consistency_check(payload: dict):
    """POST /api/v2/consistency/check"""
    result, err = ConsistencyService.check(
        payload.get('project_id', ''),
        str(payload.get('chapter_no', '')),
        payload.get('content'),
        payload.get('knowledge_state'),
        payload.get('characters'),
        payload.get('world'),
        payload.get('power_system'),
    )
    if err:
        raise HTTPException(500, err)
    return result


@router.get("/consistency/report")
async def consistency_report(project_id: str, chapter_no: str = None):
    """GET /api/v2/consistency/report?project_id=xxx"""
    result, err = ConsistencyService.get_report(project_id, chapter_no)
    if err:
        raise HTTPException(500, err)
    return result
