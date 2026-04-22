# Skill: FastMCP Server Bootstrap

**Author:** Forge  
**Date:** 2026-04-22  
**Version:** 1.0

## Purpose

Bootstrap a minimal Python + FastMCP MCP server with src layout, modern tooling, and sub-1s cold start.

## When to Use

- Starting a new MCP server project in Python.
- Need automatic JSON Schema generation from type hints.
- Want minimal boilerplate and fast iteration (no build step).
- Targeting local-first, single-process deployment (uvx, pipx).

## Prerequisites

- Python >=3.11
- uv or pip for dependency management
- Basic understanding of MCP protocol (stdio transport, tools, JSON Schema)

## Recipe

### 1. Project Structure

```
project-root/
├── pyproject.toml
├── src/
│   └── your_package_name/
│       ├── __init__.py        # version constant
│       ├── __main__.py        # entry point (mcp.run())
│       ├── server.py          # FastMCP instance, @mcp.tool() decorators
│       └── azure_client.py    # lazy credential init (if Azure)
└── tests/
    ├── __init__.py
    ├── test_server.py         # tool registration tests
    └── test_cold_start.py     # performance gate
```

### 2. pyproject.toml Template

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your-package-name"
version = "0.0.1"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0.0",
    # add Azure SDKs if needed
]

[project.optional-dependencies]
dev = [
    "ruff>=0.3.0",
    "mypy>=1.9.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
your-package-name = "your_package_name.__main__:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
```

### 3. Minimal Server (server.py)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("your-server-name")

@mcp.tool()
def health_check() -> dict[str, str]:
    """Check server health and version."""
    return {"status": "ok", "version": "0.0.1"}
```

### 4. Entry Point (__main__.py)

```python
from your_package_name.server import mcp

def main() -> None:
    """Run the MCP server via stdio transport."""
    mcp.run()  # FastMCP handles the event loop

if __name__ == "__main__":
    main()
```

### 5. Cold Start Test (tests/test_cold_start.py)

```python
import time

def test_cold_start_time() -> None:
    """Measure import + server creation time."""
    start_time = time.perf_counter()
    from your_package_name.server import mcp
    assert mcp is not None
    elapsed_ms = (end_time - start_time) * 1000
    print(f"Cold start: {elapsed_ms:.2f}ms")
    assert elapsed_ms < 5000  # hard gate
```

## Key Patterns

### 1. Lazy Credential Initialization (Azure)

```python
from azure.identity import DefaultAzureCredential

_credential: DefaultAzureCredential | None = None

def get_credential() -> DefaultAzureCredential:
    """Defer credential init until first use."""
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential
```

### 2. Automatic Schema from Type Hints

```python
@mcp.tool()
def query_resources(
    subscription_id: str,
    resource_type: str | None = None,
) -> list[dict[str, str]]:
    """Query Azure resources."""
    # FastMCP auto-generates JSON Schema:
    # - subscription_id: required string
    # - resource_type: optional string (nullable)
    # - returns: array of objects
    pass
```

### 3. Token Scrubbing for Logs

```python
import re

def token_scrub(text: str) -> str:
    """Remove Azure tokens from text."""
    jwt_pattern = r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"
    return re.sub(jwt_pattern, "[REDACTED]", text)
```

## Validation Gates

- **Lint:** `ruff check .` must pass.
- **Type check:** `mypy src` must pass (with azure.* ignore if using Azure SDK).
- **Tests:** `pytest` must pass all tests.
- **Tool listing:** Tools must appear in `mcp._tool_manager.list_tools()` with valid schemas.
- **Cold start:** Import + server creation < 1000ms preferred, < 5000ms hard limit.

## Distribution

### Local dev:
```bash
uv pip install -e ".[dev]"
```

### End user (ephemeral):
```bash
uvx your-package-name
```

### MCP client config:
```json
{
  "mcpServers": {
    "your-server": {
      "command": "uvx",
      "args": ["your-package-name"]
    }
  }
}
```

## Gotchas

1. **FastMCP.run() is synchronous.** Do NOT wrap in `asyncio.run()`. It handles the event loop internally.
2. **Ruff config deprecation.** Use `[tool.ruff.lint]` section, not top-level `select`/`ignore`.
3. **Src layout prevents import shadowing.** Always install package (`pip install -e .`) during dev. Do not run Python files directly from project root.
4. **Type hints must be runtime-evaluatable.** Use `from __future__ import annotations` if using forward references or complex types.

## References

- FastMCP docs: https://gofastmcp.com
- MCP spec: https://modelcontextprotocol.io/specification
- Python packaging (src layout): https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/

## Related Skills

- (none yet, this is the bootstrap)

## Changelog

- 2026-04-22: Initial version from mcp-server-azure-architect scaffold.
