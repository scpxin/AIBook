"""共享服务工具函数 — 避免重复代码"""
import os
import sys

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.normpath(_BASE))

from app.services.novel_generator import get_generator
from app.services.settings_service import get_ai_config


def get_default_generator():
    """获取默认AI生成器"""
    cfg = get_ai_config()
    if not cfg:
        return None
    return get_generator(cfg['endpoint'], cfg['api_key'], cfg['model'])


def safe_json_str(obj, max_len=1500):
    """将对象JSON序列化并截断"""
    import json
    s = json.dumps(obj or {}, ensure_ascii=False)
    return s[:max_len]


def build_style_str(style_profile: dict = None) -> str:
    """构建风格提示词片段（从style_profile提取关键风格信息）"""
    if not style_profile:
        return ""
    parts = []
    for key in ['narrative_perspective', 'tone', 'pacing', 'emotional_intensity']:
        val = style_profile.get(key)
        if val:
            parts.append(f"- {key}: {val}")
    if not parts:
        return ""
    return "=== 参考风格 ===\n" + "\n".join(parts) + "\n\n"
