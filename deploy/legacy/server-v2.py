#!/usr/bin/env python3
"""番茄小说下载+AI创作平台 - 服务端 v2

===============================================================
环境变量配置
===============================================================
  PORT          HTTP 端口 (默认 8000)
  BASE_DIR     基础目录
  DOWNLOAD_DIR 下载文件目录
  DB_PATH      SQLite 数据库路径 (默认 BASE_DIR/fanqie.db)
  CONTENT_API  内容 API 地址
  SEARCH_API   搜索 API 地址
  AI_TIMEOUT   AI 调用超时秒数 (默认 600)
  SESSION_TTL  下载 session 过期秒数 (默认 86400 = 24h)
  MAX_BODY_SIZE 最大 POST body 字节数 (默认 50MB)

===============================================================
API 端点 (/fanqie/api/ 由 Nginx 反代为 /api/)
===============================================================
  创作流程:  inspiration/{title,description,theme,genre}, worldbuilding, characters,
             outline, book-overview, chapter-outline, chapter
  章节管理:  chapters/{save,get,delete,status,regeneration}, chapters/generation/{start,pause,stop,update}
  大纲管理:  outline/{save,get,delete}, outline/generation/{start,pause,stop,update}
  步骤摘要:  step-summary/{save,get}
  项目管理:  projects/{save,list,load,delete}
  网文技法:  craft/{detect-ai,fix-ai,golden-three,hooks,satisfaction,quality-score,chapter,titles,descriptions,report}
  AI 工具:  ai/{analyze,generate}, novel/{analyze-style,generate-style,analyze-chapter}
  小说下载:  search, directory, content, resolve, download/{start,status,pause,resume,file},
             downloads/{list,content}
===============================================================
"""
import http.server, urllib.request, urllib.parse, urllib.error, json, os, time, re, threading, uuid, sys, traceback, shutil, logging, sqlite3

PORT = int(os.environ.get('PORT', '8000'))
BASE_DIR = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', os.path.join(BASE_DIR, 'downloads'))
PROJECTS_DIR = os.environ.get('PROJECTS_DIR', os.path.join(BASE_DIR, 'projects'))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

CONTENT_API = os.environ.get('CONTENT_API', 'http://101.35.133.34:5000/api/content?tab=%E5%B0%8F%E8%AF%B4&item_id={}')
SEARCH_API = os.environ.get('SEARCH_API', 'https://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/?aid=1967&q={}&offset=0')
DIR_API = 'https://fanqienovel.com/api/reader/directory/detail?bookId={}'
AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '600'))
SESSION_TTL = int(os.environ.get('SESSION_TTL', '86400'))
TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', '20'))
MAX_BODY_SIZE = int(os.environ.get('MAX_BODY_SIZE', '52428800'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

sessions = {}
sessions_lock = threading.Lock()

# 小说创作模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from novel_creator import NovelGenerator
from novel_creator import database as novel_db
logging.basicConfig(
    filename=os.path.join(os.environ.get('LOG_DIR', '/app/data'), 'generate.log'),
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    encoding='utf-8'
)
novel_db.init_db()

# Session 清理：后台线程定期清理过期 session
def _session_cleanup():
    while True:
        time.sleep(3600)
        now = time.time()
        with sessions_lock:
            expired = [sid for sid, s in sessions.items() if now - s.get('created_at', 0) > SESSION_TTL]
            for sid in expired:
                sessions.pop(sid, None)

threading.Thread(target=_session_cleanup, daemon=True).start()


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def resolve_book_id(q):
    m = re.search(r'(\d{16,20})', q)
    if not m:
        return None, None, None
    candidate = m.group(1)

    def extract(url):
        try:
            page = http_get(url).decode('utf-8', errors='ignore')
            m2 = re.search(r'"bookId"\s*:\s*"(\d+)"', page); bid = m2.group(1) if m2 else None
            m2 = re.search(r'"bookName"\s*:\s*"([^"]+)"', page); title = m2.group(1) if m2 else None
            m2 = re.search(r'"author"\s*:\s*"([^"]+)"', page); author = m2.group(1) if m2 else None
            return bid, title, author
        except:
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
        http_get(DIR_API.format(candidate))
        return candidate, *extract(f'https://fanqienovel.com/page/{candidate}')[1:]
    except:
        pass

    return candidate, None, None


def get_chapter_count(book_id):
    try:
        data = http_get(DIR_API.format(book_id))
        return len(json.loads(data).get('data', {}).get('allItemIds', []))
    except:
        return 0


def download_worker(sid):
    """后台下载线程 - 保存到服务器"""
    with sessions_lock:
        s = sessions.get(sid)
        if not s:
            return
    book_id = s['book_id']
    try:
        data = http_get(DIR_API.format(book_id))
        item_ids = json.loads(data).get('data', {}).get('allItemIds', [])
    except:
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

    # 创建下载目录
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
            data = http_get(CONTENT_API.format(item_id))
            result = json.loads(data)
            if result.get('code') == 200:
                text = result['data']['content']
            else:
                text = '[获取失败]'
        except:
            text = '[下载失败]'

        with sessions_lock:
            s = sessions.get(sid)
            if not s:
                return
            s['content'].append(f'\n\n第{i+1}章\n\n{text}')
            s['current'] = i + 1
            if s['current'] >= s['total']:
                s['status'] = 'done'
                # 保存完整文件
                try:
                    full_text = ''.join(s['content'])
                    with open(os.path.join(book_dir, 'content.txt'), 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    with open(os.path.join(book_dir, 'meta.json'), 'w', encoding='utf-8') as f:
                        json.dump({'book_id': book_id, 'title': s.get('title', ''), 'total': s['total'], 'dir': book_dir}, f, ensure_ascii=False)
                except:
                    pass
                return

        if i < len(item_ids) - 1:
            time.sleep(0.5)


def ai_call(endpoint, api_key, model, messages, options=None):
    """调用外部 AI API"""
    timeout = (options or {}).get('timeout', AI_TIMEOUT)
    req_body = {
        'model': model,
        'messages': messages,
        'temperature': (options or {}).get('temperature', 0.7),
        'max_tokens': (options or {}).get('max_tokens', 4096),
        'stream': (options or {}).get('stream', False),
    }
    data = json.dumps(req_body).encode('utf-8')
    # 智能拼接 URL（兼容 LongCat 等需要 /v1/chat/completions 的 API）
    ep = endpoint.rstrip("/")
    if ep.endswith("/chat/completions"):
        url = ep
    elif ep.endswith("/v1"):
        url = f"{ep}/chat/completions"
    else:
        url = f"{ep}/v1/chat/completions"
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key,
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')[:500]
        return None, f'HTTP {e.code}: {body}'
    except Exception as e:
        return None, f'连接失败: {str(e)}'
    if result.get('error'):
        return None, result['error'].get('message', str(result['error']))
    choices = result.get('choices', [])
    if not choices:
        snippet = json.dumps(result, ensure_ascii=False)[:300]
        return None, f'AI 返回空内容（响应: {snippet}）'
    choice = choices[0]
    content = choice.get('message', {}).get('content', '')
    if not content and 'content' in choice:
        content = choice['content']
    return content, None


class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_POST(self):
        p = urllib.parse.urlparse(self.path)
        path = p.path

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > MAX_BODY_SIZE:
            self.send_json({'error': f'请求体过大（上限 {MAX_BODY_SIZE // 1024 // 1024}MB）'}, 413)
            return
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'

        try:
            data = json.loads(body)
        except:
            self.send_json({'error': '无效的 JSON 数据'}, 400)
            return

        try:
            # AI 分析
            if path == '/api/ai/analyze':
                self.handle_ai_analyze(data)
            # AI 生成
            elif path == '/api/ai/generate':
                self.handle_ai_generate(data)
            # 模型连接测试
            elif path == '/api/ai/test-connection':
                self.handle_test_connection(data)
            # ===== 项目管理 =====
            elif path == '/api/projects/save':
                self.handle_project_save(data)
            elif path == '/api/projects/list':
                self.handle_project_list(data)
            elif path == '/api/projects/load':
                self.handle_project_load(data)
            elif path == '/api/projects/delete':
                self.handle_project_delete(data)
            # ===== 章节管理 =====
            elif path == '/api/chapters/save':
                self.handle_chapter_save(data)
            elif path == '/api/chapters/get':
                self.handle_chapter_get(data)
            elif path == '/api/chapters/delete':
                self.handle_chapter_delete(data)
            elif path == '/api/chapters/regenerate':
                self.handle_chapter_regenerate(data)
            elif path == '/api/chapters/status':
                self.handle_generation_status(data)
            elif path == '/api/chapters/generation/start':
                self.handle_generation_start(data)
            elif path == '/api/chapters/generation/pause':
                self.handle_generation_pause(data)
            elif path == '/api/chapters/generation/stop':
                self.handle_generation_stop(data)
            elif path == '/api/chapters/generation/update':
                self.handle_generation_update_progress(data)
            # ===== 大纲管理 =====
            elif path == '/api/outline/save':
                self.handle_outline_save(data)
            elif path == '/api/outline/get':
                self.handle_outline_get(data)
            elif path == '/api/outline/delete':
                self.handle_outline_delete(data)
            elif path == '/api/outline/generation/start':
                self.handle_outline_generation_start(data)
            elif path == '/api/outline/generation/pause':
                self.handle_outline_generation_pause(data)
            elif path == '/api/outline/generation/stop':
                self.handle_outline_generation_stop(data)
            elif path == '/api/outline/generation/update':
                self.handle_outline_generation_update(data)
            # ===== 步骤摘要 =====
            elif path == '/api/step-summary/save':
                self.handle_step_summary_save(data)
            elif path == '/api/step-summary/get':
                self.handle_step_summary_get(data)
            # ===== 小说创作 (MuMuAINovel) =====
            elif path == '/api/novel/inspiration/title':
                self.handle_novel_inspiration_title(data)
            elif path == '/api/novel/inspiration/description':
                self.handle_novel_inspiration_description(data)
            elif path == '/api/novel/inspiration/theme':
                self.handle_novel_inspiration_theme(data)
            elif path == '/api/novel/inspiration/genre':
                self.handle_novel_inspiration_genre(data)
            elif path == '/api/novel/worldbuilding':
                self.handle_novel_worldbuilding(data)
            elif path == '/api/novel/characters':
                self.handle_novel_characters(data)
            elif path == '/api/novel/worldbuilding/reparse':
                self.handle_worldbuilding_reparse(data)
            elif path == '/api/novel/characters/reparse':
                self.handle_characters_reparse(data)
            elif path == '/api/novel/outline':
                self.handle_novel_outline(data)
            elif path == '/api/novel/book-overview':
                if data.get('stream'):
                    self.handle_stream(data, lambda gen, style, data: gen.generate_book_overview_stream(
                        title=data.get('title', ''), theme=data.get('theme', ''),
                        genre=data.get('genre', ''),
                        characters_info=data.get('charactersInfo', ''),
                        narrative_perspective=data.get('narrativePerspective', '第三人称'),
                        style_profile=style,
                        world_summary=data.get('worldSummary', ''),
                        inspiration_desc=data.get('inspirationDesc', '') or data.get('description', '')
                    ))
                else:
                    self.handle_novel_book_overview(data)
            elif path == '/api/novel/chapter-outline':
                if data.get('stream'):
                    self.handle_stream(data, lambda gen, style, data: gen.generate_chapter_outline_stream(
                        project_title=data.get('projectTitle', ''),
                        genre=data.get('genre', ''),
                        book_overview_json=data.get('bookOverview', ''),
                        chapter_number=int(data.get('chapterNumber', 1)),
                        total_chapters=int(data.get('totalChapters', 1)),
                        characters_info=data.get('charactersInfo', ''),
                        narrative_perspective=data.get('narrativePerspective', '第三人称'),
                        style_profile=style,
                        world_summary=data.get('worldSummary', ''),
                        prev_chapter_title=data.get('prevChapterTitle', ''),
                        prev_chapter_tail=data.get('prevChapterTail', ''),
                        use_craft=data.get('useCraft', False)
                    ))
                else:
                    self.handle_novel_chapter_outline(data)
            elif path == '/api/novel/chapter':
                self.handle_novel_chapter(data)
            elif path == '/api/novel/chapter/polish':
                self.handle_chapter_polish(data)
            elif path == '/api/novel/chapter/summarize':
                self.handle_chapter_summarize(data)
            elif path == '/api/novel/craft/chapter':
                self.handle_craft_chapter(data)
            elif path == '/api/novel/craft/titles':
                self.handle_craft_titles(data)
            elif path == '/api/novel/craft/descriptions':
                self.handle_craft_descriptions(data)
            elif path == '/api/novel/craft/report':
                self.handle_craft_report(data)
            else:
                self.send_json({'error': 'Not found'}, 404)
        except Exception as e:
            traceback.print_exc()
            self.send_json({'error': str(e)}, 500)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path = p.path
        params = dict(urllib.parse.parse_qsl(p.query))

        try:
            # --- 健康检查 ---
            if path == '/api/health':
                self.send_json({'ok': True, 'status': 'running', 'time': time.strftime('%Y-%m-%d %H:%M:%S')})
                return
            # --- 搜索 ---
            if path == '/api/search':
                q = params.get('q', '')
                if not q:
                    self.send_json({'error': 'missing q'}, 400); return
                data = http_get(SEARCH_API.format(urllib.parse.quote(q)))
                result = json.loads(data)
                books = []
                for item in result.get('data', {}).get('ret_data', []):
                    books.append({
                        'book_id': item.get('book_id'),
                        'title': item.get('title', ''),
                        'author': item.get('author', ''),
                        'cover': item.get('thumb_url', ''),
                    })
                self.send_json({'books': books})

            # --- 目录 ---
            elif path == '/api/directory':
                book_id = params.get('book_id', '')
                if not book_id:
                    self.send_json({'error': 'missing book_id'}, 400); return
                data = http_get(DIR_API.format(book_id))
                result = json.loads(data).get('data', {})
                ids = result.get('allItemIds', [])
                self.send_json({'total': len(ids), 'ids': ids})

            # --- 章节内容 ---
            elif path == '/api/content':
                item_id = params.get('item_id', '')
                if not item_id:
                    self.send_json({'error': 'missing item_id'}, 400); return
                data = http_get(CONTENT_API.format(item_id))
                result = json.loads(data)
                if result.get('code') == 200:
                    self.send_json({'content': result['data']['content']})
                else:
                    self.send_json({'error': result.get('message', 'unknown')}, 500)

            # --- 解析链接 ---
            elif path == '/api/resolve':
                q = params.get('q', '')
                if not q:
                    self.send_json({'error': 'missing q'}, 400); return
                book_id, title, author = resolve_book_id(q)
                if book_id:
                    count = get_chapter_count(book_id)
                    self.send_json({'book_id': book_id, 'count': count, 'title': title, 'author': author})
                else:
                    self.send_json({'error': '无法识别链接'}, 400)

            # --- 下载 ---
            elif path == '/api/download/start':
                book_id = params.get('book_id', '')
                title = params.get('title', '')
                if not book_id:
                    self.send_json({'error': 'missing book_id'}, 400); return
                # 清理旧的同名书籍目录
                book_dir = os.path.join(DOWNLOAD_DIR, str(book_id))
                if os.path.exists(book_dir):
                    import shutil
                    shutil.rmtree(book_dir)
                sid = uuid.uuid4().hex[:12]
                with sessions_lock:
                    sessions[sid] = {
                        'book_id': book_id, 'title': title, 'status': 'downloading',
                        'total': 0, 'current': 0, 'paused': False,
                        'content': [], 'started_at': time.time(), 'created_at': time.time()
                    }
                threading.Thread(target=download_worker, args=(sid,), daemon=True).start()
                self.send_json({'session_id': sid})

            elif path == '/api/download/status':
                sid = params.get('session_id', '')
                with sessions_lock:
                    s = sessions.get(sid)
                    if not s:
                        self.send_json({'error': 'session not found'}, 404); return
                    resp = {
                        'status': 'paused' if s['paused'] else s['status'],
                        'total': s['total'],
                        'current': s['current'],
                        'elapsed': time.time() - s['started_at']
                    }
                self.send_json(resp)

            elif path == '/api/download/pause':
                sid = params.get('session_id', '')
                with sessions_lock:
                    s = sessions.get(sid)
                    if not s:
                        self.send_json({'error': 'session not found'}, 404); return
                    s['paused'] = True
                self.send_json({'ok': True})

            elif path == '/api/download/resume':
                sid = params.get('session_id', '')
                with sessions_lock:
                    s = sessions.get(sid)
                    if not s:
                        self.send_json({'error': 'session not found'}, 404); return
                    if s['status'] == 'done':
                        self.send_json({'ok': True, 'note': 'already done'}); return
                    if not s['paused']:
                        self.send_json({'ok': True, 'note': 'not paused'}); return
                    s['paused'] = False
                    s['status'] = 'downloading'
                threading.Thread(target=download_worker, args=(sid,), daemon=True).start()
                self.send_json({'ok': True})

            elif path == '/api/download/file':
                sid = params.get('session_id', '')
                with sessions_lock:
                    s = sessions.get(sid)
                    if not s:
                        self.send_json({'error': 'session not found'}, 404); return
                    if s['status'] == 'downloading' and not s.get('paused'):
                        self.send_json({'error': f'not done yet, status={s["status"]}'}, 400); return
                    content_text = ''.join(s['content'])
                    book_id = str(s.get('book_id', ''))
                    title = s.get('title', book_id)
                    sessions.pop(sid, None)
                # 同步保存到服务器磁盘（同名覆盖）
                try:
                    book_dir = os.path.join(DOWNLOAD_DIR, book_id)
                    if os.path.exists(book_dir):
                        import shutil
                        shutil.rmtree(book_dir)
                    os.makedirs(book_dir, exist_ok=True)
                    with open(os.path.join(book_dir, 'content.txt'), 'w', encoding='utf-8') as f:
                        f.write(content_text)
                    with open(os.path.join(book_dir, 'meta.json'), 'w', encoding='utf-8') as f:
                        json.dump({'book_id': book_id, 'title': title, 'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')}, f, ensure_ascii=False)
                except Exception as e:
                    print(f"保存到磁盘失败: {e}")
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename=fanqie_{book_id}.txt')
                self.send_header('Content-Length', str(len(content_text.encode('utf-8'))))
                self.end_headers()
                self.wfile.write(content_text.encode('utf-8'))

            elif path == '/api/download/saved':
                book_id = params.get('book_id', '')
                book_dir = os.path.join(DOWNLOAD_DIR, book_id)
                content_file = os.path.join(book_dir, 'content.txt')
                if os.path.exists(content_file):
                    with open(content_file, 'r', encoding='utf-8') as f:
                        text = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.send_header('Content-Disposition', f'attachment; filename=fanqie_{book_id}.txt')
                    self.send_header('Content-Length', str(len(text.encode('utf-8'))))
                    self.end_headers()
                    self.wfile.write(text.encode('utf-8'))
                else:
                    self.send_json({'error': 'not found'}, 404)

            # --- 已下载书籍列表 ---
            elif path == '/api/downloads/list':
                books = []
                if os.path.isdir(DOWNLOAD_DIR):
                    for book_id in os.listdir(DOWNLOAD_DIR):
                        book_dir = os.path.join(DOWNLOAD_DIR, book_id)
                        meta_file = os.path.join(book_dir, 'meta.json')
                        content_file = os.path.join(book_dir, 'content.txt')
                        if os.path.isfile(meta_file):
                            try:
                                with open(meta_file, 'r', encoding='utf-8') as f:
                                    meta = json.load(f)
                                size = os.path.getsize(content_file) if os.path.isfile(content_file) else 0
                                books.append({
                                    'book_id': book_id,
                                    'title': meta.get('title', book_id),
                                    'total': meta.get('total', 0),
                                    'size': size,
                                    'dir': book_dir,
                                })
                            except:
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
                self.send_json({'books': books})

            # --- 已下载书籍内容 ---
            elif path == '/api/downloads/content':
                book_id = params.get('book_id', '')
                book_dir = os.path.join(DOWNLOAD_DIR, book_id)
                content_file = os.path.join(book_dir, 'content.txt')
                if not os.path.exists(content_file):
                    self.send_json({'error': '未找到该书籍内容'}, 404); return
                with open(content_file, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                self.send_json({'content': full_text, 'length': len(full_text)})

            # --- 页面代理 (SSRF 防护：仅允许特定域名) ---
            elif path == '/api/proxy-text':
                target_url = params.get('url', '')
                if not target_url:
                    self.send_json({'error': 'missing url'}, 400); return
                from urllib.parse import urlparse
                parsed = urlparse(target_url)
                allowed_domains = ['fanqienovel.com', 'snssdk.com', 'novel.snssdk.com']
                if parsed.hostname not in allowed_domains:
                    self.send_json({'error': '域名不在白名单中'}, 403); return
                try:
                    html_data = http_get(target_url).decode('utf-8', errors='ignore')
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(html_data.encode('utf-8'))
                except Exception as e:
                    self.send_json({'error': str(e)}, 500)

            # --- 项目管理 (GET 快捷访问) ---
            elif path == '/api/projects':
                self.handle_project_list({})

            else:
                self.send_json({'error': 'Not found'}, 404)

        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    # ===== 项目管理 =====

    def _validate_project_id(self, project_id):
        """校验 project_id 格式，防止路径遍历"""
        if not project_id or not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', project_id):
            return False
        return True

    def handle_project_save(self, data):
        """保存项目到数据库"""
        project_id = data.get('id') or ('proj_' + uuid.uuid4().hex[:12])
        if not self._validate_project_id(project_id):
            self.send_json({'error': '无效的项目ID'}, 400); return
        name = data.get('name', '未命名项目').strip() or '未命名项目'
        novel_data = data.get('data', {})
        step = min(int(data.get('step', 0)), 10)
        tags = data.get('tags', '')
        # 限制数据大小（10MB）
        if len(json.dumps(novel_data, ensure_ascii=False)) > 10 * 1024 * 1024:
            self.send_json({'error': '项目数据过大（上限10MB）'}, 400); return

        novel_db.save_project(project_id, name, step, novel_data, tags)
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        self.send_json({'ok': True, 'id': project_id, 'name': name, 'updated_at': now})

    def handle_project_list(self, data):
        """列出所有项目"""
        projects = novel_db.list_projects()
        self.send_json({'projects': projects})

    def handle_project_load(self, data):
        """加载项目详情"""
        project_id = data.get('id', '')
        if not self._validate_project_id(project_id):
            self.send_json({'error': '无效的项目ID'}, 400); return

        project = novel_db.get_project(project_id)

        # 兼容旧文件格式：如果数据库没有但文件存在，自动迁移到数据库
        if not project:
            filepath = os.path.join(PROJECTS_DIR, project_id + '.json')
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        old = json.load(f)
                    novel_db.save_project(project_id, old.get('name', '未命名'),
                                         old.get('step', 0), old.get('data', {}))
                    project = novel_db.get_project(project_id)
                except:
                    pass

        if project:
            self.send_json(project)
        else:
            self.send_json({'error': '项目不存在'}, 404)

    def handle_project_delete(self, data):
        """删除项目（级联删除所有关联数据）"""
        project_id = data.get('id', '')
        if not self._validate_project_id(project_id):
            self.send_json({'error': '无效的项目ID'}, 400); return

        project = novel_db.get_project(project_id)
        if not project:
            self.send_json({'error': '项目不存在'}, 404)
            return

        novel_db.delete_project_cascade(project_id)
        self.send_json({'ok': True})

    # ===== 章节管理 =====

    def handle_chapter_save(self, data):
        """保存章节（支持 metadata 字典）"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber', None)
        if not project_id or chapter_number is None:
            self.send_json({'error': '缺少参数'}, 400); return
        metadata = data.get('metadata', None)
        if isinstance(metadata, str):
            try: metadata = json.loads(metadata)
            except: metadata = None
        novel_db.save_chapter(
            project_id=project_id,
            chapter_number=chapter_number,
            title=data.get('title', ''),
            content=data.get('content', ''),
            status=data.get('status', 'done'),
            error_message=data.get('errorMessage', ''),
            metadata=metadata,
        )
        self.send_json({'ok': True})

    def handle_chapter_get(self, data):
        """获取章节"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        if chapter_number:
            ch = novel_db.get_chapter(project_id, chapter_number)
            self.send_json({'chapter': ch})
        else:
            chapters = novel_db.get_all_chapters(project_id)
            status = novel_db.get_generation_status(project_id)
            counts = novel_db.get_chapter_count(project_id)
            self.send_json({'chapters': chapters, 'status': status, 'counts': counts})

    def handle_chapter_delete(self, data):
        """删除章节"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber', None)
        if not project_id or chapter_number is None:
            self.send_json({'error': '缺少参数'}, 400); return
        novel_db.delete_chapter(project_id, chapter_number)
        self.send_json({'ok': True})

    def handle_chapter_regenerate(self, data):
        """重新生成单章（清除旧内容后重新生成）"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber', None)
        if not project_id or chapter_number is None:
            self.send_json({'error': '缺少参数'}, 400); return
        # 清除旧章节
        novel_db.delete_chapter(project_id, chapter_number)
        self.send_json({'ok': True})

    def handle_generation_status(self, data):
        """获取生成状态"""
        project_id = data.get('projectId', '')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        status = novel_db.get_generation_status(project_id)
        counts = novel_db.get_chapter_count(project_id)
        pending = novel_db.get_pending_chapters(project_id, counts['total'])
        self.send_json({'status': status, 'counts': counts, 'pendingChapters': pending})

    def handle_generation_start(self, data):
        """开始/恢复批量生成"""
        project_id = data.get('projectId', '')
        total_chapters = data.get('totalChapters', 0)
        if not project_id or not total_chapters:
            self.send_json({'error': '缺少参数'}, 400); return
        # config 不包含 apiKey，避免明文存储
        config_keys = [k for k in ['endpoint', 'model', 'projectTitle', 'genre', 'styleProfile', 'bookOverview', 'targetWords', 'narrativePerspective', 'chapterCharacters'] if k in data]
        config = json.dumps({k: data[k] for k in config_keys})
        novel_db.start_generation(project_id, total_chapters, config)
        self.send_json({'ok': True})

    def handle_generation_pause(self, data):
        """暂停生成"""
        project_id = data.get('projectId', '')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        novel_db.pause_generation(project_id)
        self.send_json({'ok': True})

    def handle_generation_stop(self, data):
        """停止生成"""
        project_id = data.get('projectId', '')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        novel_db.stop_generation(project_id)
        self.send_json({'ok': True})

    def handle_generation_update_progress(self, data):
        """更新生成进度"""
        project_id = data.get('projectId', '')
        current = data.get('currentChapter', 0)
        completed = data.get('completedChapters')
        failed = data.get('failedChapters')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        novel_db.update_generation_progress(project_id, current, completed, failed)
        self.send_json({'ok': True})

    # ===== 大纲管理 =====

    def handle_outline_save(self, data):
        """保存大纲"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber', None)
        if not project_id or chapter_number is None:
            self.send_json({'error': '缺少参数'}, 400); return
        novel_db.save_outline(
            project_id=project_id, chapter_number=chapter_number,
            title=data.get('title', ''), summary=data.get('summary', ''),
            scenes=data.get('scenes'), characters=data.get('characters'),
            key_points=data.get('key_points'), emotion=data.get('emotion', ''),
            goal=data.get('goal', ''), technique_focus=data.get('techniqueFocus', ''),
            book_overview=data.get('bookOverview', ''),
            chapter_hook=data.get('chapterHook', ''),
            acts=data.get('acts'),
            status=data.get('status', 'done'), error_message=data.get('errorMessage', ''),
        )
        self.send_json({'ok': True})

    def handle_outline_get(self, data):
        """获取大纲"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        if chapter_number is not None:
            outline = novel_db.get_outline(project_id, chapter_number)
            self.send_json({'outline': outline})
        else:
            outlines = novel_db.get_all_outlines(project_id)
            status = novel_db.get_outline_generation_status(project_id)
            self.send_json({'outlines': outlines, 'status': status})

    def handle_outline_delete(self, data):
        """删除大纲"""
        project_id = data.get('projectId', '')
        chapter_number = data.get('chapterNumber', None)
        if not project_id or chapter_number is None:
            self.send_json({'error': '缺少参数'}, 400); return
        novel_db.delete_outline(project_id, chapter_number)
        self.send_json({'ok': True})

    def handle_outline_generation_start(self, data):
        """开始大纲批量生成"""
        project_id = data.get('projectId', '')
        total = data.get('totalChapters', 0)
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        config = {k: data[k] for k in ['endpoint', 'model', 'projectTitle', 'genre',
                 'styleProfile', 'bookOverview', 'targetWords', 'narrativePerspective', 'chapterCharacters']
                 if k in data}
        novel_db.start_outline_generation(project_id, total, json.dumps(config, ensure_ascii=False))
        self.send_json({'ok': True})

    def handle_outline_generation_pause(self, data):
        novel_db.pause_outline_generation(data.get('projectId', ''))
        self.send_json({'ok': True})

    def handle_outline_generation_stop(self, data):
        novel_db.stop_outline_generation(data.get('projectId', ''))
        self.send_json({'ok': True})

    def handle_outline_generation_update(self, data):
        project_id = data.get('projectId', '')
        current = data.get('currentChapter', 0)
        completed = data.get('completedChapters')
        failed = data.get('failedChapters')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        novel_db.update_outline_generation_progress(project_id, current, completed, failed)
        self.send_json({'ok': True})

    # ===== 步骤摘要管理 =====

    def handle_step_summary_save(self, data):
        """保存步骤摘要"""
        project_id = data.get('projectId', '')
        step = data.get('step', '')
        summary = data.get('summary', data.get('summaryJson', {}))
        if not project_id or not step:
            self.send_json({'error': '缺少参数'}, 400); return
        novel_db.save_step_summary(project_id, step, summary)
        self.send_json({'ok': True})

    def handle_step_summary_get(self, data):
        """获取步骤摘要"""
        project_id = data.get('projectId', '')
        step = data.get('step')
        if not project_id:
            self.send_json({'error': '缺少 projectId'}, 400); return
        if step:
            summary = novel_db.get_step_summary(project_id, step)
            self.send_json({'summaries': {step: summary or {}}})
        else:
            summaries = novel_db.get_all_step_summaries(project_id)
            result = {}
            for s in summaries:
                result[s['step']] = s.get('summary_json', {})
            self.send_json({'summaries': result})

    def handle_novel_book_overview(self, data):
        """生成全书总纲（注入步骤摘要）"""
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            # 从数据库获取步骤摘要作为补充
            project_id = data.get('projectId', '')
            world_summary = data.get('worldSummary', '')
            inspiration_desc = data.get('description', '')
            characters_info = data.get('charactersInfo', '')
            missing_steps = []
            if project_id:
                summaries = novel_db.get_all_step_summaries(project_id)
                summary_map = {s['step']: s.get('summary_json', {}) for s in summaries}
                insp = summary_map.get('inspiration', {})
                world = summary_map.get('world', {})
                chars = summary_map.get('characters', {})
                # 优先使用传入值，缺失时从步骤摘要补全
                if not inspiration_desc and insp:
                    inspiration_desc = insp.get('description', insp.get('core_premise', ''))
                elif not inspiration_desc:
                    missing_steps.append('灵感')
                if not world_summary and world:
                    world_summary = world.get('summary_text', '')
                    if not world_summary:
                        parts = []
                        if world.get('key_locations'):
                            parts.append("关键地点: " + ", ".join(world.get('key_locations', [])[:5]))
                        if world.get('power_system'):
                            parts.append("体系: " + world.get('power_system', ''))
                        world_summary = "; ".join(parts)
                elif not world_summary:
                    missing_steps.append('世界观')
                if not characters_info and chars:
                    char_names = chars.get('char_names', [])
                    if char_names:
                        characters_info = ", ".join(char_names)
                elif not characters_info:
                    missing_steps.append('角色')
            # 注入缺失步骤提醒
            if missing_steps:
                world_summary = f"[注意：缺少以下步骤的数据：{'/'.join(missing_steps)}，总纲可能不够完整]\n" + world_summary
            result, err = gen.generate_book_overview(
                title=data.get('title', ''), theme=data.get('theme', ''),
                genre=data.get('genre', ''), characters_info=characters_info,
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                world_summary=world_summary,
                inspiration_desc=inspiration_desc
            )
            if err:
                self.send_json({'error': err}, 500)
            else:
                self.send_json({'result': result})
        self._with_ai(data, do)

    def handle_novel_chapter_outline(self, data):
        """生成单章细纲（含局部上下文注入）"""
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            chapter_number = max(1, min(int(data.get('chapterNumber', 1)), 1000))
            total_chapters = max(1, min(int(data.get('totalChapters', 1)), 1000))
            if chapter_number > total_chapters:
                chapter_number = total_chapters
            result, err = gen.generate_chapter_outline(
                project_title=data.get('projectTitle', ''),
                genre=data.get('genre', ''),
                book_overview_json=data.get('bookOverview', ''),
                chapter_number=chapter_number,
                total_chapters=total_chapters,
                characters_info=data.get('charactersInfo', ''),
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                world_summary=data.get('worldSummary', ''),
                prev_chapter_title=data.get('prevChapterTitle', ''),
                prev_chapter_tail=data.get('prevChapterTail', ''),
                use_craft=data.get('useCraft', False)
            )
            if err:
                self.send_json({'error': err}, 500)
            else:
                self.send_json({'result': result})
        self._with_ai(data, do)

    def handle_ai_analyze(self, data):
        endpoint = data.get('endpoint', '')
        api_key = data.get('apiKey', '')
        model = data.get('model', '')
        content_text = data.get('content', '')

        if not all([endpoint, api_key, model, content_text]):
            self.send_json({'error': '缺少参数'}, 400); return

        messages = [
            {'role': 'system', 'content': '你是一位专业的小说分析家。请分析小说的写作风格特征，从以下维度输出结构化分析，每个维度用标签标记：\n【叙事视角】\n【句式特征】\n【词汇偏好】\n【对话风格】\n【节奏模式】\n【场景描写】\n每个维度50-100字，用中文输出。'},
            {'role': 'user', 'content': '请分析以下小说的写作风格：\n\n' + content_text[:6000]}
        ]

        result, err = ai_call(endpoint, api_key, model, messages, {'temperature': 0.3, 'max_tokens': 2000})
        if err:
            self.send_json({'error': err}, 500)
        else:
            self.send_json({'result': result})

    def handle_ai_generate(self, data):
        endpoint = data.get('endpoint', '')
        api_key = data.get('apiKey', '')
        model = data.get('model', '')
        style_profile = data.get('styleProfile', '')
        genre = data.get('genre', '未指定')
        count = min(int(data.get('count', 3)), 50)
        protagonist = data.get('protagonist', '未指定')
        world = data.get('world', '未指定')
        outline = data.get('outline', '未指定')

        if not all([endpoint, api_key, model, style_profile]):
            self.send_json({'error': '缺少参数'}, 400); return

        messages = [
            {'role': 'system', 'content': '你是一位专业的小说作家。请根据提供的风格画像和创作设定创作小说。严格按照要求的风格写作，每章 1000-2000 字。输出格式：\n第X章 章节标题\n（正文）\n\n直接开始创作，不要额外说明。'},
            {'role': 'user', 'content': f'【风格画像】\n{style_profile}\n\n【创作设定】\n题材: {genre}\n主角: {protagonist}\n世界观: {world}\n故事梗概: {outline}\n\n请生成{count}章小说。'}
        ]

        result, err = ai_call(endpoint, api_key, model, messages, {'temperature': 0.8, 'max_tokens': 4096})
        if err:
            self.send_json({'error': err}, 500)
        else:
            self.send_json({'result': result})

    def handle_test_connection(self, data):
        """测试模型连接：发送最简请求验证 API 可达"""
        endpoint = data.get('endpoint', '')
        api_key = data.get('apiKey', '')
        model_id = data.get('model', '')
        if not all([endpoint, api_key, model_id]):
            self.send_json({'ok': False, 'error': '缺少 endpoint / apiKey / model 参数'}, 400)
            return
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant. Reply briefly.'},
            {'role': 'user', 'content': 'Say "OK" if you can hear me.'}
        ]
        try:
            result, err = ai_call(endpoint, api_key, model_id, messages, {'temperature': 0, 'max_tokens': 32, 'timeout': 30})
            if err:
                self.send_json({'ok': False, 'error': err})
            else:
                self.send_json({'ok': True, 'model': model_id, 'response': (result or '')[:100]})
        except Exception as e:
            traceback.print_exc()
            self.send_json({'ok': False, 'error': str(e)[:300]})

    def _get_ai_config(self, data):
        """从请求中获取AI配置"""
        return {
            'endpoint': data.get('endpoint', ''),
            'api_key': data.get('apiKey', ''),
            'model': data.get('model', ''),
        }

    def _check_ai_config(self, cfg):
        """检查AI配置是否完整"""
        if not all([cfg['endpoint'], cfg['api_key'], cfg['model']]):
            return False
        return True

    def _create_generator(self, data):
        """创建NovelGenerator实例"""
        cfg = self._get_ai_config(data)
        return NovelGenerator(
            api_key=cfg['api_key'],
            base_url=cfg['endpoint'],
            model=cfg['model'],
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('maxTokens', 4000)
        )

    def _parse_style_profile(self, style_profile_str):
        """解析风格分析结果，返回dict"""
        if not style_profile_str:
            return None
        if isinstance(style_profile_str, dict):
            return style_profile_str
        try:
            return json.loads(style_profile_str)
        except:
            return None

    def _build_style_section(self, style):
        """构建风格信息文本段"""
        parts = []
        if style.get('narrative_perspective'):
            parts.append('- 叙事视角：' + style['narrative_perspective'])
        if style.get('tone'):
            parts.append('- 语言基调：' + style['tone'])
        if style.get('pacing'):
            parts.append('- 叙事节奏：' + style['pacing'])
        if style.get('emotional_intensity'):
            parts.append('- 情感浓度：' + style['emotional_intensity'])
        if style.get('overall_summary'):
            parts.append('- 风格总结：' + style['overall_summary'])
        if not parts:
            return ''
        return '=== 参考风格 ===\n' + '\n'.join(parts) + '\n\n'

    def _format_style_for_prompt(self, style):
        """将风格分析格式化为 prompt 可用的字段"""
        return {
            'narrative_perspective': style.get('narrative_perspective', '未指定'),
            'tone': style.get('tone', '未指定'),
            'pacing': style.get('pacing', '未指定'),
            'dialogue_style': style.get('dialogue_style', '未指定'),
            'description_style': style.get('description_style', '未指定'),
            'vocabulary_level': style.get('vocabulary_level', '未指定'),
            'sentence_structure': style.get('sentence_structure', '未指定'),
            'emotional_intensity': style.get('emotional_intensity', '未指定'),
            'unique_quirks': ', '.join(style.get('unique_quirks', [])) if isinstance(style.get('unique_quirks'), list) else str(style.get('unique_quirks', '未指定')),
            'overall_summary': style.get('overall_summary', '未指定'),
        }

    def _with_ai(self, data, handler):
        """统一AI处理器：校验配置、创建生成器、异常处理（消除17个handler中的重复样板）"""
        cfg = self._get_ai_config(data)
        if not self._check_ai_config(cfg):
            self.send_json({'error': '缺少AI配置参数'}, 400)
            return
        try:
            gen = self._create_generator(data)
            handler(gen)
        except Exception as e:
            traceback.print_exc()
            self.send_json({'error': str(e)}, 500)

    def _send_gen_result(self, result, err, key=None):
        """统一处理 (result, err) 元组响应"""
        if err:
            self.send_json({'error': str(err)}, 500)
        elif result is None:
            self.send_json({'error': '生成结果为空，请重试'}, 500)
        else:
            self.send_json({key: result} if key else result)

    # ===== 灵感模式 =====

    def handle_novel_inspiration_title(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_titles(user_input=data.get('userInput', ''), style_profile=style), key='options')
        self._with_ai(data, do)

    def handle_novel_inspiration_description(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_descriptions(data.get('title', ''), user_input=data.get('userInput', ''), style_profile=style), key='options')
        self._with_ai(data, do)

    def handle_novel_inspiration_theme(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_themes(data.get('title', ''), data.get('description', ''), user_input=data.get('userInput', ''), style_profile=style), key='options')
        self._with_ai(data, do)

    def handle_novel_inspiration_genre(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_genres(data.get('title', ''), data.get('description', ''), user_input=data.get('userInput', ''), style_profile=style), key='options')
        self._with_ai(data, do)

    # ===== 世界观构建 =====

    def handle_novel_worldbuilding(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            result, err = gen.generate_world_building(
                title=data.get('title', ''), theme=data.get('theme', ''),
                genre=data.get('genre', ''), description=data.get('description', ''),
                style_profile=style
            )
            if err:
                self.send_json({'error': err}, 500)
                return
            for k in ['time_period', 'location', 'atmosphere', 'rules']:
                if k in result and not isinstance(result[k], str):
                    result[k] = json.dumps(result[k], ensure_ascii=False) if isinstance(result[k], dict) else str(result[k])
            self._send_gen_result(result, None, key='world')
        self._with_ai(data, do)

    # ===== 角色生成 =====

    def handle_novel_characters(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            count = min(int(data.get('count', 6)), 50)
            world_data = data.get('worldData', {})
            if isinstance(world_data, str):
                try:
                    world_data = json.loads(world_data)
                except:
                    world_data = {'summary': world_data}
            # >10个角色时使用分批生成避免超时
            if count > 10:
                result, err = gen.generate_characters_batch(
                    world_data=world_data, theme=data.get('theme', ''),
                    genre=data.get('genre', ''), count=count,
                    requirements=data.get('requirements', ''), style_profile=style,
                    description=data.get('novelDescription', '')
                )
                if err:
                    self.send_json({'error': err}, 500)
                else:
                    self.send_json({'characters': result})
            else:
                self._send_gen_result(*gen.generate_characters(
                    world_data=world_data, theme=data.get('theme', ''),
                    genre=data.get('genre', ''), count=count,
                    requirements=data.get('requirements', ''), style_profile=style,
                    description=data.get('novelDescription', '')
                ), key='characters')
        self._with_ai(data, do)

    # ===== 重新解析世界观/角色（从已有正文提取结构化数据） =====

    def handle_worldbuilding_reparse(self, data):
        """从已有世界观正文重新提取结构化数据"""
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            result, err = gen.reparse_world_building(
                world_text=data.get('worldText', ''),
                style_profile=style
            )
            if err:
                self.send_json({'error': err}, 500)
                return
            for k in ['time_period', 'location', 'atmosphere', 'rules']:
                if k in result and not isinstance(result[k], str):
                    result[k] = json.dumps(result[k], ensure_ascii=False) if isinstance(result[k], dict) else str(result[k])
            self.send_json({'worldJson': result})
        self._with_ai(data, do)

    def handle_characters_reparse(self, data):
        """从已有角色正文重新提取结构化角色数据"""
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            result, err = gen.reparse_characters(
                characters_text=data.get('charactersText', ''),
                style_profile=style
            )
            if err:
                self.send_json({'error': err}, 500)
                return
            self.send_json({'charactersRaw': result})
        self._with_ai(data, do)

    def handle_novel_outline(self, data):
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            chapter_count = max(1, min(int(data.get('chapterCount', 3)), 200))
            # 从步骤摘要中获取世界观作为补充
            world_summary = data.get('worldSummary', '')
            if not world_summary and data.get('projectId'):
                summaries = novel_db.get_all_step_summaries(data['projectId'])
                summary_map = {s['step']: s.get('summary_json', {}) for s in summaries}
                world = summary_map.get('world', {})
                if world:
                    world_summary = world.get('summary_text', '')
            self._send_gen_result(*gen.generate_outline(
                title=data.get('title', ''), theme=data.get('theme', ''),
                genre=data.get('genre', ''), characters_info=data.get('charactersInfo', []),
                chapter_count=chapter_count,
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                world_summary=world_summary
            ), key='outline')
        self._with_ai(data, do)

    # ===== 章节生成 =====

    def handle_novel_chapter(self, data):
        if data.get('stream'):
            self.handle_stream(data, lambda gen, style, data: gen.generate_chapter_stream(
                project_title=data.get('projectTitle', ''), genre=data.get('genre', ''),
                chapter_number=data.get('chapterNumber', 1),
                chapter_title=data.get('chapterTitle', ''),
                chapter_outline=data.get('chapterOutline', ''),
                continuation_point=data.get('continuationPoint', ''),
                previous_chapter_summary=data.get('previousChapterSummary', ''),
                chapter_characters=data.get('chapterCharacters', ''),
                foreshadow_reminders=data.get('foreshadowReminders', ''),
                world_summary=data.get('worldSummary', ''),
                first_chapter_strategy=data.get('firstChapterStrategy', ''),
                target_word_count=data.get('targetWordCount', 3000),
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                technique_focus=data.get('techniqueFocus', ''),
                book_overview=data.get('bookOverview', ''),
                progress_content=data.get('progressContent', ''),
                segment_chars=int(data.get('segmentChars', 0)),
                prev_chapter_hook=data.get('prevChapterHook', ''),
            ))
            return
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_chapter(
                project_title=data.get('projectTitle', ''), genre=data.get('genre', ''),
                chapter_number=data.get('chapterNumber', 1),
                chapter_title=data.get('chapterTitle', ''),
                chapter_outline=data.get('chapterOutline', ''),
                continuation_point=data.get('continuationPoint', ''),
                previous_chapter_summary=data.get('previousChapterSummary', ''),
                chapter_characters=data.get('chapterCharacters', ''),
                foreshadow_reminders=data.get('foreshadowReminders', ''),
                world_summary=data.get('worldSummary', ''),
                first_chapter_strategy=data.get('firstChapterStrategy', ''),
                target_word_count=data.get('targetWordCount', 3000),
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                technique_focus=data.get('techniqueFocus', ''),
                book_overview=data.get('bookOverview', ''),
                prev_chapter_hook=data.get('prevChapterHook', ''),
            ), key='content')
        self._with_ai(data, do)

    # ===== 章节润色 =====

    def handle_chapter_polish(self, data):
        """流式润色章节"""
        if data.get('stream'):
            self.handle_stream(data, lambda gen, style, data: gen.polish_chapter_stream(
                project_title=data.get('projectTitle', ''),
                genre=data.get('genre', ''),
                chapter_number=data.get('chapterNumber', 1),
                chapter_title=data.get('chapterTitle', ''),
                chapter_outline=data.get('chapterOutline', ''),
                original_content=data.get('originalContent', ''),
                polish_focus=data.get('polishFocus', '整体优化'),
                style_profile=style,
            ))
            return
        self.send_json({'error': '仅支持流式调用'}, 400)

    def handle_chapter_summarize(self, data):
        """AI 生成章节摘要，用于后续章节的上下文"""
        endpoint = data.get('endpoint', '')
        api_key = data.get('apiKey', '')
        model = data.get('model', '')
        chapter_title = data.get('chapterTitle', '')
        chapter_number = data.get('chapterNumber', 1)
        content = data.get('content', '')
        if not all([endpoint, api_key, model]):
            self.send_json({'error': '缺少 endpoint/apiKey/model'}, 400); return
        if not content:
            self.send_json({'summary': ''}); return
        messages = [
            {'role': 'system', 'content': '你是小说编辑。请将以下章节正文压缩为100字以内的摘要，保留核心事件和关键转折。只输出摘要文字，不要任何格式或说明。'},
            {'role': 'user', 'content': f'第{chapter_number}章《{chapter_title}》正文：\n{content[:6000]}'}
        ]
        result, err = ai_call(endpoint, api_key, model, messages, {'temperature': 0.3, 'max_tokens': 200})
        if err:
            self.send_json({'summary': ''})
        else:
            self.send_json({'summary': result.strip()})

    # ===== 分析功能 =====

    def handle_novel_analyze_style(self, data):
        def do(gen):
            result, err = gen.analyze_style(data.get('content', ''))
            if err:
                self.send_json({'error': err}, 500)
            else:
                self.send_json({'result': result, 'resultJson': json.dumps(result, ensure_ascii=False)})
        self._with_ai(data, do)

    def handle_novel_analyze_chapter(self, data):
        def do(gen):
            self._send_gen_result(*gen.analyze_chapter(
                chapter_number=data.get('chapterNumber', 1),
                title=data.get('title', ''), content=data.get('content', '')
            ), key=None)
        self._with_ai(data, do)

    # ===== 风格仿写 =====

    def handle_novel_generate_style(self, data):
        def do(gen):
            self._send_gen_result(*gen.generate_with_style(
                style_profile=data.get('styleProfile', ''), genre=data.get('genre', '未指定'),
                count=data.get('count', 3), protagonist=data.get('protagonist', '未指定'),
                world=data.get('world', '未指定'), outline=data.get('outline', '未指定'),
                target_word_count=data.get('targetWordCount', 3000)
            ), key='content')
        self._with_ai(data, do)

    # ===== 网文创作技法（Craft）=====

    def handle_craft_detect_ai(self, data):
        def do(gen):
            self._send_gen_result(*gen.detect_ai_flavor(data.get('content', '')), key=None)
        self._with_ai(data, do)

    def handle_craft_fix_ai(self, data):
        def do(gen):
            self._send_gen_result(*gen.fix_ai_flavor(data.get('content', ''), data.get('issues', [])), key='content')
        self._with_ai(data, do)

    def handle_craft_golden_three(self, data):
        def do(gen):
            self._send_gen_result(*gen.analyze_golden_three(data.get('content', '')), key=None)
        self._with_ai(data, do)

    def handle_craft_hooks(self, data):
        def do(gen):
            self._send_gen_result(*gen.analyze_hooks(data.get('content', '')), key=None)
        self._with_ai(data, do)

    def handle_craft_satisfaction(self, data):
        def do(gen):
            self._send_gen_result(*gen.analyze_satisfaction_rhythm(data.get('content', '')), key=None)
        self._with_ai(data, do)

    def handle_craft_quality_score(self, data):
        def do(gen):
            self._send_gen_result(*gen.quality_score(
                data.get('content', ''), data.get('title', ''), data.get('genre', '')
            ), key=None)
        self._with_ai(data, do)

    def handle_craft_chapter(self, data):
        if data.get('stream'):
            self.handle_stream(data, lambda gen, style, data: gen.generate_chapter_craft_stream(
                project_title=data.get('projectTitle', ''), genre=data.get('genre', ''),
                chapter_number=data.get('chapterNumber', 1),
                chapter_title=data.get('chapterTitle', ''),
                chapter_outline=data.get('chapterOutline', ''),
                continuation_point=data.get('continuationPoint', ''),
                previous_chapter_summary=data.get('previousChapterSummary', ''),
                chapter_characters=data.get('chapterCharacters', ''),
                foreshadow_reminders=data.get('foreshadowReminders', ''),
                world_summary=data.get('worldSummary', ''),
                first_chapter_strategy=data.get('firstChapterStrategy', ''),
                target_word_count=data.get('targetWordCount', 3000),
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                technique_focus=data.get("techniqueFocus", ""),
                book_overview=data.get("bookOverview", ""),
                progress_content=data.get('progressContent', ''),
                segment_chars=int(data.get('segmentChars', 0)),
                prev_chapter_hook=data.get('prevChapterHook', ''),
            ))
            return
        def do(gen):
            style = self._parse_style_profile(data.get('styleProfile', ''))
            self._send_gen_result(*gen.generate_chapter_craft(
                project_title=data.get('projectTitle', ''), genre=data.get('genre', ''),
                chapter_number=data.get('chapterNumber', 1),
                chapter_title=data.get('chapterTitle', ''),
                chapter_outline=data.get('chapterOutline', ''),
                continuation_point=data.get('continuationPoint', ''),
                previous_chapter_summary=data.get('previousChapterSummary', ''),
                chapter_characters=data.get('chapterCharacters', ''),
                foreshadow_reminders=data.get('foreshadowReminders', ''),
                world_summary=data.get('worldSummary', ''),
                first_chapter_strategy=data.get('firstChapterStrategy', ''),
                target_word_count=data.get('targetWordCount', 3000),
                narrative_perspective=data.get('narrativePerspective', '第三人称'),
                style_profile=style,
                technique_focus=data.get("techniqueFocus", ""),
                book_overview=data.get("bookOverview", ""),
                prev_chapter_hook=data.get('prevChapterHook', ''),
            ), key='content')
        self._with_ai(data, do)

    def handle_craft_titles(self, data):
        def do(gen):
            self._send_gen_result(*gen.generate_titles_craft(data.get('userInput', '')), key='options')
        self._with_ai(data, do)

    def handle_craft_descriptions(self, data):
        def do(gen):
            self._send_gen_result(*gen.generate_descriptions_craft(data.get('title', ''), data.get('userInput', '')), key='options')
        self._with_ai(data, do)

    def handle_craft_report(self, data):
        def do(gen):
            self._send_gen_result(*gen.generate_analysis_report(data.get('content', '')), key='report')
        self._with_ai(data, do)

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_stream(self, data, gen_method):
        """通用流式处理：调用生成器方法并通过 SSE 返回"""
        import logging
        logger = logging.getLogger('novel_creator.server')
        cfg = self._get_ai_config(data)
        if not self._check_ai_config(cfg):
            self.send_json({'error': '缺少AI配置参数'}, 400)
            return

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'close')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()
        # 强制连接在处理完成后关闭
        self.close_connection = True

        try:
            gen = self._create_generator(data)
            style = self._parse_style_profile(data.get('styleProfile', ''))
            logger.info(f"stream started: model={cfg.get('model')}, max_tokens={cfg.get('max_tokens')}")
            # 立即发送一个空内容 chunk，防止前端首包超时
            self.wfile.write(f"data: {json.dumps({'content': ''}, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()
            chunk_count = 0
            for chunk in gen_method(gen, style, data):
                chunk_count += 1
                if 'content' in chunk:
                    self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                elif 'error' in chunk:
                    self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    logger.error(f"stream error after {chunk_count} chunks: {chunk['error']}")
                    return
                elif chunk.get('done'):
                    done_chunk = {'done': True}
                    if 'result' in chunk:
                        done_chunk['result'] = chunk['result']
                    self.wfile.write(f"data: {json.dumps(done_chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    result_size = len(json.dumps(done_chunk)) if 'result' in chunk else 0
                    logger.info(f"stream done: {chunk_count} chunks, result_size={result_size}")
                    return
        except Exception as e:
            traceback.print_exc()
            self.wfile.write(f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()
            logger.exception(f"stream exception: {e}")

    def finish(self):
        """覆盖 finish 方法，确保流式响应后连接被关闭"""
        try:
            if not self.wfile.closed:
                self.wfile.flush()
                self.wfile.close()
        except Exception:
            pass
        super().finish()


if __name__ == '__main__':
    print(f'番茄小说服务端 v2 已启动: http://0.0.0.0:{PORT}')
    # 启动时清理陈旧的 is_running 标志
    try:
        from novel_creator.database import DB_PATH
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("UPDATE outline_generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.execute("UPDATE generation_status SET is_running=0, is_paused=0 WHERE is_running=1")
            conn.commit()
        print('已清理陈旧的生成状态')
    except Exception as e:
        print(f'清理陈旧状态失败: {e}')
    http.server.ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
