def validate_ai_config(body: dict):
    """验证并提取 AI 配置参数"""
    endpoint = body.get('endpoint', '')
    api_key = body.get('apiKey', '')
    model = body.get('model', '')
    if not all([endpoint, api_key, model]):
        return None
    return {'endpoint': endpoint, 'api_key': api_key, 'model': model}
