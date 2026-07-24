import json
import logging
import os
import shutil
import threading
import time
import urllib.request
import uuid

from app.config import CONTENT_API, DIR_API, DOWNLOAD_DIR, HTTP_TIMEOUT, SESSION_TTL, UA

logger = logging.getLogger('novel_creator.download')

sessions: dict[str, dict] = {}
sessions_lock = threading.Lock()


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return r.read()


def _cleanup_loop():
    while True:
        time.sleep(3600)
        now = time.time()
        with sessions_lock:
            expired = [sid for sid, s in sessions.items() if now - s.get('created_at', 0) > SESSION_TTL]
            for sid in expired:
                sessions.pop(sid, None)


threading.Thread(target=_cleanup_loop, daemon=True).start()


def _download_worker(sid: str):
    with sessions_lock:
        s = sessions.get(sid)
        if not s:
            return
    book_id = s['book_id']
    try:
        data = _http_get(DIR_API.format(book_id))
        item_ids = json.loads(data).get('data', {}).get('allItemIds', [])
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        with sessions_lock:
            if sid in sessions:
                sessions[sid]['status'] = 'error'
        return

    with sessions_lock:
        s['total'] = len(item_ids)
        s['item_ids'] = item_ids
        s['content'] = []
        if s['total'] == 0:
            s['status'] = 'done'
            return

    book_dir = os.path.join(DOWNLOAD_DIR, book_id)
    os.makedirs(book_dir, exist_ok=True)

    for i in range(s['current'], len(item_ids)):
        with sessions_lock:
            s = sessions.get(sid)
            if not s or s['status'] == 'cancelled':
                return
            if s['paused']:
                break

        item_id = item_ids[i]
        try:
            data = _http_get(CONTENT_API.format(item_id))
            result = json.loads(data)
            if result.get('code') == 200:
                text = result['data']['content']
            else:
                text = '[获取失败]'
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
            text = '[下载失败]'

        with sessions_lock:
            s = sessions.get(sid)
            if not s:
                return
            s['content'].append(f'\n\n第{i+1}章\n\n{text}')
            s['current'] = i + 1
            if s['current'] >= s['total']:
                s['status'] = 'done'
                try:
                    full_text = ''.join(s['content'])
                    with open(os.path.join(book_dir, 'content.txt'), 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    with open(os.path.join(book_dir, 'meta.json'), 'w', encoding='utf-8') as f:
                        json.dump({'book_id': book_id, 'title': s.get('title', ''), 'total': s['total'], 'dir': book_dir}, f, ensure_ascii=False)
                except OSError as e:
                    logger.warning(f"保存章节文件失败: {e}")
                return

        if i < len(item_ids) - 1:
            time.sleep(0.5)


def create_download(book_id: str, title: str) -> str:
    book_dir = os.path.join(DOWNLOAD_DIR, str(book_id))
    if os.path.exists(book_dir):
        shutil.rmtree(book_dir)
    sid = uuid.uuid4().hex[:12]
    with sessions_lock:
        sessions[sid] = {
            'book_id': book_id, 'title': title, 'status': 'downloading',
            'total': 0, 'current': 0, 'paused': False,
            'content': [], 'started_at': time.time(), 'created_at': time.time()
        }
    threading.Thread(target=_download_worker, args=(sid,), daemon=True).start()
    return sid


def get_status(session_id: str) -> dict | None:
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return None
        return {
            'status': 'paused' if s['paused'] else s['status'],
            'total': s['total'],
            'current': s['current'],
            'elapsed': time.time() - s['started_at']
        }


def pause_download(session_id: str) -> bool:
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return False
        s['paused'] = True
        return True


def resume_download(session_id: str) -> str | None:
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return None
        if s['status'] == 'done':
            return 'already done'
        if not s['paused']:
            return 'not paused'
        s['paused'] = False
        s['status'] = 'downloading'
    threading.Thread(target=_download_worker, args=(session_id,), daemon=True).start()
    return 'ok'


def get_file(session_id: str) -> tuple | None:
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return None
        if s['status'] == 'downloading' and not s.get('paused'):
            return None
        content_text = ''.join(s['content'])
        book_id = str(s.get('book_id', ''))
        title = s.get('title', book_id)
        sessions.pop(session_id, None)
    try:
        book_dir = os.path.join(DOWNLOAD_DIR, book_id)
        if os.path.exists(book_dir):
            shutil.rmtree(book_dir)
        os.makedirs(book_dir, exist_ok=True)
        with open(os.path.join(book_dir, 'content.txt'), 'w', encoding='utf-8') as f:
            f.write(content_text)
        with open(os.path.join(book_dir, 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({'book_id': book_id, 'title': title, 'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')}, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存到磁盘失败: {e}")
    return (content_text, book_id)


def get_saved_file(book_id: str) -> str | None:
    book_dir = os.path.join(DOWNLOAD_DIR, book_id)
    content_file = os.path.join(book_dir, 'content.txt')
    if os.path.exists(content_file):
        with open(content_file, encoding='utf-8') as f:
            return f.read()
    return None


def list_downloads() -> list:
    books = []
    if os.path.isdir(DOWNLOAD_DIR):
        for book_id in os.listdir(DOWNLOAD_DIR):
            book_dir = os.path.join(DOWNLOAD_DIR, book_id)
            meta_file = os.path.join(book_dir, 'meta.json')
            content_file = os.path.join(book_dir, 'content.txt')
            if os.path.isfile(meta_file):
                try:
                    with open(meta_file, encoding='utf-8') as f:
                        meta = json.load(f)
                    size = os.path.getsize(content_file) if os.path.isfile(content_file) else 0
                    books.append({
                        'book_id': book_id,
                        'title': meta.get('title', book_id),
                        'total': meta.get('total', 0),
                        'size': size,
                        'dir': book_dir,
                    })
                except (OSError, json.JSONDecodeError):
                    pass
            elif os.path.isfile(content_file):
                size = os.path.getsize(content_file)
                books.append({
                    'book_id': book_id,
                    'title': book_id,
                    'total': 0,
                    'size': size,
                    'dir': book_dir,
                })
    return books


def get_downloaded_content(book_id: str) -> str | None:
    book_dir = os.path.join(DOWNLOAD_DIR, book_id)
    content_file = os.path.join(book_dir, 'content.txt')
    if not os.path.exists(content_file):
        return None
    with open(content_file, encoding='utf-8') as f:
        return f.read()
