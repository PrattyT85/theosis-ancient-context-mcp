"""Base adapter interface for corpus backends."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import SearchResult, TextResult


class BaseAdapter(ABC):
    """Abstract base for corpus adapters."""

    corpus_id: str

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this adapter can serve requests right now."""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> SearchResult:
        """Search the corpus for `query`."""
        ...

    @abstractmethod
    def get_text(self, reference: str) -> TextResult:
        """Retrieve text by reference identifier."""
        ...

    @abstractmethod
    def get_metadata(self, reference: str) -> TextResult:
        """Retrieve metadata for a reference."""
        ...
