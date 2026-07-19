"""设置API — 模型配置的持久化读写"""
import json
import urllib.error
import urllib.request

from fastapi import APIRouter, Body

from app.models.v2_schemas import SettingsSaveModelsRequest
from app.services.settings_service import get_settings, save_models

router = APIRouter(prefix="/api/v2/settings", tags=["设置"])


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
    req_timeout = min(timeout, 600)
    try:
        resp = urllib.request.urlopen(req, timeout=req_timeout)
        body = json.loads(resp.read().decode('utf-8'))
        content = body.get('choices', [{}])[0].get('message', {}).get('content', '')
        return content, None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)[:300]


@router.get("")
def get_all():
    """获取所有设置（模型列表中 apiKey 脱敏处理）"""
    data = get_settings()
    for m in data.get('models', []):
        key = m.get('apiKey', '')
        if len(key) > 8:
            m['apiKey'] = key[:4] + '...' + key[-4:]
        else:
            m['apiKey'] = '***'
    return data


@router.post("/models")
def save_model_list(payload: SettingsSaveModelsRequest):
    """保存模型配置列表"""
    # Convert Pydantic models to dicts for JSON serialization
    models = [m.model_dump() for m in payload.models]
    save_models(models, payload.activeModelId)
    return {"ok": True, "count": len(payload.models)}


@router.post("/test-connection")
def test_connection(body: dict = Body(...)):
    """测试AI模型连接"""
    endpoint = body.get('endpoint', '')
    api_key = body.get('apiKey', '')
    model_id = body.get('model', '')
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
