"""统一错误处理工具"""

def safe_error(err: str) -> str:
    """脱敏错误消息，避免内部异常暴露给客户端"""
    if not err:
        return "服务暂时不可用"
    if any(kw in err.lower() for kw in ['urlopen', 'connection', 'timeout', 'name resolution', 'refused']):
        return "AI 生成服务暂时不可用，请检查网络连接和 API 配置"
    if any(kw in err.lower() for kw in ['json', 'decode', 'parse', 'schema']):
        return "AI 返回数据格式异常，请稍后重试"
    if '未配置' in err or 'not configured' in err.lower():
        return "AI 生成器未配置，请先在设置中配置模型"
    return str(err)[:200]


def categorize_error(err: str) -> tuple[str, int]:
    """分类错误并返回 (安全消息, HTTP状态码)"""
    if not err:
        return ("服务暂时不可用", 500)

    err_lower = err.lower()

    client_keywords = ['required', 'missing', '不能为空', 'invalid', '必须在', '超出范围', 'too long', 'too large']
    if any(kw in err_lower or kw in err for kw in client_keywords):
        return (safe_error(err), 400)

    not_found_keywords = ['not found', '不存在', '未找到']
    if any(kw in err_lower or kw in err for kw in not_found_keywords):
        return (safe_error(err), 400)

    server_keywords = ['urlopen', 'connection', 'timeout', 'name resolution', 'refused', 'json', 'decode', 'parse', 'schema']
    if any(kw in err_lower for kw in server_keywords):
        return (safe_error(err), 500)

    if '未配置' in err or 'not configured' in err_lower:
        return (safe_error(err), 503)

    if '不可用' in err or 'not available' in err_lower:
        return (safe_error(err), 503)

    return (safe_error(err), 500)
