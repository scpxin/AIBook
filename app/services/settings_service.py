"""持久化设置服务 - SQLite 数据库存储"""
import json
import os
import threading

from novel_creator.database_v2 import get_setting, set_setting, get_all_settings

_lock = threading.RLock()

SETTINGS_KEY_MODELS = 'models'
SETTINGS_KEY_ACTIVE = 'active_model_id'


def get_settings() -> dict:
    """从数据库获取所有设置"""
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


def save_models(models: list, active_model_id: str = '') -> dict:
    """保存模型配置到数据库"""
    with _lock:
        set_setting(SETTINGS_KEY_MODELS, json.dumps(models, ensure_ascii=False))
        if active_model_id:
            set_setting(SETTINGS_KEY_ACTIVE, active_model_id)
    return get_settings()


def get_ai_config() -> dict | None:
    """获取AI模型配置，优先环境变量，其次数据库"""
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
            return {
                'endpoint': active['endpoint'],
                'api_key': active['apiKey'],
                'model': active.get('model', 'gpt-4o-mini'),
                'source': 'db',
            }
    return None
