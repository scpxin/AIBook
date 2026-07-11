import json
import urllib.request
import urllib.error
from fastapi import APIRouter, Body
from app.models.schemas import AIAnalyzeRequest, AIGenerateRequest, AITestConnectionRequest

router = APIRouter()


def _ai_call(endpoint: str, api_key: str, model: str, messages: list, options: dict = None):
    timeout = (options or {}).get('timeout', 600)
    req_body = {
        'model': model,
        'messages': messages,
        'temperature': (options or {}).get('temperature', 0.7),
        'max_tokens': (options or {}).get('max_tokens', 4096),
        'stream': (options or {}).get('stream', False),
    }
    data = json.dumps(req_body).encode('utf-8')
    ep = endpoint.rstrip("/")
    if ep.endswith("/chat/completions"):
        url = ep
    elif ep.endswith("/v1"):
        url = f"{ep}/chat/completions"
    else:
        url = f"{ep}/v1/chat/completions"
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')[:500]
        return None, f'HTTP {e.code}: {body}'
    except Exception as e:
        return None, f'连接失败: {str(e)}'
    if result.get('error'):
        return None, result['error'].get('message', str(result['error']))
    choices = result.get('choices', [])
    if not choices:
        snippet = json.dumps(result, ensure_ascii=False)[:300]
        return None, f'AI 返回空内容（响应: {snippet}）'
    choice = choices[0]
    msg = choice.get('message', {})
    content = msg.get('content', '')
    if not content:
        content = msg.get('reasoning_content', '')
    if not content and 'content' in choice:
        content = choice['content']
    return content, None


@router.post("/api/ai/analyze")
def ai_analyze(body: AIAnalyzeRequest):
    endpoint = body.endpoint
    api_key = body.apiKey
    model = body.model
    content_text = body.content
    if not all([endpoint, api_key, model, content_text]):
        return {"error": "缺少参数"}
    messages = [
        {'role': 'system', 'content': '你是一位专业的小说分析家。请分析小说的写作风格特征，从以下维度输出结构化分析，每个维度用标签标记：\n【叙事视角】\n【句式特征】\n【词汇偏好】\n【对话风格】\n【节奏模式】\n【场景描写】\n每个维度50-100字，用中文输出。'},
        {'role': 'user', 'content': '请分析以下小说的写作风格：\n\n' + content_text[:6000]}
    ]
    result, err = _ai_call(endpoint, api_key, model, messages, {'temperature': 0.3, 'max_tokens': 2000})
    if err:
        return {"error": err}
    return {"result": result}


@router.post("/api/ai/generate")
def ai_generate(body: AIGenerateRequest):
    endpoint = body.endpoint
    api_key = body.apiKey
    model = body.model
    style_profile = body.styleProfile
    genre = body.genre
    count = min(body.count, 50)
    protagonist = body.protagonist
    world = body.world
    outline = body.outline
    if not all([endpoint, api_key, model, style_profile]):
        return {"error": "缺少参数"}
    messages = [
        {'role': 'system', 'content': '你是一位专业的小说作家。请根据提供的风格画像和创作设定创作小说。严格按照要求的风格写作，每章 1000-2000 字。输出格式：\n第X章 章节标题\n（正文）\n\n直接开始创作，不要额外说明。'},
        {'role': 'user', 'content': f'【风格画像】\n{style_profile}\n\n【创作设定】\n题材: {genre}\n主角: {protagonist}\n世界观: {world}\n故事梗概: {outline}\n\n请生成{count}章小说。'}
    ]
    result, err = _ai_call(endpoint, api_key, model, messages, {'temperature': 0.8, 'max_tokens': 4096})
    if err:
        return {"error": err}
    return {"result": result}


@router.post("/api/ai/raw-generate")
def ai_raw_generate(body: dict = Body(None)):
    """通用AI生成接口 - 自定义system/user prompt,返回原始文本"""
    if not body:
        return {"error": "请求体不能为空"}
    endpoint = body.get("endpoint", "")
    api_key = body.get("apiKey", "")
    model = body.get("model", "")
    system_prompt = body.get("system", "你是一个智能助手。")
    user_prompt = body.get("user", "")
    temperature = body.get("temperature", 0.8)
    max_tokens = body.get("maxTokens", 4000)
    if not all([endpoint, api_key, model, user_prompt]):
        return {"error": "缺少 endpoint / apiKey / model / user 参数"}
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        result, err = _ai_call(endpoint, api_key, model, messages,
                               {"temperature": temperature, "max_tokens": max_tokens, "timeout": 300})
        if err:
            return {"error": err}
        return {"result": result}
    except Exception as e:
        return {"error": str(e)[:300]}


@router.post("/api/ai/test-connection")
def test_connection(body: AITestConnectionRequest):
    endpoint = body.endpoint
    api_key = body.apiKey
    model_id = body.model
    if not all([endpoint, api_key, model_id]):
        return {"ok": False, "error": "缺少 endpoint / apiKey / model 参数"}
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant. Reply briefly.'},
        {'role': 'user', 'content': 'Say "OK" if you can hear me.'}
    ]
    try:
        result, err = _ai_call(endpoint, api_key, model_id, messages, {'temperature': 0, 'max_tokens': 32, 'timeout': 30})
        if err:
            return {"ok": False, "error": err}
        else:
            return {"ok": True, "model": model_id, "response": (result or '')[:100]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}
