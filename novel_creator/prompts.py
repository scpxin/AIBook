"""小说创作 Prompt 工具函数 - 格式化器和JSON解析器"""
import json
import logging
import string

logger = logging.getLogger("novel_creator.prompts")

class SafeFormatter(string.Formatter):
    """安全的字符串格式化器：缺失的 key 替换为空字符串，不会抛 KeyError"""
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            return kwargs.get(key, "")
        return super().get_value(key, args, kwargs)


_safe_formatter = SafeFormatter()


def format_prompt(template, **kwargs):
    """安全格式化 prompt 模板。

    自动转义用户值中的大括号（防止被误认为是 placeholder），
    且模板中未传入的 placeholder 会被替换为空字符串，不会抛 KeyError。
    """
    safe_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, str):
            v = v.replace("{", "{{").replace("}", "}}")
        safe_kwargs[k] = v
    return _safe_formatter.format(template, **safe_kwargs)


def parse_json_response(text):
    """从AI响应中解析JSON"""
    if not text:
        logger.warning("parse_json_response: empty text")
        return None
    text = text.strip()
    logger.debug(f"parse_json_response: {len(text)} chars, first 200: {text[:200]!r}")
    import re
    # 优先提取代码块内容（```json ... ``` 或 ``` ... ``` 或 '''json ... ''' 等）
    block_pattern = r'(?:```|~~~|\'\'\')(?:json|javascript)?\s*\n?(.*?)\n?\s*(?:```|~~~|\'\'\')'
    blocks = re.findall(block_pattern, text, re.DOTALL | re.IGNORECASE)
    logger.debug(f"parse_json_response: found {len(blocks)} code blocks")
    for block in blocks:
        stripped = block.strip()
        try:
            result = json.loads(stripped)
            logger.debug("parse_json_response: block direct parse OK")
            return result
        except json.JSONDecodeError:
            pass
        # 代码块内可能仍有前后缀，尝试提取第一个JSON对象
        for match in re.finditer(r'[\{\[]', stripped):
            try:
                result = json.loads(stripped[match.start():])
                logger.debug("parse_json_response: block inner JSON parse OK")
                return result
            except json.JSONDecodeError:
                continue
    # 去除所有代码块标记，保留纯文本
    cleaned = re.sub(r'(?:```|~~~|\'\'\')(?:json|javascript)?\s*\n?', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'(?:```|~~~|\'\'\')\s*$', '', cleaned.strip())
    cleaned = cleaned.strip()
    # 尝试直接解析清理后的文本
    try:
        result = json.loads(cleaned)
        logger.debug("parse_json_response: cleaned direct parse OK")
        return result
    except json.JSONDecodeError:
        pass
    # 尝试找到第一个完整的 JSON 对象
    for match in re.finditer(r'[\{\[]', cleaned):
        candidate = cleaned[match.start():]
        try:
            result = json.loads(candidate)
            logger.debug(f"parse_json_response: substring parse OK at pos {match.start()}")
            return result
        except json.JSONDecodeError:
            continue
    # 尝试修复截断的JSON：关闭未闭合的括号和引号
    for match in re.finditer(r'[\{\[]', cleaned):
        candidate = cleaned[match.start():]
        fixed = _fix_truncated_json(candidate)
        if fixed is not None:
            logger.info(f"parse_json_response: truncated JSON fixed at pos {match.start()}")
            return fixed
    logger.error(f"parse_json_response: all methods failed for {len(text)} chars")
    return None


def _fix_truncated_json(text):
    """尝试修复截断的JSON字符串 - 关闭未闭合的括号和字符串"""
    import json as _json
    stack = []
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in '{[':
            stack.append(ch)
        elif ch in '}]':
            if stack:
                opening = stack[-1]
                if (ch == '}' and opening == '{') or (ch == ']' and opening == '['):
                    stack.pop()
                else:
                    return None

    # 移除末尾不完整的 token（如未完成的属性值）
    text = text.rstrip()
    # 如果末尾是逗号，移除
    if text.endswith(','):
        text = text[:-1]

    # 未闭合的字符串 - 关闭它
    if in_string:
        text = text + '"'

    # 关闭所有未闭合的括号
    for ch in reversed(stack):
        text = text + ('}' if ch == '{' else ']')

    try:
        return _json.loads(text)
    except _json.JSONDecodeError:
        return None

# 从 templates 模块重新导出所有模板常量，保持向后兼容
from .prompts_templates import *  # noqa: F403
