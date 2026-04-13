"""Abstract base class for all language normalizers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class BaseNormalizer(ABC):
    """Every language normalizer must subclass this."""

    def __init__(self, context: dict):
        self.context = context

    def normalize(self, text: str) -> str:
        """Run the full normalization pipeline on *text*."""
        tokens = self.tokenize(text)
        normalized = [self.normalize_token(tok) for tok in tokens]
        return self.join(normalized)

    def tokenize(self, text: str) -> List[str]:
        """Split text into segments (substrings to process individually).

        Default: treat the entire string as one token.
        Override in subclasses for smarter segmentation.
        """
        return [text]

    @abstractmethod
    def normalize_token(self, token: str) -> str:
        """Normalize a single token segment."""

    def join(self, tokens: List[str]) -> str:
        return "".join(tokens)
