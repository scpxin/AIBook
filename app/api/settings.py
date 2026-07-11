"""设置API — 模型配置的持久化读写"""
import re
from fastapi import APIRouter, HTTPException

from app.services.settings_service import get_settings, save_models
from app.models.v2_schemas import SettingsSaveModelsRequest

router = APIRouter(prefix="/api/v2/settings", tags=["设置"])


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
