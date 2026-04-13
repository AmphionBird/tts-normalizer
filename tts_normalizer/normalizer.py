"""Core Normalizer — language-aware pipeline that converts written text to spoken form."""

from __future__ import annotations

from typing import Optional

from .languages.zh import ZhNormalizer
from .languages.en import EnNormalizer
from .languages.ja import JaNormalizer
from .languages.es import EsNormalizer


_LANG_MAP = {
    "zh": ZhNormalizer,
    "en": EnNormalizer,
    "ja": JaNormalizer,
    "es": EsNormalizer,
}


class Normalizer:
    """High-level entry point.

    Usage::

        norm = Normalizer(lang="zh")
        norm.normalize("今天是2026年4月13日，气温10.5度")
        # → "今天是二零二六年四月十三日，气温十点五度"
    """

    def __init__(self, lang: str = "zh", context: Optional[dict] = None):
        """
        Args:
            lang: Language code ("zh" | "en").
            context: Optional hints for ambiguity resolution, e.g.
                     {"date_format": "MDY"} or {"domain": "finance"}.
        """
        if lang not in _LANG_MAP:
            raise ValueError(f"Unsupported language: {lang!r}. Supported: {list(_LANG_MAP)}")
        self.lang = lang
        self.context = context or {}
        self._engine = _LANG_MAP[lang](context=self.context)

    def normalize(self, text: str) -> str:
        """Normalize *text* to spoken form.

        Args:
            text: Raw input text.

        Returns:
            Text with numbers/symbols replaced by their spoken equivalents.
        """
        return self._engine.normalize(text)
