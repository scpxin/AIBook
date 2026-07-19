"""AI 客户端 - 支持 OpenAI 兼容 API"""
import json
import os
import re
import ssl
import urllib.error
import urllib.request

_ssl_context = ssl.create_default_context()
if os.getenv("AI_VERIFY_SSL", "true").lower() == "false":
    _ssl_context.check_hostname = False
    _ssl_context.verify_mode = ssl.CERT_NONE


class AIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000, timeout=600):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _build_request(self, body):
        """构建 HTTP 请求对象

        支持两种填写方式：
        - 完整 URL：https://api.longcat.chat/openai/v1/chat/completions
        - Base URL：https://api.longcat.chat/openai  (自动拼接 /v1/chat/completions)
        """
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            url = base
        elif base.endswith("/v1"):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/v1/chat/completions"
        data = json.dumps(body).encode("utf-8")
        return urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )

    def _build_messages(self, prompt, system_prompt):
        """构建消息列表"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _clean_error_body(self, error_body):
        """清洗错误响应（去除HTML标签）"""
        return re.sub(r'<[^>]+>', '', error_body).strip()[:200]

    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """非流式文本生成"""
        body = {
            "model": self.model,
            "messages": self._build_messages(prompt, system_prompt),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        try:
            req = self._build_request(body)
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_context) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = self._clean_error_body(e.read().decode("utf-8", errors="ignore"))
            return None, f"API错误 {e.code}: {error_body}"
        except Exception as e:
            return None, str(e)

        if result.get("error"):
            return None, result["error"].get("message", str(result["error"]))

        choices = result.get("choices", [])
        if not choices:
            return None, "AI返回空内容"

        content = choices[0].get("message", {}).get("content", "")
        return content, None

    def generate_stream(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """流式文本生成（生成器）- 超时600s"""
        body = {
            "model": self.model,
            "messages": self._build_messages(prompt, system_prompt),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
        }

        try:
            req = self._build_request(body)
            with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_context) as resp:
                for line in resp:
                    line = line.decode("utf-8", errors="ignore").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        yield {"done": True}
                        return
                    try:
                        obj = json.loads(chunk)
                        if obj.get("error"):
                            yield {"error": obj["error"].get("message", str(obj["error"]))}
                            return
                        choices = obj.get("choices", [])
                        if choices:
                            choice = choices[0]
                            delta = choice.get("delta", {})
                            content = delta.get("content", "")
                            if not content:
                                content = choice.get("text", "")
                            if content:
                                yield {"content": content}
                            finish_reason = choice.get("finish_reason")
                            if finish_reason in ("stop", "length", "content_filter"):
                                yield {"done": True}
                                return
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            error_body = self._clean_error_body(e.read().decode("utf-8", errors="ignore"))
            yield {"error": f"API错误 {e.code}: {error_body}"}
        except Exception as e:
            yield {"error": str(e)}
