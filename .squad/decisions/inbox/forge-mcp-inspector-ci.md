# Decision: MCP Inspector Smoke Test in CI

**Status:** Implemented  
**Decider:** Forge  
**Date:** 2026-05-12  
**Issue:** #19

## Context

The server now has 5 tools registered. We need automated validation in CI to catch:
1. Tool registration regressions (missing or extra tools)
2. JSON Schema validity failures for tool inputs
3. Basic protocol layer breakage

The MCP Inspector exists as `@modelcontextprotocol/inspector` (npm), but installing npm in the Python CI adds complexity and latency. The `mcp` Python SDK already provides `stdio_client` for talking to MCP servers, which is what the Inspector uses under the hood.

## Decision

Ship a Python smoke test script (`scripts/mcp_smoke.py`) that uses the `mcp.client.stdio` SDK to:
1. Spawn the server via stdio transport
2. Send `tools/list` request
3. Assert exactly 5 expected tools are registered
4. Validate every tool's inputSchema has `type: "object"` and a `properties` dict
5. Call `health_check` and assert response shape (`status: "ok"`, non-empty `version`)

Add a separate CI job `inspector-smoke` (ubuntu-latest, Python 3.12 only) that runs the script. No need to matrix across Python versions, one smoke run per PR is sufficient.

## Rationale

**Why Python SDK over npm Inspector:**
- Zero npm install overhead (CI time budget)
- Reuses existing `mcp[cli]` dependency from `[dev]` extras
- Validates the Python client path (the one Copilot CLI skills will use)

**Why separate job from `test`:**
- Isolation. Smoke test spawns a subprocess server, different failure mode than unit tests.
- Clear signal in CI status. If `inspector-smoke` fails, it's a protocol/registration issue, not a unit test.

**Why Python 3.12 only:**
- Smoke test is protocol-level, not Python-version-sensitive.
- Running on both 3.11 and 3.12 doubles cost for no signal gain.

**What the smoke asserts:**
1. Tool registration completeness: exactly `health_check`, `alz_query_by_id`, `pricing_lookup_sku`, `pricing_compare_skus`, `alz_scorecard`
2. JSON Schema validity: every tool has `inputSchema.type == "object"` and `inputSchema.properties` is a dict
3. Basic invocability: `health_check` returns `{"status": "ok", "version": "0.0.1"}`

**Read-only constraint:**
Only `health_check` is invoked. No Azure calls. Smoke test runs offline.

## Consequences

**Positive:**
- Catches tool registration regressions before merge (e.g., decorator typo, import error)
- Validates JSON Schema generation from FastMCP type hints
- Fast (< 5s runtime, under 60s total job time with install)

**Negative:**
- Hardcoded tool list. Adding a new tool requires updating `EXPECTED_TOOLS` in `scripts/mcp_smoke.py`.
- Fragile to MCP protocol breaking changes in `mcp` SDK major version bumps (mitigated by upper-bound constraint in `pyproject.toml`).

**Follow-up:**
- Sentinel to add `inspector-smoke` to required-status-checks list in branch protection (not done in this PR per constraints).
- If the tool count grows beyond 10, consider generating `EXPECTED_TOOLS` from `server.py` introspection (deferred, not needed yet).

## Alternatives Considered

**Alt 1: Use npm MCP Inspector in CI**  
Rejected. Adds 15-30s npm install overhead, requires Node.js setup in CI, less control over assertions.

**Alt 2: Inline smoke test in pytest suite**  
Rejected. Spawning the server in a subprocess is slower than mocked unit tests, would dominate pytest runtime. Separate job is cleaner.

**Alt 3: No smoke test, rely on unit tests**  
Rejected. Unit tests mock FastMCP tool manager, don't validate end-to-end stdio transport or tool registration from the `__main__.py` entry point.

## Implementation Notes

- Script uses `async with` combining stdio_client and ClientSession (per ruff SIM117 lint rule).
- JSON import is inline (after session setup) to defer import cost, though negligible here.
- Exit code 0 on success, non-zero with stderr diagnostics on failure (CI-friendly pattern).
- Script header documents what it asserts, for future maintainers who see a CI failure.

## References

- MCP SDK stdio client: https://github.com/modelcontextprotocol/python-sdk
- FastMCP tool registration: https://github.com/jlowin/fastmcp
- Issue #19: https://github.com/martinopedal/mcp-server-azure-architect/issues/19
- CI job added: `.github/workflows/ci.yml` inspector-smoke
- README updated: Development section now lists `python scripts/mcp_smoke.py` for local validation
