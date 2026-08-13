"""settings_service 模型配置保存测试 — 重点覆盖脱敏 key 保留"""
import json
from unittest.mock import patch

import pytest

from app.services import settings_service


class TestIsMaskedApiKey:
    def test_masked_format_detected(self):
        assert settings_service._is_masked_api_key("sk-abcd...wxyz") is True

    def test_real_key_not_masked(self):
        assert settings_service._is_masked_api_key("sk-abcd123456wxyz") is False

    def test_empty_key(self):
        assert settings_service._is_masked_api_key("") is False

    def test_only_ellipsis(self):
        assert settings_service._is_masked_api_key("...") is False


def _run_save(models, active_id=''):
    """执行 save_models 并捕获 set_setting 写入的 models 内容"""
    saved = {}

    def fake_set_setting(key, value):
        saved[key] = value

    with patch('app.utils.security.validate_public_endpoint', return_value=True), \
         patch.object(settings_service, 'set_setting', fake_set_setting):
        settings_service.save_models(models, active_id)
    return json.loads(saved['models'])


class TestSaveModelsMaskedKeyPreserved:
    def test_masked_key_preserves_existing_value(self):
        current_models = [
            {'id': 'm1', 'name': '旧模型', 'endpoint': 'https://api.openai.com/v1',
             'apiKey': 'sk-real-secret-value-1234', 'model': 'gpt-4o-mini'}
        ]
        incoming = [
            {'id': 'm1', 'name': '改名模型', 'endpoint': 'https://api.openai.com/v1',
             'apiKey': 'sk-r...1234', 'model': 'gpt-4o-mini'}
        ]
        with patch.object(settings_service, 'get_settings', return_value={'models': current_models}):
            saved_models = _run_save(incoming, 'm1')
        assert saved_models[0]['apiKey'] == 'sk-real-secret-value-1234'
        assert saved_models[0]['name'] == '改名模型'

    def test_real_key_overwrites(self):
        current_models = [
            {'id': 'm1', 'name': 'm', 'endpoint': 'https://api.openai.com/v1',
             'apiKey': 'sk-old-value', 'model': 'm'}
        ]
        incoming = [
            {'id': 'm1', 'name': 'm', 'endpoint': 'https://api.openai.com/v1',
             'apiKey': 'sk-new-real-key', 'model': 'm'}
        ]
        with patch.object(settings_service, 'get_settings', return_value={'models': current_models}):
            saved_models = _run_save(incoming)
        assert saved_models[0]['apiKey'] == 'sk-new-real-key'

    def test_new_model_with_masked_key_keeps_mask(self):
        """无既有原值的新模型，脱敏串原样保留（由用户自行补充真实 key）"""
        incoming = [
            {'id': 'm2', 'name': '新模型', 'endpoint': 'https://api.openai.com/v1',
             'apiKey': 'sk-a...b', 'model': 'm'}
        ]
        with patch.object(settings_service, 'get_settings', return_value={'models': []}):
            saved_models = _run_save(incoming)
        assert saved_models[0]['apiKey'] == 'sk-a...b'

    def test_invalid_endpoint_rejected(self):
        incoming = [
            {'id': 'm1', 'name': 'm', 'endpoint': 'http://192.168.1.1/v1',
             'apiKey': 'sk-new-real-key', 'model': 'm'}
        ]
        with patch.object(settings_service, 'get_settings', return_value={'models': []}), \
             patch.object(settings_service, 'set_setting'):
            with pytest.raises(ValueError):
                settings_service.save_models(incoming, '')
