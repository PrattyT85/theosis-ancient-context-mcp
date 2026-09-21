"""Corpus registry — all known sources and their integration status."""
from __future__ import annotations

import os
from typing import Any

from .models import (
    AccessStatus,
    CorpusRecord,
    ProvenanceEnvelope,
    SourceType,
)

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
        licence_notes="DOI: 10.5281/zenodo.10695308. 278 KTU texts. Text-Fabric format. Do NOT treat ORACC as Ugaritic.",
        integration_notes="local_optional — requires CUC_CORPUS_DIR. Safe lookup only when configured. No dependency on Text-Fabric unless available.",
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
        licence_notes="Searchable records with transliteration, translation, commentary, bibliography, provenance, images. Exact public API not confirmed.",
        integration_notes="remote_only — no safe adapter in v0.1.0.",
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
    env_map = {
        "coptic_scriptorium": "COPTSCRIPTORIUM_CORPUS_DIR",
        "cuc": "CUC_CORPUS_DIR",
        "tlhdig": "HITTITE_TLHDIG_DIR",
    }
    env_var = env_map.get(corpus_id)
    if env_var:
        return os.environ.get(env_var)
    return None


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
