# Lazy Import Results (Wave 7)

**Date**: 2026-05-12  
**Issues**: #67 (azure.identity), #68 (httpx)  
**PR**: TBD

## Summary

Refactored eager imports to lazy (function-local) imports to reduce cold-start overhead. Measured improvement: **157ms** (7.7% faster).

## Measurements

| Metric | Before | After | Savings |
|---|---:|---:|---:|
| Total server import | 2,035,173 µs (2.04s) | 1,878,198 µs (1.88s) | **156,975 µs (157ms)** |
| azure.identity | 435,610 µs (435ms) | *deferred* | 435ms (moved to first credential use) |
| httpx | 213,839 µs (213ms) | 213,839 µs (213ms) | 0ms (FastMCP-owned, not fixable) |

**Measurement method**: `python -X importtime -c "import mcp_server_azure_architect.server" 2> {before,after}.log` on Python 3.14.0, Windows.

## Changes

### Issue #67: azure.identity lazy import

**Problem**: `azure.identity` was eagerly imported at module top in `src/mcp_server_azure_architect/azure_client.py:5`, adding 435ms to cold start.

**Solution**: Moved the import inside `get_credential()` function, guarded by `if TYPE_CHECKING:` for type hints at module top. The import now happens only when a tool actually requests a credential (e.g., scorecard, ALZ queries).

**Impact**:
- Server import no longer pulls in azure.identity (verified via sys.modules check).
- First call to `get_credential()` pays the 435ms cost once.
- Subsequent calls reuse the cached credential.

**Canary test**: `tests/test_cold_start.py::test_azure_identity_lazy_import_canary` ensures azure.identity is NOT in sys.modules after server import.

### Issue #68: httpx in pricing module

**Problem**: Sage's cold-start investigation found httpx (~213ms) in the import chain, suspected to be from `pricing.py`.

**Investigation**: httpx was already lazy-imported in `pricing._get_client()` (PR #46). The 213ms httpx import is actually pulled in by **FastMCP** itself via `mcp.shared._httpx_utils`, not by our code.

**Solution**: No code change. Added documentation in `pricing.py` docstring noting that httpx is FastMCP-owned and not under our control. Our lazy import in `_get_client()` only defers the cost until the pricing tool is invoked, but FastMCP's own import happens at server startup regardless.

**Impact**:
- httpx remains in sys.modules after server import (expected and not a bug).
- This is an upstream dependency, not fixable without changes to FastMCP.

**Canary test**: `tests/test_cold_start.py::test_httpx_fastmcp_owned_note` documents that httpx WILL appear in sys.modules after server import.

## Test coverage

Added 2 new canary tests (both use subprocess for clean import environment):

1. `test_azure_identity_lazy_import_canary` - regression guard for #67
2. `test_httpx_fastmcp_owned_note` - documents FastMCP ownership for #68

Total tests: **82 passed** (up from 80).

## Validation

All gates passed:

- ✅ `python scripts/check_readonly.py src/` — no mutation methods
- ✅ `python -m pytest -q` — 82 tests passed
- ✅ `python -m ruff check .` — clean
- ✅ `python -m mypy src/ tests/ scripts/` — clean
- ✅ `python scripts/mcp_smoke.py` — server starts, 5 tools registered

## Future work

- **FastMCP httpx import**: If FastMCP refactors to lazy-import httpx, we would gain the 213ms savings automatically. No action on our side.
- **Other Azure SDK modules**: Consider similar lazy-import treatment for `azure.mgmt.resourcegraph` if it shows up in future profiles. Currently it is already lazy-loaded in `scorecard._get_resource_graph_client()`.

## References

- [docs/perf/coldstart-investigation.md](./coldstart-investigation.md) - Sage's initial analysis
- Issue #67: `perf: lazy-import azure.identity to reduce cold start by 945ms`
- Issue #68: `perf: lazy-import httpx in pricing module to reduce cold start by 1.46s`
- PR #46: Original httpx lazy-import (Forge, 2026-05-12)
