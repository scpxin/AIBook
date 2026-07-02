"""小说创作模块 - 从 MuMuAINovel 提取的核心 AI 创作功能"""
from .generator import NovelGenerator
from .ai_client import AIClient
from .prompts import parse_json_response

__all__ = ["NovelGenerator", "AIClient", "parse_json_response"]
