import logging
import os
import re
import sys

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """应用配置 — 启动时验证所有必需环境变量"""

    # 服务器配置
    PORT: int = Field(default=8000, description="服务端口")
    DB_PATH: str = Field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fanqie.db'), description="数据库路径")
    DOWNLOAD_DIR: str = Field(default='/app/data/downloads', description="下载目录")
    PROJECTS_DIR: str = Field(default='/app/data/projects', description="项目目录")
    LOG_DIR: str = Field(default='/app/data/logs', description="日志目录")

    # 项目 ID 验证
    PROJECT_ID_PATTERN: re.Pattern = Field(default_factory=lambda: re.compile(r'^[\w\-]{1,128}$'), description="项目 ID 正则")

    # 外部 API
    SEARCH_API: str = Field(default='', description="搜索 API 地址")
    CONTENT_API: str = Field(default='', description="内容 API 地址")
    DIR_API: str = Field(default='', description="目录 API 地址")
    UA: str = Field(default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', description="User-Agent")
    HTTP_TIMEOUT: int = Field(default=30, ge=5, le=300, description="HTTP 超时 (秒)")

    # 安全配置
    ALLOWED_PROXY_DOMAINS: str = Field(default='', description="允许的代理域名，逗号分隔")
    ALLOWED_ORIGINS: str = Field(
        default='http://localhost:3000,http://localhost:5173,http://127.0.0.1:80',
        description="CORS 允许来源，逗号分隔",
    )

    @field_validator('ALLOWED_PROXY_DOMAINS', mode='before')
    @classmethod
    def parse_allowed_domains(cls, v: str) -> str:
        """将逗号分隔的字符串转为列表前的预处理"""
        return v or ''

    # 会话配置
    SESSION_TTL: int = Field(default=86400, ge=3600, description="会话存活时间 (秒)")

    # 生成常量
    DEFAULT_CHAPTER_COUNT: int = Field(default=300, ge=100, le=2000, description="默认章节数")
    DEFAULT_WORD_COUNT: int = Field(default=3000, ge=1000, le=10000, description="默认每章字数")
    DEFAULT_CHAPTER_WORD_MIN: int = Field(default=2000, ge=500, description="章节字数下限")
    DEFAULT_CHAPTER_WORD_MAX: int = Field(default=3000, ge=2000, description="章节字数上限")
    MAX_TOKENS_OVERVIEW: int = Field(default=16000, ge=1000, description="总纲 max_tokens")
    MAX_TOKENS_OUTLINE: int = Field(default=16000, ge=1000, description="大纲 max_tokens")
    MAX_TOKENS_CHAPTER_PLAN: int = Field(default=16000, ge=1000, description="章节规划 max_tokens")
    STRING_TRUNCATE_DESC: int = Field(default=3000, ge=100, description="描述截断长度")
    STRING_TRUNCATE_SHORT: int = Field(default=600, ge=100, description="短文本截断长度")

    model_config = {'extra': 'ignore'}


def load_settings() -> Settings:
    """加载并验证配置"""
    try:
        settings = Settings()
        logger.info(f"配置加载成功：PORT={settings.PORT}, DB_PATH={settings.DB_PATH}")
        return settings
    except ValidationError as e:
        logger.error(f"配置校验失败：{e}")
        sys.exit(1)


# 全局配置实例
settings = load_settings()

# 向后兼容：保留原有模块级变量
PORT = settings.PORT
DB_PATH = settings.DB_PATH
DOWNLOAD_DIR = settings.DOWNLOAD_DIR
PROJECTS_DIR = settings.PROJECTS_DIR
LOG_DIR = settings.LOG_DIR
PROJECT_ID_PATTERN = settings.PROJECT_ID_PATTERN
SEARCH_API = settings.SEARCH_API
CONTENT_API = settings.CONTENT_API
DIR_API = settings.DIR_API
UA = settings.UA
HTTP_TIMEOUT = settings.HTTP_TIMEOUT
ALLOWED_PROXY_DOMAINS = settings.ALLOWED_PROXY_DOMAINS.split(',') if settings.ALLOWED_PROXY_DOMAINS else []
ALLOWED_ORIGINS = settings.ALLOWED_ORIGINS.split(',') if settings.ALLOWED_ORIGINS else []
SESSION_TTL = settings.SESSION_TTL
DEFAULT_CHAPTER_COUNT = settings.DEFAULT_CHAPTER_COUNT
DEFAULT_WORD_COUNT = settings.DEFAULT_WORD_COUNT
DEFAULT_CHAPTER_WORD_MIN = settings.DEFAULT_CHAPTER_WORD_MIN
DEFAULT_CHAPTER_WORD_MAX = settings.DEFAULT_CHAPTER_WORD_MAX
MAX_TOKENS_OVERVIEW = settings.MAX_TOKENS_OVERVIEW
MAX_TOKENS_OUTLINE = settings.MAX_TOKENS_OUTLINE
MAX_TOKENS_CHAPTER_PLAN = settings.MAX_TOKENS_CHAPTER_PLAN
STRING_TRUNCATE_DESC = settings.STRING_TRUNCATE_DESC
STRING_TRUNCATE_SHORT = settings.STRING_TRUNCATE_SHORT
