# ADR-001: Runtime choice and cold-start expectation

- Status: Accepted
- Date: 2026-04-22

## Context

This project uses Python with FastMCP to keep implementation small and maintainable for architect-facing orchestration tools.

Initial runtime guidance targeted cold start below 1 second, based on prior FastMCP benchmark guidance that reported startup in the 200ms to 800ms range for lightweight servers.

Investigation data for this repository shows:

- Python 3.12 cached startup is about 943ms.
- Python 3.11 startup is materially more variable.
- Startup cost is dominated by `mcp` imports, not Azure SDK imports.

## Decision

Keep Python plus FastMCP as the runtime.

Revise enforceable cold-start expectation to the following:

- Keep a soft target of 1000ms for visibility.
- Enforce a hard gate of 2000ms in tests for reproducibility across Python 3.11 and 3.12.
- Recommend Python 3.12+ for best cold-start consistency while retaining `>=3.11` compatibility.

## Consequences

- The server remains within the original sub-1 second intent on Python 3.12 cached runs.
- CI can remain stable across supported Python versions without failing on expected 3.11 variance.
- Performance work can continue incrementally without blocking baseline runtime adoption.

## Evidence

- `docs/perf/coldstart-investigation.md`
- `docs/perf/coldstart-importtime-3.12.txt`
- `tests/test_cold_start.py`
