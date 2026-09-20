"""Tests for remote-only and deferred adapter behavior."""
from theosis_ancient_context.adapters.remote_status import (
    TLAAdapter,
    HPMAdapter,
    DASIAdapter,
    OCIANAAdapter,
    DeferredAdapter,
)


class TestRemoteStatusAdapters:
    def test_tla_remote_only(self):
        adapter = TLAAdapter()
        assert adapter.is_available() is False
        result = adapter.search("test")
        assert result.status == "remote_only"

    def test_hpm_remote_only(self):
        adapter = HPMAdapter()
        assert adapter.is_available() is False
        result = adapter.get_text("test")
        assert result.status == "remote_only"

    def test_dasi_remote_only(self):
        adapter = DASIAdapter()
        result = adapter.search("test")
        assert result.status == "remote_only"

    def test_ociana_remote_only(self):
        adapter = OCIANAAdapter()
        result = adapter.get_text("test")
        assert result.status == "remote_only"

    def test_deferred_dppc(self):
        adapter = DeferredAdapter("dppc")
        assert adapter.is_available() is False
        result = adapter.search("test")
        assert result.status == "deferred"
        assert "not integrated" in result.message.lower()

    def test_deferred_cip(self):
        adapter = DeferredAdapter("cip")
        result = adapter.get_text("test")
        assert result.status == "deferred"

    def test_provenance_envelope_on_all(self):
        for cls in (TLAAdapter, HPMAdapter, DASIAdapter, OCIANAAdapter):
            adapter = cls()
            result = adapter.search("q")
            assert result.provenance is not None
            assert result.provenance.corpus_id
            assert result.provenance.licence

    def test_deferred_provenance(self):
        adapter = DeferredAdapter("dppc")
        result = adapter.search("q")
        assert result.provenance.corpus_id == "dppc"
        assert result.provenance.source_url
