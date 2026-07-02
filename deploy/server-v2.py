#!/usr/bin/env python3
"""番茄小说下载器 - 服务端 v2 (下载持久化 + AI分析生成)"""
import http.server, urllib.request, urllib.parse, urllib.error, json, os, time, re, threading, uuid

PORT = int(os.environ.get('PORT', '8000'))
BASE_DIR = os.environ.get('BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', os.path.join(BASE_DIR, 'downloads'))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SEARCH_API   = 'https://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/?aid=1967&q={}&offset=0'
DIR_API      = 'https://fanqienovel.com/api/reader/directory/detail?bookId={}'
CONTENT_API  = 'http://101.35.133.34:5000/api/content?tab=%E5%B0%8F%E8%AF%B4&item_id={}'
TIMEOUT = 20
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

sessions = {}
sessions_lock = threading.Lock()


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
    req_body = {
        'model': model,
        'messages': messages,
        'temperature': (options or {}).get('temperature', 0.7),
        'max_tokens': (options or {}).get('max_tokens', 4096),
    }
    data = json.dumps(req_body).encode('utf-8')
    req = urllib.request.Request(endpoint, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key,
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        result = json.loads(r.read())
    if result.get('error'):
        return None, result['error'].get('message', str(result['error']))
    choices = result.get('choices', [])
    if not choices:
        return None, 'AI 返回空内容'
    content = choices[0].get('message', {}).get('content', '')
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
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'

        try:
            data = json.loads(body)
        except:
            data = {}

        try:
            # AI 分析
            if path == '/api/ai/analyze':
                self.handle_ai_analyze(data)
            # AI 生成
            elif path == '/api/ai/generate':
                self.handle_ai_generate(data)
            else:
                self.send_json({'error': 'Not found'}, 404)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)

    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        path = p.path
        params = dict(urllib.parse.parse_qsl(p.query))

        try:
            # --- 搜索 ---
            if path == '/api/search':
                q = params.get('q', '')
                if not q:
                    self.send_json({'error': 'missing q'}, 400); return
                data = http_get(SEARCH_API.format(urllib.request.quote(q)))
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
                        'content': [], 'started_at': time.time()
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
                    if not s['paused']:
                        self.send_json({'ok': True, 'note': 'not paused'}); return
                    s['paused'] = False
                threading.Thread(target=download_worker, args=(sid,), daemon=True).start()
                self.send_json({'ok': True})

            elif path == '/api/download/file':
                sid = params.get('session_id', '')
                with sessions_lock:
                    s = sessions.get(sid)
                    if not s:
                        self.send_json({'error': 'session not found'}, 404); return
                    if s['status'] not in ('done', 'partial') and not s.get('paused'):
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

            # --- 页面代理 ---
            elif path == '/api/proxy-text':
                target_url = params.get('url', '')
                if not target_url:
                    self.send_json({'error': 'missing url'}, 400); return
                try:
                    html_data = http_get(target_url).decode('utf-8', errors='ignore')
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(html_data.encode('utf-8'))
                except Exception as e:
                    self.send_json({'error': str(e)}, 500)

            else:
                self.send_json({'error': 'Not found'}, 404)

        except Exception as e:
            self.send_json({'error': str(e)}, 500)

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
        count = data.get('count', 3)
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

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    print(f'番茄小说服务端 v2 已启动: http://0.0.0.0:{PORT}')
    http.server.HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
