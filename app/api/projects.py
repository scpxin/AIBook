import json
import logging
import re
import time
import uuid

from fastapi import APIRouter, HTTPException

from app.config import PROJECT_ID_PATTERN
from app.database import novel_db

router = APIRouter()
logger = logging.getLogger('novel_creator.api.projects')


def sanitize_project_name(name: str) -> str:
    """清理项目名，限制长度和字符集"""
    if not name or not name.strip():
        return '未命名项目'
    name = name.strip()[:64]
    # 移除控制字符和 HTML 标签
    name = re.sub(r'<[^>]+>', '', name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    return name or '未命名项目'


def validate_project_id(project_id: str) -> bool:
    """校验项目ID格式（字母数字+下划线+连字符，上限128字符）"""
    return bool(project_id and re.match(PROJECT_ID_PATTERN, project_id))


@router.post("/api/projects/save-v2")
def project_save_v2(body: dict):
    """保存V2项目全量数据：所有模块数据 + 流水线状态 + 模板选择 + 共享上下文"""
    project_id = body.get('id') or ('proj_' + uuid.uuid4().hex[:12])
    if not validate_project_id(project_id):
        raise HTTPException(status_code=400, detail="无效的项目ID")

    name = sanitize_project_name(body.get('name'))
    modules_data = body.get('modules', {})
    pipeline_state = body.get('pipeline', {})
    template_selections = body.get('templateSelections', {})
    shared_context = body.get('sharedContext', {})
    expected_updated_at = body.get('expectedUpdatedAt', '')

    if not isinstance(modules_data, dict):
        raise HTTPException(status_code=400, detail="modules数据格式错误")
    if len(json.dumps(modules_data, ensure_ascii=False)) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="项目数据过大（上限20MB）")

    # Optimistic lock: check updated_at to detect concurrent modifications
    if expected_updated_at:
        existing = novel_db.get_project(project_id)
        if existing and existing.get('updated_at') and existing['updated_at'] != expected_updated_at:
            raise HTTPException(status_code=409, detail="项目已被其他标签页修改，请刷新后重试")

    # 1. 保存每个模块数据（使用专用保存函数确保数据流正确）
    save_count = 0
    failed_modules = []
    for mod_name, mod_data in modules_data.items():
        if mod_data is None:
            continue
        try:
            _save_module_data(project_id, mod_name, mod_data)
            save_count += 1
        except Exception as e:
            logger.warning(f"保存模块 {mod_name} 失败: {e}")
            failed_modules.append(mod_name)

    # 2. 更新流水线进度状态（包含每个模块的status）
    if pipeline_state:
        try:
            _update_pipeline_status(project_id, pipeline_state)
        except Exception as e:
            logger.warning(f"保存流水线状态失败: {e}")

    # 3. 保存项目元数据（包含模板选择+共享上下文）
    project_data = {
        'v2': True,
        'templateSelections': template_selections,
        'sharedContext': shared_context,
        'moduleOrder': list(modules_data.keys()),
        'moduleCount': save_count,
    }
    novel_db.save_project(project_id, name, 0, json.dumps(project_data, ensure_ascii=False), 'v2')

    now = time.strftime('%Y-%m-%d %H:%M:%S')
    result = {"ok": True, "id": project_id, "name": name, "updated_at": now}
    if failed_modules:
        result["failedModules"] = failed_modules
    return result


def _save_module_data(project_id: str, module_name: str, data: any):
    """根据模块名选择正确的保存方式"""
    from novel_creator import database_v2
    from app.services.pipeline import LEGACY_MODULE_MAP
    # 归一化旧模块名
    resolved = LEGACY_MODULE_MAP.get(module_name)
    if resolved is not None:
        module_name = resolved

    save_map = {
        "idea": lambda pid, d: database_v2.save_pipeline_state(pid, "idea", d.get('module_data', d) if isinstance(d, dict) else d),
        "project": lambda pid, d: database_v2.save_pipeline_state(pid, "project", d.get('module_data', d) if isinstance(d, dict) else d),
        "world": database_v2.save_world,
        "characters": lambda pid, d: _save_characters_from_data(pid, d),
        "architecture": lambda pid, d: database_v2.save_pipeline_state(pid, "architecture", d.get('module_data', d) if isinstance(d, dict) else d),
        "relation_map": lambda pid, d: database_v2.save_relation_map(pid, d),
        "outline": lambda pid, d: database_v2.save_pipeline_state(pid, "outline", d.get('module_data', d) if isinstance(d, dict) else d),
        "volumes": lambda pid, d: _save_volumes_from_data(pid, d),
        "chapter_plan": lambda pid, d: _save_chapter_plans_from_data(pid, d),
        "draft": lambda pid, d: _save_drafts_from_data(pid, d),
        "parse": lambda pid, d: database_v2.save_pipeline_state(pid, "parse", d.get('module_data', d) if isinstance(d, dict) else d),
        "polish": lambda pid, d: database_v2.save_pipeline_state(pid, "polish", d.get('module_data', d) if isinstance(d, dict) else d),
        "consistency": database_v2.save_consistency_report,
    }
    save_fn = save_map.get(module_name)
    if save_fn:
        try:
            save_fn(project_id, data)
        except Exception:
            database_v2.save_pipeline_state(project_id, module_name,
                data.get('module_data', data) if isinstance(data, dict) else data)
    else:
        database_v2.save_pipeline_state(project_id, module_name,
            data.get('module_data', data) if isinstance(data, dict) else data)


def _save_characters_from_data(project_id, data):
    from novel_creator import database_v2
    if isinstance(data, dict) and 'module_data' in data:
        data = data['module_data']
    if isinstance(data, dict):
        chars = data.get('characters') or data.get('protagonists') or []
        villains = data.get('villains') or data.get('antagonists') or []
        for i, c in enumerate(chars if isinstance(chars, list) else [chars]):
            cid = c.get('charId') or c.get('id') or c.get('name', f'char_{i}')
            database_v2.save_character(project_id, str(cid), c)
        for i, v in enumerate(villains if isinstance(villains, list) else [villains]):
            vid = v.get('charId') or v.get('id') or v.get('name', f'villain_{i}')
            v_data = {**v, 'role_type': 'antagonist'}
            database_v2.save_character(project_id, str(vid), v_data)


def _save_volumes_from_data(project_id, data):
    from novel_creator import database_v2
    if isinstance(data, dict) and 'module_data' in data:
        data = data['module_data']
    volumes = data.get('volumes', data) if isinstance(data, dict) else data
    for v in (volumes if isinstance(volumes, list) else [volumes] if isinstance(volumes, dict) else []):
        vno = v.get('volume_no') or v.get('id') or 1
        database_v2.save_volume(project_id, int(vno), v)


def _save_chapter_plans_from_data(project_id, data):
    from novel_creator import database_v2
    if isinstance(data, dict) and 'module_data' in data:
        data = data['module_data']
    plans = data.get('chapterPlans', data) if isinstance(data, dict) else data
    for p in (plans if isinstance(plans, list) else [plans] if isinstance(plans, dict) else []):
        cno = p.get('chapter_no') or p.get('id') or '1'
        database_v2.save_chapter_plan(project_id, str(cno), p)


def _save_drafts_from_data(project_id, data):
    from novel_creator import database_v2
    if isinstance(data, dict) and 'module_data' in data:
        data = data['module_data']
    drafts = data.get('drafts', data) if isinstance(data, dict) else data
    if isinstance(drafts, list):
        for d in drafts:
            ch = str(d.get('chapter_no', '1'))
            database_v2.save_draft(project_id, ch, d)
    elif isinstance(drafts, dict):
        for ch, content in drafts.items():
            database_v2.save_draft(project_id, ch, content)


def _update_pipeline_status(project_id: str, pipeline_state: dict):
    """更新流水线进度状态"""
    from novel_creator import database_v2
    modules_status = pipeline_state.get('modules', {})
    for mod_name, mod_state in modules_status.items():
        if isinstance(mod_state, dict):
            status = mod_state.get('status', 'pending')
            existing = database_v2.get_pipeline_module_data(project_id, mod_name)
            data = existing or {}
            if isinstance(data, dict):
                data['status'] = status
            database_v2.save_pipeline_state(project_id, mod_name, data)


@router.post("/api/projects/load-v2")
def project_load_v2(body: dict):
    """加载V2项目全量数据"""
    project_id = body.get('id', '')
    if not validate_project_id(project_id):
        raise HTTPException(status_code=400, detail="无效的项目ID")

    project = novel_db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 1. 获取所有模块数据
    from app.api.pipeline import get_all_module_data
    all_data = get_all_module_data(project_id)

    # 2. 获取流水线状态
    from app.services.pipeline import get_pipeline_progress
    pipeline_status = get_pipeline_progress(project_id)

    # 3. 解析项目元数据
    template_selections = {}
    shared_context = {}
    try:
        meta = json.loads(project.get('data', '{}')) if isinstance(project.get('data'), str) else (project.get('data') or {})
        if isinstance(meta, dict) and meta.get('v2'):
            template_selections = meta.get('templateSelections', {})
            shared_context = meta.get('sharedContext', {})
    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "id": project_id,
        "name": project.get('name', '未命名项目'),
        "updated_at": project.get('updated_at', ''),
        "modules": all_data.get('modules', {}),
        "pipeline": pipeline_status,
        "templateSelections": template_selections,
        "sharedContext": shared_context,
    }


# ==================== 5.4-2: 软删除与恢复 ====================

@router.post("/api/v2/projects/soft-delete")
def project_soft_delete(body: dict):
    """将项目标记为已删除（移入回收站），而非永久删除"""
    project_id = body.get('project_id', '')
    if not validate_project_id(project_id):
        return {"error": "无效的项目ID"}
    project = novel_db.get_project(project_id)
    if not project:
        return {"error": "项目不存在"}
    # get_project 返回的 data 可能是 dict 或 JSON string，兼容处理
    raw = project.get('data', None)
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                data = {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    else:
        data = {}
    data['deleted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    tags = project.get('tags', '') or ''
    novel_db.save_project(project_id, project.get('name', '未命名') or '未命名',
                         project.get('step', 0) or 0,
                         json.dumps(data, ensure_ascii=False), tags)
    return {"ok": True}


@router.post("/api/v2/projects/restore")
def project_restore(body: dict):
    """从回收站恢复项目"""
    project_id = body.get('project_id', '')
    if not validate_project_id(project_id):
        return {"error": "无效的项目ID"}
    project = novel_db.get_project(project_id)
    if not project:
        return {"error": "项目不存在"}
    raw = project.get('data', None)
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                data = {}
        except (json.JSONDecodeError, TypeError):
            data = {}
    else:
        data = {}
    data.pop('deleted_at', None)
    tags = project.get('tags', '') or ''
    novel_db.save_project(project_id, project.get('name', '未命名') or '未命名',
                         project.get('step', 0) or 0,
                         json.dumps(data, ensure_ascii=False), tags)
    return {"ok": True}

@router.get("/api/v2/projects/list")
async def list_v2_projects():
    from novel_creator.database_v2 import _v2_db
    conn = _v2_db()
    rows = conn.execute("""
        SELECT v2.project_id, v2.project_overview, v2.created_at, v2.updated_at,
               COALESCE(p.name, v2.project_overview) as display_name
        FROM v2_projects v2
        LEFT JOIN projects p ON v2.project_id = p.id
        WHERE v2.deleted_at IS NULL
        ORDER BY v2.updated_at DESC
    """).fetchall()
    conn.close()
    projects = []
    for r in rows:
        projects.append({
            "id": r[0],
            "name": r[4] or r[1] or r[0],
            "created_at": r[2],
            "updated_at": r[3],
            "tags": "v2",
        })
    return {"projects": projects}

@router.post("/api/v2/projects/derive-fields")
def derive_project_fields(body: dict):
    """从项目数据推导结构化字段: 预估章节/字数/关键词/标签/系列潜力"""
    from app.services.design_service import (
        _assess_series_potential,
        _estimate_chapters,
        _estimate_words,
        _extract_keywords,
        _generate_tags,
    )
    from novel_creator import database_v2

    project_id = body.get("project_id", "")
    project_data = body.get("project_data", {})

    if isinstance(project_data, dict):
        overview = str(project_data.get("overview", project_data.get("project_overview", "")))
        idea = str(project_data.get("idea", project_data.get("concept", "")))
    else:
        overview = str(project_data)
        idea = ""

    combined_text = f"{overview} {idea}".strip()

    derived = {
        "estimatedChapters": _estimate_chapters(combined_text),
        "estimatedWords": _estimate_words(combined_text),
        "titleKeywords": _extract_keywords(combined_text),
        "contentTags": _generate_tags(combined_text),
        "seriesPotential": _assess_series_potential(combined_text),
    }

    if project_id:
        try:
            existing = database_v2.get_project_detail(project_id) or {}
            existing["derived_fields"] = derived
            database_v2.save_project_detail(project_id, existing)
        except Exception as e:
            logger.warning(f"保存derived_fields失败: {e}")

    return derived
