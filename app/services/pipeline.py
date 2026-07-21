"""V2 流水线编排引擎 — 管理 13 模块创作流程的执行

功能:
- 定义模块执行顺序和依赖关系
- 状态机管理 (pending → generating → done / failed)
- 支持断点续传 (从任意模块继续)
- 支持单模块重跑
- 完整的执行日志记录
- 状态持久化到数据库 (服务重启后恢复)

设计原则:
- 规划链 (M1-M9): 串行执行,前置模块未完成则后续模块locked
- 执行闭环 (M10-M13): 迭代循环,不合格则重修
"""
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from enum import StrEnum
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from novel_creator.data_bridge import DataBridge

logger = logging.getLogger('novel_creator.pipeline')


class ModuleStatus(StrEnum):
    LOCKED = "locked"
    PENDING = "pending"
    GENERATING = "generating"
    DONE = "done"
    FAILED = "failed"


class PipelineModule:
    """单个流水线模块的定义"""

    def __init__(self, name: str, display_name: str, layer: str,
                 dependencies: list[str], is_parallel: bool = False,
                 is_iterative: bool = False):
        self.name = name
        self.display_name = display_name
        self.layer = layer
        self.dependencies = dependencies
        self.is_parallel = is_parallel
        self.is_iterative = is_iterative


# ========== 13 模块定义 ==========

PIPELINE_MODULES: dict[str, PipelineModule] = {
    # 设计层 (M1-M6): 串行
    "idea": PipelineModule("idea", "灵感", "design", []),
    "project": PipelineModule("project", "项目定位", "design", ["idea"]),
    "world": PipelineModule("world", "世界观体系", "design", ["project"]),
    "characters": PipelineModule("characters", "人物系统", "design", ["project", "world"]),
    "architecture": PipelineModule("architecture", "故事架构", "design", ["characters"]),
    "relation_map": PipelineModule("relation_map", "角色关系网", "design",
                                    ["characters"], is_parallel=True),

    # 结构层 (M7): 并行
    "outline": PipelineModule("outline", "全书大纲", "structure",
                               ["architecture"], is_parallel=True),

    # 规划层 (M8-M9): 串行
    "volumes": PipelineModule("volumes", "卷纲", "planning", ["architecture"]),
    "chapter_plan": PipelineModule("chapter_plan", "章节规划", "planning",
                                    ["volumes", "architecture"]),

    # 执行闭环 (M10-M13): 迭代
    "draft": PipelineModule("draft", "正文生成", "execution",
                             ["chapter_plan"], is_iterative=True),
    "parse": PipelineModule("parse", "内容解析", "execution",
                            ["draft"], is_iterative=True),
    "polish": PipelineModule("polish", "润色", "execution",
                             ["draft"], is_iterative=True),
    "consistency": PipelineModule("consistency", "一致性检查", "execution",
                                   ["parse", "polish"], is_iterative=True),
}

MODULE_ORDER = [
    "idea", "project", "world", "characters", "architecture",
    "relation_map",
    "outline",
    "volumes", "chapter_plan",
    "draft", "parse", "polish", "consistency",
]

# 旧模块名到新模块名的映射 (兼容现有数据)
LEGACY_MODULE_MAP = {
    "story_architecture": "architecture",
    "draft_generation": "draft",
    "content_parsing": "parse",
    "chapter_outline": "chapter_plan",
    "consistency_check": "consistency",
    "scene_design": "chapter_plan",
    "power_system": "world",
    "factions": "world",
    "timeline": "architecture",
    "knowledge_update": "parse",
    "plot_nodes": None,  # 已删除
}

# ========== 流水线状态持久化 ==========

_state_locks: 'OrderedDict[str, threading.RLock]' = OrderedDict()
_global_lock = threading.Lock()


def _get_pipeline_state(project_id, module_name=None):
    """从 DataBridge 读取流水线状态"""
    rows = DataBridge._conn().execute(
        "SELECT * FROM v2_pipeline_states WHERE project_id=?"
        + (" AND module_name=?" if module_name else "")
        + " ORDER BY id",
        (project_id,) if not module_name else (project_id, module_name)
    )
    return [dict(r) for r in rows.fetchall()]


def _save_pipeline_state(project_id, module_name, fields):
    """通过 DataBridge 连接写入流水线状态"""
    conn = DataBridge._conn()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    existing = _get_pipeline_state(project_id, module_name)
    existing_dict = existing[0] if existing else {}
    merged = {**existing_dict, **fields}
    conn.execute("""
        INSERT INTO v2_pipeline_states (project_id, module_name, status, retry_count,
            error, consistency_score, started_at, completed_at, updated_at, data_json)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(project_id, module_name) DO UPDATE SET
            status=excluded.status, retry_count=excluded.retry_count,
            error=excluded.error, consistency_score=excluded.consistency_score,
            started_at=excluded.started_at, completed_at=excluded.completed_at,
            updated_at=excluded.updated_at, data_json=excluded.data_json
    """, (project_id, module_name,
          merged.get('status', 'pending'), merged.get('retry_count', 0),
          merged.get('error', ''), merged.get('consistency_score', 0),
          merged.get('started_at', ''), merged.get('completed_at', ''),
          now, merged.get('data_json', '{}')))
    conn.commit()


def _get_project_lock(project_id: str) -> threading.RLock:
    with _global_lock:
        if project_id not in _state_locks:
            if len(_state_locks) >= 200:
                for _ in range(50):
                    _state_locks.popitem(last=False)
            _state_locks[project_id] = threading.RLock()
        return _state_locks[project_id]


def _db_row_to_module_dict(row: dict) -> dict[str, Any]:
    return {
        "name": row["module_name"],
        "status": row["status"],
        "retry_count": row.get("retry_count", 0),
        "error": row.get("error", ""),
        "consistency_score": row.get("consistency_score", 0),
        "started_at": row.get("started_at", ""),
        "completed_at": row.get("completed_at", ""),
        "updated_at": row.get("updated_at", ""),
    }


def _build_full_state(project_id: str) -> dict[str, Any]:
    db_rows = _get_pipeline_state(project_id)
    modules = {}
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        db_row = next((r for r in db_rows if r["module_name"] == name), None)
        if db_row:
            modules[name] = _db_row_to_module_dict(db_row)
            modules[name]["display_name"] = mod.display_name
            modules[name]["layer"] = mod.layer
        else:
            status = ModuleStatus.LOCKED if mod.dependencies else ModuleStatus.PENDING
            modules[name] = {
                "name": name,
                "display_name": mod.display_name,
                "layer": mod.layer,
                "status": status.value,
                "started_at": None,
                "completed_at": None,
                "error": None,
                "retry_count": 0,
                "consistency_score": 0,
            }
    current = "idea"
    for name in MODULE_ORDER:
        if modules.get(name, {}).get("status") != ModuleStatus.DONE.value:
            current = name
            break
    else:
        current = MODULE_ORDER[-1]

    for name in MODULE_ORDER:
        mod_state = modules.get(name, {})
        if mod_state.get("status") == ModuleStatus.LOCKED.value:
            deps_ok = all(
                modules.get(dep, {}).get("status") == ModuleStatus.DONE.value
                for dep in PIPELINE_MODULES[name].dependencies
            )
            if deps_ok:
                modules[name]["status"] = ModuleStatus.PENDING.value

    return {
        "project_id": project_id,
        "current_module": current,
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        "modules": modules
    }


def _init_project_state(project_id: str):
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        status = ModuleStatus.LOCKED if mod.dependencies else ModuleStatus.PENDING
        _save_pipeline_state(project_id, name, {
            "status": status.value,
            "retry_count": 0,
            "error": "",
            "consistency_score": 0,
            "started_at": "",
            "completed_at": "",
        })


def get_or_create_state(project_id: str) -> dict[str, Any]:
    lock = _get_project_lock(project_id)
    with lock:
        db_rows = _get_pipeline_state(project_id)
        if not db_rows:
            _init_project_state(project_id)
        return _build_full_state(project_id)


def get_module_status(project_id: str, module_name: str) -> str:
    state = get_or_create_state(project_id)
    return state["modules"].get(module_name, {}).get("status", "unknown")


def get_next_pending_module(project_id: str) -> str | None:
    state = get_or_create_state(project_id)
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        mod_state = state["modules"].get(name, {})
        if mod_state.get("status") == ModuleStatus.PENDING.value:
            deps_ok = all(
                state["modules"].get(dep, {}).get("status") == ModuleStatus.DONE.value
                for dep in mod.dependencies
            )
            if deps_ok:
                return name
    return None


def set_module_status(project_id: str, module_name: str,
                      status: ModuleStatus, error: str = None,
                      consistency_score: float = None,
                      data_json: str = None):
    lock = _get_project_lock(project_id)
    with lock:
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        db_rows = _get_pipeline_state(project_id, module_name)
        existing = db_rows[0] if db_rows else {}

        retry_count = existing.get("retry_count", 0)
        started_at = existing.get("started_at", "") or ""
        completed_at = existing.get("completed_at", "") or ""
        consistency = consistency_score if consistency_score is not None else existing.get("consistency_score", 0)
        existing_data_json = existing.get("data_json", "{}") or "{}"

        if status == ModuleStatus.GENERATING and not started_at:
            started_at = now
        elif status == ModuleStatus.DONE:
            completed_at = now
        elif status == ModuleStatus.FAILED:
            retry_count = existing.get("retry_count", 0) + 1

        final_data_json = data_json if data_json is not None else existing_data_json

        _save_pipeline_state(project_id, module_name, {
            "status": status.value,
            "retry_count": retry_count,
            "error": error or "",
            "consistency_score": consistency,
            "started_at": started_at,
            "completed_at": completed_at,
            "data_json": final_data_json,
        })

        if status == ModuleStatus.DONE:
            _unlock_dependents(project_id, module_name)


def _unlock_dependents(project_id: str, completed_module: str):
    db_rows = _get_pipeline_state(project_id)
    state_modules = {}
    for row in db_rows:
        state_modules[row["module_name"]] = _db_row_to_module_dict(row)

    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        if completed_module in mod.dependencies:
            mod_state = state_modules.get(name, {})
            if mod_state.get("status") == ModuleStatus.LOCKED.value:
                deps_done = all(
                    state_modules.get(dep, {}).get("status") == ModuleStatus.DONE.value
                    for dep in mod.dependencies
                )
                if deps_done:
                    _save_pipeline_state(project_id, name, {
                        "status": ModuleStatus.PENDING.value,
                        "retry_count": mod_state.get("retry_count", 0),
                        "error": "",
                        "consistency_score": 0,
                        "started_at": "",
                        "completed_at": "",
                    })


def get_pipeline_progress(project_id: str) -> dict[str, Any]:
    state = get_or_create_state(project_id)
    total = len(MODULE_ORDER)
    done = sum(1 for m in state["modules"].values() if m.get("status") == ModuleStatus.DONE.value)
    failed = sum(1 for m in state["modules"].values() if m.get("status") == ModuleStatus.FAILED.value)
    generating = sum(1 for m in state["modules"].values() if m.get("status") == ModuleStatus.GENERATING.value)
    return {
        "project_id": project_id,
        "total_modules": total,
        "completed": done,
        "failed": failed,
        "generating": generating,
        "progress_pct": round(done / total * 100, 1),
        "current_module": state.get("current_module"),
        "next_module": get_next_pending_module(project_id),
        "modules": state["modules"],
        "updated_at": state.get("updated_at")
    }


def get_executionlayer_state(project_id: str) -> dict[str, Any]:
    state = get_or_create_state(project_id)
    execution_modules = {}
    for name in ["draft", "parse", "polish", "consistency"]:
        execution_modules[name] = state["modules"].get(name, {})
    return execution_modules


_CONSISTENCY_THRESHOLD = int(os.environ.get("CONSISTENCY_THRESHOLD", 70))


def is_execution_loop_complete(project_id: str, chapter_no: str = None) -> bool:
    state = get_or_create_state(project_id)
    required = ["draft"]
    for name in required:
        if state["modules"].get(name, {}).get("status") != ModuleStatus.DONE.value:
            return False
    cc_state = state["modules"].get("consistency", {})
    if cc_state.get("status") == ModuleStatus.DONE.value:
        score = cc_state.get("consistency_score", 0)
        return score >= _CONSISTENCY_THRESHOLD
    return False


def cleanup_project_state(project_id: str):
    db_rows = _get_pipeline_state(project_id)
    if db_rows:
        _save_pipeline_state(project_id, "idea", {"status": "pending"})
    lock = _get_project_lock(project_id)
    with lock:
        _state_locks.pop(project_id, None)


def get_module_info(module_name: str) -> dict[str, Any] | None:
    mod = PIPELINE_MODULES.get(module_name)
    if not mod:
        return None
    return {
        "name": mod.name,
        "display_name": mod.display_name,
        "layer": mod.layer,
        "dependencies": mod.dependencies,
        "is_parallel": mod.is_parallel,
        "is_iterative": mod.is_iterative
    }


def get_all_modules_info() -> list[dict[str, Any]]:
    return [get_module_info(name) for name in MODULE_ORDER]


_module_validators: dict[str, Callable] = {}


def register_validator(module_name: str, validator: Callable):
    _module_validators[module_name] = validator


def validate_module_output(project_id: str, module_name: str, output: Any) -> tuple:
    validator = _module_validators.get(module_name)
    if validator:
        try:
            return validator(project_id, output)
        except Exception as e:
            return False, f"模块输出验证失败: {e}"
    return True, ""
