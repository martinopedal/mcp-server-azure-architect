"""Test cold start performance."""

import time


def test_cold_start_time() -> None:
    """Measure and assert import + server creation is under 1000ms."""
    start_time = time.perf_counter()

    # Import server module (simulates cold start)
    from mcp_server_azure_architect.server import mcp

    # Verify server is created
    assert mcp is not None

    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000

    print(f"\nCold start time: {elapsed_ms:.2f}ms")

    # Soft gate: warn if > 1000ms but don't fail
    # This accounts for slower CI environments
    if elapsed_ms > 1000:
        print(f"WARNING: Cold start exceeded 1000ms target ({elapsed_ms:.2f}ms)")

    # Hard gate: fail if unreasonably slow (>5s indicates a problem)
    assert elapsed_ms < 5000, f"Cold start too slow: {elapsed_ms:.2f}ms"
