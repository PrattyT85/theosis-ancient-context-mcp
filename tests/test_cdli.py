"""Tests for the CDLI adapter stub."""
from theosis_ancient_context.adapters.cdli import CDLIAdapter


class TestCDLIAdapter:
    def test_not_available(self):
        adapter = CDLIAdapter()
        assert adapter.is_available() is False

    def test_search_returns_not_ready(self):
        adapter = CDLIAdapter()
        result = adapter.search("tablet")
        assert result.status == "not_ready"
        assert "cdli.earth" in result.message

    def test_get_text_returns_not_ready(self):
        adapter = CDLIAdapter()
        result = adapter.get_text("P000001")
        assert result.status == "not_ready"

    def test_get_metadata_returns_not_ready(self):
        adapter = CDLIAdapter()
        result = adapter.get_metadata("P000001")
        assert result.status == "not_ready"

    def test_provenance_present(self):
        adapter = CDLIAdapter()
        result = adapter.search("test")
        assert result.provenance.corpus_id == "cdli"
        assert result.provenance.licence == "Open access"
