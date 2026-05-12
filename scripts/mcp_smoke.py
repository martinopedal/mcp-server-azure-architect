#!/usr/bin/env python3
"""MCP Inspector smoke test for mcp-server-azure-architect.

Validates the running MCP server against three invariants:

1. **Tool registration completeness:** Exactly the expected 5 tools are
   registered (health_check, alz_query_by_id, pricing_lookup_sku,
   pricing_compare_skus, alz_scorecard). Catches tool addition/removal
   regressions.

2. **JSON Schema validity:** Every tool's inputSchema has type "object"
   and a "properties" dict. This is the minimal contract for MCP clients
   to generate forms or validate calls.

3. **Basic invocability:** Calling health_check returns a dict with
   status "ok" and a non-empty version string. Validates the end-to-end
   stdio transport + tool dispatch path without calling Azure.

Intended for CI (inspector-smoke job) and local pre-commit validation.
Exit 0 on all assertions passing, non-zero with human-readable error on
any failure.

Usage:
    python scripts/mcp_smoke.py

Dependencies:
    mcp[cli]>=1.27.0 (from project [dev] extras)

Note: This script does NOT call Azure. Only health_check is invoked.
"""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = frozenset(
    [
        "health_check",
        "alz_query_by_id",
        "pricing_lookup_sku",
        "pricing_compare_skus",
        "alz_scorecard",
    ]
)


async def run_smoke_test() -> None:
    """Run the MCP smoke test suite."""
    # Spawn the server via stdio transport
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server_azure_architect"],
        env=None,
    )

    async with (
        stdio_client(server_params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()

        # 1. List tools
        tools_result = await session.list_tools()
        tools = tools_result.tools

        tool_names = {tool.name for tool in tools}

        # 2. Assert exactly expected tool set
        if tool_names != EXPECTED_TOOLS:
            missing = EXPECTED_TOOLS - tool_names
            extra = tool_names - EXPECTED_TOOLS
            error_lines = ["Tool registration mismatch:"]
            if missing:
                error_lines.append(f"  Missing: {sorted(missing)}")
            if extra:
                error_lines.append(f"  Extra: {sorted(extra)}")
            error_lines.append(f"  Expected: {sorted(EXPECTED_TOOLS)}")
            error_lines.append(f"  Got: {sorted(tool_names)}")
            print("\n".join(error_lines), file=sys.stderr)
            sys.exit(1)

        print(f"✓ Tool registration: {len(tools)} tools match expected set")

        # 3. Validate JSON Schema for each tool
        for tool in tools:
            input_schema = tool.inputSchema
            if not isinstance(input_schema, dict):
                print(
                    f"✗ Tool {tool.name}: inputSchema is not a dict",
                    file=sys.stderr,
                )
                sys.exit(1)

            if input_schema.get("type") != "object":
                print(
                    f"✗ Tool {tool.name}: inputSchema.type is not 'object'",
                    file=sys.stderr,
                )
                sys.exit(1)

            if "properties" not in input_schema:
                print(
                    f"✗ Tool {tool.name}: inputSchema missing 'properties'",
                    file=sys.stderr,
                )
                sys.exit(1)

            if not isinstance(input_schema["properties"], dict):
                print(
                    f"✗ Tool {tool.name}: inputSchema.properties is not a dict",
                    file=sys.stderr,
                )
                sys.exit(1)

        print("✓ JSON Schema validity: all tools have valid inputSchema")

        # 4. Call health_check and validate response shape
        result = await session.call_tool("health_check", arguments={})

        if not result.content:
            print(
                "✗ health_check returned no content",
                file=sys.stderr,
            )
            sys.exit(1)

        # Extract the text content from the result
        content_item = result.content[0]
        if not hasattr(content_item, "text"):
            print(
                "✗ health_check content[0] has no text attribute",
                file=sys.stderr,
            )
            sys.exit(1)

        # The MCP protocol returns tool results as JSON-serialized strings
        import json

        try:
            response_data = json.loads(content_item.text)
        except json.JSONDecodeError as e:
            print(
                f"✗ health_check response is not valid JSON: {e}",
                file=sys.stderr,
            )
            sys.exit(1)

        if not isinstance(response_data, dict):
            print(
                f"✗ health_check response is not a dict: {type(response_data)}",
                file=sys.stderr,
            )
            sys.exit(1)

        status = response_data.get("status")
        version = response_data.get("version")

        if status != "ok":
            print(
                f"✗ health_check status is not 'ok': {status}",
                file=sys.stderr,
            )
            sys.exit(1)

        if not version or not isinstance(version, str):
            print(
                f"✗ health_check version is empty or not a string: {version}",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"✓ Basic invocability: health_check returned status=ok, version={version}")

    print("\n✓ All smoke tests passed")


def main() -> None:
    """Entry point."""
    try:
        asyncio.run(run_smoke_test())
    except Exception as e:
        print(f"\n✗ Smoke test failed with exception: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
