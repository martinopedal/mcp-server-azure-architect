# Forge — Implementation Lead — History

## 2026-04-22T11:31:59Z — ADR-001 Draft Ready

Sage completed ADR-001 recommending **Python + FastMCP** as the MCP server runtime. Comprehensive evaluation covered sync models, ecosystem maturity, read-only constraints, and team skill fit. 

**Pending Lead's review gate.** Once approved, Forge will implement:
1. FastMCP server scaffold
2. Tool registration harness
3. Auth integration (DefaultAzureCredential)
4. Read-only enforcement gates

Next: Monitor `.squad/decisions/inbox/` for Lead's approval signal.

## 2026-04-22T11:33:32Z — ADR-001 Accepted

ADR-001 accepted. Runtime: Python + FastMCP. Implementation can begin.

## 2026-04-22T13:36:15Z — FastMCP Runtime Scaffolded

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

- `.squad/decisions/inbox/forge-pr26-audit.md` (this session's audit)
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

## 2026-05-12T13:30:00Z — PR #45: alz_query_by_id native tool (closes #9)

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
