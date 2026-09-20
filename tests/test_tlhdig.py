"""Tests for the Hittite TLHdig local adapter."""
import os
import xml.etree.ElementTree as ET

from theosis_ancient_context.adapters.tlhdig import (
    HittiteTlhdigAdapter,
    _extract_cth_number,
    _list_cth_dirs,
    _list_xml_files,
)


# ---------------------------------------------------------------------------
# Helper: create a minimal TLHdig-style directory tree in tmp_path
# ---------------------------------------------------------------------------

def _make_tlhdig_tree(tmp_path, cth_dirs=None):
    """Create a mock TLHdig corpus directory with CTH subdirs and XML files.

    Returns (root_path, {cth_num: [xml_file_paths]}).
    """
    if cth_dirs is None:
        cth_dirs = {"100": ["kbo_001.xml"], "200": ["kbo_002.xml"]}

    created: dict[str, list] = {}
    for cth_num, files in cth_dirs.items():
        cth_dir = tmp_path / f"CTH {cth_num}_XML"
        cth_dir.mkdir()
        created[cth_num] = []
        for fname in files:
            xml_path = cth_dir / fname
            xml_path.write_text(
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
                f'  <teiHeader>\n'
                f'    <fileDesc>\n'
                f'      <titleStmt><title>CTH {cth_num} text</title></titleStmt>\n'
                f'    </fileDesc>\n'
                f'  </teiHeader>\n'
                f'  <text>\n'
                f'    <body>\n'
                f'      <ab>nu-uš-ma-aš LUGAL URUatti</ab>\n'
                f'      <ab>1 # nu-kán GIŠ BANŠUR</ab>\n'
                f'    </body>\n'
                f'  </text>\n'
                f'</TEI>\n'
            )
            created[cth_num].append(xml_path)
    return tmp_path, created


# ---------------------------------------------------------------------------
# Unit tests for helpers
# ---------------------------------------------------------------------------

class TestCthExtraction:
    def test_standard_name(self):
        assert _extract_cth_number("CTH 100_XML") == "100"

    def test_single_digit(self):
        assert _extract_cth_number("CTH 9_XML") == "9"

    def test_non_matching(self):
        assert _extract_cth_number("other_dir") == "other_dir"


class TestListCthDirs:
    def test_finds_cth_dirs(self, tmp_path):
        (tmp_path / "CTH 100_XML").mkdir()
        (tmp_path / "CTH 200_XML").mkdir()
        (tmp_path / "other_dir").mkdir()
        dirs = _list_cth_dirs(tmp_path)
        assert len(dirs) == 2
        assert all(d.name.startswith("CTH") for d in dirs)

    def test_bounded(self, tmp_path):
        for i in range(10):
            (tmp_path / f"CTH {i}_XML").mkdir()
        dirs = _list_cth_dirs(tmp_path, limit=3)
        assert len(dirs) == 3

    def test_nonexistent_dir(self, tmp_path):
        dirs = _list_cth_dirs(tmp_path / "nonexistent")
        assert dirs == []


class TestListXmlFiles:
    def test_finds_xml(self, tmp_path):
        (tmp_path / "a.xml").write_text("<root/>")
        (tmp_path / "b.txt").write_text("text")
        files = _list_xml_files(tmp_path)
        assert len(files) == 1
        assert files[0].name == "a.xml"

    def test_bounded(self, tmp_path):
        for i in range(5):
            (tmp_path / f"f{i}.xml").write_text("<root/>")
        files = _list_xml_files(tmp_path, limit=2)
        assert len(files) == 2


# ---------------------------------------------------------------------------
# Adapter integration tests
# ---------------------------------------------------------------------------

class TestHittiteTlhdigAdapter:
    def test_not_available_without_env(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        adapter = HittiteTlhdigAdapter()
        assert adapter.is_available() is False

    def test_not_available_with_nonexistent_path(self, monkeypatch):
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", "/nonexistent")
        adapter = HittiteTlhdigAdapter()
        assert adapter.is_available() is False

    def test_available_with_real_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        assert adapter.is_available() is True

    def test_search_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        adapter = HittiteTlhdigAdapter()
        result = adapter.search("LUGAL")
        assert result.status == "local_not_configured"
        assert "zenodo.org" in result.message

    def test_search_with_corpus(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path)
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.search("LUGAL")
        assert result.status == "ok"
        assert len(result.results) >= 1
        assert "CC-BY 4.0" in result.message

    def test_search_no_matches(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path)
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.search("NOMATCH")
        assert result.status == "ok"
        assert len(result.results) == 0

    def test_search_result_has_cth(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path)
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.search("LUGAL")
        assert result.results[0]["cth"] in ("100", "200")

    def test_get_text_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_text("100")
        assert result.status == "local_not_configured"

    def test_get_text_by_cth_number(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path, cth_dirs={"100": ["kbo_001.xml"]})
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_text("100")
        assert result.status == "ok"
        assert "TEI" in result.text
        assert result.metadata["cth_number"] == "100"

    def test_get_text_by_cth_label(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path, cth_dirs={"200": ["kbo_002.xml"]})
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_text("CTH 200")
        assert result.status == "ok"
        assert result.metadata["cth_number"] == "200"

    def test_get_text_path_traversal_blocked(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path)
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_text("../../etc/passwd")
        assert result.status == "not_found"

    def test_get_text_not_found(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path, cth_dirs={"100": ["kbo_001.xml"]})
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_text("999")
        assert result.status == "not_found"

    def test_get_metadata_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_metadata("100")
        assert result.status == "local_not_configured"

    def test_get_metadata_by_cth(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path, cth_dirs={"100": ["kbo_001.xml"]})
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.get_metadata("100")
        assert result.status == "ok"
        assert result.metadata["cth_number"] == "100"
        assert "xml_root_tag" in result.metadata

    def test_search_result_has_licence_warning(self, monkeypatch, tmp_path):
        _make_tlhdig_tree(tmp_path)
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        adapter = HittiteTlhdigAdapter()
        result = adapter.search("nu-kán")
        assert "CC-BY 4.0" in result.message
