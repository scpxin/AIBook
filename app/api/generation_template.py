"""生成模板API — 全模块模板CRUD、匹配、复用"""
import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.template_service import (
    apply_template_to_project,
    auto_save_template,
    compute_input_fingerprint,
    match_templates_strict,
)
from novel_creator.database_v2 import (
    delete_generation_template,
    get_compatibility_group_templates,
    get_generation_template,
    get_project_templates,
    list_generation_templates,
    save_generation_template,
    update_generation_template,
)

logger = logging.getLogger('novel_creator.api.v2.generation_template')

router = APIRouter(prefix="/api/v2/generation-templates", tags=["生成模板"])


# ========== 模板CRUD ==========

@router.get("/")
def list_templates(
    module_key: str | None = None,
    genre: str | None = None,
    world_type: str | None = None,
    compatibility_group: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """获取模板列表（支持筛选）"""
    templates = list_generation_templates(
        module_key=module_key,
        genre=genre,
        world_type=world_type,
        compatibility_group=compatibility_group,
        limit=limit,
        offset=offset,
    )
    return {"templates": templates, "total": len(templates)}


@router.get("/{template_id}")
def get_template(template_id: int):
    """获取单个模板详情"""
    tpl = get_generation_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"template": tpl}


@router.post("/")
def create_template(body: dict):
    """手动创建模板"""
    required = ['name', 'module_key', 'output_data']
    for f in required:
        if f not in body:
            raise HTTPException(status_code=422, detail=f"缺少必填字段: {f}")

    try:
        tpl = save_generation_template(
            name=body['name'],
            module_key=body['module_key'],
            output_data=body['output_data'],
            input_context=body.get('input_context', {}),
            entity_refs=body.get('entity_refs'),
            compatibility_group=body.get('compatibility_group', ''),
            source_project_id=body.get('source_project_id', ''),
            genre=body.get('genre', ''),
            sub_genre=body.get('sub_genre', ''),
            tone=body.get('tone', ''),
            world_type=body.get('world_type', ''),
            target_audience=body.get('target_audience', ''),
            input_fingerprint=compute_input_fingerprint(body.get('input_context', {})),
            is_public=body.get('is_public', False),
        )
        return {"ok": True, "template": tpl}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新模板失败: {e}")
        raise HTTPException(status_code=500, detail="更新模板失败，请稍后重试")


# ========== 更新模板 ==========

@router.put("/{template_id}")
def update_template(template_id: int, body: dict):
    """更新模板"""
    updated = update_generation_template(template_id, **{k: v for k, v in body.items() if k in (
        'name', 'module_key', 'output_data', 'input_context', 'entity_refs',
        'compatibility_group', 'source_project_id', 'genre', 'sub_genre', 'tone',
        'world_type', 'target_audience', 'is_public', 'quality_rating',
    )})
    if not updated:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"ok": True, "template": updated}


# ========== 删除模板 ==========

@router.delete("/{template_id}")
def delete_template(template_id: int):
    """删除模板"""
    deleted = delete_generation_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"ok": True}


# ========== 模板匹配 ==========

@router.post("/match")
def match_templates(body: dict):
    """匹配模板 — 对指定模块的全部模板做兼容性打分，返回 compatible/incompatible 两组"""
    module_key = body.get('module_key', '')
    project_context = body.get('project_context', {})
    selected_templates = body.get('selected_templates', {})

    all_templates = list_generation_templates(module_key=module_key, limit=200)
    compatible, incompatible = [], []
    for tpl in all_templates:
        result = match_templates_strict(tpl, project_context, selected_templates, all_templates)
        if result.get('is_compatible'):
            compatible.append(result)
        else:
            incompatible.append(result)

    return {
        "compatible": compatible,
        "incompatible": incompatible,
        "total_candidates": len(all_templates),
    }


# ========== 应用模板 ==========

@router.post("/{template_id}/apply")
def apply_template(template_id: int, body: dict):
    """应用模板到项目"""
    project_id = body.get('project_id', '')
    if not project_id:
        raise HTTPException(status_code=422, detail="缺少 project_id")

    try:
        result = apply_template_to_project(template_id, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result

@router.get("/compat-group/{group_id}")
def get_compat_group(group_id: str):
    """获取同一兼容组的所有模板"""
    templates = get_compatibility_group_templates(group_id)
    return {"group_id": group_id, "templates": templates, "total": len(templates)}


# ========== 项目模板查询 ==========

@router.get("/project/{project_id}")
def get_project_templates_api(project_id: str):
    """获取指定项目的所有生成模板"""
    templates = get_project_templates(project_id)
    return {"project_id": project_id, "templates": templates, "total": len(templates)}


# ========== 评分 ==========

@router.post("/{template_id}/rate")
def rate_template(template_id: int, body: dict):
    """模板评分"""
    rating = body.get('rating')
    if not rating or not (1 <= rating <= 5):
        raise HTTPException(status_code=422, detail="评分必须在1-5之间")
    try:
        tpl = update_generation_template(template_id, quality_rating=rating)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"ok": True, "template": tpl}


# ========== 自动保存钩子（供内部调用） ==========

@router.post("/auto-save")
def auto_save_api(body: dict):
    """AI生成成功后自动保存为模板（内部API）"""
    project_id = body.get('project_id', '')
    module_key = body.get('module_key', '')
    module_data = body.get('module_data')
    input_context = body.get('input_context', {})
    compat_group = body.get('compatibility_group', '')

    if not project_id or not module_key or module_data is None:
        raise HTTPException(status_code=422, detail="缺少必填字段")
    if not isinstance(module_data, dict) or len(str(module_data)) > 500000:
        raise HTTPException(status_code=400, detail="模块数据格式错误或过大")

    tpl = auto_save_template(
        project_id=project_id,
        module_key=module_key,
        module_data=module_data,
        input_context=input_context,
        existing_compat_group=compat_group,
    )

    if tpl:
        return {"ok": True, "template_id": tpl['id'], "auto_saved": True}
    return {"ok": False, "auto_saved": False}
