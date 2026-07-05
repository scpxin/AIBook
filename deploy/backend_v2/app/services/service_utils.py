"""共享服务工具函数 — 避免重复代码"""
import os
import sys

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, os.path.normpath(_BASE))

from app.services.novel_generator import get_generator


def get_default_generator():
    """获取默认AI生成器"""
    endpoint = os.environ.get('AI_ENDPOINT', '')
    api_key = os.environ.get('AI_API_KEY', '')
    model = os.environ.get('AI_MODEL', 'gpt-4o-mini')
    if not endpoint or not api_key:
        return None
    return get_generator(endpoint, api_key, model)


def safe_json_str(obj, max_len=1500):
    """将对象JSON序列化并截断"""
    import json
    s = json.dumps(obj or {}, ensure_ascii=False)
    return s[:max_len]
