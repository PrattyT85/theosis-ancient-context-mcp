"""FastMCP stdio server for ancient text corpora."""
from __future__ import annotations

from fastmcp import FastMCP

from . import __version__
from .adapters.registry import get_adapter
from .registry import (
    corpus_status,
    get_source_manifest as get_source_manifest_records,
    list_corpora as list_corpora_records,
    REGISTRY,
)

mcp = FastMCP(
    name="theosis-ancient-context",
    version=__version__,
    instructions=(
        "Theosis Ancient Context MCP — access ancient text corpora: "
        "Egyptian (TLA), Coptic (Scriptorium), Hittite (HPM/HDivT), "
        "Ugaritic (CUC), Akkadian/Sumerian (CDLI, OCIANA), "
        "Arabic epigraphic (DASI), Phoenician/Punic (DPPC, CIP). "
        "All results include provenance envelopes with source layer, "
        "licence, and integration status."
    ),
)

# ---------------------------------------------------------------------------
# Response-size guard
# ---------------------------------------------------------------------------
MAX_SEARCH_RESULTS = 50
MAX_TEXT_BYTES = 200_000


# ---------------------------------------------------------------------------
# Tool 1: list_corpora
# ---------------------------------------------------------------------------
@mcp.tool()
def list_corpora() -> list[dict]:
    """List all registered ancient text corpora with metadata.

    Returns registry records for TLA, Coptic SCRIPTORIUM, HPM/HDivT,
    CUC, DASI, OCIANA, CDLI, DPPC, CIP — each with source_type,
    language, period, access_status, source_url, licence notes, and
    integration notes.
    """
    records = list_corpora_records()
    return [r.model_dump() for r in records]


# Backward-compatible Python import name; the MCP tool is ``list_corpora``.
list_corpora_tool = list_corpora


# ---------------------------------------------------------------------------
# Tool 2: get_corpus_status
# ---------------------------------------------------------------------------
@mcp.tool()
def get_corpus_status(corpus: str) -> dict:
    """Get detailed status for a specific corpus.

    Includes configured local path, availability checks, and version/commit
    info when discoverable.
    """
    return corpus_status(corpus)


# ---------------------------------------------------------------------------
# Tool 3: get_source_manifest
# ---------------------------------------------------------------------------
@mcp.tool()
def get_source_manifest() -> list[dict]:
    """Return the machine-readable source manifest with live local-path status.

    Each entry includes source_url, source_type, language, period,
    access_status, licence, licence_notes, local_path_env_var,
    version_or_commit, doi, last_reviewed, and next_review fields.
    Local path status is overlaid from the current environment.
    """
    return get_source_manifest_records()


# ---------------------------------------------------------------------------
# Tool 4: search_corpus
# ---------------------------------------------------------------------------
@mcp.tool()
def search_corpus(corpus: str, query: str, limit: int = 20) -> dict:
    """Search a corpus for a query string.

    For enabled/local adapters, returns matching results. For deferred or
    remote-only sources, returns an explicit not_ready/remote_only result
    with provenance envelope rather than failing ambiguously.
    """
    limit = min(limit, MAX_SEARCH_RESULTS)
    adapter = get_adapter(corpus)
    if adapter is None:
        return {
            "provenance": None,
            "status": "unknown_corpus",
            "message": f"Unknown corpus: {corpus}. Use list_corpora to see available corpora.",
        }
    result = adapter.search(query, limit=limit)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 5: get_text
# ---------------------------------------------------------------------------
@mcp.tool()
def get_text(corpus: str, reference: str) -> dict:
    """Retrieve text content by reference identifier.

    For local adapters, returns bounded text with provenance. For
    deferred/remote-only sources, returns explicit status.
    """
    adapter = get_adapter(corpus)
    if adapter is None:
        return {
            "provenance": None,
            "status": "unknown_corpus",
            "message": f"Unknown corpus: {corpus}.",
        }
    result = adapter.get_text(reference)
    return result.model_dump()


# ---------------------------------------------------------------------------
# Tool 6: get_text_metadata
# ---------------------------------------------------------------------------
@mcp.tool()
def get_text_metadata(corpus: str, reference: str) -> dict:
    """Retrieve metadata for a text reference.

    For local adapters, returns file metadata and provenance. For
    deferred/remote-only sources, returns explicit status.
    """
    adapter = get_adapter(corpus)
    if adapter is None:
        return {
            "provenance": None,
            "status": "unknown_corpus",
            "message": f"Unknown corpus: {corpus}.",
        }
    result = adapter.get_metadata(reference)
    return result.model_dump()
