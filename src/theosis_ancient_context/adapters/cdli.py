"""CDLI adapter — safe read-only REST client (when API contract is confirmed).

In v0.1.0 this operates as a status-only stub. The adapter structure is
in place so a future version can add a tested HTTP client.
"""
from __future__ import annotations

import os

from ..models import SearchResult, TextResult
from ..registry import make_provenance
from . import BaseAdapter

CORPUS_ID = "cdli"


class CDLIAdapter(BaseAdapter):
    """CDLI adapter — currently status-only.

    TODO: Implement safe read-only adapter when REST JSON API shape is
    confirmed from https://cdli.earth/docs/api. Use mocked HTTP in tests
    before going live.
    """

    corpus_id = CORPUS_ID

    def is_available(self) -> bool:
        # Status-only: not ready for live queries
        return False

    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(CORPUS_ID)
        return SearchResult(
            provenance=prov,
            status="not_ready",
            message=(
                "CDLI adapter is status-only in v0.1.0. "
                "REST JSON API docs at https://cdli.earth/docs/api — "
                "adapter will be implemented when endpoint shape is confirmed."
            ),
        )

    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        return TextResult(
            provenance=prov,
            status="not_ready",
            message=(
                "CDLI adapter is status-only in v0.1.0. "
                "See https://cdli.earth/docs/api for API documentation."
            ),
        )

    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        return TextResult(
            provenance=prov,
            status="not_ready",
            message=(
                "CDLI adapter is status-only in v0.1.0. "
                "See https://cdli.earth/docs/api for API documentation."
            ),
        )
