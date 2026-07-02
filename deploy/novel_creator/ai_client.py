"""AI 客户端 - 支持 OpenAI 兼容 API"""
import json
import urllib.request
import urllib.error


class AIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        """非流式文本生成"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            return None, f"API错误 {e.code}: {error_body[:200]}"
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
        """流式文本生成（生成器）"""
        import ssl

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": True,
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        # 允许自签名证书
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, timeout=120, context=ssl_context) as resp:
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
                        choices = obj.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield {"content": content}
                            if choices[0].get("finish_reason") == "stop":
                                yield {"done": True}
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            yield {"error": f"API错误 {e.code}: {error_body[:200]}"}
        except Exception as e:
            yield {"error": str(e)}
