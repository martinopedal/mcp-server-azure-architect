# MCP Tool Docstring Style Guide

## Why Docstrings Matter for MCP Tools

When you register a tool with FastMCP using `@mcp.tool()`, the tool's Python docstring becomes the **description** that callers (Copilot CLI, Claude Desktop, other MCP clients) see. This docstring is the only human-readable documentation the client has. It is not optional.it is the source of truth for how and when a tool should be used.

FastMCP automatically extracts the docstring and parses it alongside the function signature to produce the tool's JSON Schema. The schema is read by MCP clients, which use it to:
1. Decide whether to invoke this tool for a user's request.
2. Guide users on which parameters are required and what they mean.
3. Display help text and examples.

A poor docstring results in confusing or unhelpful tool behavior in the hands of end users.

## Required Structure

Every tool docstring must include the following sections, in this order:

### 1. One-Line Summary

The first line of the docstring is a concise summary under 80 characters. It is the first thing a user sees. Use imperative mood.

Example (from `alz_query_by_id`):
```
Look up a vendored Azure Landing Zone (ALZ) checklist query by ID.
```

### 2. Blank Line

Separate the summary from the description.

### 3. Multi-Line Description

2-4 sentences explaining the tool's purpose, when to use it, and how it differs from related tools or APIs.

For read-only tools backed by public data, explicitly note "Read-only" and why (e.g., static lookup, public API, no auth required). This reassures callers about safety and scope.

For tools that take Azure scope parameters (`subscription_id`, `resource_group`, etc.), note the Azure surface and any auth/quota implications.

Example (from `pricing_lookup_sku`):
```
Calls the public Azure Retail Prices API. No auth, no Azure SDK, read-only.
Results cached for 24h. Caveats: retail only (no EA/CSP), USD default,
no real-time freshness SLA.
```

### 4. Args Section

Use a Python docstring `Args:` block. List each parameter with:
- **Name**: the parameter name (must match the function signature exactly).
- **Type annotation**: from the function signature.
- **Default (if any)**: shown in the signature; repeat here for emphasis if ambiguous.
- **Semantics**: 1-2 sentences explaining what the parameter means and what values are valid. Include examples or caveats.

Do not use `Optional[X]` in docstrings; FastMCP infers optionality from the function signature. If the signature has a default, it is optional.

Format (numpy-style, used in our examples):
```
Args:
    checklist_id: The ALZ checklist item ID (matches the vendored
        `.kql` filename stem). Must not be empty or None.
    subscription_id: Azure subscription ID to evaluate. Format: valid UUID.
    region: Azure region name (e.g., 'eastus', 'westus2').
        Case-insensitive. Matched against the Retail Prices API region list.
    term: Pricing term. One of 'ondemand', '1yr', '3yr'. Default is 'ondemand'.
```

### 5. Returns Section

Describe the return value type and shape. If returning a dict, enumerate the keys and their types/meanings.

Example (from `alz_query_by_id`):
```
Returns:
    A dictionary with `checklist_id`, `kql`, `source`, `source_repo`,
    `source_commit`, `source_ref`, `source_file`, `vendored_at`,
    `vendored_path`, and `citation`.
```

For complex dicts or TypedDicts, link to the class definition if it is exported, or describe structure inline.

### 6. Raises Section

List exceptions that a **caller should handle**. Do not list implementation details or internal errors (e.g., no need to document `json.JSONDecodeError` if it is caught and re-raised as a public exception).

Include the exception type and when it is raised.

Example (from `alz_query_by_id`):
```
Raises:
    LookupError: if the checklist ID is not in the vendored snapshot.
```

### 7. Examples Section (Optional but Recommended)

1-2 minimal usage snippets showing how to call the tool. Keep examples short; they appear inline in client help.

Example (from an imaginary tool):
```
Examples:
    Look up a single query by checklist ID:

        result = alz_query_by_id("reliability-001")
        print(result["kql"])

    Run a scorecard for a subscription:

        scorecard = await alz_scorecard("12345678-1234-1234-1234-123456789012")
        print(f"Pass: {scorecard['aggregate']['pass']}")
```

## Required Parameter Conventions

1. **Optionality in signatures.** Use Python 3.11+ union syntax (`X | None`) in the signature. FastMCP's schema generator handles this correctly. Do not use `Optional[X]` in new code (deprecated by PEP 604).

2. **Defaults in signatures.** Always supply defaults for optional parameters in the function signature, not just in the docstring. FastMCP reads the signature, not the docstring, to infer schema defaults.

   ```python
   # Correct:
   def example(region: str, term: str = "ondemand") -> dict[str, Any]:
       ...

   # Incorrect (term appears optional in doc but required in schema):
   def example(region: str, term: str) -> dict[str, Any]:
       # Docstring says "Default: ondemand"
       ...
   ```

3. **List and dict types.** Use `list[X]` and `dict[K, V]` (Python 3.11+ syntax). FastMCP converts these to JSON Schema arrays and objects automatically.

   ```python
   def example(skus: list[str], options: dict[str, str]) -> None:
       ...
   ```

4. **Literal types for enums.** Use `Literal["ondemand", "1yr", "3yr"]` for fixed sets of allowed values. FastMCP generates a schema enum constraint.

   ```python
   from typing import Literal
   
   def pricing_lookup_sku(term: Literal["ondemand", "1yr", "3yr"] = "ondemand") -> dict[str, Any]:
       ...
   ```

## Citations: Two Worked Examples

### Example 1: alz_query_by_id (Simple Static Lookup)

**Location:** `src/mcp_server_azure_architect/server.py` lines 33-58.

```python
@mcp.tool()
def alz_query_by_id(checklist_id: str) -> dict[str, str]:
    """Look up a vendored Azure Landing Zone (ALZ) checklist query by ID.

    Returns the KQL query text plus source metadata (repo, commit SHA, ref,
    citation) so the caller can run the query against Azure Resource Graph
    and reference the upstream ALZ checklist item.

    Read-only: this tool performs a static lookup against the vendored ALZ
    snapshot under `data/alz-queries/`. It does not call Azure and does not
    accept a subscription ID, so there is no confused-deputy surface here.

    Args:
        checklist_id: The ALZ checklist item ID (matches the vendored
            `.kql` filename stem).

    Returns:
        A dictionary with `checklist_id`, `kql`, `source`, `source_repo`,
        `source_commit`, `source_ref`, `source_file`, `vendored_at`,
        `vendored_path`, and `citation`.

    Raises:
        LookupError: if the checklist ID is not in the vendored snapshot.
    """
    record = get_query(checklist_id)
    return {key: str(value) for key, value in record.items()}
```

**Patterns:**
- One-line summary states the action (Look up) and the resource (checklist query).
- Multi-line description includes read-only guarantee and explains why (static lookup, no Azure surface).
- Args block is brief because there is only one parameter.
- Returns documents the dict shape inline (appropriate for simple cases).
- Raises lists the one public exception.
- No Examples section (tool is self-explanatory).

### Example 2: pricing_lookup_sku (Public API with Multiple Parameters)

**Location:** `src/mcp_server_azure_architect/server.py` lines 62-74.

```python
@mcp.tool()
def pricing_lookup_sku(
    sku: str,
    region: str,
    term: Literal["ondemand", "1yr", "3yr"] = "ondemand",
    currency: str = "USD",
) -> dict[str, Any]:
    """Look up Azure retail pricing for a single SKU in a region.

    Calls the public Azure Retail Prices API. No auth, no Azure SDK, read-only.
    Results cached for 24h. Caveats: retail only (no EA/CSP), USD default,
    no real-time freshness SLA.
    """
    return _pricing_lookup_sku(sku=sku, region=region, term=term, currency=currency)
```

**Patterns:**
- One-line summary clearly states the action and resource.
- Multi-line description is brief (3 sentences) but covers public API, caveats (retail only, no real-time SLA), and caching behavior.
- No Args block in the tool wrapper (it delegates to `_pricing_lookup_sku`); the actual args are documented in the implementation module.
- Return type is inferred from the signature.
- No Raises block here because the wrapper does not raise; error handling is in `_pricing_lookup_sku`.

**Note on tool wrappers:** Some tools are thin wrappers around implementation functions (like `pricing_lookup_sku` above). In such cases, the tool docstring can be brief because the real documentation lives in the implementation module. However, every tool must still have a one-line summary and a multi-line description explaining its purpose to end users.

## Pitfalls to Avoid

1. **Multi-line description merged into summary.** Do not do this:
   ```python
   def tool() -> None:
       """Look up pricing for a SKU. Calls the Azure Retail Prices API which is read-only
       and publicly accessible, and caches results for 24 hours."""
   ```
   This violates the 80-character rule and buries the summary. Use a blank line separator.

2. **Missing Returns shape.** Do not return a dict without documenting its keys:
   ```python
   def alz_query_by_id(checklist_id: str) -> dict[str, str]:
       """Look up a query by ID.

       Read-only static lookup.
       """
   ```
   Callers cannot use the result without knowing what keys exist. Document the shape.

3. **Missing exception types in Raises.** Do not list exceptions that callers cannot catch:
   ```python
   def tool() -> None:
       """Do something.

       Raises:
           Exception: if something goes wrong.
       """
   ```
   Too vague. List the specific exception (`ValueError`, `LookupError`, etc.) and when it is raised.

4. **Ambiguous parameter names without semantics.** Do not do this:
   ```python
   def tool(term: str) -> None:
       """Look up pricing.

       Args:
           term: The term.
       """
   ```
   "The term" is not clear. Is it a pricing term ('1yr')? A search term? A time period? Include an example: `term: Pricing term. One of 'ondemand', '1yr', '3yr'.`

5. **No distinction between required and optional parameters.** The function signature should make this clear (optional parameters have defaults). The docstring must reflect this:
   ```python
   def tool(required_param: str, optional_param: str = "default") -> None:
       """Do something.

       Args:
           required_param: Must be supplied.
           optional_param: Optional; defaults to 'default'.
       """
   ```

## Test Pattern

Every tool should have at least 4 tests covering:

1. **Happy path:** tool succeeds with valid inputs and returns the expected structure.
2. **Edge case:** boundary conditions (empty list, empty string, maximum allowed size, etc.).
3. **Error path:** tool raises the documented exception with a clear message.
4. **Schema validation:** if the tool's return type is complex, validate the structure matches the type hint (run via `await mcp._tool_manager.call_tool(name, args)` for end-to-end schema check).

**Reference examples:**
- `tests/test_alz_queries.py` . tests for `alz_query_by_id`, covering load, lookup, and error cases.
- `tests/test_pricing.py` . tests for `pricing_lookup_sku` and `pricing_compare_skus`, including cache validation.
- `tests/test_scorecard.py` . tests for `alz_scorecard`, including bounded concurrency and truncation.

**Test file layout:**
```python
def test_tool_happy_path() -> None:
    """Tool succeeds with valid inputs and returns expected keys."""
    result = my_tool(valid_input)
    assert "key1" in result
    assert "key2" in result

def test_tool_edge_case() -> None:
    """Tool handles boundary conditions correctly."""
    result = my_tool("")  # or other edge case
    assert result is not None

def test_tool_error_path() -> None:
    """Tool raises the documented exception on invalid input."""
    with pytest.raises(LookupError) as exc_info:
        my_tool("nonexistent")
    assert "helpful message" in str(exc_info.value)

async def test_tool_schema_validation() -> None:
    """Tool's return value matches the schema (async tools only)."""
    result = await mcp._tool_manager.call_tool("tool_name", {"param": "value"})
    parsed = json.loads(result.content[0].text)
    assert "expected_key" in parsed
```

## Docstring Format: Google Style

This guide uses **Google-style docstrings** (as recommended in PEP 257 and used by Google and many open-source projects). The format is readable both in raw Python source and when rendered by documentation generators.

**Why Google style?**
- Sections (Args, Returns, Raises) are clearly labeled and machine-parseable.
- Parameter descriptions are prose, not type signatures (type info is in the Python signature).
- Compatible with Sphinx, mkdocs, and other generators.
- Familiar to most Python developers.

**Alternatives (not used here):**
- NumPy style: detailed but verbose; suitable for large scientific libraries.
- reStructuredText: closer to reST markup; less readable in raw source.

Stick to Google style for consistency across the project.
