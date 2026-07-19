"""灵感模板API — 模板CRUD管理"""
import sqlite3

from fastapi import APIRouter, HTTPException

from app.models.v2_schemas import TemplateCreateRequest, TemplateUpdateRequest
from novel_creator.database_v2 import (
    create_idea_template,
    delete_idea_template,
    get_idea_templates,
    update_idea_template,
)

router = APIRouter(prefix="/api/v2/templates", tags=["灵感模板"])


@router.get("/{project_id}")
async def list_templates(project_id: str):
    templates = get_idea_templates(project_id)
    return {"templates": templates}


@router.post("/")
async def create(payload: TemplateCreateRequest):
    try:
        tpl = create_idea_template(
            project_id=payload.project_id,
            name=payload.name,
            genre=payload.genre,
            prompt=payload.prompt,
            icon=payload.icon or '💡',
            reference=payload.reference or '',
        )
        return {"ok": True, "template": tpl}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="模板名称已存在")


@router.put("/{template_id}")
async def update(template_id: int, payload: TemplateUpdateRequest):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="无更新内容")
    try:
        tpl = update_idea_template(template_id, **fields)
        if tpl is None:
            raise HTTPException(status_code=404, detail="模板不存在")
        return {"ok": True, "template": tpl}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}")
async def delete(template_id: int):
    ok = delete_idea_template(template_id)
    if not ok:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"ok": True}
