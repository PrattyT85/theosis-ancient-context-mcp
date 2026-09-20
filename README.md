# theosis-ancient-context-mcp

FastMCP stdio service for ancient text corpora. Part of the [Theosis](https://github.com/PrattyT85) ancient-context integration.

## Corpora

| Corpus | Language(s) | Status | Licence |
|--------|------------|--------|---------|
| **TLA** (Thesaurus Linguae Aegyptiae) | Egyptian | Remote/status-only | Free non-commercial research |
| **Coptic SCRIPTORIUM** | Coptic | Local optional | CC-BY (exceptions exist) |
| **HPM/HDivT** (Hittite ritual texts) | Hittite | Remote/status-only | Academic |
| **CUC** (Copenhagen Ugaritic Corpus) | Ugaritic | Local optional | CC BY-NC 4.0 |
| **DASI** | Arabic epigraphic | Remote/status-only | Academic |
| **OCIANA** | Akkadian/Sumerian | Remote/status-only | Academic |
| **CDLI** | Akkadian/Sumerian/Elamite | Remote/status-only | Open access |
| **DPPC** | Phoenician/Punic | Deferred | Not published |
| **CIP** | Punic | Deferred | Not published |

## What's integrated vs. what's not

- **DPPC and CIP are NOT integrated** — no public API, data, or licence has been confirmed. They are registered as `deferred` with no scraper or adapter.
- **CUC is CC BY-NC and local-only** — commercial use is prohibited. The adapter only works when `CUC_CORPUS_DIR` is configured to point at a local checkout of the corpus.
- **TLA, HPM, DASI, OCIANA** are remote/status-only until a stable public API contract is verified. They return structured `remote_only` results with provenance envelopes.
- **CDLI** is status-only until the REST JSON API shape is confirmed from [cdli.earth/docs/api](https://cdli.earth/docs/api).
- **Coptic SCRIPTORIUM** requires a local corpus directory. The adapter supports `meta.json`-backed metadata and bounded text-file search.

## Tools

1. `list_corpora` — all registered corpus records with metadata
2. `get_corpus_status(corpus)` — detailed status, local path, availability
3. `search_corpus(corpus, query, limit)` — search with explicit status results
4. `get_text(corpus, reference)` — text retrieval with provenance envelope
5. `get_text_metadata(corpus, reference)` — metadata retrieval with provenance

## Setup

```bash
# Install
uv sync --extra dev

# Run tests
uv run pytest -v

# Compile check
uv run python -m compileall src/theosis_ancient_context -q

# Run the server (stdio)
uv run python -m theosis_ancient_context
```

### Optional local corpora

```bash
# Coptic SCRIPTORIUM
export COPTSCRIPTORIUM_CORPUS_DIR=/path/to/corpora

# Copenhagen Ugaritic Corpus
export CUC_CORPUS_DIR=/path/to/cuc
```

## Integration

All results include a provenance envelope with:
- `source_layer` — integration type (local_optional, remote_only, deferred, etc.)
- `corpus_id` — canonical corpus identifier
- `source_url` — upstream URL
- `licence` — licence summary
- `licence_warning` — detailed licence notes and restrictions
- `access_status` — current integration status

## Safety

- Path traversal prevention for all local file access
- Bounded search results and text retrieval
- No persistent cache
- No secrets required
- No network requests in v0.1.0 (all adapters are local or status-only)
