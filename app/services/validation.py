"""AI返回结构校验工具"""

REQUIRED_KEYS = {
    "idea": ["concept"],
    "world_origin": ["cosmology"],
    "protagonist": ["name"],
    "supporting": ["name"],
    "villains": [],
    "master_outline": [],
    "volumes": ["volumes"],
    "chapter_plan": [],
    "chapter_outline": ["scenes"],
    "scene_design": ["setting"],
    "draft": ["content"],
    "polish": ["content"],
    "content_parse": ["scene_segments"],
}


def validate_result(module_name: str, result) -> tuple:
    """校验AI返回是否包含必要字段. 返回 (is_valid, error_msg)"""
    if result is None:
        return False, f"{module_name}: 返回None"
    if isinstance(result, list):
        if not result:
            return False, f"{module_name}: 返回空数组"
        return True, ""
    if not isinstance(result, dict):
        return False, f"{module_name}: 非dict格式"
    if not result:
        return False, f"{module_name}: 返回空对象"
    required = REQUIRED_KEYS.get(module_name, [])
    missing = [k for k in required if not result.get(k)]
    if missing:
        if len(result) == 1:
            return True, ""
        return False, f"{module_name}: 缺少必要字段: {missing}"
    return True, ""
