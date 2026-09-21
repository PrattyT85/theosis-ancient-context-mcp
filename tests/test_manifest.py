"""Tests for the source manifest and routing guidance."""
import json

from theosis_ancient_context.models import AccessStatus, SourceType
from theosis_ancient_context.registry import (
    get_corpus,
    get_source_manifest,
    load_sources_manifest,
    SOURCES_JSON_PATH,
)


REQUIRED_MANIFEST_FIELDS = [
    "corpus_id",
    "name",
    "source_url",
    "source_type",
    "language",
    "period",
    "access_status",
    "licence",
    "licence_notes",
    "local_path_env_var",
    "version_or_commit",
    "doi",
    "last_reviewed",
    "next_review",
    "integration_notes",
]

REQUIRED_CORPORA = [
    "tla",
    "coptic_scriptorium",
    "hpm_hdivt",
    "tlhdig",
    "cuc",
    "dasi",
    "ociana",
    "cdli",
    "dppc",
    "cip",
]


class TestSourcesJsonManifest:
    """sources.json must exist and be well-formed."""

    def test_sources_json_exists(self):
        assert SOURCES_JSON_PATH.exists(), f"sources.json not found at {SOURCES_JSON_PATH}"

    def test_sources_json_is_valid_json(self):
        data = load_sources_manifest()
        assert isinstance(data, list)

    def test_ten_entries_in_manifest(self):
        data = load_sources_manifest()
        assert len(data) == 10, f"Expected 10 manifest entries, got {len(data)}"

    def test_all_required_corpora_in_manifest(self):
        data = load_sources_manifest()
        ids = {e["corpus_id"] for e in data}
        for cid in REQUIRED_CORPORA:
            assert cid in ids, f"Missing corpus in manifest: {cid}"

    def test_all_entries_have_required_fields(self):
        data = load_sources_manifest()
        for entry in data:
            for field in REQUIRED_MANIFEST_FIELDS:
                assert field in entry, f"Entry {entry.get('corpus_id', '?')} missing field: {field}"

    def test_manifest_entry_types(self):
        data = load_sources_manifest()
        for entry in data:
            assert isinstance(entry["language"], list), (
                f"{entry['corpus_id']}: language must be a list"
            )
            assert isinstance(entry["licence"], str)
            assert isinstance(entry["licence_notes"], str)
            # source_type and access_status must be valid enums
            SourceType(entry["source_type"])
            AccessStatus(entry["access_status"])

    def test_local_optional_corpora_have_env_var(self):
        data = load_sources_manifest()
        for entry in data:
            if entry["source_type"] == "local_optional":
                assert entry["local_path_env_var"] is not None, (
                    f"{entry['corpus_id']}: local_optional must have local_path_env_var"
                )

    def test_deferred_corpora_are_deferred(self):
        data = load_sources_manifest()
        for entry in data:
            if entry["corpus_id"] in ("dppc", "cip"):
                assert entry["source_type"] == "deferred"
                assert entry["access_status"] == "deferred"

    def test_cuc_is_cc_by_nc(self):
        data = load_sources_manifest()
        cuc = next(e for e in data if e["corpus_id"] == "cuc")
        assert "CC BY-NC" in cuc["licence"]
        assert "ORACC" in cuc["licence_notes"] or "ORACC" in cuc.get("integration_notes", "")

    def test_tlhdig_has_doi(self):
        data = load_sources_manifest()
        tlhdig = next(e for e in data if e["corpus_id"] == "tlhdig")
        assert tlhdig["doi"] == "10.5281/zenodo.15459134"
        assert tlhdig["local_path_env_var"] == "HITTITE_TLHDIG_DIR"

    def test_review_dates_are_strings(self):
        data = load_sources_manifest()
        for entry in data:
            assert isinstance(entry["last_reviewed"], str)
            assert isinstance(entry["next_review"], str)
            assert len(entry["last_reviewed"]) == 10  # YYYY-MM-DD


class TestGetSourceManifestTool:
    """The get_source_manifest function merges manifest + registry + live env."""

    def test_returns_list_of_dicts(self):
        result = get_source_manifest()
        assert isinstance(result, list)
        assert len(result) == 10

    def test_each_entry_has_local_path_fields(self):
        result = get_source_manifest()
        for entry in result:
            assert "local_path_configured" in entry
            assert "local_path_exists" in entry
            assert "local_path_value" in entry

    def test_source_type_from_registry(self):
        """source_type should match the registry, not just the JSON."""
        result = get_source_manifest()
        for entry in result:
            rec = get_corpus(entry["corpus_id"])
            if rec:
                assert entry["source_type"] == rec.source_type.value

    def test_manifest_entries_have_all_required_fields(self):
        result = get_source_manifest()
        for entry in result:
            for field in REQUIRED_MANIFEST_FIELDS:
                assert field in entry, f"Entry {entry.get('corpus_id', '?')} missing: {field}"

    def test_no_local_path_when_not_configured(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        result = get_source_manifest()
        for entry in result:
            if entry["source_type"] == "local_optional":
                assert entry["local_path_configured"] is False


class TestRoutingGuidanceInREADME:
    """README must document source-layer routing."""

    def test_readme_exists(self):
        from pathlib import Path
        readme = Path(SOURCES_JSON_PATH).parent / "README.md"
        assert readme.exists()

    def test_oracc_warning_in_readme(self):
        from pathlib import Path
        readme = Path(SOURCES_JSON_PATH).parent / "README.md"
        content = readme.read_text()
        assert "ORACC" in content
        assert "NOT" in content.upper() or "not" in content

    def test_cuc_cc_by_nc_warning_in_readme(self):
        from pathlib import Path
        readme = Path(SOURCES_JSON_PATH).parent / "README.md"
        content = readme.read_text()
        assert "CC BY-NC" in content

    def test_routing_table_in_readme(self):
        from pathlib import Path
        readme = Path(SOURCES_JSON_PATH).parent / "README.md"
        content = readme.read_text()
        # Should mention routing guidance section
        assert "routing" in content.lower()
        # Should mention key source-layer domains
        for domain in ["Egyptian", "Hittite", "Ugaritic", "Coptic", "Phoenician"]:
            assert domain in content, f"README missing routing mention for {domain}"

    def test_dppc_cip_deferred_in_readme(self):
        from pathlib import Path
        readme = Path(SOURCES_JSON_PATH).parent / "README.md"
        content = readme.read_text()
        assert "DPPC" in content
        assert "CIP" in content
        assert "Deferred" in content or "deferred" in content
