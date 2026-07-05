"""V2 流水线 API — 模块编排和状态管理

提供18模块流水线的状态查询、进度跟踪和模块推进功能。
实际模块执行端点在后续迭代中逐步实现。
"""
import sys
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

_current = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current, '..', '..', '..'))
from novel_creator import database_v2
from app.services.pipeline import (
    get_pipeline_progress,
    get_all_modules_info,
    get_module_info,
    set_module_status,
    get_next_pending_module,
    cleanup_project_state,
    ModuleStatus,
)

logger = logging.getLogger('novel_creator.api.v2.pipeline')

router = APIRouter(prefix="/api/v2/pipeline", tags=["V2流水线"])


@router.get("/modules")
async def list_modules():
    """获取所有18模块的元信息(执行顺序/依赖/层级)"""
    modules = get_all_modules_info()
    return {"modules": modules, "total": len(modules)}


@router.get("/{project_id}/status")
async def get_status(project_id: str):
    """获取项目流水线完整进度"""
    state = get_pipeline_progress(project_id)
    return state


@router.get("/{project_id}/modules/{module_name}/status")
async def get_module_status_api(project_id: str, module_name: str):
    """获取单个模块状态"""
    info = get_module_info(module_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未知模块: {module_name}")

    state = get_pipeline_progress(project_id)
    module_state = state["modules"].get(module_name, {})
    return {
        "module": info,
        "status": module_state.get("status", "unknown"),
        "started_at": module_state.get("started_at"),
        "completed_at": module_state.get("completed_at"),
        "error": module_state.get("error"),
        "retry_count": module_state.get("retry_count", 0),
    }


@router.post("/{project_id}/modules/{module_name}/status")
async def update_module_status_api(project_id: str, module_name: str,
                                    status: str, error: Optional[str] = None):
    """更新模块状态(供模块执行器回调)"""
    info = get_module_info(module_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未知模块: {module_name}")

    try:
        new_status = ModuleStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效状态: {status}")

    set_module_status(project_id, module_name, new_status, error)
    return {"success": True, "module": module_name, "status": status}


@router.get("/{project_id}/next")
async def get_next_module(project_id: str):
    """获取下一个可执行的模块"""
    next_mod = get_next_pending_module(project_id)
    if not next_mod:
        info = None
    else:
        info = get_module_info(next_mod)
    return {"next_module": next_mod, "module_info": info}


@router.delete("/{project_id}")
async def cleanup_state(project_id: str):
    """清理项目的流水线状态(内存+DB)"""
    cleanup_project_state(project_id)
    database_v2.delete_project_v2(project_id)
    return {"success": True, "message": f"已清理项目 {project_id} 的流水线状态"}


# ========== V2 数据查询API(18模块) ==========

@router.get("/{project_id}/data/{module_name}")
async def get_module_data(project_id: str, module_name: str):
    """获取模块的V2数据"""
    info = get_module_info(module_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未知模块: {module_name}")

    data = _query_v2_data(project_id, module_name)
    return {"module": module_name, "data": data}


def _query_v2_data(project_id: str, module_name: str):
    """根据模块名查询对应V2表"""
    query_map = {
        "idea": database_v2.get_idea,
        "project": database_v2.get_project_detail,
        "world": database_v2.get_world,
        "characters": database_v2.get_all_characters,
        "story": database_v2.get_story,
        "power_system": database_v2.get_power_system,
        "factions": database_v2.get_factions,
        "timeline": database_v2.get_timeline,
        "master_outline": None,
        "volumes": database_v2.get_volumes,
        "plot_nodes": database_v2.get_plot_nodes,
        "chapter_plan": database_v2.get_chapter_plans,
        "chapter_outline": None,
        "scene_design": database_v2.get_scenes,
        "foreshadowings": database_v2.get_foreshadows,
        "knowledge_update": database_v2.get_knowledge_state,
        "consistency_check": lambda pid: database_v2.get_ai_generations(pid, 'consistency_check'),
        "draft_generation": database_v2.get_drafts,
    }
    query_fn = query_map.get(module_name)
    if not query_fn:
        return None
    try:
        result = query_fn(project_id)
        return result
    except Exception as e:
        logger.error(f"查询模块数据失败 {module_name}: {e}")
        return None
