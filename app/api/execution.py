"""V2 执行层 API — M14-M19 REST端点"""
import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.execution_service import (
    SceneService, DraftService, PolishService,
    ContentParserService, KnowledgeService, ConsistencyService,
)
from app.utils.errors import safe_error as _safe_error, categorize_error as _categorize_error
from app.models.v2_schemas import (
    ScenesDesignRequest, ScenesSaveRequest,
    DraftGenerateRequest, DraftSaveRequest,
    PolishRequest, ContentParseRequest,
    KnowledgeUpdateRequest, ConsistencyCheckRequest,
)

logger = logging.getLogger('novel_creator.api.v2.execution')

router = APIRouter(prefix="/api/v2", tags=["V2执行层"])


# ========== 世界观一致性检查 ==========

@router.get("/world/{project_id}/consistency-check")
def world_consistency_check(project_id: str):
    """GET /api/v2/world/{project_id}/consistency-check"""
    result, err = ConsistencyService.world_check(project_id)
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return {"passed": result.get("passed", False), "message": result.get("message", "世界观一致性检查完成"), "data": result}


# ========== 角色一致性检查 ==========

@router.get("/character/{project_id}/consistency-check")
def character_consistency_check(project_id: str):
    """GET /api/v2/character/{project_id}/consistency-check"""
    result, err = ConsistencyService.character_check(project_id)
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return {"passed": result.get("passed", False), "message": result.get("message", "角色一致性检查完成"), "data": result}


# ========== M14: 场景设计 ==========

@router.post("/scenes/design")
def scenes_design(payload: ScenesDesignRequest):
    """POST /api/v2/scenes/design"""
    result, err = SceneService.design(
        payload.project_id,
        payload.chapter_outline,
        payload.foreshadow_plan,
        payload.power_system,
        payload.characters,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.post("/scenes/save")
def scenes_save(payload: ScenesSaveRequest):
    """POST /api/v2/scenes/save"""
    result, err = SceneService.save(
        payload.project_id,
        payload.scene_id,
        payload.data,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M15: 正文生成 (流式) ==========

@router.post("/draft/generate")
def draft_generate(payload: DraftGenerateRequest):
    """POST /api/v2/draft/generate — 流式正文生成"""

    def generate():
        try:
            for chunk in DraftService.generate_stream(
                payload.project_id,
                str(payload.chapter_no),
                payload.scene_skeleton,
                payload.constraints,
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Draft generation error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': _safe_error(str(e))})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/draft/save")
def draft_save(payload: DraftSaveRequest):
    """POST /api/v2/draft/save"""
    result, err = DraftService.save(
        payload.project_id,
        payload.chapter_no,
        {'content': payload.content},
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M16: 润色 ==========

@router.post("/polish")
def polish(payload: PolishRequest):
    """POST /api/v2/polish"""
    result, err = PolishService.polish(
        payload.project_id,
        payload.content,
        payload.style_profile,
        payload.focus,
        payload.foreshadow_protected,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M17: 内容解析 ==========

@router.post("/content/parse")
def content_parse(payload: ContentParseRequest):
    """POST /api/v2/content/parse"""
    result, err = ContentParserService.parse(
        payload.project_id,
        payload.chapter_no,
        payload.content,
        payload.existing_characters,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M18: 知识库 ==========

@router.post("/knowledge/update")
def knowledge_update(payload: KnowledgeUpdateRequest):
    """POST /api/v2/knowledge/update"""
    result, err = KnowledgeService.update(
        payload.project_id,
        payload.chapter_no,
        payload.parse_result,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.get("/knowledge/snapshot")
def knowledge_snapshot(project_id: str):
    """GET /api/v2/knowledge/snapshot?project_id=xxx"""
    result, err = KnowledgeService.snapshot(project_id)
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.get("/knowledge/foreshadows")
def knowledge_foreshadows(project_id: str, status: str = None):
    """GET /api/v2/knowledge/foreshadows?project_id=xxx"""
    result, err = KnowledgeService.get_foreshadows(project_id, status)
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


# ========== M19: 一致性检查 ==========

@router.post("/consistency/check")
def consistency_check(payload: ConsistencyCheckRequest):
    """POST /api/v2/consistency/check"""
    result, err = ConsistencyService.check(
        payload.project_id,
        payload.chapter_no,
        payload.content,
        payload.knowledge_state,
        payload.characters,
        payload.world,
        payload.power_system,
    )
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result


@router.get("/consistency/report")
def consistency_report(project_id: str, chapter_no: str = None):
    """GET /api/v2/consistency/report?project_id=xxx"""
    result, err = ConsistencyService.get_report(project_id, chapter_no)
    if err:
        msg, status = _categorize_error(err)
        raise HTTPException(status, msg)
    return result
