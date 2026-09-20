"""Remote-only status adapters for TLA, HPM, DASI, OCIANA.

These sources do not have safe adapters in v0.1.0. They return explicit
not_ready / remote_only results with provenance envelopes.
"""
from __future__ import annotations

from ..models import SearchResult, TextResult
from ..registry import make_provenance
from . import BaseAdapter


class _RemoteStatusAdapter(BaseAdapter):
    """Generic remote-only status adapter."""

    corpus_id: str

    def is_available(self) -> bool:
        return False

    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(self.corpus_id)
        return SearchResult(
            provenance=prov,
            status="remote_only",
            message=f"{self.corpus_id} is remote-only in v0.1.0. No safe adapter available.",
        )

    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(self.corpus_id)
        return TextResult(
            provenance=prov,
            status="remote_only",
            message=f"{self.corpus_id} is remote-only in v0.1.0. No safe adapter available.",
        )

    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(self.corpus_id)
        return TextResult(
            provenance=prov,
            status="remote_only",
            message=f"{self.corpus_id} is remote-only in v0.1.0. No safe adapter available.",
        )


class TLAAdapter(_RemoteStatusAdapter):
    """Thesaurus Linguae Aegyptiae — remote/status-only."""
    corpus_id = "tla"


class HPMAdapter(_RemoteStatusAdapter):
    """Hittite HPM/HDivT — remote/status-only."""
    corpus_id = "hpm_hdivt"


class DASIAdapter(_RemoteStatusAdapter):
    """DASI — remote/status-only."""
    corpus_id = "dasi"


class OCIANAAdapter(_RemoteStatusAdapter):
    """OCIANA — remote/status-only."""
    corpus_id = "ociana"


class DeferredAdapter(_RemoteStatusAdapter):
    """Deferred sources (DPPC, CIP) — no scraper, no adapter."""
    corpus_id: str  # set in __init__

    def __init__(self, corpus_id: str) -> None:
        self.corpus_id = corpus_id

    def is_available(self) -> bool:
        return False

    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(self.corpus_id)
        return SearchResult(
            provenance=prov,
            status="deferred",
            message=f"{self.corpus_id} is deferred — no public API, data, or licence confirmed. Not integrated.",
        )

    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(self.corpus_id)
        return TextResult(
            provenance=prov,
            status="deferred",
            message=f"{self.corpus_id} is deferred — not integrated.",
        )

    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(self.corpus_id)
        return TextResult(
            provenance=prov,
            status="deferred",
            message=f"{self.corpus_id} is deferred — not integrated.",
        )
