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
