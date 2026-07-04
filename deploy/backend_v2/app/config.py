import os

PORT = int(os.environ.get('PORT', '8000'))
BASE_DIR = os.environ.get('BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', os.path.join(BASE_DIR, 'downloads'))
PROJECTS_DIR = os.environ.get('PROJECTS_DIR', os.path.join(BASE_DIR, 'projects'))
CONTENT_API = os.environ.get('CONTENT_API', 'http://101.35.133.34:5000/api/content?tab=%E5%B0%8F%E8%AF%B4&item_id={}')
SEARCH_API = os.environ.get('SEARCH_API', 'https://novel.snssdk.com/api/novel/channel/homepage/search/search/v1/?aid=1967&q={}&offset=0')
DIR_API = 'https://fanqienovel.com/api/reader/directory/detail?bookId={}'
AI_TIMEOUT = int(os.environ.get('AI_TIMEOUT', '600'))
SESSION_TTL = int(os.environ.get('SESSION_TTL', '86400'))
HTTP_TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', '20'))
MAX_BODY_SIZE = int(os.environ.get('MAX_BODY_SIZE', '52428800'))
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
ALLOWED_PROXY_DOMAINS = ['fanqienovel.com', 'snssdk.com', 'novel.snssdk.com']
PROJECT_ID_PATTERN = r'^[a-zA-Z0-9_\-]{1,64}$'
