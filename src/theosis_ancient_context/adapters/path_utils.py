"""Safe local-path utilities shared across adapters."""
from __future__ import annotations

import os
import re
from pathlib import Path


def safe_resolve(base: str, user_path: str) -> Path | None:
    """Resolve a user-supplied path under `base`, preventing traversal.

    Returns None if the resolved path escapes `base`.
    """
    base_resolved = Path(base).resolve()
    candidate = (base_resolved / user_path).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError:
        return None
    if not candidate.exists():
        return None
    return candidate


def list_text_files(directory: str, max_files: int = 500) -> list[Path]:
    """List .txt/.conllu/.xml/.json files in `directory`, bounded."""
    base = Path(directory)
    if not base.is_dir():
        return []
    results: list[Path] = []
    try:
        for entry in sorted(base.iterdir()):
            if entry.is_file() and entry.suffix.lower() in {".txt", ".conllu", ".xml", ".json", ".rels"}:
                results.append(entry)
                if len(results) >= max_files:
                    break
    except (PermissionError, OSError):
        pass
    return results


def read_bounded(path: Path, max_bytes: int = 100_000) -> str:
    """Read a file with a byte limit."""
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return f"[File too large: {size} bytes. Showing first {max_bytes} bytes.]\n" + path.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        return path.read_text(encoding="utf-8", errors="replace")
    except (PermissionError, OSError) as exc:
        return f"[Error reading {path}: {exc}]"
