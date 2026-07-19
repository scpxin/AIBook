import os
import re

PORT = int(os.environ.get('PORT', 8000))
DB_PATH = os.environ.get('DB_PATH', os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db')))
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/app/data/downloads')
PROJECTS_DIR = os.environ.get('PROJECTS_DIR', '/app/data/projects')
LOG_DIR = os.environ.get('LOG_DIR', '/app/data/logs')

PROJECT_ID_PATTERN = re.compile(r'^[\w\-]{1,128}$')  # 字母数字+下划线+连字符,1-128字符

SEARCH_API = os.environ.get('SEARCH_API', '')
CONTENT_API = os.environ.get('CONTENT_API', '')
DIR_API = os.environ.get('DIR_API', '')
UA = os.environ.get('UA', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
HTTP_TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', 30))

ALLOWED_PROXY_DOMAINS = os.environ.get('ALLOWED_PROXY_DOMAINS', '').split(',') if os.environ.get('ALLOWED_PROXY_DOMAINS') else []

SESSION_TTL = int(os.environ.get('SESSION_TTL', 86400))
