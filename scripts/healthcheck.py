#!/usr/bin/env python3
"""Ancient context health-check script.

Offline/default mode (CI-safe): no network requests. Checks:
  - CUC local status if CUC_CORPUS_DIR is set
  - TLHdig local status if HITTITE_TLHDIG_DIR is set
  - CDLI adapter instantiation and validation helpers
  - Registry loads correctly

Live mode (--live or ANCIENT_CONTEXT_LIVE=1): additionally runs bounded
read-only CDLI adapter calls (search, metadata, ATF) and optional
Perseus/ORACC/Theosis URL probes when their env vars are set.

Output: compact JSON (default) or text (--text). Exit nonzero only on
configured check failure.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure the package is importable when run from any working directory.
# Only add src/ if the package isn't already installed (e.g. not in a venv).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
try:
    import theosis_ancient_context  # noqa: F401 — already importable
except ImportError:
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))

from theosis_ancient_context.adapters.cdli import (
    CDLIAdapter,
    _validate_id,
    _validate_query,
)
from theosis_ancient_context.adapters.cuc import CUCAdapter
from theosis_ancient_context.adapters.tlhdig import HittiteTlhdigAdapter
from theosis_ancient_context.registry import REGISTRY, corpus_status, list_corpora

# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

CheckResult = dict[str, Any]


def _ok(name: str, detail: str = "", **extra: Any) -> CheckResult:
    r: CheckResult = {"check": name, "status": "pass", "detail": detail}
    r.update(extra)
    return r


def _fail(name: str, detail: str = "", **extra: Any) -> CheckResult:
    r: CheckResult = {"check": name, "status": "fail", "detail": detail}
    r.update(extra)
    return r


def _error(name: str, detail: str = "", **extra: Any) -> CheckResult:
    r: CheckResult = {"check": name, "status": "error", "detail": detail}
    r.update(extra)
    return r


def _skip(name: str, detail: str = "", **extra: Any) -> CheckResult:
    r: CheckResult = {"check": name, "status": "skip", "detail": detail}
    r.update(extra)
    return r


# ---------------------------------------------------------------------------
# Offline checks (CI-safe, no network)
# ---------------------------------------------------------------------------


def check_registry_loads() -> CheckResult:
    """Verify the static registry has the expected number of entries."""
    try:
        corpora = list_corpora()
        count = len(corpora)
        ids = sorted(corpora, key=lambda c: c.corpus_id)
        ids_str = ", ".join(c.corpus_id for c in ids)
        if count < 8:
            return _fail("registry_loads", f"Expected >=8 corpora, got {count}")
        return _ok("registry_loads", f"{count} corpora: {ids_str}")
    except Exception as exc:
        return _error("registry_loads", str(exc))


def check_cuc_local() -> CheckResult:
    """Check CUC local corpus availability."""
    cucumber = os.environ.get("CUC_CORPUS_DIR")
    if not cucumber:
        return _skip("cuc_local", "CUC_CORPUS_DIR not set")

    adapter = CUCAdapter()
    if not adapter.is_available():
        return _fail("cuc_local", f"CUC_CORPUS_DIR={cucumber} but directory not accessible")

    status_info = corpus_status("cuc")
    file_count = status_info.get("local_file_count", "unknown")
    return _ok("cuc_local", f"CUC accessible, ~{file_count} entries", path=cucumber)


def check_tlhdig_local() -> CheckResult:
    """Check TLHdig local corpus availability."""
    tlhdig_dir = os.environ.get("HITTITE_TLHDIG_DIR")
    if not tlhdig_dir:
        return _skip("tlhdig_local", "HITTITE_TLHDIG_DIR not set")

    adapter = HittiteTlhdigAdapter()
    if not adapter.is_available():
        return _fail(
            "tlhdig_local",
            f"HITTITE_TLHDIG_DIR={tlhdig_dir} but directory not accessible",
        )

    status_info = corpus_status("tlhdig")
    file_count = status_info.get("local_file_count", "unknown")
    return _ok("tlhdig_local", f"TLHdig accessible, ~{file_count} entries", path=tlhdig_dir)


def check_cdli_instantiation() -> CheckResult:
    """Verify CDLI adapter can be instantiated and validation helpers work."""
    try:
        adapter = CDLIAdapter()
        assert adapter.is_available()
        # Validate helpers
        assert _validate_query("tablet") == "tablet"
        assert _validate_query("") is None
        assert _validate_id("1") == 1
        assert _validate_id("P000001") == 1
        assert _validate_id("abc") is None
        return _ok("cdli_instantiation", "CDLI adapter and validation OK")
    except Exception as exc:
        return _error("cdli_instantiation", str(exc))


def check_coptic_scriptorium_local() -> CheckResult:
    """Check Coptic SCRIPTORIUM local corpus availability."""
    cs_dir = os.environ.get("COPTSCRIPTORIUM_CORPUS_DIR")
    if not cs_dir:
        return _skip("coptic_scriptorium_local", "COPTSCRIPTORIUM_CORPUS_DIR not set")

    if not os.path.isdir(cs_dir):
        return _fail(
            "coptic_scriptorium_local",
            f"COPTSCRIPTORIUM_CORPUS_DIR={cs_dir} but not a directory",
        )

    return _ok("coptic_scriptorium_local", f"Corpus dir accessible", path=cs_dir)


# ---------------------------------------------------------------------------
# Live-only checks (require --live or ANCIENT_CONTEXT_LIVE=1)
# ---------------------------------------------------------------------------


def check_cdli_search(adapter: CDLIAdapter) -> CheckResult:
    """Test CDLI search with a simple query."""
    try:
        result = adapter.search("clay tablet", limit=3)
        if result.status == "ok":
            return _ok(
                "cdli_search",
                f"Found {len(result.results)} result(s)",
                sample=result.results[0] if result.results else None,
            )
        return _fail("cdli_search", f"status={result.status}: {result.message}")
    except Exception as exc:
        return _error("cdli_search", str(exc))


def check_cdli_metadata(adapter: CDLIAdapter) -> CheckResult:
    """Test CDLI metadata for artifact P000001."""
    try:
        result = adapter.get_metadata("P000001")
        if result.status == "ok":
            return _ok("cdli_metadata", f"Metadata retrieved for P000001")
        return _fail("cdli_metadata", f"status={result.status}: {result.message}")
    except Exception as exc:
        return _error("cdli_metadata", str(exc))


def check_cdli_atf(adapter: CDLIAdapter) -> CheckResult:
    """Test CDLI ATF text retrieval for P000001."""
    try:
        result = adapter.get_text("P000001")
        if result.status == "ok":
            has_text = bool(result.text.strip())
            atf_preview = result.text[:120] if has_text else "(empty)"
            return _ok(
                "cdli_atf",
                f"ATF retrieved: {len(result.text)} chars, has_text={has_text}",
                atf_preview=atf_preview,
            )
        return _fail("cdli_atf", f"status={result.status}: {result.message}")
    except Exception as exc:
        return _error("cdli_atf", str(exc))


def check_perseus() -> CheckResult:
    """Probe Perseus Digital Library (only when PERSEUS_PROBE=1)."""
    import urllib.request
    import urllib.error

    if os.environ.get("PERSEUS_PROBE") != "1":
        return _skip("perseus_probe", "PERSEUS_PROBE != 1, skipping")

    url = "https://www.perseus.tufts.edu/hopper/"
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        code = resp.getcode()
        return _ok("perseus_probe", f"HTTP {code}", url=url)
    except Exception as exc:
        return _error("perseus_probe", str(exc), url=url)


def check_oracc() -> CheckResult:
    """Probe ORACC (only when ORACC_PROBE=1)."""
    import urllib.request
    import urllib.error

    if os.environ.get("ORACC_PROBE") != "1":
        return _skip("oracc_probe", "ORACC_PROBE != 1, skipping")

    url = "http://build-oracc.museum.upenn.edu/json/"
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        code = resp.getcode()
        return _ok("oracc_probe", f"HTTP {code}", url=url)
    except Exception as exc:
        return _error("oracc_probe", str(exc), url=url)


def check_theosis() -> CheckResult:
    """Probe Theosis GitHub repo (only when THEOSIS_PROBE=1)."""
    import urllib.request
    import urllib.error

    if os.environ.get("THEOSIS_PROBE") != "1":
        return _skip("theosis_probe", "THEOSIS_PROBE != 1, skipping")

    url = "https://github.com/PrattyT85"
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        code = resp.getcode()
        return _ok("theosis_probe", f"HTTP {code}", url=url)
    except Exception as exc:
        return _error("theosis_probe", str(exc), url=url)


# ---------------------------------------------------------------------------
# Offline sample checks (local corpus read sample)
# ---------------------------------------------------------------------------


def check_cuc_sample() -> CheckResult:
    """Read a bounded sample from CUC if available."""
    cucumber = os.environ.get("CUC_CORPUS_DIR")
    if not cucumber:
        return _skip("cuc_sample", "CUC_CORPUS_DIR not set")

    adapter = CUCAdapter()
    if not adapter.is_available():
        return _skip("cuc_sample", "CUC not accessible")

    try:
        result = adapter.search("ktu", limit=2)
        if result.status == "ok":
            return _ok(
                "cuc_sample",
                f"Sample search returned {len(result.results)} result(s)",
            )
        return _skip("cuc_sample", f"Sample search: {result.status}")
    except Exception as exc:
        return _error("cuc_sample", str(exc))


def check_tlhdig_sample() -> CheckResult:
    """Read a bounded sample from TLHdig if available."""
    tlhdig_dir = os.environ.get("HITTITE_TLHDIG_DIR")
    if not tlhdig_dir:
        return _skip("tlhdig_sample", "HITTITE_TLHDIG_DIR not set")

    adapter = HittiteTlhdigAdapter()
    if not adapter.is_available():
        return _skip("tlhdig_sample", "TLHdig not accessible")

    try:
        result = adapter.search("LUGAL", limit=2)
        if result.status == "ok":
            return _ok(
                "tlhdig_sample",
                f"Sample search returned {len(result.results)} match(es)",
            )
        return _skip("tlhdig_sample", f"Sample search: {result.status}")
    except Exception as exc:
        return _error("tlhdig_sample", str(exc))


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def run_offline_checks() -> list[CheckResult]:
    """Run all CI-safe offline checks."""
    results: list[CheckResult] = []
    results.append(check_registry_loads())
    results.append(check_cuc_local())
    results.append(check_tlhdig_local())
    results.append(check_coptic_scriptorium_local())
    results.append(check_cdli_instantiation())
    return results


def run_live_checks() -> list[CheckResult]:
    """Run network-dependent live checks (bounded read-only)."""
    results: list[CheckResult] = []
    adapter = CDLIAdapter(timeout=15)
    results.append(check_cdli_search(adapter))
    results.append(check_cdli_metadata(adapter))
    results.append(check_cdli_atf(adapter))
    # Remote URL probes — only when explicitly enabled
    results.append(check_perseus())
    results.append(check_oracc())
    results.append(check_theosis())
    return results


def run_sample_checks() -> list[CheckResult]:
    """Run bounded local corpus samples (CI-safe but reads local files)."""
    results: list[CheckResult] = []
    results.append(check_cuc_sample())
    results.append(check_tlhdig_sample())
    return results


def format_text(results: list[CheckResult], elapsed_ms: float) -> str:
    """Format results as human-readable text."""
    lines: list[str] = []
    lines.append(f"Ancient Context Health Check ({elapsed_ms:.0f}ms)")
    lines.append("=" * 50)
    for r in results:
        tag = r["status"].upper()
        lines.append(f"  [{tag}] {r['check']}: {r.get('detail', '')}")
    passed = sum(1 for r in results if r["status"] == "pass")
    skipped = sum(1 for r in results if r["status"] == "skip")
    failed = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")
    lines.append("-" * 50)
    lines.append(
        f"  {passed} passed, {skipped} skipped, {failed} failed, {errors} errors"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ancient Context health check (CI-safe offline by default)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Enable live network checks (CDLI adapter, optional probes)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        default=False,
        help="Output human-readable text instead of JSON",
    )
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        default=False,
        help="Treat skip results as failures (exit nonzero)",
    )
    args = parser.parse_args()

    live = args.live or os.environ.get("ANCIENT_CONTEXT_LIVE") == "1"

    t0 = time.monotonic()
    results: list[CheckResult] = []

    # Always-run offline checks
    results.extend(run_offline_checks())

    # Local corpus samples (CI-safe, reads local files only)
    results.extend(run_sample_checks())

    # Live network checks
    if live:
        results.extend(run_live_checks())

    elapsed_ms = (time.monotonic() - t0) * 1000

    if args.text:
        print(format_text(results, elapsed_ms))
    else:
        output = {
            "elapsed_ms": round(elapsed_ms, 1),
            "live_mode": live,
            "checks": results,
        }
        print(json.dumps(output, indent=2, default=str))

    # Exit nonzero only on actual failures or errors
    has_failure = any(r["status"] in ("fail", "error") for r in results)
    has_skip_fail = args.fail_on_skip and any(r["status"] == "skip" for r in results)

    return 1 if (has_failure or has_skip_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
