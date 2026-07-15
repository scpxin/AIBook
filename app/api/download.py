import os
import urllib.request
import urllib.parse
import json
import re
import time
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, JSONResponse
from app.services.download_service import (
    create_download, get_status, pause_download, resume_download,
    get_file, get_saved_file, list_downloads, get_downloaded_content
)
from app.config import SEARCH_API, CONTENT_API, DIR_API, UA, HTTP_TIMEOUT, ALLOWED_PROXY_DOMAINS

router = APIRouter()


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.read()


def _resolve_book_id(q: str):
    m = re.search(r'(\d{16,20})', q)
    if not m:
        return None, None, None
    candidate = m.group(1)

    def extract(url):
        try:
            page = _http_get(url).decode('utf-8', errors='ignore')
            m2 = re.search(r'"bookId"\s*:\s*"(\d+)"', page); bid = m2.group(1) if m2 else None
            m2 = re.search(r'"bookName"\s*:\s*"([^"]+)"', page); title = m2.group(1) if m2 else None
            m2 = re.search(r'"author"\s*:\s*"([^"]+)"', page); author = m2.group(1) if m2 else None
            return bid, title, author
        except (urllib.error.URLError, OSError, UnicodeDecodeError):
            return None, None, None

    if '/reader/' in q:
        return extract(f'https://fanqienovel.com/reader/{candidate}')
    if '/page/' in q:
        bid, title, author = extract(f'https://fanqienovel.com/page/{candidate}')
        return candidate if not bid else bid, title, author

    bid, title, author = extract(f'https://fanqienovel.com/reader/{candidate}')
    if bid:
        return bid, title, author

    try:
        _http_get(DIR_API.format(candidate))
        return candidate, *extract(f'https://fanqienovel.com/page/{candidate}')[1:]
    except (urllib.error.URLError, OSError):
        pass

    return candidate, None, None


def _get_chapter_count(book_id: str) -> int:
    try:
        data = _http_get(DIR_API.format(book_id))
        return len(json.loads(data).get('data', {}).get('allItemIds', []))
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return 0


@router.get("/api/health")
def health():
    return {"ok": True, "status": "running", "time": time.strftime('%Y-%m-%d %H:%M:%S')}


@router.get("/api/search")
def search(q: str = ''):
    if not q:
        return {"error": "missing q"}
    if not SEARCH_API:
        return JSONResponse({"error": "search source not configured", "books": []}, status_code=503)
    data = _http_get(SEARCH_API.format(urllib.parse.quote(q)))
    result = json.loads(data)
    books = []
    for item in result.get('data', {}).get('ret_data', []):
        books.append({
            'book_id': item.get('book_id'),
            'title': item.get('title', ''),
            'author': item.get('author', ''),
            'cover': item.get('thumb_url', ''),
        })
    return {"books": books}


@router.get("/api/directory")
def directory(book_id: str = ''):
    if not book_id:
        return {"error": "missing book_id"}
    data = _http_get(DIR_API.format(book_id))
    result = json.loads(data).get('data', {})
    ids = result.get('allItemIds', [])
    return {"total": len(ids), "ids": ids}


@router.get("/api/content")
def content(item_id: str = ''):
    if not item_id:
        return {"error": "missing item_id"}
    data = _http_get(CONTENT_API.format(item_id))
    result = json.loads(data)
    if result.get('code') == 200:
        return {"content": result['data']['content']}
    else:
        return {"error": result.get('message', 'unknown')}


@router.get("/api/resolve")
def resolve(q: str = ''):
    if not q:
        return {"error": "missing q"}
    book_id, title, author = _resolve_book_id(q)
    if book_id:
        count = _get_chapter_count(book_id)
        return {"book_id": book_id, "count": count, "title": title, "author": author}
    else:
        return {"error": "无法识别链接"}


@router.get("/api/download/start")
def download_start(book_id: str = '', title: str = ''):
    if not book_id:
        return {"error": "missing book_id"}
    sid = create_download(book_id, title)
    return {"session_id": sid}


@router.get("/api/download/status")
def download_status(session_id: str = ''):
    status = get_status(session_id)
    if status is None:
        return {"error": "session not found"}
    return status


@router.get("/api/download/pause")
def download_pause(session_id: str = ''):
    ok = pause_download(session_id)
    if not ok:
        return {"error": "session not found"}
    return {"ok": True}


@router.get("/api/download/resume")
def download_resume(session_id: str = ''):
    result = resume_download(session_id)
    if result is None:
        return {"error": "session not found"}
    return {"ok": True, "note": result} if result in ('already done', 'not paused') else {"ok": True}


@router.get("/api/download/file")
def download_file(session_id: str = ''):
    result = get_file(session_id)
    if result is None:
        return {"error": "not done yet or session not found"}
    content_text, book_id = result
    return PlainTextResponse(
        content=content_text,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Disposition": f'attachment; filename=fanqie_{book_id}.txt',
            "Content-Length": str(len(content_text.encode('utf-8')))
        }
    )


@router.get("/api/download/saved")
def download_saved(book_id: str = ''):
    text = get_saved_file(book_id)
    if text is None:
        return {"error": "not found"}
    return PlainTextResponse(
        content=text,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Content-Disposition": f'attachment; filename=fanqie_{book_id}.txt',
            "Content-Length": str(len(text.encode('utf-8')))
        }
    )


@router.get("/api/downloads/list")
def downloads_list():
    books = list_downloads()
    return {"books": books}


@router.get("/api/downloads/content")
def downloads_content(book_id: str = ''):
    content_val = get_downloaded_content(book_id)
    if content_val is None:
        return {"error": "未找到该书籍内容"}
    return {"content": content_val, "length": len(content_val)}


@router.get("/api/proxy-text")
def proxy_text(url: str = ''):
    if not url:
        return {"error": "missing url"}
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_PROXY_DOMAINS:
        return {"error": "域名不在白名单中"}
    try:
        html_data = _http_get(url).decode('utf-8', errors='ignore')
        return PlainTextResponse(
            content=html_data,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        return {"error": str(e)}
