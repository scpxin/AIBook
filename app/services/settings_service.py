"""持久化设置服务 - SQLite 数据库存储"""
import json
import os
import threading

from novel_creator.database_v2 import get_all_settings, set_setting

_lock = threading.RLock()

SETTINGS_KEY_MODELS = 'models'
SETTINGS_KEY_ACTIVE = 'active_model_id'


def get_settings() -> dict:
    """从数据库获取所有设置

    与 save_models 共用同一把锁，避免读到"models 已更新但 active 未更新"的中间态。
    """
    with _lock:
        raw = get_all_settings()
        result = {}
        # 解析 models
        models_raw = raw.get(SETTINGS_KEY_MODELS, '')
        if models_raw:
            try:
                result['models'] = json.loads(models_raw)
            except (json.JSONDecodeError, TypeError):
                result['models'] = []
        else:
            result['models'] = []
        # 解析 activeModelId
        active = raw.get(SETTINGS_KEY_ACTIVE, '')
        if active:
            result['activeModelId'] = active
        return result


def _is_masked_api_key(key: str) -> bool:
    """识别后端脱敏格式 (prefix...suffix), 形如 sk-a1...wxyz"""
    if not key or '...' not in key:
        return False
    parts = key.split('...')
    if len(parts) != 2 or not all(parts):
        return False
    return True


def save_models(models: list, active_model_id: str = '') -> dict:
    """保存模型配置到数据库 (校验 endpoint 为公网地址, 防 SSRF)

    脱敏 apiKey (prefix...suffix) 视为未修改，保留数据库中已有原值，防止覆盖。
    """
    from app.utils.security import validate_public_endpoint

    with _lock:
        current = get_settings()
        existing = {m.get('id'): m.get('apiKey', '') for m in current.get('models', []) if m.get('id')}
        for m in models:
            endpoint = m.get('endpoint', '')
            if endpoint and not validate_public_endpoint(endpoint):
                raise ValueError(f"模型 {m.get('name', m.get('id', '未知'))} 的 endpoint 不在允许访问范围（SSRF 防护）")
            api_key = m.get('apiKey', '')
            if _is_masked_api_key(api_key):
                m['apiKey'] = existing.get(m.get('id'), api_key)
        set_setting(SETTINGS_KEY_MODELS, json.dumps(models, ensure_ascii=False))
        if active_model_id:
            set_setting(SETTINGS_KEY_ACTIVE, active_model_id)
    return get_settings()


def get_ai_config() -> dict | None:
    """获取AI模型配置，优先环境变量，其次数据库 (DB 来源做 SSRF 兜底校验)"""
    from app.utils.security import validate_public_endpoint

    endpoint = os.environ.get('AI_ENDPOINT', '')
    api_key = os.environ.get('AI_API_KEY', '')
    model = os.environ.get('AI_MODEL', '')

    if endpoint and api_key:
        return {
            'endpoint': endpoint,
            'api_key': api_key,
            'model': model or 'gpt-4o-mini',
            'source': 'env',
        }

    settings = get_settings()
    models = settings.get('models', [])
    active_id = settings.get('activeModelId', '')
    if models:
        active = next((m for m in models if m.get('id') == active_id), models[-1])
        if active.get('endpoint') and active.get('apiKey'):
            # SSRF 兜底: DB 中遗留的非法 endpoint 不参与运行时调用
            if not validate_public_endpoint(active['endpoint']):
                return None
            return {
                'endpoint': active['endpoint'],
                'api_key': active['apiKey'],
                'model': active.get('model', 'gpt-4o-mini'),
                'source': 'db',
            }
    return None
