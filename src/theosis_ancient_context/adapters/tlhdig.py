"""Hittite TLHdig local adapter — reads XML corpus from Zenodo dataset.

Requires HITTITE_TLHDIG_DIR pointing to the extracted TLHdig XML dataset
(e.g. TLHbasisONLINE25.1_ZENODO/ from the Zenodo zip archive).
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..models import SearchResult, TextResult
from ..registry import make_provenance
from . import BaseAdapter
from .path_utils import read_bounded, safe_resolve

CORPUS_ID = "tlhdig"

# ---------------------------------------------------------------------------
# Bounded directory traversal helpers
# ---------------------------------------------------------------------------

_MAX_SUBDIRS = 500  # CTH directories to scan
_MAX_FILES_PER_DIR = 200  # XML files per CTH directory
_MAX_SEARCH_FILES = 1000  # total files scanned in search


def _list_cth_dirs(root: Path, limit: int = _MAX_SUBDIRS) -> list[Path]:
    """List CTH_*_XML subdirectories under root, bounded."""
    results: list[Path] = []
    try:
        for entry in sorted(root.iterdir()):
            if entry.is_dir() and entry.name.startswith("CTH"):
                results.append(entry)
                if len(results) >= limit:
                    break
    except (PermissionError, OSError):
        pass
    return results


def _list_xml_files(cth_dir: Path, limit: int = _MAX_FILES_PER_DIR) -> list[Path]:
    """List .xml files in a CTH directory, bounded."""
    results: list[Path] = []
    try:
        for entry in sorted(cth_dir.iterdir()):
            if entry.is_file() and entry.suffix.lower() == ".xml":
                results.append(entry)
                if len(results) >= limit:
                    break
    except (PermissionError, OSError):
        pass
    return results


def _extract_cth_number(dirname: str) -> str:
    """Extract CTH number from a directory name like 'CTH 100_XML'."""
    m = re.match(r"CTH\s+(\d+)", dirname)
    return m.group(1) if m else dirname


def _parse_xml_metadata(xml_path: Path) -> dict:
    """Extract basic metadata from a TLHdig XML file.

    Returns a dict with cth_number, file, size, and any top-level
    attributes found on the root element.
    """
    meta: dict = {
        "file": xml_path.name,
        "size": xml_path.stat().st_size,
        "cth_number": _extract_cth_number(xml_path.parent.name),
    }
    try:
        tree = ET.parse(xml_path)  # noqa: S314 — trusted local corpus
        root = tree.getroot()
        # Capture root tag and any attributes
        meta["xml_root_tag"] = root.tag
        if root.attrib:
            meta["xml_root_attrs"] = dict(root.attrib)
        # Try to find a title or identifier in first-level children
        for child in list(root)[:5]:
            if child.text and child.text.strip():
                tag_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag_local in ("title", "id", "identifier", "repository"):
                    meta[tag_local] = child.text.strip()[:200]
    except (ET.ParseError, OSError):
        pass
    return meta


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class HittiteTlhdigAdapter(BaseAdapter):
    """Local adapter for the TLHdig XML dataset (Zenodo CC-BY 4.0).

    Requires the HITTITE_TLHDIG_DIR environment variable pointing to the
    extracted TLHdig directory (e.g. TLHbasisONLINE25.1_ZENODO/).
    """

    corpus_id = CORPUS_ID

    def __init__(self) -> None:
        self.corpus_dir: str | None = os.environ.get("HITTITE_TLHDIG_DIR")

    def is_available(self) -> bool:
        if not self.corpus_dir:
            return False
        return os.path.isdir(self.corpus_dir)

    def search(self, query: str, limit: int = 20) -> SearchResult:
        prov = make_provenance(CORPUS_ID)
        corpus_dir = self.corpus_dir
        if not corpus_dir:
            return SearchResult(
                provenance=prov,
                status="local_not_configured",
                message=(
                    "HITTITE_TLHDIG_DIR not configured or not a directory. "
                    "Download TLHdig from https://zenodo.org/records/15459134 "
                    "and extract to set up local search."
                ),
            )

        root = Path(corpus_dir)
        cth_dirs = _list_cth_dirs(root)
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        matches: list[dict] = []
        files_scanned = 0

        for cth_dir in cth_dirs:
            cth_num = _extract_cth_number(cth_dir.name)
            xml_files = _list_xml_files(cth_dir)
            for xf in xml_files:
                files_scanned += 1
                if files_scanned > _MAX_SEARCH_FILES:
                    break
                content = read_bounded(xf, max_bytes=80_000)
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        matches.append({
                            "file": xf.name,
                            "cth": cth_num,
                            "line": i,
                            "text": line.strip()[:200],
                        })
                        if len(matches) >= limit:
                            break
                if len(matches) >= limit:
                    break
            if len(matches) >= limit:
                break

        return SearchResult(
            provenance=prov,
            status="ok",
            results=matches,
            message=(
                f"Found {len(matches)} match(es) across {files_scanned} file(s). "
                "Licence: CC-BY 4.0 (Zenodo DOI: 10.5281/zenodo.15459134). "
                "HPM site notes CC BY-SA — verify for your use case."
            ),
        )

    def get_text(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        corpus_dir = self.corpus_dir
        if not corpus_dir:
            return TextResult(
                provenance=prov,
                status="local_not_configured",
                message="HITTITE_TLHDIG_DIR not configured.",
            )

        # Try resolving as a direct file path under corpus root
        target = safe_resolve(corpus_dir, reference)
        if target is not None and target.suffix.lower() == ".xml":
            content = read_bounded(target)
            return TextResult(
                provenance=prov,
                status="ok",
                text=content,
                metadata=_parse_xml_metadata(target),
            )

        # Try resolving as CTH number — look up all XML files in that CTH dir
        cth_match = re.match(r"^(?:CTH\s*)?(\d+)$", reference.strip(), re.IGNORECASE)
        if cth_match:
            cth_num = cth_match.group(1)
            root = Path(corpus_dir)
            for cth_dir in _list_cth_dirs(root):
                if _extract_cth_number(cth_dir.name) == cth_num:
                    xml_files = _list_xml_files(cth_dir)
                    if xml_files:
                        # Return first XML file for the CTH number
                        target = xml_files[0]
                        content = read_bounded(target)
                        return TextResult(
                            provenance=prov,
                            status="ok",
                            text=content,
                            metadata=_parse_xml_metadata(target),
                        )

        return TextResult(
            provenance=prov,
            status="not_found",
            message=f"Reference '{reference}' not found in TLHdig corpus.",
        )

    def get_metadata(self, reference: str) -> TextResult:
        prov = make_provenance(CORPUS_ID)
        corpus_dir = self.corpus_dir
        if not corpus_dir:
            return TextResult(
                provenance=prov,
                status="local_not_configured",
                message="HITTITE_TLHDIG_DIR not configured.",
            )

        # Try direct file path
        target = safe_resolve(corpus_dir, reference)
        if target is not None and target.suffix.lower() == ".xml":
            return TextResult(
                provenance=prov,
                status="ok",
                metadata=_parse_xml_metadata(target),
            )

        # Try CTH number
        cth_match = re.match(r"^(?:CTH\s*)?(\d+)$", reference.strip(), re.IGNORECASE)
        if cth_match:
            cth_num = cth_match.group(1)
            root = Path(corpus_dir)
            for cth_dir in _list_cth_dirs(root):
                if _extract_cth_number(cth_dir.name) == cth_num:
                    xml_files = _list_xml_files(cth_dir)
                    if xml_files:
                        return TextResult(
                            provenance=prov,
                            status="ok",
                            metadata=_parse_xml_metadata(xml_files[0]),
                        )

        return TextResult(
            provenance=prov,
            status="not_found",
            message=f"No metadata for '{reference}' in TLHdig corpus.",
        )
