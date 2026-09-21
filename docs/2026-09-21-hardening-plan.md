# Ancient Context Hardening Plan

**Goal:** Make the ancient-context service reliable for recurring research use by improving CDLI filtering, source/version provenance, routing guidance, and read-only health checks.

## Tasks

1. **CDLI filtering**
   - Validate/filter returned language metadata instead of trusting CDLI query syntax.
   - Preserve the raw query and report when upstream results do not match the requested language.
   - Add mocked and live regression tests.

2. **Source/version manifest**
   - Add a machine-readable manifest for CUC, TLHdig, CDLI, TLA, Coptic SCRIPTORIUM, HPM/HDivT, DASI, OCIANA, DPPC, and CIP.
   - Record repository/Zenodo identifiers, local paths, licences, retrieval dates, hashes where available, and access status.
   - Expose manifest/status through the MCP service and document local-only restrictions.

3. **Research-routing guidance**
   - Add a source-layer guide describing when to use each corpus and how to distinguish primary texts, epigraphy, translations, later interpretation, and scholarly synthesis.
   - Include explicit warnings that ORACC is not a Ugaritic corpus and that CUC is CC BY-NC.

4. **Read-only health checks**
   - Add a bounded health-check script for MCP handshake, local CUC/TLHdig status/sample retrieval, CDLI search/metadata/ATF, Perseus discovery, ORACC archive access, and the three Theosis HTTP services.
   - Keep live checks opt-in and non-mutating; add offline tests with mocked endpoints.
   - Provide a cron-ready command and failure-only output. Do not install a recurring cron job until the script passes locally and CI.

5. **Selective Coptic readiness**
   - Do not clone the 2.8GB repository wholesale. Add release metadata and a documented subset-selection procedure; integrate a small corpus only after per-file licence review and a concrete study need.

## Gates

- All offline tests pass.
- All enabled live probes pass or produce an explicit, documented upstream-unavailable result.
- CI is green.
- The Hermes profile still exposes the five ancient-context tools and existing MCP servers remain unchanged.
- No restricted or CC BY-NC corpus is published or bundled.
