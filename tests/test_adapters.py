"""Tests for Coptic SCRIPTORIUM and CUC local adapters."""
import os
import json

from theosis_ancient_context.adapters.coptic import CopticScriptoriumAdapter
from theosis_ancient_context.adapters.cuc import CUCAdapter


class TestCopticAdapter:
    def test_not_available_without_env(self, monkeypatch):
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        adapter = CopticScriptoriumAdapter()
        assert adapter.is_available() is False

    def test_not_available_with_nonexistent_path(self, monkeypatch):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", "/nonexistent")
        adapter = CopticScriptoriumAdapter()
        assert adapter.is_available() is False

    def test_available_with_real_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        adapter = CopticScriptoriumAdapter()
        assert adapter.is_available() is True

    def test_search_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        adapter = CopticScriptoriumAdapter()
        result = adapter.search("test")
        assert result.status == "local_not_configured"

    def test_search_with_corpus(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        (tmp_path / "test.txt").write_text("line one\nPsalm of David\nline three")
        adapter = CopticScriptoriumAdapter()
        result = adapter.search("Psalm")
        assert result.status == "ok"
        assert len(result.results) == 1
        assert "Psalm" in result.results[0]["text"]

    def test_get_text_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        adapter = CopticScriptoriumAdapter()
        result = adapter.get_text("file.txt")
        assert result.status == "local_not_configured"

    def test_get_text_found(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        (tmp_path / "doc.xml").write_text("<text>content</text>")
        adapter = CopticScriptoriumAdapter()
        result = adapter.get_text("doc.xml")
        assert result.status == "ok"
        assert "content" in result.text

    def test_get_text_path_traversal_blocked(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        adapter = CopticScriptoriumAdapter()
        result = adapter.get_text("../../etc/passwd")
        assert result.status == "not_found"

    def test_get_metadata_with_meta_json(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        meta = {"doc.xml": {"title": "Test", "author": "Unknown"}}
        (tmp_path / "meta.json").write_text(json.dumps(meta))
        adapter = CopticScriptoriumAdapter()
        result = adapter.get_metadata("doc.xml")
        assert result.status == "ok"
        assert result.metadata["title"] == "Test"


class TestCUCAdapter:
    def test_not_available_without_env(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        adapter = CUCAdapter()
        assert adapter.is_available() is False

    def test_search_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        adapter = CUCAdapter()
        result = adapter.search("ktu")
        assert result.status == "local_not_configured"

    def test_search_with_corpus(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CUC_CORPUS_DIR", str(tmp_path))
        (tmp_path / "ktu_1_1.txt").write_text("grt ilm rbm\nilm ybbq\nktu text")
        adapter = CUCAdapter()
        result = adapter.search("ilm")
        assert result.status == "ok"
        assert len(result.results) == 2  # two lines match

    def test_get_text_path_traversal_blocked(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CUC_CORPUS_DIR", str(tmp_path))
        adapter = CUCAdapter()
        result = adapter.get_text("../../../etc/passwd")
        assert result.status == "not_found"

    def test_search_result_has_licence_warning(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CUC_CORPUS_DIR", str(tmp_path))
        (tmp_path / "test.txt").write_text("ug")
        adapter = CUCAdapter()
        result = adapter.search("ug")
        assert "CC BY-NC 4.0" in result.message
