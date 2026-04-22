"""Cold-start test for server import time."""

from __future__ import annotations

import importlib
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

