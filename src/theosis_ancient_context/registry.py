"""Corpus registry — all known sources and their integration status."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    AccessStatus,
    CorpusRecord,
    ProvenanceEnvelope,
    SourceType,
)

SOURCES_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "sources.json"

# ---------------------------------------------------------------------------
# Static registry
# ---------------------------------------------------------------------------

REGISTRY: dict[str, CorpusRecord] = {
    "tla": CorpusRecord(
        corpus_id="tla",
        name="Thesaurus Linguae Aegyptiae",
        languages=["Egyptian"],
        period="Old Egyptian – Coptic (3000 BCE – 1700 CE)",
        source_type=SourceType.PLANNED_ADAPTER,
        access_status=AccessStatus.REMOTE_STATUS_ONLY,
        source_url="https://thesaurus-linguae-aegyptiae.de/",
        licence="Free for non-commercial research",
        licence_notes="Public research platform; no stable public API contract confirmed. Raw JSON/TEI publication planned.",
        integration_notes="remote_only — no safe adapter in v0.1.0. Search page exists but undocumented form internals.",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "coptic_scriptorium": CorpusRecord(
        corpus_id="coptic_scriptorium",
        name="Coptic SCRIPTORIUM",
        languages=["Coptic"],
        period="2nd – 13th century CE",
        source_type=SourceType.LOCAL_OPTIONAL,
        access_status=AccessStatus.LOCAL_NOT_CONFIGURED,
        source_url="https://github.com/CopticScriptorium/corpora",
        licence="CC-BY (with explicit exceptions)",
        licence_notes="v6.3.0 release; CoNLL-U/relANNIS/PAULA/TEI formats. Some parts under different licences — check individual files.",
        integration_notes="local_optional — requires COPTSCRIPTORIUM_CORPUS_DIR. Do not bundle 2.38m-word data. Safe local search over bounded text files only.",
        local_path_env_var="COPTSCRIPTORIUM_CORPUS_DIR",
        version_or_commit="v6.3.0",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "hpm_hdivt": CorpusRecord(
        corpus_id="hpm_hdivt",
        name="Hittite Ritual Texts (HPM / HDivT)",
        languages=["Hittite"],
        period="2nd millennium BCE",
        source_type=SourceType.REMOTE_ONLY,
        access_status=AccessStatus.REMOTE_STATUS_ONLY,
        source_url="https://hethport.net/",
        licence="Research/academic use",
        licence_notes="HPM is mostly HTML, no REST API. TLHdig XML dataset available separately (see tlhdig corpus).",
        integration_notes="remote_only — no safe adapter in v0.1.0. Bulk download not performed.",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "tlhdig": CorpusRecord(
        corpus_id="tlhdig",
        name="Thesaurus Linguarum Hethaeorum digitalis (TLHdig)",
        languages=["Hittite"],
        period="2nd millennium BCE",
        source_type=SourceType.LOCAL_OPTIONAL,
        access_status=AccessStatus.LOCAL_NOT_CONFIGURED,
        source_url="https://zenodo.org/records/15459134",
        licence="CC-BY 4.0",
        licence_notes=(
            "Zenodo DOI: 10.5281/zenodo.15459134. CC-BY 4.0 per Zenodo metadata. "
            "HPM site states CC BY-SA — verify for your use case. "
            "Do not bundle 63.9 MB archive; require HITTITE_TLHDIG_DIR."
        ),
        integration_notes=(
            "local_optional — requires HITTITE_TLHDIG_DIR pointing to extracted "
            "TLHdig XML dataset. CTH subdirectories contain XML transliterations. "
            "Safe local search and text retrieval only."
        ),
        local_path_env_var="HITTITE_TLHDIG_DIR",
        version_or_commit="25.1",
        doi="10.5281/zenodo.15459134",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "cuc": CorpusRecord(
        corpus_id="cuc",
        name="Copenhagen Ugaritic Corpus",
        languages=["Ugaritic"],
        period="2nd millennium BCE",
        source_type=SourceType.LOCAL_OPTIONAL,
        access_status=AccessStatus.LOCAL_NOT_CONFIGURED,
        source_url="https://github.com/DT-UCPH/cuc",
        licence="CC BY-NC 4.0",
        licence_notes="DOI: 10.5281/zenodo.10695308. 278 KTU texts. Text-Fabric format. Do NOT treat ORACC as Ugaritic. Commercial use is prohibited.",
        integration_notes="local_optional — requires CUC_CORPUS_DIR. Safe lookup only when configured. No dependency on Text-Fabric unless available.",
        local_path_env_var="CUC_CORPUS_DIR",
        doi="10.5281/zenodo.10695308",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "dasi": CorpusRecord(
        corpus_id="dasi",
        name="Digital Archive for the Study of Pre-Islamic Arabian Inscriptions",
        languages=["Arabic", "Epigraphic"],
        period="1st millennium BCE – early CE",
        source_type=SourceType.REMOTE_ONLY,
        access_status=AccessStatus.REMOTE_STATUS_ONLY,
        source_url="https://dasi.cnr.it/",
        licence="Academic/research",
        licence_notes="API endpoint mentioned in help page; exact API contract not yet confirmed.",
        integration_notes="remote_only — no safe adapter in v0.1.0.",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "ociana": CorpusRecord(
        corpus_id="ociana",
        name="Online Corpus of the Inscriptions of Ancient North Arabia (OCIANA)",
        languages=["Ancient North Arabian", "Safaitic", "Dadanitic"],
        period="1st millennium BCE – early CE",
        source_type=SourceType.REMOTE_ONLY,
        access_status=AccessStatus.REMOTE_STATUS_ONLY,
        source_url="https://ociana.osu.edu/",
        licence="Academic/research",
        licence_notes="Searchable records with transliteration, translation, commentary, bibliography, provenance, images.",
        integration_notes="remote_only — no safe adapter in v0.1.0.",
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "cdli": CorpusRecord(
        corpus_id="cdli",
        name="Cuneiform Digital Library Initiative",
        languages=["Akkadian", "Sumerian", "Elamite"],
        period="4th millennium – 1st millennium BCE",
        source_type=SourceType.REMOTE_ONLY,
        access_status=AccessStatus.ADAPTER_READY,
        source_url="https://cdli.earth",
        licence="Open access",
        licence_notes=(
            "REST JSON API at https://cdli.earth. Search, artifact metadata, and inscription "
            "ATF endpoints verified. Open access — verify licence for your specific use case."
        ),
        integration_notes=(
            "adapter_ready — read-only HTTP adapter using stdlib urllib. "
            "Endpoints: /search/?q=...&format=json, /artifacts/<id>.json, /inscriptions/<id>.json. "
            "Strict query/id validation, 15s timeout, 5 MiB response cap. "
            "Do not claim full text when API returns metadata only."
        ),
        last_reviewed="2026-09-21",
        next_review="2026-12-21",
    ),
    "dppc": CorpusRecord(
        corpus_id="dppc",
        name="Dictionnaire de Phénicien et de Punique",
        languages=["Phoenician", "Punic"],
        period="1st millennium BCE – early CE",
        source_type=SourceType.DEFERRED,
        access_status=AccessStatus.DEFERRED,
        source_url="http://www.phoinikeia.org/PunicProjectCorpus/",
        licence="Unknown / not published",
        licence_notes="No public API, data, or licence confirmed. Not integrated.",
        integration_notes="deferred — no scraper, no adapter.",
        last_reviewed="2026-09-21",
        next_review="2027-03-21",
    ),
    "cip": CorpusRecord(
        corpus_id="cip",
        name="Corpus Inscriptionum Punicarum",
        languages=["Punic"],
        period="1st millennium BCE – early CE",
        source_type=SourceType.DEFERRED,
        access_status=AccessStatus.DEFERRED,
        source_url="http://www.phoinikeia.org/PunicProjectCorpus/",
        licence="Unknown / not published",
        licence_notes="No public API, data, or licence confirmed. Not integrated.",
        integration_notes="deferred — no scraper, no adapter.",
        last_reviewed="2026-09-21",
        next_review="2027-03-21",
    ),
}


def list_corpora() -> list[CorpusRecord]:
    """Return all registered corpus records."""
    return list(REGISTRY.values())


def get_corpus(corpus_id: str) -> CorpusRecord | None:
    """Look up a corpus by ID."""
    return REGISTRY.get(corpus_id)


def _local_path(corpus_id: str) -> str | None:
    """Return the configured local path for a corpus, or None."""
    rec = get_corpus(corpus_id)
    if rec and rec.local_path_env_var:
        return os.environ.get(rec.local_path_env_var)
    return None


def load_sources_manifest() -> list[dict[str, Any]]:
    """Load the machine-readable sources.json manifest."""
    if SOURCES_JSON_PATH.exists():
        return json.loads(SOURCES_JSON_PATH.read_text())
    return []


def get_source_manifest() -> list[dict[str, Any]]:
    """Return manifest records with live local-path status overlaid."""
    manifest = load_sources_manifest()
    results = []
    for entry in manifest:
        rec = get_corpus(entry["corpus_id"])
        merged = dict(entry)
        if rec:
            merged["source_type"] = rec.source_type.value
            merged["access_status"] = rec.access_status.value
        lp = _local_path(entry["corpus_id"])
        merged["local_path_configured"] = lp is not None
        merged["local_path_value"] = lp
        if lp and os.path.isdir(lp):
            merged["local_path_exists"] = True
            merged["access_status"] = AccessStatus.LOCAL_CONFIGURED.value
        else:
            merged["local_path_exists"] = False
        results.append(merged)
    return results


def corpus_status(corpus_id: str) -> dict[str, Any]:
    """Return detailed status for a corpus, including local path info."""
    rec = get_corpus(corpus_id)
    if rec is None:
        return {"error": f"Unknown corpus: {corpus_id}"}

    local_path = _local_path(corpus_id)
    status_info: dict[str, Any] = {
        "corpus_id": rec.corpus_id,
        "name": rec.name,
        "source_type": rec.source_type.value,
        "access_status": rec.access_status.value,
        "local_path_configured": local_path is not None,
        "local_path": local_path,
        "source_url": rec.source_url,
        "licence": rec.licence,
        "licence_notes": rec.licence_notes,
        "integration_notes": rec.integration_notes,
        "version_or_commit": rec.version_or_commit,
        "doi": rec.doi,
        "last_reviewed": rec.last_reviewed,
        "next_review": rec.next_review,
    }

    # Check local availability
    if local_path:
        if os.path.isdir(local_path):
            status_info["local_path_exists"] = True
            status_info["access_status"] = AccessStatus.LOCAL_CONFIGURED.value
            # Count files
            try:
                file_count = sum(1 for _ in os.scandir(local_path))
                status_info["local_file_count"] = file_count
            except (PermissionError, OSError):
                status_info["local_file_count"] = "unknown"
        else:
            status_info["local_path_exists"] = False

    return status_info


def make_provenance(corpus_id: str) -> ProvenanceEnvelope:
    """Build a provenance envelope for a corpus result."""
    rec = get_corpus(corpus_id)
    if rec is None:
        return ProvenanceEnvelope(
            source_layer="unknown",
            corpus_id=corpus_id,
            source_url="",
            licence="",
            licence_warning="Unknown corpus",
            access_status="unknown",
        )

    warning = ""
    if rec.licence_notes:
        warning = f"Licence notes: {rec.licence_notes}"

    access_status = rec.access_status.value
    local_path = _local_path(corpus_id)
    if local_path and os.path.isdir(local_path):
        access_status = AccessStatus.LOCAL_CONFIGURED.value

    return ProvenanceEnvelope(
        source_layer=rec.source_type.value,
        corpus_id=corpus_id,
        source_url=rec.source_url,
        licence=rec.licence,
        licence_warning=warning,
        access_status=access_status,
    )
