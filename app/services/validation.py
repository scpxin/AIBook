"""AI返回结构校验工具 — 向后兼容重导出"""
import warnings

from novel_creator._validator import REQUIRED_KEYS as REQUIRED_KEYS
from novel_creator._validator import validate_result as validate_result

warnings.warn(
    "app.services.validation is deprecated. Use novel_creator._validator instead.",
    DeprecationWarning,
    stacklevel=2,
)
