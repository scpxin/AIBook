"""V2 流水线 API — 19模块编排和状态管理

提供19模块流水线的状态查询、进度跟踪和模块推进功能。
"""
import sys
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Body
from typing import Any

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
    MODULE_ORDER,
)
from app.models.v2_schemas import (
    IdeaConfirmRequest, ModuleStatusUpdateRequest,
)

logger = logging.getLogger('novel_creator.api.v2.pipeline')

router = APIRouter(prefix="/api/v2/pipeline", tags=["V2流水线"])


@router.get("/modules")
def list_modules():
    """获取所有18模块的元信息(执行顺序/依赖/层级)"""
    modules = get_all_modules_info()
    return {"modules": modules, "total": len(modules)}


@router.get("/{project_id}/status")
def get_status(project_id: str):
    """获取项目流水线完整进度"""
    state = get_pipeline_progress(project_id)
    return state


@router.get("/{project_id}/modules/{module_name}/status")
def get_module_status_api(project_id: str, module_name: str):
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
def update_module_status_api(project_id: str, module_name: str,
                                    body: ModuleStatusUpdateRequest):
    """更新模块状态(供模块执行器回调)"""
    info = get_module_info(module_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未知模块: {module_name}")

    try:
        new_status = ModuleStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效状态: {body.status}")

    set_module_status(project_id, module_name, new_status,
                     body.error, body.consistency_score)
    return {"success": True, "module": module_name, "status": body.status}


@router.get("/{project_id}/next")
def get_next_module(project_id: str):
    """获取下一个可执行的模块"""
    next_mod = get_next_pending_module(project_id)
    if not next_mod:
        info = None
    else:
        info = get_module_info(next_mod)
    return {"next_module": next_mod, "module_info": info}


@router.post("/{project_id}/confirm-idea")
def confirm_idea(project_id: str, body: IdeaConfirmRequest):
    """确认灵感创意 (兼容 idea_id 和 idea 两种参数)"""
    idea_ref = body.idea_id or body.idea or "default"
    logger.info(f"确认创意: project={project_id}, idea={idea_ref}")
    set_module_status(project_id, "idea", ModuleStatus.DONE)
    return {"success": True, "project_id": project_id}


@router.delete("/{project_id}")
def cleanup_state(project_id: str, confirm: bool = False):
    """清理项目的流水线状态(内存+DB) — 需要 confirm=true 确认"""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="删除操作需要确认，请传递 confirm=true 参数"
        )
    cleanup_project_state(project_id)
    database_v2.delete_project_v2(project_id)
    return {"success": True, "message": f"已清理项目 {project_id} 的流水线状态"}


# ========== V2 数据查询API(18模块) ==========

@router.get("/{project_id}/data/{module_name}")
def get_module_data(project_id: str, module_name: str):
    """获取模块的V2数据"""
    info = get_module_info(module_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未知模块: {module_name}")

    data = _query_v2_data(project_id, module_name)
    return {"module": module_name, "data": data}


@router.get("/{project_id}/data")
def get_all_module_data(project_id: str):
    """获取项目所有上游模块数据(供下游模块联动)"""
    result = {}
    for name in MODULE_ORDER:
        data = _query_v2_data(project_id, name)
        if data:
            result[name] = data
    return {"project_id": project_id, "modules": result}


def _ensure_v2_project_exists(project_id, name=""):
    conn = _get_db_local()
    now = _now_iso_str()
    existing = conn.execute("SELECT project_id FROM v2_projects WHERE project_id=?", (project_id,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO v2_projects (project_id, project_overview, created_at, updated_at) VALUES (?,?,?,?)",
            (project_id, name or project_id, now, now))
        conn.commit()
    conn.close()

def _get_db_local():
    import sqlite3
    from novel_creator.database_v2 import DB_PATH as V2_DB_PATH
    return sqlite3.connect(V2_DB_PATH)

def _now_iso_str():
    from datetime import datetime
    return datetime.utcnow().isoformat()[:19]

@router.post("/{project_id}/data/{module_name}")

def save_module_data(project_id: str, module_name: str, data: Any = Body(None)):
    """保存模块的V2数据。data 为 None 时仅标记模块完成，跳过数据存储。"""
    save_map = {
        "idea": lambda pid, d: database_v2.save_pipeline_state(pid, "idea", d),
        "project": lambda pid, d: database_v2.save_pipeline_state(pid, "project", d),
        "world": database_v2.save_world,
        "characters": lambda pid, d: _save_characters_batch(pid, d),
        "power_system": lambda pid, d: database_v2.save_power_system(pid, _map_power_system(d)),
        "factions": lambda pid, d: _save_factions_batch(pid, d),
        "volumes": _save_volumes_batch,
        "chapter_plan": _save_chapter_plans_batch,
        "chapter_outline": lambda pid, d: _save_chapter_outline(pid, d),
        "plot_nodes": lambda pid, d: [database_v2.save_plot_node(pid, e.get('event_id', f'pn{i}') , e) for i, e in enumerate(d.get('events', []))],
        "scene_design": lambda pid, d: database_v2.save_pipeline_state(pid, "scene_design", d),
        "draft_generation": lambda pid, d: _save_draft_generation(pid, d),
        "content_parsing": lambda pid, d: database_v2.save_pipeline_state(pid, "content_parsing", d),
        "polish": lambda pid, d: database_v2.save_pipeline_state(pid, "polish", d),
        "knowledge_update": database_v2.save_knowledge_state,
        "consistency_check": database_v2.save_consistency_report,
        "story_architecture": lambda pid, d: database_v2.save_pipeline_state(pid, "story_architecture", d),
        "timeline": lambda pid, d: database_v2.save_timeline(pid, d),
        "outline": lambda pid, d: database_v2.save_pipeline_state(pid, "outline", d),
    }
    _ensure_v2_project_exists(project_id)
    save_fn = save_map.get(module_name)
    if data is not None:
        if not save_fn:
            known_modules = list(save_map.keys())
            logger.warning(f"保存到未知模块 '{module_name}' (已知模块: {known_modules})")
            database_v2.save_pipeline_state(project_id, module_name, data)
            return {"success": True, "module": module_name, "project_id": project_id, "warning": "模块名未在流水线中注册"}
        save_fn(project_id, data)

        if isinstance(data, dict) and not data.get('_apply_from_template'):
            try:
                from app.services.template_service import auto_save_template
                auto_save_template(
                    project_id=project_id,
                    module_key=module_name,
                    module_data=data.get('module_data', data),
                    input_context=data.get('input_context', {}),
                )
            except Exception as e:
                logger.warning(f"自动存模板失败（不影响保存）: {e}")

    # Mark module as done in pipeline_state
    try:
        database_v2.mark_module_done(project_id, module_name)
    except Exception as e:
        logger.warning(f"mark_module_done failed: {e}")
    return {"success": True, "module": module_name, "project_id": project_id}


def _save_draft_generation(project_id: str, data):
    """保存正文草稿 — 支持批量格式 {chapters: {1: {title, content, char_count}}} 或单章格式"""
    # 批量格式：frontend sends {chapters: {"1": {"title":"...", "content":"...", "char_count":3000}, ...}}
    chapters = data.get('chapters') if isinstance(data, dict) else None
    if isinstance(chapters, dict) and chapters:
        database_v2.save_drafts_batch(project_id, chapters)
    elif isinstance(chapters, list) and chapters:
        for ch in chapters:
            database_v2.save_draft(project_id, str(ch.get('chapter_no', ch.get('chapter_id', ''))), {
                "content_raw": ch.get("content", ""),
                "word_count_raw": int(ch.get("word_count", 0) or 0),
                "skeleton": ch.get("skeleton", ""),
                "style_note": ch.get("style_note", ""),
            })
    elif isinstance(data, dict) and data.get('chapter_no'):
        # 单章格式
        database_v2.save_draft(project_id, str(data['chapter_no']), {
            "content_raw": data.get("content", ""),
            "word_count_raw": len(data.get("content", "")),
            "skeleton": data.get("skeleton", ""),
            "style_note": data.get("style_note", ""),
        })
    elif isinstance(data, dict) and data.get('module_data'):
        # 嵌套在 module_data 中的格式
        inner = data['module_data']
        inner_chapters = inner.get('chapters')
        if isinstance(inner_chapters, dict) and inner_chapters:
            database_v2.save_drafts_batch(project_id, inner_chapters)


def _save_volumes_batch(project_id: str, data):
    """批量保存卷纲(支持list/dict格式)"""
    if isinstance(data, list):
        for i, vol in enumerate(data):
            no = str(vol.get("volume_no", vol.get("volume_id", str(i + 1))))
            database_v2.save_volume(project_id, no, vol)
    elif isinstance(data, dict):
        items = data.get("module_data") or data.get("volumes")
        if isinstance(items, list):
            for i, vol in enumerate(items):
                no = str(vol.get("volume_no", vol.get("volume_id", str(i + 1))))
                database_v2.save_volume(project_id, no, vol)
        elif data.get("volume_no"):
            database_v2.save_volume(project_id, str(data["volume_no"]), data)


def _save_chapter_plans_batch(project_id: str, data):
    """批量保存章节规划(支持list/dict格式)"""
    if isinstance(data, list):
        for i, cp in enumerate(data):
            no = str(cp.get("chapter_no", cp.get("chapter_id", str(i + 1))))
            database_v2.save_chapter_plan(project_id, no, cp)
        return
    if isinstance(data, dict):
        items = data.get("module_data") or data.get("chapterPlans") or data.get("chapter_plans") or data.get("chapter_assignments")
        if isinstance(items, list):
            for i, cp in enumerate(items):
                no = str(cp.get("chapter_no", cp.get("chapter_id", str(i + 1))))
                database_v2.save_chapter_plan(project_id, no, cp)
            return
        if data.get("chapter_no"):
            database_v2.save_chapter_plan(project_id, str(data["chapter_no"]), data)
            return
    # 兜底: 将dict整体保存为pipeline_state
    database_v2.save_pipeline_state(project_id, "chapter_plan", data if isinstance(data, dict) else {})


def _save_chapter_outline(project_id: str, data):
    """保存章节细纲(支持list或dict格式)"""
    if isinstance(data, list):
        database_v2.save_pipeline_state(project_id, "chapter_outline", {"outlines": data})
    elif isinstance(data, dict) and "module_data" in data:
        inner = data["module_data"]
        if isinstance(inner, list):
            database_v2.save_pipeline_state(project_id, "chapter_outline", {"outlines": inner})
        else:
            database_v2.save_pipeline_state(project_id, "chapter_outline", inner)
    elif isinstance(data, dict):
        database_v2.save_pipeline_state(project_id, "chapter_outline", data)
    else:
        database_v2.save_pipeline_state(project_id, "chapter_outline", {"outlines": []})


def _save_characters_batch(project_id: str, data):
    """批量保存角色(支持{protagonist, supporting, villains}结构或list或单条)"""
    if isinstance(data, list):
        for c in data:
            cid = c.get("char_id", c.get("name", "c1"))
            database_v2.save_character(project_id, cid, c)
    elif isinstance(data, dict):
        if "protagonist" in data or "supporting" in data or "villains" in data:
            if data.get("protagonist"):
                p = data["protagonist"] if isinstance(data["protagonist"], dict) else data["protagonist"]
                pid_ = p.get("char_id", p.get("name", "protagonist"))
                p_with_role = dict(p, role_type="protagonist") if isinstance(p, dict) else p
                database_v2.save_character(project_id, pid_, p_with_role)
            for i, c in enumerate(data.get("supporting", [])):
                if isinstance(c, dict):
                    c = dict(c, role_type="supporting")
                cid = c.get("char_id", c.get("name", f"sup_{i+1}")) if isinstance(c, dict) else f"sup_{i+1}"
                database_v2.save_character(project_id, cid, c)
            villains_data = data.get("villains", [])
            if isinstance(villains_data, dict):
                v = villains_data
                vid_ = v.get("char_id", v.get("name", v.get("main_character", "villain_1")))
                database_v2.save_character(project_id, vid_, dict(v, role_type="antagonist"))
            elif isinstance(villains_data, list):
                for i, c in enumerate(villains_data):
                    if isinstance(c, dict):
                        c = dict(c, role_type="antagonist")
                    cid = c.get("char_id", c.get("name", f"ant_{i+1}")) if isinstance(c, dict) else f"ant_{i+1}"
                    database_v2.save_character(project_id, cid, c)
        elif data.get("char_id") or data.get("name"):
            cid = data.get("char_id", data.get("name", "c1"))
            database_v2.save_character(project_id, cid, data)


def _save_factions_batch(project_id: str, data):
    """批量保存势力(支持{pattern, factions:[...]}结构或list或单条)"""
    if isinstance(data, list):
        for i, f in enumerate(data):
            fid = f.get("faction_id", f.get("name", f"f{i+1}"))
            database_v2.save_faction(project_id, fid, f)
    elif isinstance(data, dict):
        if "factions" in data and isinstance(data["factions"], list):
            for i, f in enumerate(data["factions"]):
                fid = f.get("faction_id", f.get("name", f"f{i+1}"))
                database_v2.save_faction(project_id, fid, f)
        elif data.get("faction_id") or data.get("name"):
            fid = data.get("faction_id", data.get("name", "f1"))
            database_v2.save_faction(project_id, fid, data)


def _save_scenes_batch(project_id: str, data):
    """批量保存场景(支持{scenes:[...]}结构或list或单条)"""
    if isinstance(data, list):
        for i, s in enumerate(data):
            sid = s.get("scene_id", s.get("sceneName", f"s{i+1}"))
            database_v2.save_scene(project_id, sid, s)
    elif isinstance(data, dict):
        if "scenes" in data and isinstance(data["scenes"], list):
            for i, s in enumerate(data["scenes"]):
                sid = s.get("scene_id", s.get("sceneName", f"s{i+1}"))
                database_v2.save_scene(project_id, sid, s)
        elif data.get("scene_id") or data.get("sceneName"):
            sid = data.get("scene_id", data.get("sceneName", "s1"))
            database_v2.save_scene(project_id, sid, data)


def _map_power_system(d: dict) -> dict:
    """将前端power_system字段映射到数据库schema"""
    import json as _json
    levels = d.get("levels", "")
    if isinstance(levels, str) and levels.strip():
        tiers = [{"name": l.strip(), "level": i + 1} for i, l in enumerate(levels.split("\n")) if l.strip()]
    else:
        tiers = d.get("tiers", [])
    growth = d.get("growth_method", d.get("system_type", d.get("systemType", "")))
    return {
        "tiers": tiers,
        "combat_categories": d.get("combat_categories", []),
        "growth_method": _json.dumps(growth, ensure_ascii=False) if isinstance(growth, dict) else growth,
        "limits": d.get("rules", d.get("limits", "")),
        "bottlenecks": d.get("bottlenecks", []),
    }


def _query_v2_data(project_id: str, module_name: str):
    """根据模块名查询对应V2表，无专用表时从pipeline_state的data_json读取"""
    query_map = {
        "idea": lambda pid: database_v2.get_pipeline_module_data(pid, "idea"),
        "project": lambda pid: database_v2.get_pipeline_module_data(pid, "project"),
        "world": database_v2.get_world,
        "characters": lambda pid: _restructure_characters(database_v2.get_all_characters(pid)),
        "power_system": database_v2.get_power_system,
        "factions": lambda pid: {"factions": database_v2.get_factions(pid)},
        "plot_nodes": lambda pid: {"events": database_v2.get_plot_nodes(pid)},
        "volumes": database_v2.get_volumes,
        "chapter_plan": database_v2.get_chapter_plans,
        "chapter_outline": lambda pid: database_v2.get_pipeline_module_data(pid, "chapter_outline"),
        "scene_design": lambda pid: database_v2.get_pipeline_module_data(pid, "scene_design"),
        "content_parsing": lambda pid: database_v2.get_pipeline_module_data(pid, "content_parsing"),
        "polish": lambda pid: database_v2.get_pipeline_module_data(pid, "polish"),
        "knowledge_update": database_v2.get_knowledge_state,
        "consistency_check": database_v2.get_consistency_reports,
        "draft_generation": database_v2.get_drafts,
        "story_architecture": lambda pid: database_v2.get_pipeline_module_data(pid, "story_architecture"),
        "outline": lambda pid: database_v2.get_pipeline_module_data(pid, "outline"),
        "timeline": lambda pid: {"events": database_v2.get_timeline(pid)},
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


def _restructure_characters(characters) -> dict:
    """将角色数据重组为{protagonist, supporting, villains}嵌套结构"""
    if not characters:
        return {"protagonist": {}, "supporting": [], "villains": [], "relations": {}}
    if isinstance(characters, dict):
        return characters
    result = {"protagonist": {}, "supporting": [], "villains": [], "relations": {}}
    for c in characters:
        if not isinstance(c, dict):
            continue
        role = c.get("role_type", "")
        if role == "protagonist":
            result["protagonist"] = c
        elif role in ("antagonist", "villain"):
            result["villains"].append(c)
        else:
            result["supporting"].append(c)
    return result


@router.post("/{project_id}/compatibility-check")
def compatibility_check(project_id: str, body: dict):
    """检查项目数据与目标平台的兼容性"""
    platform = body.get("platform", "tomato")

    results = []
    warnings = []

    try:
        detail = database_v2.get_project_detail(project_id)
    except Exception:
        detail = None

    if not detail:
        return {"success": True, "results": [], "message": "项目数据为空，无法执行兼容性检查"}

    overview = detail.get("project_overview", "")
    wordcount_plan = detail.get("wordcount_plan", {})

    # 1. 字数检查
    planned_words = wordcount_plan.get("total_words", 0) if isinstance(wordcount_plan, dict) else 0
    if platform == "tomato":
        if planned_words and planned_words < 100000:
            warnings.append({
                "check": "字数要求",
                "requirement": "番茄小说建议总字数 >= 10万",
                "actual": f"{planned_words}字",
                "status": "warning",
            })

    # 2. 平台兼容性规则
    platform_rules = {
        "tomato": {
            "min_words": 100000,
            "genres_supported": ["都市", "修仙", "重生", "穿越", "系统", "赘婿", "战神", "玄幻", "仙侠"],
            "notes": "推荐快节奏、强冲突、每日更新2000+字",
        },
        "qidian": {
            "min_words": 200000,
            "genres_supported": ["玄幻", "仙侠", "都市", "历史", "科幻", "游戏", "轻小说"],
            "notes": "推荐章节2000-3000字，重视世界构建和升级体系",
        },
    }

    rules = platform_rules.get(platform, platform_rules["tomato"])

    results.append({
        "check": "平台规则",
        "platform": platform,
        "rules": rules,
        "status": "info",
    })

    if warnings:
        results.extend(warnings)
        return {"success": True, "results": results, "message": f"发现{len(warnings)}个兼容性提示"}
    return {"success": True, "results": results}
