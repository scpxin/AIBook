"""AI 客户端 - 支持 OpenAI 兼容 API"""
import json
import os
import re

import httpx

_ssl_verify = os.getenv("AI_VERIFY_SSL", "true").lower() != "false"


class AIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000, timeout=600):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout), verify=_ssl_verify)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _build_url(self):
        base = self.base_url.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    def _build_messages(self, prompt, system_prompt):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _clean_error_body(self, error_body):
        return re.sub(r'<[^>]+>', '', error_body).strip()[:200]

    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        body = {
            "model": self.model,
            "messages": self._build_messages(prompt, system_prompt),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        try:
            resp = self._client.post(
                self._build_url(),
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            result = resp.json()
        except httpx.HTTPStatusError as e:
            error_body = self._clean_error_body(e.response.text)
            return None, f"API错误 {e.response.status_code}: {error_body}"
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
        body = {
            "model": self.model,
            "messages": self._build_messages(prompt, system_prompt),
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
        }

        try:
            with self._client.stream(
                "POST",
                self._build_url(),
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    line = line.strip()
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
        except httpx.HTTPStatusError as e:
            error_body = self._clean_error_body(e.response.text)
            yield {"error": f"API错误 {e.response.status_code}: {error_body}"}
        except Exception as e:
            yield {"error": str(e)}
