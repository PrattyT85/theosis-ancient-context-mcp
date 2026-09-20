"""Copenhagen Ugaritic Corpus (CUC) local adapter — safe file-based lookup."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ..models import SearchResult, TextResult
from ..registry import make_provenance
from . import BaseAdapter
from .path_utils import list_text_files, read_bounded, safe_resolve

CORPUS_ID = "cuc"


class CUCAdapter(BaseAdapter):
    corpus_id = CORPUS_ID

    def __init__(self) -> None:
        self.corpus_dir = os.environ.get("CUC_CORPUS_DIR")

    def is_available(self) -> bool:
        if not self.corpus_dir:
            return False
        return os.path.isdir(self.corpus_dir)

    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(CORPUS_ID)
        if not self.is_available():
            return SearchResult(
                provenance=prov,
                status="local_not_configured",
                message="CUC_CORPUS_DIR not configured or not a directory. Local search unavailable.",
            )

        files = list_text_files(self.corpus_dir, max_files=500)
        matches: list[dict] = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for f in files:
            content = read_bounded(f, max_bytes=50_000)
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    matches.append({
                        "file": f.name,
                        "line": i,
                        "text": line.strip()[:200],
                    })
                    if len(matches) >= limit:
                        break
            if len(matches) >= limit:
                break

        return SearchResult(
            provenance=prov,
            status="ok",
            results=matches,
            message=f"Found {len(matches)} match(es). Licence: CC BY-NC 4.0 — commercial use prohibited.",
        )

    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        if not self.is_available():
            return TextResult(
                provenance=prov,
                status="local_not_configured",
                message="CUC_CORPUS_DIR not configured.",
            )

        target = safe_resolve(self.corpus_dir, reference)
        if target is None:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Reference '{reference}' not found or path traversal blocked.",
            )

        content = read_bounded(target)
        return TextResult(
            provenance=prov,
            status="ok",
            text=content,
            metadata={"file": target.name, "size": target.stat().st_size},
        )

    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        if not self.is_available():
            return TextResult(
                provenance=prov,
                status="local_not_configured",
                message="CUC_CORPUS_DIR not configured.",
            )

        target = safe_resolve(self.corpus_dir, reference)
        if target:
            return TextResult(
                provenance=prov,
                status="ok",
                metadata={
                    "file": target.name,
                    "size": target.stat().st_size,
                    "corpus_dir": self.corpus_dir,
                    "format": target.suffix.lstrip("."),
                },
            )

        return TextResult(
            provenance=prov,
            status="not_found",
            message=f"No metadata for '{reference}'.",
        )
