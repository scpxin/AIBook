import json
from fastapi import APIRouter
from app.models.schemas import (
    OutlineSaveRequest, OutlineGetRequest, OutlineDeleteRequest,
    OutlineGenerationStartRequest
)
from app.database import novel_db

router = APIRouter()


@router.post("/api/outline/save")
async def outline_save(body: OutlineSaveRequest):
    novel_db.save_outline(
        project_id=body.projectId,
        chapter_number=body.chapterNumber,
        title=body.title,
        summary=body.summary,
        scenes=body.scenes,
        characters=body.characters,
        key_points=body.key_points,
        emotion=body.emotion,
        goal=body.goal,
        technique_focus=body.techniqueFocus,
        book_overview=body.bookOverview,
        chapter_hook=body.chapterHook,
        acts=body.acts,
        status=body.status,
        error_message=body.errorMessage,
    )
    return {"ok": True}


@router.post("/api/outline/get")
async def outline_get(body: dict):
    project_id = body.get('projectId', '')
    chapter_number = body.get('chapterNumber')
    if not project_id:
        return {"error": "缺少 projectId"}
    if chapter_number is not None:
        outline = novel_db.get_outline(project_id, chapter_number)
        return {"outline": outline}
    else:
        outlines = novel_db.get_all_outlines(project_id)
        status = novel_db.get_outline_generation_status(project_id)
        return {"outlines": outlines, "status": status}


@router.post("/api/outline/delete")
async def outline_delete(body: OutlineDeleteRequest):
    novel_db.delete_outline(body.projectId, body.chapterNumber)
    return {"ok": True}


@router.post("/api/outline/generation/start")
async def outline_generation_start(body: dict):
    project_id = body.get('projectId', '')
    total = body.get('totalChapters', 0)
    if not project_id:
        return {"error": "缺少 projectId"}
    config = {k: body[k] for k in ['endpoint', 'model', 'projectTitle', 'genre',
             'styleProfile', 'bookOverview', 'targetWords', 'narrativePerspective', 'chapterCharacters']
             if k in body}
    novel_db.start_outline_generation(project_id, total, json.dumps(config, ensure_ascii=False))
    return {"ok": True}


@router.post("/api/outline/generation/pause")
async def outline_generation_pause(body: dict):
    novel_db.pause_outline_generation(body.get('projectId', ''))
    return {"ok": True}


@router.post("/api/outline/generation/stop")
async def outline_generation_stop(body: dict):
    novel_db.stop_outline_generation(body.get('projectId', ''))
    return {"ok": True}


@router.post("/api/outline/generation/update")
async def outline_generation_update(body: dict):
    project_id = body.get('projectId', '')
    current = body.get('currentChapter', 0)
    completed = body.get('completedChapters')
    failed = body.get('failedChapters')
    if not project_id:
        return {"error": "缺少 projectId"}
    novel_db.update_outline_generation_progress(project_id, current, completed, failed)
    return {"ok": True}
