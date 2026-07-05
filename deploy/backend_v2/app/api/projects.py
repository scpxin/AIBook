import os
import re
import time
import uuid
import json
from typing import Optional
from fastapi import APIRouter
from app.models.schemas import ProjectSaveRequest
from app.database import novel_db
from app.config import PROJECT_ID_PATTERN, PROJECTS_DIR

router = APIRouter()


def validate_project_id(project_id: str) -> bool:
    return bool(project_id and re.match(PROJECT_ID_PATTERN, project_id))


@router.post("/api/projects/save")
async def project_save(body: ProjectSaveRequest):
    project_id = body.id or ('proj_' + uuid.uuid4().hex[:12])
    if not validate_project_id(project_id):
        return {"error": "无效的项目ID"}
    name = body.name.strip() or '未命名项目'
    data = body.data if isinstance(body.data, dict) else {}
    step = min(body.step, 10)
    tags = body.tags
    if len(json.dumps(data, ensure_ascii=False)) > 10 * 1024 * 1024:
        return {"error": "项目数据过大（上限10MB）"}
    novel_db.save_project(project_id, name, step, data, tags)
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    return {"ok": True, "id": project_id, "name": name, "updated_at": now}


@router.post("/api/projects/list")
async def projects_list():
    projects = novel_db.list_projects()
    return {"projects": projects}


@router.post("/api/projects/load")
async def project_load(body: dict):
    project_id = body.get('id', '')
    if not validate_project_id(project_id):
        return {"error": "无效的项目ID"}
    project = novel_db.get_project(project_id)
    if not project:
        filepath = os.path.join(PROJECTS_DIR, project_id + '.json')
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    old = json.load(f)
                novel_db.save_project(project_id, old.get('name', '未命名'),
                                     old.get('step', 0), old.get('data', {}))
                project = novel_db.get_project(project_id)
            except (json.JSONDecodeError, IOError, KeyError):
                pass
    if project:
        return project
    return {"error": "项目不存在"}


@router.post("/api/projects/delete")
async def project_delete(body: dict):
    project_id = body.get('id', '')
    if not validate_project_id(project_id):
        return {"error": "无效的项目ID"}
    project = novel_db.get_project(project_id)
    if not project:
        return {"error": "项目不存在"}
    novel_db.delete_project_cascade(project_id)
    return {"ok": True}
