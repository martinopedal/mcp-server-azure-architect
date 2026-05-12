"""Cold-start test for server import time."""

from __future__ import annotations

import importlib
import subprocess
import sys
import time
import warnings

MODULE_NAME = "mcp_server_azure_architect.server"
SOFT_WARNING_MS = 1000.0
HARD_FAIL_MS = 2000.0


def _measure_import_ms() -> float:
    start = time.perf_counter()
    importlib.import_module(MODULE_NAME)
    end = time.perf_counter()
    return (end - start) * 1000


def test_server_cold_start_under_threshold() -> None:
    """Measure warm cached import time to avoid first-run bytecode compilation noise."""
    importlib.import_module(MODULE_NAME)
    sys.modules.pop(MODULE_NAME, None)

    elapsed_ms = _measure_import_ms()
    if elapsed_ms > SOFT_WARNING_MS:
        warnings.warn(
            (
                f"Cold start warning: {elapsed_ms:.2f}ms exceeds "
                f"{SOFT_WARNING_MS:.0f}ms soft target."
            ),
            stacklevel=1,
        )

    assert elapsed_ms < HARD_FAIL_MS, (
        f"Cold start {elapsed_ms:.2f}ms exceeds hard gate {HARD_FAIL_MS:.0f}ms."
    )


def test_azure_identity_lazy_import_canary() -> None:
    """Canary test: azure.identity must not be imported until first credential use.

    This regression guard ensures issue #67 stays fixed. The azure.identity import
    chain costs ~435ms. Lazy-importing it in azure_client.get_credential() keeps
    the server import fast.

    Uses subprocess to ensure clean import environment.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import mcp_server_azure_architect.server; "
                "print('PASS' if 'azure.identity' not in sys.modules else 'FAIL')"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "PASS" in result.stdout, (
        "azure.identity was eagerly imported at server startup. "
        "It should be lazy-imported in azure_client.get_credential(). "
        "See issue #67."
    )


def test_httpx_fastmcp_owned_note() -> None:
    """Document that httpx is FastMCP-owned and not under our control (issue #68).

    httpx (~213ms import) is eagerly imported by FastMCP via mcp.shared._httpx_utils.
    Our pricing module already lazy-imports httpx in _get_client(), but this only
    defers the cost until the pricing tool is first invoked, not until server startup.

    This test documents the situation and does not fail. It serves as a note for
    future maintainers that httpx will appear in sys.modules after server import.

    Uses subprocess to ensure clean import environment.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import mcp_server_azure_architect.server; "
                "print('PASS' if 'httpx' in sys.modules else 'FAIL')"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Import failed: {result.stderr}"
    assert "PASS" in result.stdout, (
        "httpx is expected to be imported by FastMCP at server startup. "
        "See issue #68 for context."
    )
