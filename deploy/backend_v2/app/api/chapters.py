import json
from fastapi import APIRouter
from app.models.schemas import (
    ChapterSaveRequest, ChapterGetRequest, ChapterDeleteRequest,
    ChapterRegenerateRequest, GenerationStatusRequest,
    GenerationStartRequest, GenerationPauseRequest, GenerationStopRequest,
    GenerationUpdateRequest
)
from app.database import novel_db

router = APIRouter()


@router.post("/api/chapters/save")
async def chapter_save(body: ChapterSaveRequest):
    metadata = body.metadata
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError, ValueError):
            metadata = None
    novel_db.save_chapter(
        project_id=body.projectId,
        chapter_number=body.chapterNumber,
        title=body.title,
        content=body.content,
        status=body.status,
        error_message=body.errorMessage,
        metadata=metadata,
    )
    return {"ok": True}


@router.post("/api/chapters/get")
async def chapter_get(body: dict):
    project_id = body.get('projectId', '')
    chapter_number = body.get('chapterNumber')
    if not project_id:
        return {"error": "缺少 projectId"}
    if chapter_number:
        ch = novel_db.get_chapter(project_id, chapter_number)
        return {"chapter": ch}
    else:
        chapters = novel_db.get_all_chapters(project_id)
        status = novel_db.get_generation_status(project_id)
        counts = novel_db.get_chapter_count(project_id)
        return {"chapters": chapters, "status": status, "counts": counts}


@router.post("/api/chapters/delete")
async def chapter_delete(body: ChapterDeleteRequest):
    novel_db.delete_chapter(body.projectId, body.chapterNumber)
    return {"ok": True}


@router.post("/api/chapters/regenerate")
async def chapter_regenerate(body: ChapterRegenerateRequest):
    novel_db.delete_chapter(body.projectId, body.chapterNumber)
    return {"ok": True}


@router.post("/api/chapters/status")
async def generation_status(body: dict):
    project_id = body.get('projectId', '')
    if not project_id:
        return {"error": "缺少 projectId"}
    status = novel_db.get_generation_status(project_id)
    counts = novel_db.get_chapter_count(project_id)
    pending = novel_db.get_pending_chapters(project_id, counts['total'])
    return {"status": status, "counts": counts, "pendingChapters": pending}


@router.post("/api/chapters/generation/start")
async def generation_start(body: dict):
    project_id = body.get('projectId', '')
    total_chapters = body.get('totalChapters', 0)
    if not project_id or not total_chapters:
        return {"error": "缺少参数"}
    config_keys = [k for k in ['endpoint', 'model', 'projectTitle', 'genre', 'styleProfile', 'bookOverview', 'targetWords', 'narrativePerspective', 'chapterCharacters'] if k in body]
    config = json.dumps({k: body[k] for k in config_keys})
    novel_db.start_generation(project_id, total_chapters, config)
    return {"ok": True}


@router.post("/api/chapters/generation/pause")
async def generation_pause(body: dict):
    project_id = body.get('projectId', '')
    if not project_id:
        return {"error": "缺少 projectId"}
    novel_db.pause_generation(project_id)
    return {"ok": True}


@router.post("/api/chapters/generation/stop")
async def generation_stop(body: dict):
    project_id = body.get('projectId', '')
    if not project_id:
        return {"error": "缺少 projectId"}
    novel_db.stop_generation(project_id)
    return {"ok": True}


@router.post("/api/chapters/generation/update")
async def generation_update(body: dict):
    project_id = body.get('projectId', '')
    current = body.get('currentChapter', 0)
    completed = body.get('completedChapters')
    failed = body.get('failedChapters')
    if not project_id:
        return {"error": "缺少 projectId"}
    novel_db.update_generation_progress(project_id, current, completed, failed)
    return {"ok": True}
