import sys
import os
import json
import re
import logging
from typing import Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from novel_creator import NovelGenerator

logger = logging.getLogger('novel_creator.server')

_generator_cache: Dict[str, NovelGenerator] = {}


def _make_generator_key(endpoint: str, api_key: str, model: str) -> str:
    return f"{endpoint}|{api_key}|{model}"


def get_generator(endpoint: str, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 4000) -> NovelGenerator:
    key = _make_generator_key(endpoint, api_key, model)
    if key not in _generator_cache:
        _generator_cache[key] = NovelGenerator(
            api_key=api_key,
            base_url=endpoint,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _generator_cache[key]


def parse_style_profile(style_profile_str) -> Optional[Dict]:
    if not style_profile_str:
        return None
    if isinstance(style_profile_str, dict):
        return style_profile_str
    try:
        return json.loads(style_profile_str)
    except:
        return None


def send_gen_result(result, err, key=None):
    if err:
        return {"error": str(err)}, 500
    elif result is None:
        return {"error": "生成结果为空，请重试"}, 500
    else:
        return {key: result} if key else result, 200


def build_style_section(style) -> str:
    parts = []
    if style.get('narrative_perspective'):
        parts.append('- 叙事视角：' + style['narrative_perspective'])
    if style.get('tone'):
        parts.append('- 语言基调：' + style['tone'])
    if style.get('pacing'):
        parts.append('- 叙事节奏：' + style['pacing'])
    if style.get('emotional_intensity'):
        parts.append('- 情感浓度：' + style['emotional_intensity'])
    if style.get('overall_summary'):
        parts.append('- 风格总结：' + style['overall_summary'])
    if not parts:
        return ''
    return '=== 参考风格 ===\n' + '\n'.join(parts) + '\n\n'
