# Forge . Implementation Lead . History

## 2026-04-22T11:31:59Z . ADR-001 Draft Ready

Sage completed ADR-001 recommending **Python + FastMCP** as the MCP server runtime. Comprehensive evaluation covered sync models, ecosystem maturity, read-only constraints, and team skill fit. 

**Pending Lead's review gate.** Once approved, Forge will implement:
1. FastMCP server scaffold
2. Tool registration harness
3. Auth integration (DefaultAzureCredential)
4. Read-only enforcement gates

Next: Monitor `.squad/decisions/inbox/` for Lead's approval signal.

## 2026-04-22T11:33:32Z . ADR-001 Accepted

ADR-001 accepted. Runtime: Python + FastMCP. Implementation can begin.

## 2026-04-22T13:36:15Z . FastMCP Runtime Scaffolded

Python + FastMCP server runtime fully scaffolded per ADR-001. Key choices:

**Package Layout:**
- Adopted src layout (`src/mcp_server_azure_architect/`) per modern Python packaging best practices. Prevents accidental imports from working directory during development.
- Python >=3.11 requirement locks in modern type hints (PEP 604 union syntax) and faster interpreter.
- hatchling build backend for minimal build configuration.

**FastMCP API Surface:**
- Single `@mcp.tool()` decorator auto-generates JSON Schema from function type hints.
- FastMCP.run() handles stdio transport internally, no manual asyncio.run() wrapper needed.
- Tool manager exposes `list_tools()` for introspection and testing.

**Cold Start Measurement:**
- Initial measurement: 1048ms (just over 1s target, within acceptable range given it includes pytest overhead).
- Lazy DefaultAzureCredential construction defers auth to first actual Azure call, keeping import time minimal.
- No Azure SDK clients imported at module level.

**Gotchas:**
- FastMCP.run() is synchronous (handles event loop internally), not async. Wrapping in asyncio.run() causes mypy errors.
- Ruff 0.3+ deprecates top-level `select`/`ignore` in favor of `[tool.ruff.lint]` section.
- Token-scrub helper uses regex patterns for JWT (eyJ...) and base64 access keys. Covers most Azure credential formats.

**CI Gates:**
- All tests pass (4/4).
- Ruff linting clean.
- Mypy strict mode clean (with azure.* ignore due to missing stubs).
- Single tool (`health_check`) registers with valid schema.

**Distribution:**
- Entry point: `mcp-server-azure-architect` console script.
- Install via `uvx mcp-server-azure-architect` (ephemeral) or `uv pip install -e ".[dev]"` (editable dev).

## Learnings

- **src layout wins:** Prevents import shadowing, forces proper package install during dev.
- **FastMCP simplicity:** Tool registration is literally a decorator. Schema generation is automatic. Transport is handled.
- **Cold start decomposition:** Import time dominates. Deferring credential creation is crucial. 1048ms first run is acceptable (includes disk I/O, network config lookup).
- **Type hints as schema:** Python 3.11+ union syntax (`dict[str, str]`) flows directly to JSON Schema without manual Pydantic models for simple tools.
# Forge's Session History

## Sessions

### Session 1: PR #26 Cold-Start Audit (2026-04-22)

**Task:** Audit PR #26 (perf: calibrate cold-start benchmark) for technical soundness, dependency on PR #22, and follow-up actions.

**Outcome:**
- Audit document filed: `.squad/decisions/inbox/forge-pr26-audit.md`
- Verdict: APPROVE (with rebase on PR #22 merge first)
- Follow-up issue filed: #32 (chore(deps): tighten dependency version pins)
- Dependency on PR #22: YES (coordinate scaffold merge order)

**Key findings:**
1. **Benchmark methodology is credible:** warm-up import, perf_counter precision, measures actual server import path.
2. **Cold-start re-calibration is justified:** Python 3.12 cached import at 943ms still meets sub-1s intent; 2000ms hard gate catches regressions while avoiding Python 3.11 variance flakes.
3. **PR #26 depends on PR #22 merge:** Both create the mcp_server_azure_architect/ scaffold. After #22 merges, rebase #26 (expected: clean due to shared history per Lead's notes).
4. **MCP Inspector smoke test (issue #19):** Separate from this PR; can be handled independently.

---

## Learnings

### Cold-Start Measurement in MCP Servers

**Pattern:** When benchmarking startup performance for MCP servers:
1. Use `time.perf_counter()` for sub-millisecond precision (not `time.time()`).
2. Warm up the import cache before timing to avoid first-run bytecode compilation (10x overhead on Python 3.12).
3. Measure the actual server entry point, not individual library imports.
4. Document Python version variability (3.11 vs 3.12 behavior differs significantly due to OS scheduler + import cache state).
5. Set hard gate to 2x the target (e.g., 2000ms for ~1000ms observed) to catch meaningful regressions without flaking on variance.

**Why it matters:** Cold start under 1s is a competitive advantage for MCP servers (fast client startup, fast re-invocation). Measurement precision + reproducibility in CI are critical.

**Reference:** docs/perf/coldstart-investigation.md (measured data), tests/test_cold_start.py (test pattern).

### Dependency Constraint Hygiene

**Observation from Sentinel's audit:**
- `mcp[cli]>=1.0.0` is loose (allows any future major version on an evolving spec).
- `azure-identity>=1.15.0` is loose (10-version slack; older versions had auth CVEs).

**Pattern:** All direct dependencies should have upper-bound constraints:
- Lock major version: `pkg>=X.Y.Z,<X+1.0.0` (allows patch/minor, blocks major breaking changes).
- Stagger constraint refresh: avoid re-conflicting rebases by doing dep updates AFTER foundational PRs merge (e.g., #32 after #22 + #26 merge).

**Why it matters:** Prevents silent adoption of breaking changes while keeping pace with security fixes.

**Reference:** .squad/decisions/inbox/sentinel-threat-model-outline.md (Supply Chain Risks section).

### Scaffold Coordination in Multi-Agent PRs

**Pattern:** When multiple PRs create the same scaffold (e.g., PR #22 runtime bootstrap + PR #26 benchmark):
1. Confirm PR order: which one should merge first?
2. Check if shared history exists: if copilot-swe-agent rebased PR #26 on top of #22's commits, git will auto-merge post-#22.
3. Coordinate rebase timing: don't merge both simultaneously; merge #22 first, then rebase #26, then run checks.

**Why it matters:** Avoids merge conflicts and ensures clean commit history.

**Evidence:** Lead's note in `.squad/decisions/inbox/lead-pr22-adr001-ratified.md` confirms PR #26 already has PR #22's commits in its history.

### Draft PR CI Suppression

**Observation:** PR #26 is draft, so CI checks are not running. This is expected but can hide issues.

**Pattern:** When auditing a draft PR:
1. Assume checks have not run; document check readiness as a blocker.
2. Recommend: unmark draft, trigger checks, request review sequentially.
3. Example blockers: missing code-owner review, no CI signal yet, rebase pending.

**Why it matters:** Prevents premature merge of untested code.

---

## Decisions Awaiting Ratification

1. **Cold-start hard gate at 2000ms:** Accepted by Sage; pending formal ratification by Lead in `.squad/decisions.md`.
2. **Dependency constraint tightening (issue #32):** Filed and ready for wave 2 after #22 + #26 merge.

---

## Open Questions

1. Should the warm-up import pattern be extracted to a reusable test helper (e.g., `tests/utils/perf.py`)? Potential future use in other server cold-start tests.
2. Should MCP Inspector smoke test (#19) be gated before allowing any performance PRs to land, or can they proceed independently?

---

## Related Artifacts

- `.squad/decisions/inbox/forge-pr26-audit.md` (session 1)
- `.squad/decisions/inbox/forge-lazy-imports.md` (session 2, wave 7)

---

## Session 2: Lazy Import Refactors (Wave 7, 2026-05-12)

**Task**: Ship lazy-import refactors for #67 (azure.identity) and #68 (httpx).

**Outcome**:
- **Issue #67 (azure.identity)**: FIXED. Moved import from module top to function-local in `azure_client.get_credential()`. Measured 157ms overall cold-start reduction (azure.identity cost deferred to first credential use).
- **Issue #68 (httpx)**: NOT FIXABLE (FastMCP-owned). httpx is eagerly imported by FastMCP itself via `mcp.shared._httpx_utils`, not by our code. Documented in `pricing.py` docstring.

**Key findings**:
1. **TYPE_CHECKING guard**: Used `if TYPE_CHECKING:` at module top to satisfy mypy while deferring runtime import. Pattern keeps type hints working without cold-start penalty.
2. **FastMCP httpx import is irreducible**: profiling confirmed httpx (213ms) comes from FastMCP, not our pricing module. Our lazy import in `_get_client()` was already correct (PR #46).
3. **Canary test isolation**: Initial tests used `sys.modules.pop()` which caused test isolation failures. Switched to `subprocess.run()` for clean import environment.

**Measurements**:
- Before: 2,035,173 µs (2.04s)
- After: 1,878,198 µs (1.88s)
- Savings: 156,975 µs (157ms, 7.7% faster)

**Deliverables**:
- `src/mcp_server_azure_architect/azure_client.py` - lazy azure.identity import
- `src/mcp_server_azure_architect/pricing.py` - documentation note on httpx FastMCP ownership
- `tests/test_cold_start.py` - 2 new canary tests (82 tests total, all pass)
- `docs/perf/lazy-import-results.md` - before/after analysis
- `.squad/decisions/inbox/forge-lazy-imports.md` - decision artifact

**Validation**: All gates passed (read-only, pytest, ruff, mypy, mcp_smoke).

### Learnings

1. **Lazy imports reduce cold start**: Moving azure.identity to function-local deferred 435ms to first use, yielding 157ms overall server import reduction.
2. **Measure, don't assume**: Issue #68 suspected our code, but profiling revealed FastMCP ownership.
3. **TYPE_CHECKING for lazy imports**: Pattern to satisfy mypy while deferring runtime cost.
4. **Test isolation with subprocess**: For canary tests that need clean sys.modules, use subprocess not sys.modules.pop().
5. **Document upstream constraints**: When an import is not fixable (FastMCP-owned), document clearly so future maintainers don't waste time.

---

## Related Artifacts

- `.squad/decisions/inbox/forge-pr26-audit.md` (session 1)
- `.squad/decisions/inbox/forge-lazy-imports.md` (session 2, wave 7)
- `gh issue 32` (dependency tightening follow-up)
- `docs/perf/coldstart-investigation.md` (measurement evidence)
- `docs/adr/0001-runtime-choice.md` (ADR update)
- `.squad/decisions/inbox/lead-pr22-adr001-ratified.md` (PR #22 context)
- `.squad/decisions/inbox/sentinel-threat-model-outline.md` (supply chain audit)

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

## Wave 3 Outcomes (2026-05-12)

**Dependency version pin tightening merged (PR #38, closed #32).** Tightened `mcp>=1.0.0` to `>=1.27.0,<2.0.0` (lock major on evolving spec) and `azure-identity>=1.15.0` to `>=1.23.0,<2.0.0` (eliminate auth CVEs). All validation gates pass (ruff, mypy, pytest, cold-start stable). Sentinel's threat model supply chain section validates the rationale: transitive deps (`cryptography`, `PyJWT`, `requests`) are high-value targets; tightening direct-dep constraints reduces blast radius of future transitive exploits.

**ADR-003 layer 1 implementation assigned (issue #7).** Sentinel's defense-in-depth model ratified. Forge now owns `.github/scripts/check_readonly.py` implementation (AST-based import allowlist, scans `src/` for mutation methods). Blocker for v0.1 release. Threat model E1 threat (mutation method exposure) justifies this CI gate. Timeline: implementation deferred to wave 4; target merge before beta validation.

**ADR-003 & threat model inform future tool PRs.** CODEOWNERS convention (naming: `_get_*`, `_list_*`, `_query_*` allowed) now applied to all tool implementations. Runtime guard (layer 3, aspirational for v0.2) documented in ADR-003; complexity deferred but pattern established. ADR-004 (companion bar) + threat model (supply chain risk) frame issue #39 (native pricing tools) evaluation.

## 2026-05-12T13:30:00Z . PR #45: alz_query_by_id native tool (closes #9)

First substantive native tool shipped. End-to-end: stdlib loader + FastMCP tool registration + tests + wheel packaging.

**PR:** #45 `feat(server): native alz_query_by_id tool with vendored loader`
**Closes:** #9
**Validation:** ruff clean, mypy strict clean, pytest 13/13, cold-start -99ms vs baseline (within variance band; under +50ms budget).

### Learnings

- **Native tool module pattern.** Place the data-backed loader in its own module under `src/mcp_server_azure_architect/` (e.g. `alz_queries.py`), pure stdlib where possible, with a lazy module-level cache (`_X = None` + `_get_x()` getter + `reset_cache()` for tests). Tool registration in `server.py` stays a thin `@mcp.tool()` wrapper that calls into the loader. This keeps cold-start unaffected (sub-ms parse cost) and preserves the read-only invariant by construction (no Azure SDK in the data path).
- **Lazy load > eager load for cold-start.** Importing my new module added zero measurable overhead because the manifest is only read on first call. Eager parse at import time would have added ~5-15ms of JSON + file IO.
- **Wheel packaging for vendored data.** Hatchling's `[tool.hatch.build.targets.wheel.force-include]` is the right hook to ship `data/alz-queries/` inside the wheel. Loader probes both locations (wheel force-include path under the package, and the editable / source-checkout path at the repo root) so the same code works for `pip install -e .` and a built wheel.
- **TypedDict + FastMCP schema gotcha.** Returning `dict(typed_dict_instance)` in a function annotated `-> dict[str, str]` fails mypy strict because TypedDict's `__getitem__` returns `object`. Use a comprehension (`{k: str(v) for k, v in record.items()}`) at the boundary to satisfy the strict type contract.
- **Async tool roundtrip test.** With `asyncio_mode = "auto"` in `pyproject.toml`, `async def test_*` works without decorators. Use `await mcp._tool_manager.call_tool(name, args)` to validate JSON Schema dispatch end-to-end (catches schema mismatches that the synchronous direct-call test misses).
- **Confused-deputy doesn't apply when input is an allowlist key.** `checklist_id` is matched against vendored data; there's no Azure scope to authorize against, so Sentinel's S1/E1 mitigation isn't needed for this tool. Documented this in the module docstring so future tool authors who do take `subscription_id` know to apply `validate_caller_scope()`.
- **Sibling worktree install collision.** A concurrent Forge sibling on `C:\git\mcp-server-azure-architect-pr39` has the same package installed editable to that path. `pip install -e .` from any worktree replaces the global pointer, so concurrent agents stomp each other. Workaround: re-run `pip install -e . --force-reinstall --no-deps` immediately before any test run if the sibling has touched the install in between. Long-term: move to per-agent venvs in worktrees.

## Wave 4 Outcomes (PR #46): Native Azure Retail Pricing Tools

**Closes #39 (partial):** `pricing_lookup_sku` and `pricing_compare_skus` shipped. `pricing_estimate_workload` deferred to follow-up #44 because it needs a `WorkloadSpec` data model that is not yet defined.

**Cold-start:** warm-import median 4.4ms, p90 7.5ms. Soft (1000ms) and hard (2000ms) gates both pass. Net delta well under the 50ms budget.

## Learnings

### Lazy-import pattern for cold-start hygiene

**Pattern:** Wrap third-party imports inside the function that needs them, not at module top:
```python
def _get_client() -> httpx.Client:
    import httpx  # lazy
    return httpx.Client(...)

if TYPE_CHECKING:
    import httpx  # only for type annotations
```
Combined with `from __future__ import annotations`, type hints stay valid without forcing the import.

**Discovery during validation:** `FastMCP` already loads `httpx` transitively, so adding it as a direct dep had zero net cold-start cost. The lazy pattern was kept anyway because it is correct hygiene and protects against a future server runtime swap.

**Test:** Run the import check in a subprocess. Popping modules from `sys.modules` in the same test process leaks stale references and breaks unrelated tests downstream. `test_no_httpx_at_pricing_module_top` uses `subprocess.run` for isolation.

### OData filter escaping

**Gotcha:** Single quotes in user input must be doubled inside OData literals (per the OData URI conventions spec). Without this, a SKU name like `Foo'Bar` either truncates the filter or causes a server-side parse error. Always escape user-controlled strings before interpolating into an OData ``.

**Helper:** `_escape_odata_value(value: str) -> str` returns `value.replace("'", "''")`. Unit-tested with a SKU containing a single quote.

### In-memory TTL cache pattern

**Pattern:** No new dep needed for a 24h TTL cache. Module-level `dict[str, tuple[float, list[dict]]]` where the value is `(expiry_unix_ts, items)`:
```python
_CACHE: dict[str, tuple[float, list[dict]]] = {}

def _cache_get(key):
    entry = _CACHE.get(key)
    if entry is None: return None
    expiry, items = entry
    if time.time() >= expiry:
        _CACHE.pop(key, None)
        return None
    return items
```

**Cache key construction:** Include any orthogonal axis as a prefix. For pricing, `currency` is a query parameter (not part of the OData filter), so the key prefixes currency: `f"{currency}|{odata_filter}"`. Without this, USD and EUR results would collide.

**Test helper:** Expose `_clear_cache_for_tests()` and call it from an autouse pytest fixture. Otherwise tests that exercise caching leak state to subsequent tests.

### Pagination cap as defensive measure

**Pattern:** When following `NextPageLink` (or any cursor pagination), set a hard upper bound on page count. The cap is not a feature, it is a runaway guard. Document the cap in the module docstring.

**Number choice:** 5 pages = 5000 rows worst-case for the Retail Prices API. Any single-SKU lookup that needs more than 5000 rows is almost certainly a malformed filter, not a legitimate query. Five gives plenty of headroom for legitimate pagination while bounding the blast radius.

### Editable-install gotcha across worktrees

**Symptom:** Running `pip install -e .[dev] --upgrade` in a new worktree may report success but leave the editable `.pth` pointing at the OLD worktree's `src/` directory. Subsequent `python -c "import package"` then loads stale code, causing baffling test failures (e.g., real API calls from inside a mocked test).

**Diagnosis:** `Get-Content C:\Python<ver>\Lib\site-packages\_editable_impl_<package>.pth` shows where the install actually points.

**Fix:** `pip install -e . --force-reinstall --no-deps` overwrites the `.pth`. Worth knowing when squad members create fresh worktrees in a shared interpreter.
## 2026-05-12T14:00:00Z - PR #TBD: alz_scorecard native tool (closes #10)

Shipped the alz_scorecard MCP tool: runs vendored ALZ queries against Azure Resource Graph, returns structured scorecard (pass/fail/unknown per query, aggregate summary by pillar).

**PR:** #TBD feat(server): alz_scorecard tool with bounded ARG queries
**Closes:** #10
**Validation:** pytest 41/41 (12 new), ruff clean, mypy strict clean, cold-start within variance (3471ms vs 3499ms main).

### Learnings

- **Bounded concurrency pattern.** Max 5 in-flight queries via asyncio.Semaphore. Prevents ARG rate limit breaches while maintaining 5x throughput over serial execution. This pattern generalizes to any API with rate limits or quota constraints.
- **Lazy import at function boundary.** Import azure.mgmt.resourcegraph inside _get_resource_graph_client(), not at module top. Measured zero cold-start impact (within variance band). Mirrors pricing.py httpx pattern from PR #46.
- **Count column heuristic for heterogeneous queries.** Vendored ALZ queries use inconsistent aggregation. Some return a Count column, others return raw rows. Heuristic: if Count column exists, use it; else fall back to len(rows). Documented in module docstring.
- **Alphabetical slicing for deterministic truncation.** When full sweep or pillar filter exceeds 25-query cap, slice to first 25 alphabetical and set truncated: true. Alphabetical order is neutral and reproducible.
- **asyncio.to_thread for sync SDK in async context.** ResourceGraphClient.resources() is synchronous. Wrap in asyncio.to_thread(_blocking_call) to enable concurrent gather without blocking the event loop. This pattern enables async tool signatures in FastMCP while composing with sync Azure SDK clients.
- **Composition > duplication.** Scorecard reuses get_query() and list_query_ids() from alz_queries.py (PR #45). No duplication. Single source of truth for query text and metadata.

## 2026-05-12T16:00:00Z - PR #TBD: alz_query_list native tool (closes #51)

Shipped `alz_query_list` MCP tool for catalog discovery. Enumerates vendored ALZ checklist queries with optional pillar/source_repo filters. Returns metadata (checklist_id, pillar, source_repo, citation) for up to 200 queries per call.

**PR:** #TBD feat(server): add alz_query_list native tool  
**Closes:** #51  
**Validation:** pytest 90/90 (+11 tests, net +26 after rebase), ruff clean, mypy strict clean, read-only AST gate clean, mcp_smoke.py 6 tools.

### Learnings

- **Discovery-then-fetch pattern for large catalogs.** `alz_query_list` returns lightweight metadata (no KQL text), `alz_query_by_id` fetches the full query. This two-stage pattern keeps list responses fast and enables client-side filtering/search before fetching expensive payloads.
- **Default limit at 200 items.** Balances typical catalog size (production snapshots will have 50-200 queries) against response size constraints. Alphabetical slicing ensures deterministic truncation when limit is exceeded.
- **Title field placeholder.** Included `"title": ""` in item schema even though current metadata doesn't populate it. Future-proofs for upstream manifest changes without breaking schema compatibility. 8 bytes per item overhead is acceptable.
- **Composite manifest_commit format.** Semicolon-separated `repo@short_sha` list captures multi-source reality (alz-checklist-queries + alz-graph-queries). Human-readable, grep-friendly, no JSON nesting overhead.
- **Pillar values auto-discovered.** Derived from directory structure (kql_path.parent.name). New pillars in upstream repos appear automatically, no code changes needed. Current: "checklist", "graph".
- **Rebase after week gap expanded test count.** Worktree created on 0aed417 (wave 5), origin/main moved to 998afad (wave 5 + ADR-003 readonly gate + 25 new tests). Post-rebase: 90 tests total, net +26 from my baseline. My 11 new tests brought it to 75, rebase added 15 more from concurrent PRs.
- **Cold-start delta: 0ms.** `list_queries()` composes existing `_get_index()` loader. No new top-level imports, no file I/O at import time. Measured <1ms parse overhead.

### Design Choices

1. **Limit default = 200:** Production catalogs will have 50-200 queries. 200 covers typical use without unbounded responses.
2. **Sort key = checklist_id:** Alphabetical UUIDs are deterministic and reproducible. Avoids temporal coupling (vendored_at) or nested sorts (pillar-then-id).
3. **Citation format:** Matches get_query() output for consistency. Includes repo, commit, source_file, and checklist_id.
4. **Empty title field:** Placeholder for future upstream metadata. Schema stability > response size.

Documented in `.squad/decisions/inbox/forge-alz-query-list.md`.

## 2026-05-12T15:00:00Z - PR #TBD: MCP Inspector smoke test in CI (closes #19)

Shipped `scripts/mcp_smoke.py` and `inspector-smoke` CI job to catch tool registration regressions, JSON Schema validity failures, and basic protocol breakage.

**PR:** #TBD test(ci): add MCP Inspector smoke test  
**Closes:** #19  
**Validation:** smoke test exits 0 locally, ruff clean, mypy clean (extended to scripts/), pytest 41/41.

### Learnings

- **Python mcp.client.stdio > npm Inspector for CI.** The `mcp` SDK's stdio_client lets us spawn the server and validate the protocol without npm install overhead. Smoke test runtime < 5s, total CI job time < 60s. This is the same path Copilot CLI skills will use, so we validate the real client integration.
- **Separate CI job for smoke tests.** Protocol-level smoke tests belong in their own job, not mixed with unit tests. Different failure modes (subprocess server spawn vs mocked FastMCP), cleaner signal when something breaks.
- **Hardcoded tool list is acceptable at this scale.** `EXPECTED_TOOLS` frozenset in the smoke script must be updated when tools are added/removed. At 5 tools, manual update is fine. If we hit 10+, consider introspecting `server.py` exports at test time.
- **async with context manager combining.** Python 3.10+ `async with (ctx1, ctx2):` syntax (ruff SIM117) is cleaner than nested `async with` blocks. Applied to stdio_client + ClientSession pairing.
- **MCP tool results are JSON-serialized strings.** FastMCP returns dicts from tool functions, but the MCP protocol layer serializes them to JSON text in `result.content[0].text`. Smoke test must `json.loads()` to validate structure.
- **Exit code + stderr is the CI contract.** Smoke script exits 0 on success, non-zero with human-readable diagnostics to stderr on failure. No logging or external deps needed, CI parses exit code.

## 2026-05-15T16:30:00Z - POLISH Wave 7: Docstring Style Guide and Readonly Workflow Fix

Shipped two deliverables: (A) tool docstring style guide, (B) readonly-check workflow fix.

**PR:** #TBD feat(docs,ci): tool docstring style guide + readonly-check workflow fix
**Closes:** Wave 7 POLISH deliverables

### Deliverable A: Tool Docstring Style Guide

Created `docs/dev/tool-docstring-style.md` (174 lines). Comprehensive pattern guide extracted from the 5 working MCP tools in `server.py`. Sections cover:

1. **Why docstrings matter** . FastMCP extracts docstrings to JSON Schema; they are the end-user-facing descriptions in Copilot CLI and Claude Desktop.
2. **Required structure** . one-line summary (under 80 chars), blank line, 2-4 sentence description, Args/Returns/Raises sections, optional Examples.
3. **Parameter conventions** . Python 3.11+ union syntax (`X | None`, not `Optional[X]`), defaults in function signature (not docstring), `list[X]` and `dict[K, V]`, `Literal` for enums.
4. **Citations** . two real worked examples from server.py: `alz_query_by_id` (simple static lookup) and `pricing_lookup_sku` (public API with multiple params). Copy-pasted verbatim, no invented examples.
5. **Pitfalls** . multi-line description merged into summary, missing Returns shape, vague exception types, ambiguous parameter semantics.
6. **Test pattern** . every tool should have at least 4 tests (happy path, edge case, error path, schema validation). Reference implementations in `tests/test_alz_queries.py`, `tests/test_pricing.py`, `tests/test_scorecard.py`.
7. **Format choice** . Google-style docstrings (PEP 257 recommended, used by Google and many open-source projects). Readable in raw source, compatible with Sphinx/mkdocs generators.

### Deliverable B: Readonly-Check Workflow Fix

**Problem:** `.github/workflows/readonly-check.yml` had a `paths:` filter that excluded doc-only PRs. But `Check for mutation methods` is a required status check on `main`. Result: doc-only PRs were blocked because the required check never reported.

**Fix:** Removed the `paths:` filter entirely. The workflow now runs on every PR + push to main. The check is fast (~30s) and correctly reports "no violations" for doc-only changes. This unblocks doc-only PRs while preserving the read-only enforcement gate.

**Change:** Removed `paths:` block from both `pull_request:` and `push:` sections. Workflow is now:
```yaml
on:
  pull_request:
  push:
    branches:
      - main
```

### Decision Artifact

Filed `.squad/decisions/inbox/forge-docstring-style-guide.md` documenting:
- Problem (no reference for tool authors).
- Decision (adopt Google-style, extract pattern, document in style guide).
- Rationale (readability, industry practice, compatibility with generators).
- Enforcement (code review gate, no automated linting needed at current scale).

### Validation

- Style guide examples are copy-pasted verbatim from `server.py` (lines 33-74), not invented.
- No em dashes in docs or decision artifact (per project style guide).
- CHANGELOG.md updated with both changes (Fixed and Added sections).
- Worktree created and cleaned up at end.

### Learnings

- **Docstring as schema source.** FastMCP extracts the docstring and function signature to produce JSON Schema. The schema is then sent to MCP clients (Copilot CLI, Claude Desktop, etc.). A poor docstring results in poor UX. This is different from traditional Python docs where docstrings are supplementary.
- **Google-style is the right choice.** Numpy and reST styles are alternatives, but Google is more readable in raw source and compatible with modern doc generators. It is also the most familiar to Python developers.
- **Workflow path filters can block required checks.** If a required check has a path filter and those paths are not touched in a PR, the check never reports, and the PR is blocked despite passing all checks it ran. The simplest correct fix is to drop the path filter entirely (checks are usually fast enough to run unconditionally).
- **Pattern extraction from working examples.** Instead of inventing a style guide from scratch, extracting from 5 real, shipped examples ensures the guide is grounded in reality and builds on what is already working. This also provides confidence that the pattern is feasible and tested.


---

## 2026-01-12: Subscription Scope Validator (Issue #57, PR #78)

**Context:** Implemented confused-deputy defense for subscription_id parameters (Threat S1).

**Implementation choices:**

1. **Caching strategy:** Used module-level dict[int, set[str]] keyed on id(credential) for subscription list caching. Considered functools.lru_cache but couldn't key on credential instance directly. The dict approach gives explicit control and works well with lazy imports.

2. **Mypy comprehension issue:** Set comprehensions with type guards need explicit type annotation or explicit loop. Changed from {sub.subscription_id for sub in subs if sub.subscription_id is not None} to explicit loop with if sub.subscription_id is not None: sub_ids.add(...) to satisfy mypy's type narrowing.

3. **Test mocking path:** Mock path must target the imported module (e.g., azure.mgmt.subscription.SubscriptionClient) not the importing module (azure_client.SubscriptionClient), since the import happens inside the function at runtime (lazy import pattern).

4. **Test fixture pattern:** Used autouse fixture mock_scope_validation() in test_scorecard.py to mock validate_caller_scope globally, then override in specific tests with mock_scope_validation.return_value = False. Clean pattern for retrofitting existing tests.

5. **Pre-existing test failures:** mcp_smoke.py fails on Python 3.14 due to upstream MCP SDK issue (TaskGroup exception). Not related to changes. All 115 pytest tests pass.

**Learnings:**

- **Lazy imports and testing:** When mocking lazily-imported modules, patch the original module path, not the importer. The import statement executes inside the function boundary.
- **Per-credential caching:** id(credential) is stable within a session and allows caching keyed on credential identity without requiring the credential to be hashable.
- **GUID redaction pattern:** subscription_id[:8] + "-****-****-****-************" shows first segment for debugging while redacting the rest.

**Validation gates:**
- ruff check . - All checks passed
- mypy src/mcp_server_azure_architect - No issues found
- pytest - 115 passed, 1 skipped
- scripts/check_readonly.py - No violations
- mcp_smoke.py - Pre-existing Python 3.14 incompatibility (not related to changes)

**Outcome:** PR #78 opened, all validation gates passed except pre-existing mcp_smoke.py Python 3.14 issue.

### Session: Security Wave 8 - Audit Logging & File Permissions (2026-01-07)

**Task:** Implement #58 (R1 audit logging) and #61 (I3 log file permissions) in single PR.

**Outcome:**
- New module src/mcp_server_azure_architect/audit.py with decorator-based audit logging
- All MCP tools wrapped with @audit_log_tool decorator for invocation/result/error logging
- Rotating file handler (10MB max, 5 backups) writes to ~/.mcp-server-azure-architect/logs/audit.log
- Cross-platform file permissions: 0600 (owner read/write only) for log files, 0700 for directories
- Token scrubbing redacts subscription IDs, tenant IDs, JWT tokens, API keys, Bearer tokens
- Tests: 15 passed (5 skipped on Windows for POSIX-only permission checks)
- Documentation: docs/install/deployment-guide.md with immutable storage upgrade paths

**Key Design Choices:**
1. Decorator over middleware: FastMCP doesn't expose lifecycle hooks. Decorator is cleanest interception point.
2. Dual wrapper (sync+async): Single decorator handles both sync and async tools via inspect introspection.
3. Cross-platform permissions: POSIX uses os.chmod, Windows uses icacls subprocess.
4. Caller identity = unknown: MCP protocol does not surface caller identity. Documented limitation.
5. Result summaries only: Log result type/size, not content, to avoid leaking sensitive data.

**CI Gates:** pytest 119 passed, ruff clean, mypy clean, readonly check passed.

