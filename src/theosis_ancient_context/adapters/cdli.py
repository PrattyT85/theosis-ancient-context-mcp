"""CDLI adapter — bounded read-only HTTP client for cdli.earth REST JSON API.

Endpoints verified:
  GET /search/?q=<query>&format=json  → JSON list of artifact records
  GET /artifacts/<id>.json            → JSON list with artifact metadata
  GET /inscriptions/<id>.json         → JSON list with ATF and artifact_id

All methods are synchronous, stateless, and use stdlib urllib.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..models import SearchResult, TextResult
from ..registry import make_provenance
from . import BaseAdapter

CORPUS_ID = "cdli"

# ---------------------------------------------------------------------------
# Safety bounds
# ---------------------------------------------------------------------------
DEFAULT_TIMEOUT_S: int = 15
MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 MiB
_MAX_QUERY_LEN: int = 500
_MAX_ID: int = 50_000_000  # CDLI IDs are well below this
_MAX_LIMIT: int = 50

_BASE_URL = "https://cdli.earth"


def _validate_query(query: str) -> str | None:
    """Return stripped query or None if invalid."""
    q = query.strip()
    if not q or len(q) > _MAX_QUERY_LEN:
        return None
    return q


def _validate_id(reference: str) -> int | None:
    """Parse a CDLI numeric ID from a reference string.

    Accepts plain integers or CDLI P/Q-style references with numeric suffixes.
    Returns the integer ID or None if invalid.
    """
    ref = reference.strip()
    if not ref:
        return None
    # Accept plain integer
    if ref.isdigit():
        val = int(ref)
        return val if 0 < val <= _MAX_ID else None
    # Accept P000001, Q000002 style — extract trailing digits
    m = re.match(r"^[PpQq](\d+)$", ref)
    if m:
        val = int(m.group(1))
        return val if 0 < val <= _MAX_ID else None
    return None


def _fetch_json(url: str, timeout: int = DEFAULT_TIMEOUT_S) -> Any:
    """Fetch a JSON URL with bounds. Returns parsed data or raises."""
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "theosis-ancient-context-mcp/0.1"},
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError(f"Response exceeds {MAX_RESPONSE_BYTES} bytes limit")
    return json.loads(raw.decode("utf-8", errors="replace"))


def _artifact_summary(art: dict[str, Any]) -> dict[str, Any]:
    """Extract a bounded summary from an artifact dict."""
    summary: dict[str, Any] = {
        "id": art.get("id"),
        "designation": art.get("designation"),
        "museum_no": art.get("museum_no"),
        "excavation_no": art.get("excavation_no"),
        "dates_referenced": art.get("dates_referenced"),
    }
    # Languages
    langs = []
    for lang_entry in art.get("languages", []):
        lang_obj = lang_entry.get("language", {})
        code = lang_obj.get("inline_code") or lang_obj.get("language", "")
        if code:
            langs.append(code)
    if langs:
        summary["languages"] = langs
    # Genres
    genres = []
    for g in art.get("genres", []):
        genre_obj = g.get("genre", {})
        name = genre_obj.get("genre", "")
        if name:
            genres.append(name)
    if genres:
        summary["genres"] = genres
    # Provenience hints
    for field in ("findspot_comments", "findspot_square", "provenience"):
        val = art.get(field)
        if val:
            summary[field] = val
    # Dimensions
    for field in ("height", "width", "thickness"):
        val = art.get(field)
        if val:
            summary[field] = val
    # Source URL
    summary["source_url"] = f"{_BASE_URL}/artifact/{art.get('id', '')}"
    return summary


def _inscription_summary(insc: dict[str, Any]) -> dict[str, Any]:
    """Extract a bounded summary from an inscription dict."""
    summary: dict[str, Any] = {
        "id": insc.get("id"),
        "artifact_id": insc.get("artifact_id"),
        "source_url": f"{_BASE_URL}/inscription/{insc.get('id', '')}",
    }
    if insc.get("atf"):
        summary["has_atf"] = True
        # Don't dump full ATF into summary — caller can get_text for it
    return summary


class CDLIAdapter(BaseAdapter):
    """CDLI adapter — read-only HTTP client for cdli.earth REST JSON API.

    Methods:
      - search(query, limit): keyword search via /search/?q=...&format=json
      - get_text(reference):  ATF text via /inscriptions/<id>.json
      - get_metadata(reference): artifact metadata via /artifacts/<id>.json

    All network access is bounded (timeout, response-size cap).
    """

    corpus_id = CORPUS_ID

    def __init__(self, base_url: str = _BASE_URL, timeout: int = DEFAULT_TIMEOUT_S) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def is_available(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # search
    # ------------------------------------------------------------------
    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(CORPUS_ID)
        q = _validate_query(query)
        if q is None:
            return SearchResult(
                provenance=prov,
                status="error",
                message="Invalid or empty query (max 500 chars).",
            )
        limit = min(max(limit, 1), _MAX_LIMIT)
        url = f"{self._base_url}/search/?q={urllib.parse.quote(q, safe='')}&format=json"
        try:
            data = _fetch_json(url, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            return SearchResult(
                provenance=prov,
                status="upstream_error",
                message=f"CDLI returned HTTP {exc.code}: {exc.reason}",
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return SearchResult(
                provenance=prov,
                status="network_error",
                message=f"Failed to reach CDLI: {exc}",
            )
        if not isinstance(data, list):
            return SearchResult(
                provenance=prov,
                status="error",
                message="Unexpected response format from CDLI search.",
            )
        results = [_artifact_summary(item) for item in data[:limit]]
        return SearchResult(
            provenance=prov,
            status="ok",
            results=results,
            message=f"CDLI found {len(results)} artifact(s) for query '{q}'. Open access — verify licence for your use.",
        )

    # ------------------------------------------------------------------
    # get_text  (ATF via inscriptions endpoint)
    # ------------------------------------------------------------------
    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        art_id = _validate_id(reference)
        if art_id is None:
            return TextResult(
                provenance=prov,
                status="error",
                message=f"Invalid CDLI reference: '{reference}'. Use a numeric ID or P/Q-style reference.",
            )
        # First get artifact to find inscription_id
        art_url = f"{self._base_url}/artifacts/{art_id}.json"
        try:
            art_data = _fetch_json(art_url, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return TextResult(
                    provenance=prov,
                    status="not_found",
                    message=f"Artifact {art_id} not found on CDLI.",
                )
            return TextResult(
                provenance=prov,
                status="upstream_error",
                message=f"CDLI returned HTTP {exc.code}: {exc.reason}",
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return TextResult(
                provenance=prov,
                status="network_error",
                message=f"Failed to reach CDLI: {exc}",
            )
        if not isinstance(art_data, list) or len(art_data) == 0:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Artifact {art_id} not found on CDLI.",
            )
        art = art_data[0]
        # Look for nested inscription
        inscription = art.get("inscription")
        if not inscription:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Artifact {art_id} has no inscription available on CDLI.",
            )
        insc_id = inscription.get("id")
        if not insc_id:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Artifact {art_id} inscription has no ID.",
            )
        # Fetch full inscription via dedicated endpoint
        insc_url = f"{self._base_url}/inscriptions/{insc_id}.json"
        try:
            insc_data = _fetch_json(insc_url, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            return TextResult(
                provenance=prov,
                status="upstream_error",
                message=f"CDLI inscription endpoint returned HTTP {exc.code}: {exc.reason}",
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return TextResult(
                provenance=prov,
                status="network_error",
                message=f"Failed to reach CDLI inscription endpoint: {exc}",
            )
        if not isinstance(insc_data, list) or len(insc_data) == 0:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Inscription {insc_id} not found on CDLI.",
            )
        insc_full = insc_data[0]
        atf = insc_full.get("atf", "")
        if not atf:
            return TextResult(
                provenance=prov,
                status="ok",
                text="",
                metadata=_inscription_summary(insc_full) | _artifact_summary(art),
                message=f"Inscription {insc_id} returned no ATF text. Metadata provided.",
            )
        return TextResult(
            provenance=prov,
            status="ok",
            text=atf,
            metadata={
                "inscription_id": insc_id,
                "artifact_id": art_id,
                "designation": art.get("designation"),
                "source_url": f"{_BASE_URL}/inscription/{insc_id}",
            },
            message=f"ATF text from inscription {insc_id} (artifact {art_id}). Open access — verify licence for your use.",
        )

    # ------------------------------------------------------------------
    # get_metadata
    # ------------------------------------------------------------------
    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        art_id = _validate_id(reference)
        if art_id is None:
            return TextResult(
                provenance=prov,
                status="error",
                message=f"Invalid CDLI reference: '{reference}'. Use a numeric ID or P/Q-style reference.",
            )
        url = f"{self._base_url}/artifacts/{art_id}.json"
        try:
            data = _fetch_json(url, timeout=self._timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return TextResult(
                    provenance=prov,
                    status="not_found",
                    message=f"Artifact {art_id} not found on CDLI.",
                )
            return TextResult(
                provenance=prov,
                status="upstream_error",
                message=f"CDLI returned HTTP {exc.code}: {exc.reason}",
            )
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return TextResult(
                provenance=prov,
                status="network_error",
                message=f"Failed to reach CDLI: {exc}",
            )
        if not isinstance(data, list) or len(data) == 0:
            return TextResult(
                provenance=prov,
                status="not_found",
                message=f"Artifact {art_id} not found on CDLI.",
            )
        art = data[0]
        summary = _artifact_summary(art)
        # Add additional metadata fields
        for field in ("materials", "genres", "publications", "composites"):
            items = art.get(field, [])
            if items:
                summary[field] = items
        return TextResult(
            provenance=prov,
            status="ok",
            metadata=summary,
            message=f"Metadata for artifact {art_id} from CDLI. Open access — verify licence for your use.",
        )
