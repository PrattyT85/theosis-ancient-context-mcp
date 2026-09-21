"""Tests for the ancient-context healthcheck script.

All tests are CI-safe: network calls are mocked, local corpus paths are
controlled via tmp_path and monkeypatch. The script is imported as a module
so we can exercise individual check functions.
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure scripts/ is importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import healthcheck  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(data, status=200):
    """Create a mock urllib response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode("utf-8")
    resp.getcode.return_value = status
    resp.status = status
    return resp


def _mock_http_error(code, reason="Error"):
    url = "https://cdli.earth/test"
    fp = io.BytesIO(b"")
    return urllib.error.HTTPError(url, code, reason, {}, fp)


# ---------------------------------------------------------------------------
# Registry checks
# ---------------------------------------------------------------------------


class TestCheckRegistryLoads:
    def test_ok(self):
        result = healthcheck.check_registry_loads()
        assert result["status"] == "pass"
        assert "corpora" in result["detail"]


# ---------------------------------------------------------------------------
# Local corpus checks
# ---------------------------------------------------------------------------


class TestCheckCucLocal:
    def test_skip_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        result = healthcheck.check_cuc_local()
        assert result["status"] == "skip"

    def test_fail_when_not_dir(self, monkeypatch, tmp_path):
        bad_path = str(tmp_path / "nonexistent")
        monkeypatch.setenv("CUC_CORPUS_DIR", bad_path)
        result = healthcheck.check_cuc_local()
        assert result["status"] == "fail"
        assert "not accessible" in result["detail"]

    def test_pass_when_dir_exists(self, monkeypatch, tmp_path):
        cucumber = tmp_path / "cuc"
        cucumber.mkdir()
        # Create a text file so CUCAdapter.is_available() returns True
        (cucumber / "test.txt").write_text("sample")
        monkeypatch.setenv("CUC_CORPUS_DIR", str(cucumber))
        result = healthcheck.check_cuc_local()
        assert result["status"] == "pass"


class TestCheckTlhdigLocal:
    def test_skip_when_not_set(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        result = healthcheck.check_tlhdig_local()
        assert result["status"] == "skip"

    def test_fail_when_not_dir(self, monkeypatch, tmp_path):
        bad_path = str(tmp_path / "nonexistent")
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", bad_path)
        result = healthcheck.check_tlhdig_local()
        assert result["status"] == "fail"

    def test_pass_when_dir_exists(self, monkeypatch, tmp_path):
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        result = healthcheck.check_tlhdig_local()
        assert result["status"] == "pass"


class TestCheckCopticScriptoriumLocal:
    def test_skip_when_not_set(self, monkeypatch):
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        result = healthcheck.check_coptic_scriptorium_local()
        assert result["status"] == "skip"

    def test_fail_when_not_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv(
            "COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path / "nonexistent")
        )
        result = healthcheck.check_coptic_scriptorium_local()
        assert result["status"] == "fail"

    def test_pass_when_dir_exists(self, monkeypatch, tmp_path):
        monkeypatch.setenv("COPTSCRIPTORIUM_CORPUS_DIR", str(tmp_path))
        result = healthcheck.check_coptic_scriptorium_local()
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# CDLI instantiation check
# ---------------------------------------------------------------------------


class TestCheckCdliInstantiation:
    def test_ok(self):
        result = healthcheck.check_cdli_instantiation()
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# Local corpus sample checks
# ---------------------------------------------------------------------------


class TestCheckCucSample:
    def test_skip_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        result = healthcheck.check_cuc_sample()
        assert result["status"] == "skip"

    def test_pass_with_sample(self, monkeypatch, tmp_path):
        cucumber = tmp_path / "cuc"
        cucumber.mkdir()
        (cucumber / "ktu_001.txt").write_text("KTU 1.1 test text\n")
        monkeypatch.setenv("CUC_CORPUS_DIR", str(cucumber))
        result = healthcheck.check_cuc_sample()
        assert result["status"] == "pass"
        assert "match(es)" in result["detail"] or "result(s)" in result["detail"]


class TestCheckTlhdigSample:
    def test_skip_when_not_set(self, monkeypatch):
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        result = healthcheck.check_tlhdig_sample()
        assert result["status"] == "skip"

    def test_pass_with_sample(self, monkeypatch, tmp_path):
        # Create a minimal TLHdig-style tree
        cth_dir = tmp_path / "CTH 100_XML"
        cth_dir.mkdir()
        (cth_dir / "kbo_001.xml").write_text(
            '<?xml version="1.0"?>\n<TEI>\n  <text>LUGAL</text>\n</TEI>\n'
        )
        monkeypatch.setenv("HITTITE_TLHDIG_DIR", str(tmp_path))
        result = healthcheck.check_tlhdig_sample()
        assert result["status"] == "pass"
        assert "match(es)" in result["detail"]


# ---------------------------------------------------------------------------
# Live CDLI checks (mocked network)
# ---------------------------------------------------------------------------


class TestCheckCdliSearch:
    def test_pass(self):
        adapter = healthcheck.CDLIAdapter()
        sample = [{"id": 1, "designation": "Test", "museum_no": "M1"}]
        with patch("urllib.request.urlopen", return_value=_mock_response(sample)):
            result = healthcheck.check_cdli_search(adapter)
            assert result["status"] == "pass"
            assert "1 result(s)" in result["detail"]

    def test_fail_on_error_status(self):
        adapter = healthcheck.CDLIAdapter()
        with patch("urllib.request.urlopen", return_value=_mock_response({})):
            result = healthcheck.check_cdli_search(adapter)
            assert result["status"] == "fail"

    def test_fail_on_network_error(self):
        adapter = healthcheck.CDLIAdapter()
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            result = healthcheck.check_cdli_search(adapter)
            # Adapter catches OSError internally → returns network_error → healthcheck maps to fail
            assert result["status"] == "fail"
            assert "network_error" in result["detail"]


class TestCheckCdliMetadata:
    def test_pass(self):
        adapter = healthcheck.CDLIAdapter()
        sample = [{"id": 1, "designation": "Test", "languages": []}]
        with patch("urllib.request.urlopen", return_value=_mock_response(sample)):
            result = healthcheck.check_cdli_metadata(adapter)
            assert result["status"] == "pass"

    def test_fail_on_not_found(self):
        adapter = healthcheck.CDLIAdapter()
        with patch(
            "urllib.request.urlopen",
            side_effect=_mock_http_error(404, "Not Found"),
        ):
            result = healthcheck.check_cdli_metadata(adapter)
            assert result["status"] == "fail"


class TestCheckCdliAtf:
    def test_pass(self):
        adapter = healthcheck.CDLIAdapter()
        art = [{"id": 1, "inscription": {"id": 100, "artifact_id": 1}}]
        insc = [{"id": 100, "artifact_id": 1, "atf": "&P000001\n@tablet"}]
        with patch(
            "urllib.request.urlopen",
            side_effect=[_mock_response(art), _mock_response(insc)],
        ):
            result = healthcheck.check_cdli_atf(adapter)
            assert result["status"] == "pass"
            assert "has_text=True" in result["detail"]


# ---------------------------------------------------------------------------
# Remote URL probes
# ---------------------------------------------------------------------------


class TestPerseusProbe:
    def test_skip_by_default(self, monkeypatch):
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        result = healthcheck.check_perseus()
        assert result["status"] == "skip"

    def test_pass_with_probe(self, monkeypatch):
        monkeypatch.setenv("PERSEUS_PROBE", "1")
        with patch("urllib.request.urlopen") as mock:
            mock.return_value = MagicMock(getcode=MagicMock(return_value=200))
            result = healthcheck.check_perseus()
            assert result["status"] == "pass"

    def test_error_on_failure(self, monkeypatch):
        monkeypatch.setenv("PERSEUS_PROBE", "1")
        with patch("urllib.request.urlopen", side_effect=OSError("refused")):
            result = healthcheck.check_perseus()
            assert result["status"] == "error"


class TestOraccProbe:
    def test_skip_by_default(self, monkeypatch):
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        result = healthcheck.check_oracc()
        assert result["status"] == "skip"

    def test_pass_with_probe(self, monkeypatch):
        monkeypatch.setenv("ORACC_PROBE", "1")
        with patch("urllib.request.urlopen") as mock:
            mock.return_value = MagicMock(getcode=MagicMock(return_value=200))
            result = healthcheck.check_oracc()
            assert result["status"] == "pass"


class TestTheosisProbe:
    def test_skip_by_default(self, monkeypatch):
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        result = healthcheck.check_theosis()
        assert result["status"] == "skip"

    def test_pass_with_probe(self, monkeypatch):
        monkeypatch.setenv("THEOSIS_PROBE", "1")
        with patch("urllib.request.urlopen") as mock:
            mock.return_value = MagicMock(getcode=MagicMock(return_value=200))
            result = healthcheck.check_theosis()
            assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# Format and output tests
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_basic_format(self):
        results = [
            {"check": "a", "status": "pass", "detail": "ok"},
            {"check": "b", "status": "skip", "detail": "n/a"},
            {"check": "c", "status": "fail", "detail": "broken"},
            {"check": "d", "status": "error", "detail": "oops"},
        ]
        text = healthcheck.format_text(results, 12.3)
        assert "PASS" in text
        assert "SKIP" in text
        assert "FAIL" in text
        assert "ERROR" in text
        assert "1 passed" in text
        assert "1 skipped" in text
        assert "1 failed" in text
        assert "1 errors" in text


class TestMainOffline:
    def test_exits_zero(self, monkeypatch):
        monkeypatch.delenv("ANCIENT_CONTEXT_LIVE", raising=False)
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        with patch("sys.argv", ["healthcheck.py"]):
            rc = healthcheck.main()
        assert rc == 0

    def test_json_output(self, monkeypatch, capsys):
        monkeypatch.delenv("ANCIENT_CONTEXT_LIVE", raising=False)
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        with patch("sys.argv", ["healthcheck.py"]):
            healthcheck.main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "checks" in data
        assert "elapsed_ms" in data
        assert data["live_mode"] is False

    def test_text_output(self, monkeypatch, capsys):
        monkeypatch.delenv("ANCIENT_CONTEXT_LIVE", raising=False)
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        with patch("sys.argv", ["healthcheck.py", "--text"]):
            healthcheck.main()
        out = capsys.readouterr().out
        assert "Health Check" in out
        assert "passed" in out

    def test_live_flag(self, monkeypatch):
        monkeypatch.delenv("ANCIENT_CONTEXT_LIVE", raising=False)
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        # Mock all network calls for live checks
        with patch("urllib.request.urlopen", side_effect=OSError("mocked")), \
             patch("sys.argv", ["healthcheck.py", "--live"]):
            # Live mode + mocked network = CDLI checks will error, but
            # main should still exit (errors don't cause nonzero unless configured)
            # Actually errors DO cause nonzero. Let's test that.
            rc = healthcheck.main()
        # CDLI errors cause nonzero exit
        assert rc == 1

    def test_env_live_flag(self, monkeypatch):
        monkeypatch.setenv("ANCIENT_CONTEXT_LIVE", "1")
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        monkeypatch.delenv("PERSEUS_PROBE", raising=False)
        monkeypatch.delenv("ORACC_PROBE", raising=False)
        monkeypatch.delenv("THEOSIS_PROBE", raising=False)
        with patch("urllib.request.urlopen", side_effect=OSError("mocked")), \
             patch("sys.argv", ["healthcheck.py"]):
            rc = healthcheck.main()
        assert rc == 1  # CDLI live checks error


# ---------------------------------------------------------------------------
# Check result shape validation
# ---------------------------------------------------------------------------


class TestCheckResultShape:
    """Every check function must return a dict with check, status, detail."""

    ALL_CHECKS = [
        healthcheck.check_registry_loads,
        healthcheck.check_cdli_instantiation,
        healthcheck.check_cuc_local,
        healthcheck.check_tlhdig_local,
        healthcheck.check_coptic_scriptorium_local,
        healthcheck.check_cuc_sample,
        healthcheck.check_tlhdig_sample,
    ]

    def test_all_checks_have_required_keys(self, monkeypatch):
        monkeypatch.delenv("CUC_CORPUS_DIR", raising=False)
        monkeypatch.delenv("HITTITE_TLHDIG_DIR", raising=False)
        monkeypatch.delenv("COPTSCRIPTORIUM_CORPUS_DIR", raising=False)
        for fn in self.ALL_CHECKS:
            result = fn()
            assert "check" in result, f"{fn.__name__} missing 'check'"
            assert "status" in result, f"{fn.__name__} missing 'status'"
            assert "detail" in result, f"{fn.__name__} missing 'detail'"
            assert result["status"] in (
                "pass", "fail", "error", "skip"
            ), f"{fn.__name__} bad status: {result['status']}"
