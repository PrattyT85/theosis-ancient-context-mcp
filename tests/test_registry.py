"""Tests for the corpus registry."""
import os

from theosis_ancient_context.models import AccessStatus, SourceType
from theosis_ancient_context.registry import (
    get_corpus,
    list_corpora,
    corpus_status,
    make_provenance,
)


REQUIRED_CORPORA = [
    "tla",
    "coptic_scriptorium",
    "hpm_hdivt",
    "cuc",
    "dasi",
    "ociana",
    "cdli",
    "dppc",
    "cip",
]


class TestRegistryCompleteness:
    """Registry must contain all required corpora with valid fields."""

    def test_all_required_corpora_present(self):
        records = list_corpora()
        ids = {r.corpus_id for r in records}
        for cid in REQUIRED_CORPORA:
            assert cid in ids, f"Missing corpus: {cid}"

    def test_nine_corpora_registered(self):
        assert len(list_corpora()) == 9

    def test_all_records_have_required_fields(self):
        for rec in list_corpora():
            assert rec.corpus_id
            assert rec.name
            assert rec.languages
            assert rec.period
            assert isinstance(rec.source_type, SourceType)
            assert isinstance(rec.access_status, AccessStatus)
            assert rec.source_url
            assert rec.licence

    def test_deferred_corpora_marked_deferred(self):
        for cid in ["dppc", "cip"]:
            rec = get_corpus(cid)
            assert rec is not None
            assert rec.source_type == SourceType.DEFERRED
            assert rec.access_status == AccessStatus.DEFERRED

    def test_local_optional_corpora(self):
        for cid in ["coptic_scriptorium", "cuc"]:
            rec = get_corpus(cid)
            assert rec is not None
            assert rec.source_type == SourceType.LOCAL_OPTIONAL

    def test_remote_only_corpora(self):
        for cid in ["tla", "hpm_hdivt", "dasi", "ociana", "cdli"]:
            rec = get_corpus(cid)
            assert rec is not None
            assert rec.source_type in (SourceType.REMOTE_ONLY, SourceType.PLANNED_ADAPTER)

    def test_unknown_corpus_returns_none(self):
        assert get_corpus("nonexistent") is None


class TestCorpusStatus:
    """Status checks for corpora with and without local paths."""

    def test_unknown_corpus_status(self):
        result = corpus_status("nonexistent")
        assert "error" in result

    def test_local_not_configured(self, monkeypatch):
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        result = corpus_status("coptic_scriptorium")
        assert result["local_path_configured"] is False

    def test_local_configured_missing_path(self, monkeypatch):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", "/nonexistent/path")
        result = corpus_status("coptic_scriptorium")
        assert result["local_path_configured"] is True
        assert result["local_path_exists"] is False

    def test_local_configured_existing_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CUC_CORPUS_DIR", str(tmp_path))
        # Create a test file
        (tmp_path / "ktu_1.txt").write_text("test content")
        result = corpus_status("cuc")
        assert result["local_path_configured"] is True
        assert result["local_path_exists"] is True
        assert result["local_file_count"] >= 1

    def test_remote_only_status(self):
        result = corpus_status("tla")
        assert result["access_status"] == "remote_status_only"
        assert result["local_path_configured"] is False

    def test_deferred_status(self):
        result = corpus_status("dppc")
        assert result["access_status"] == "deferred"


class TestProvenance:
    """Provenance envelopes are correct for all corpora."""

    def test_provenance_for_every_corpus(self):
        for cid in REQUIRED_CORPORA:
            prov = make_provenance(cid)
            assert prov.corpus_id == cid
            assert prov.source_url
            assert prov.licence
            assert prov.source_layer
            assert prov.access_status

    def test_provenance_for_unknown(self):
        prov = make_provenance("nonexistent")
        assert prov.source_layer == "unknown"
        assert prov.licence_warning == "Unknown corpus"

    def test_provenance_has_licence_notes(self):
        prov = make_provenance("cuc")
        assert "CC BY-NC 4.0" in prov.licence
        assert prov.licence_warning
