"""Tests for the FastMCP server tools."""
import json

from theosis_ancient_context.server import (
    list_corpora_tool,
    get_corpus_status,
    search_corpus,
    get_text,
    get_text_metadata,
)


class TestListCorporaTool:
    def test_returns_nine_corpora(self):
        result = list_corpora_tool()
        assert len(result) == 9

    def test_all_have_required_keys(self):
        for rec in list_corpora_tool():
            assert "corpus_id" in rec
            assert "source_type" in rec
            assert "licence" in rec
            assert "source_url" in rec


class TestGetCorpusStatusTool:
    def test_unknown_corpus(self):
        result = get_corpus_status("nonexistent")
        assert "error" in result

    def test_known_corpus(self):
        result = get_corpus_status("tla")
        assert result["corpus_id"] == "tla"
        assert "access_status" in result


class TestSearchCorpusTool:
    def test_unknown_corpus(self):
        result = search_corpus("nonexistent", "query")
        assert result["status"] == "unknown_corpus"

    def test_deferred_corpus(self):
        result = search_corpus("dppc", "test")
        assert result["status"] == "deferred"

    def test_remote_only_corpus(self):
        result = search_corpus("tla", "test")
        assert result["status"] == "remote_only"

    def test_cdli_not_ready(self):
        result = search_corpus("cdli", "test")
        assert result["status"] == "not_ready"
        assert "cdli.earth" in result["message"]

    def test_coptic_not_configured(self):
        result = search_corpus("coptic_scriptorium", "test")
        assert result["status"] == "local_not_configured"

    def test_cuc_not_configured(self):
        result = search_corpus("cuc", "test")
        assert result["status"] == "local_not_configured"

    def test_limit_capped(self):
        result = search_corpus("tla", "test", limit=1000)
        # Should not crash; remote adapters return status regardless
        assert result["status"] == "remote_only"


class TestGetTextTool:
    def test_unknown_corpus(self):
        result = get_text("nonexistent", "ref1")
        assert result["status"] == "unknown_corpus"

    def test_deferred_corpus(self):
        result = get_text("dppc", "ref1")
        assert result["status"] == "deferred"

    def test_remote_only_corpus(self):
        result = get_text("tla", "ref1")
        assert result["status"] == "remote_only"


class TestGetTextMetadataTool:
    def test_unknown_corpus(self):
        result = get_text_metadata("nonexistent", "ref1")
        assert result["status"] == "unknown_corpus"

    def test_deferred_corpus(self):
        result = get_text_metadata("cip", "ref1")
        assert result["status"] == "deferred"
