#!/usr/bin/env python3
"""
阿里云 FC HTTP 函数 - 番茄小说代理 + AI 代理
零依赖，纯标准库

地址映射:
  GET  /api/search?q=xxx            → 搜索
  GET  /api/directory?bookId=xxx    → 目录
  GET  /api/content?item_id=xxx     → 章节内容
  POST /api/ai/generate             → AI 代理
  OPTIONS *                         → CORS 预检
"""

import json
import urllib.request
import urllib.parse
import os
import time

SEARCH_API = "https://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/?aid=1967&q="
DIR_API    = "https://fanqienovel.com/api/reader/directory/detail?bookId="
CONTENT_API = "http://101.35.133.34:5000/api/content?tab=%E5%B0%8F%E8%AF%B4&item_id="

BAIDU_API = "https://fanqienovel.com"

UA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

CORS_HEADERS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
    ("Access-Control-Allow-Headers", "*"),
    ("Access-Control-Max-Age", "86400"),
]


def proxy_get(url, referer=False):
    hdrs = dict(UA_HEADERS)
    if referer:
        hdrs["Referer"] = BAIDU_API + "/"
    else:
        hdrs["Referer"] = "https://fanqienovel.com/"

    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"code": e.code, "error": body[:300]}
    except Exception as e:
        return {"code": 500, "error": str(e)}


def json_resp(start_response, data, status="200 OK"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = CORS_HEADERS + [("Content-Type", "application/json; charset=utf-8")]
    start_response(status, headers)
    return [body]


def handler(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path   = environ.get("PATH_INFO", "/")
    qs     = environ.get("QUERY_STRING", "")
    args   = urllib.parse.parse_qs(qs)

    # ---- CORS preflight ----
    if method == "OPTIONS":
        start_response("204 No Content", CORS_HEADERS)
        return [b""]

    # ---- force redirect to https (FC passes X-Forwarded-Proto) ----
    # Not needed because FC HTTP trigger handles TLS termination.

    # ---- REST API routes ----
    if method == "GET":
        if path == "/api/search":
            keyword = args.get("q", [""])[0]
            data = proxy_get(SEARCH_API + urllib.parse.quote(keyword))
            return json_resp(start_response, data)

        if path == "/api/directory":
            book_id = args.get("bookId", [""])[0]
            if not book_id:
                return json_resp(start_response, {"error": "missing bookId"}, "400 Bad Request")
            data = proxy_get(DIR_API + book_id)
            return json_resp(start_response, data)

        if path == "/api/content":
            item_id = args.get("item_id", [""])[0]
            if not item_id:
                return json_resp(start_response, {"error": "missing item_id"}, "400 Bad Request")
            data = proxy_get(CONTENT_API + item_id, referer=False)
            return json_resp(start_response, data)

    # ---- AI proxy ----
    if method == "POST" and path == "/api/ai/generate":
        try:
            length = int(environ.get("CONTENT_LENGTH", 0))
            raw = environ["wsgi.input"].read(length)
            body = json.loads(raw)

            endpoint = body.get("endpoint", "")
            api_key  = body.get("apiKey", "")
            model    = body.get("model", "")
            messages = body.get("messages", [])
            options  = body.get("options", {})

            if not all([endpoint, api_key, model, messages]):
                return json_resp(start_response, {"error": "缺少必填字段"}, "400 Bad Request")

            req_body = json.dumps({
                "model": model,
                "messages": messages,
                "temperature": options.get("temperature", 0.7),
                "max_tokens": options.get("max_tokens", 4096),
            }).encode("utf-8")

            # 不传 Referer，避免被 AI 平台拦截
            req = urllib.request.Request(endpoint, data=req_body, headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            })

            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            content = ""
            if data.get("choices") and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                content = msg.get("content", "")

            return json_resp(start_response, {"content": content, "usage": data.get("usage")})

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            return json_resp(start_response, {"error": f"AI API {e.code}: {body[:300]}"}, "502 Bad Gateway")
        except Exception as e:
            return json_resp(start_response, {"error": str(e)}, "500 Internal Server Error")

    # ---- 404 ----
    return json_resp(start_response, {"error": "not found", "path": path}, "404 Not Found")
