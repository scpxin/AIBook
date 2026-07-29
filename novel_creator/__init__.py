"""小说创作模块 - 从 MuMuAINovel 提取的核心 AI 创作功能"""
from .ai_client import AIClient
from .data_bridge import DataBridge
from .generator import NovelGenerator
from .prompts import parse_json_response

__all__ = ["NovelGenerator", "AIClient", "DataBridge", "parse_json_response"]
