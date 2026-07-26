from ._generator_base import _BaseGeneratorMixin
from ._generator_chapter import _ChapterMixin
from ._generator_design import _DesignMixin
from ._generator_outline import _OutlineMixin
from .ai_client import AIClient


class NovelGenerator(_BaseGeneratorMixin, _DesignMixin, _OutlineMixin, _ChapterMixin):

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini", temperature=0.7, max_tokens=4000, timeout=120):
        self.client = AIClient(api_key=api_key, base_url=base_url, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        self.max_tokens = max_tokens
