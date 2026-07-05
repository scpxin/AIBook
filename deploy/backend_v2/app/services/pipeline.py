"""V2 流水线编排引擎 — 管理 18 模块创作流程的执行

功能:
- 定义模块执行顺序和依赖关系
- 状态机管理 (pending → generating → done / failed)
- 支持断点续传 (从任意模块继续)
- 支持单模块重跑
- 完整的执行日志记录

设计原则:
- 规划链 (M1-M12): 串行执行,前置模块未完成则后续模块locked
- 执行闭环 (M13-M18): 迭代循环,不合格则重修
"""
import json
import time
import threading
import logging
from typing import Optional, Dict, Any, Callable, List
from enum import Enum

logger = logging.getLogger('novel_creator.pipeline')


class ModuleStatus(str, Enum):
    LOCKED = "locked"       # 前置模块未完成,不可执行
    PENDING = "pending"     # 等待执行
    GENERATING = "generating"  # 正在执行
    DONE = "done"           # 已完成
    FAILED = "failed"       # 执行失败


class PipelineModule:
    """单个流水线模块的定义"""

    def __init__(self, name: str, display_name: str, layer: str,
                 dependencies: List[str], is_parallel: bool = False,
                 is_iterative: bool = False):
        self.name = name
        self.display_name = display_name
        self.layer = layer  # design/structure/planning/execution/refinement
        self.dependencies = dependencies  # 前置模块名列表
        self.is_parallel = is_parallel    # 是否可并行(同层)
        self.is_iterative = is_iterative  # 是否迭代(执行闭环)


# ========== 18 模块定义 ==========

PIPELINE_MODULES: Dict[str, PipelineModule] = {
    # 设计层 (M1-M5): 串行,完全依赖前序
    "idea": PipelineModule("idea", "灵感", "design", []),
    "project": PipelineModule("project", "项目定位", "design", ["idea"]),
    "world": PipelineModule("world", "世界观", "design", ["project"]),
    "characters": PipelineModule("characters", "人物系统", "design", ["project", "world"]),
    "story": PipelineModule("story", "故事体系", "design", ["characters"]),

    # 结构层 (M6-M8): 可并行(依赖设计层完成)
    "power_system": PipelineModule("power_system", "力量体系", "structure",
                                   ["world", "characters", "story"], is_parallel=True),
    "factions": PipelineModule("factions", "势力体系", "structure",
                               ["world", "characters", "story"], is_parallel=True),
    "timeline": PipelineModule("timeline", "时间线", "structure",
                               ["world", "story"], is_parallel=True),
    "master_outline": PipelineModule("master_outline", "全书大纲", "structure",
                                     ["story", "power_system", "factions", "timeline"]),

    # 规划层 (M9-M12): 串行
    "volumes": PipelineModule("volumes", "卷纲", "planning", ["master_outline"]),
    "plot_nodes": PipelineModule("plot_nodes", "剧情节点", "planning", ["volumes"]),
    "chapter_plan": PipelineModule("chapter_plan", "章节规划", "planning", ["volumes", "plot_nodes"]),
    "chapter_outline": PipelineModule("chapter_outline", "章节细纲", "planning",
                                     ["chapter_plan", "plot_nodes"]),

    # 执行层闭环 (M13-M16): 迭代
    "scene_design": PipelineModule("scene_design", "场景设计", "execution",
                                   ["chapter_outline"], is_iterative=True),
    "draft_generation": PipelineModule("draft_generation", "正文生成", "execution",
                                       ["scene_design"], is_iterative=True),
    "content_parsing": PipelineModule("content_parsing", "内容解析", "execution",
                                      ["draft_generation"], is_iterative=True),
    "polish": PipelineModule("polish", "润色", "execution",
                             ["draft_generation"], is_iterative=True),

    # 完善层闭环 (M17-M18): 迭代,闭环核心
    "knowledge_update": PipelineModule("knowledge_update", "知识库更新", "refinement",
                                       ["content_parsing"], is_iterative=True),
    "consistency_check": PipelineModule("consistency_check", "一致性检查", "refinement",
                                        ["knowledge_update", "polish"], is_iterative=True),
}

# 模块执行顺序(拓扑排序后)
MODULE_ORDER = [
    "idea", "project", "world", "characters", "story",
    "power_system", "factions", "timeline", "master_outline",
    "volumes", "plot_nodes", "chapter_plan", "chapter_outline",
    "scene_design", "draft_generation", "content_parsing", "polish",
    "knowledge_update", "consistency_check"
]

# ========== 项目流水线状态 ==========

_project_states: Dict[str, Dict[str, Any]] = {}
_state_lock = threading.RLock()


def get_initial_state(project_id: str) -> Dict[str, Any]:
    """生成项目初始流水线状态"""
    modules = {}
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        status = ModuleStatus.LOCKED if mod.dependencies else ModuleStatus.PENDING
        modules[name] = {
            "name": name,
            "display_name": mod.display_name,
            "layer": mod.layer,
            "status": status.value,
            "started_at": None,
            "completed_at": None,
            "error": None,
            "retry_count": 0
        }
    return {
        "project_id": project_id,
        "current_module": "idea",
        "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        "modules": modules
    }


def get_or_create_state(project_id: str) -> Dict[str, Any]:
    """获取或创建项目流水线状态"""
    with _state_lock:
        if project_id not in _project_states:
            _project_states[project_id] = get_initial_state(project_id)
        return _project_states[project_id]


def get_module_status(project_id: str, module_name: str) -> str:
    """获取模块状态"""
    state = get_or_create_state(project_id)
    return state["modules"].get(module_name, {}).get("status", "unknown")


def get_next_pending_module(project_id: str) -> Optional[str]:
    """获取下一个待执行模块(依赖已完成的第一个PENDING)"""
    state = get_or_create_state(project_id)
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        mod_state = state["modules"].get(name, {})
        if mod_state.get("status") == ModuleStatus.PENDING.value:
            # 检查依赖是否全部DONE
            deps_ok = all(
                state["modules"].get(dep, {}).get("status") == ModuleStatus.DONE.value
                for dep in mod.dependencies
            )
            if deps_ok:
                return name
    return None


def set_module_status(project_id: str, module_name: str,
                      status: ModuleStatus, error: str = None):
    """更新模块状态"""
    with _state_lock:
        state = get_or_create_state(project_id)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        mod_state = state["modules"].get(module_name, {})
        mod_state["status"] = status.value
        mod_state["updated_at"] = now

        if status == ModuleStatus.GENERATING:
            mod_state["started_at"] = now
        elif status == ModuleStatus.DONE:
            mod_state["completed_at"] = now
        elif status == ModuleStatus.FAILED:
            mod_state["error"] = error
            mod_state["retry_count"] = mod_state.get("retry_count", 0) + 1

        state["modules"][module_name] = mod_state

        # 解锁后续模块(完成当前模块时)
        if status == ModuleStatus.DONE:
            _unlock_dependents(project_id, module_name)

        state["updated_at"] = now


def _unlock_dependents(project_id: str, completed_module: str):
    """解锁依赖已完成模块的后续模块"""
    state = _project_states.get(project_id)
    if not state:
        return
    for name in MODULE_ORDER:
        mod = PIPELINE_MODULES[name]
        if completed_module in mod.dependencies:
            mod_state = state["modules"].get(name, {})
            if mod_state.get("status") == ModuleStatus.LOCKED.value:
                # 检查所有依赖是否已完成
                deps_done = all(
                    state["modules"].get(dep, {}).get("status") == ModuleStatus.DONE.value
                    for dep in mod.dependencies
                )
                if deps_done:
                    mod_state["status"] = ModuleStatus.PENDING.value


def get_pipeline_progress(project_id: str) -> Dict[str, Any]:
    """获取流水线整体进度"""
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


def get_executionlayer_state(project_id: str) -> Dict[str, Any]:
    """获取执行层闭环状态(M13-M18)"""
    state = get_or_create_state(project_id)
    execution_modules = {}
    for name in ["scene_design", "draft_generation", "content_parsing",
                     "polish", "knowledge_update", "consistency_check"]:
        execution_modules[name] = state["modules"].get(name, {})
    return execution_modules


def is_execution_loop_complete(project_id: str, chapter_no: str = None) -> bool:
    """检查执行闭环是否全部通过"""
    state = get_or_create_state(project_id)
    required = ["scene_design", "draft_generation"]
    for name in required:
        if state["modules"].get(name, {}).get("status") != ModuleStatus.DONE.value:
            return False
    # 检查一致性评分
    cc_state = state["modules"].get("consistency_check", {})
    if cc_state.get("status") == ModuleStatus.DONE.value:
        score = cc_state.get("consistency_score", 0)
        return score >= 0.7
    return False


def cleanup_project_state(project_id: str):
    """清理项目流水线状态"""
    with _state_lock:
        _project_states.pop(project_id, None)


def get_module_info(module_name: str) -> Optional[Dict[str, Any]]:
    """获取模块元信息"""
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


def get_all_modules_info() -> List[Dict[str, Any]]:
    """获取所有模块元信息(按执行顺序)"""
    return [get_module_info(name) for name in MODULE_ORDER]


# ========== 模块验证回调 ==========

_module_validators: Dict[str, Callable] = {}


def register_validator(module_name: str, validator: Callable):
    """注册模块完成后的验证回调"""
    _module_validators[module_name] = validator


def validate_module_output(project_id: str, module_name: str, output: Any) -> tuple:
    """验证模块输出是否有效"""
    validator = _module_validators.get(module_name)
    if validator:
        try:
            return validator(project_id, output)
        except Exception as e:
            return False, f"验证失败: {e}"
    return True, ""
