"""Tests for the native Azure retail pricing tools."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from mcp_server_azure_architect import pricing


@pytest.fixture(autouse=True)
def _clear_pricing_cache() -> None:
    pricing._clear_cache_for_tests()


def _make_item(
    arm_sku: str = "Standard_D2s_v5",
    region: str = "westeurope",
    price: float = 0.096,
    uom: str = "1 Hour",
    price_type: str = "Consumption",
    reservation_term: str | None = None,
) -> dict[str, Any]:
    return {
        "currencyCode": "USD",
        "tierMinimumUnits": 0.0,
        "retailPrice": price,
        "unitPrice": price,
        "armRegionName": region,
        "location": "EU West",
        "effectiveStartDate": "2024-01-01T00:00:00Z",
        "meterId": "00000000-0000-0000-0000-000000000001",
        "meterName": f"{arm_sku} meter",
        "productId": "DZH318Z0BQPS",
        "skuId": "0001",
        "productName": "Virtual Machines DSv5 Series",
        "skuName": arm_sku.replace("Standard_", "").replace("_", " "),
        "serviceName": "Virtual Machines",
        "serviceId": "DZH313Z7MMC8",
        "serviceFamily": "Compute",
        "unitOfMeasure": uom,
        "type": price_type,
        "isPrimaryMeterRegion": True,
        "armSkuName": arm_sku,
        "reservationTerm": reservation_term,
    }


def _install_mock_transport(
    handler: Any,
) -> Any:
    """Patch pricing._get_client to return an httpx.Client backed by MockTransport."""
    transport = httpx.MockTransport(handler)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport)

    return patch.object(pricing, "_get_client", _factory)


def test_lookup_sku_happy_path() -> None:
    """Mock the API, assert correct OData filter built and parsed response correct."""
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["filter"] = request.url.params.get("$filter")
        captured["currency"] = request.url.params.get("currencyCode")
        return httpx.Response(
            200,
            json={"Items": [_make_item()], "NextPageLink": None, "Count": 1},
        )

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope", term="ondemand"
        )

    assert "armSkuName eq 'Standard_D2s_v5'" in captured["filter"]
    assert "armRegionName eq 'westeurope'" in captured["filter"]
    assert "priceType eq 'Consumption'" in captured["filter"]
    assert "reservationTerm" not in captured["filter"]
    assert captured["currency"] == "USD"

    assert result["sku"] == "Standard_D2s_v5"
    assert result["region"] == "westeurope"
    assert result["term"] == "ondemand"
    assert result["item_count"] == 1
    assert result["items"][0]["retail_price"] == 0.096
    assert result["items"][0]["unit_of_measure"] == "1 Hour"
    assert result["items"][0]["arm_sku_name"] == "Standard_D2s_v5"


def test_lookup_sku_reservation_term_in_filter() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["filter"] = request.url.params.get("$filter")
        return httpx.Response(
            200,
            json={
                "Items": [
                    _make_item(
                        price=0.05,
                        uom="1 Hour",
                        price_type="Reservation",
                        reservation_term="1 Year",
                    )
                ],
                "NextPageLink": None,
            },
        )

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope", term="1yr"
        )

    assert "priceType eq 'Reservation'" in captured["filter"]
    assert "reservationTerm eq '1 Year'" in captured["filter"]
    assert result["items"][0]["reservation_term"] == "1 Year"


def test_lookup_sku_pagination() -> None:
    """Mock returns NextPageLink once. Assert second call is made and results combined."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        calls.append(url)
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={
                    "Items": [_make_item(price=0.10)],
                    "NextPageLink": "https://prices.azure.com/api/retail/prices?page=2",
                },
            )
        return httpx.Response(
            200,
            json={"Items": [_make_item(price=0.20)], "NextPageLink": None},
        )

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope"
        )

    assert len(calls) == 2
    assert "page=2" in calls[1]
    assert result["item_count"] == 2
    prices = sorted(item["retail_price"] for item in result["items"])
    assert prices == [0.10, 0.20]


def test_lookup_sku_pagination_capped() -> None:
    """If the API keeps returning NextPageLink, abort at the defensive cap."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={
                "Items": [_make_item(price=0.01 * call_count)],
                "NextPageLink": (
                    f"https://prices.azure.com/api/retail/prices?page={call_count + 1}"
                ),
            },
        )

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope"
        )

    assert call_count == pricing._MAX_PAGES
    assert result["item_count"] == pricing._MAX_PAGES


def test_lookup_sku_caching() -> None:
    """Call twice with the same args. Assert the second call is served from cache."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200, json={"Items": [_make_item()], "NextPageLink": None}
        )

    with _install_mock_transport(handler):
        pricing.pricing_lookup_sku(sku="Standard_D2s_v5", region="westeurope")
        pricing.pricing_lookup_sku(sku="Standard_D2s_v5", region="westeurope")

    assert call_count == 1


def test_lookup_sku_cache_currency_isolation() -> None:
    """Different currency should not collide on the cache key."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200, json={"Items": [_make_item()], "NextPageLink": None}
        )

    with _install_mock_transport(handler):
        pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope", currency="USD"
        )
        pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope", currency="EUR"
        )

    assert call_count == 2


def test_lookup_sku_empty_results() -> None:
    """Empty Items should produce an empty items list, not an error."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_NotARealSku", region="westeurope"
        )

    assert result["items"] == []
    assert result["item_count"] == 0


def test_lookup_sku_invalid_term_raises() -> None:
    with pytest.raises(ValueError, match="Unknown term"):
        pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5", region="westeurope", term="lifetime"  # type: ignore[arg-type]
        )


def test_odata_escape_handles_single_quote() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["filter"] = request.url.params.get("$filter")
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    with _install_mock_transport(handler):
        pricing.pricing_lookup_sku(sku="Foo'Bar", region="westeurope")

    assert "Foo''Bar" in captured["filter"]


def test_compare_skus_combines_results() -> None:
    """compare_skus should call lookup per SKU and assemble a comparison table."""

    def handler(request: httpx.Request) -> httpx.Response:
        sku_clause = request.url.params.get("$filter") or ""
        if "D2s_v5" in sku_clause:
            return httpx.Response(
                200,
                json={"Items": [_make_item("Standard_D2s_v5", price=0.096)],
                      "NextPageLink": None},
            )
        if "D4s_v5" in sku_clause:
            return httpx.Response(
                200,
                json={"Items": [_make_item("Standard_D4s_v5", price=0.192)],
                      "NextPageLink": None},
            )
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    with _install_mock_transport(handler):
        result = pricing.pricing_compare_skus(
            skus=["Standard_D2s_v5", "Standard_D4s_v5"], region="westeurope"
        )

    assert result["region"] == "westeurope"
    assert len(result["comparison"]) == 2
    rows = {row["sku"]: row for row in result["comparison"]}
    assert rows["Standard_D2s_v5"]["found"] is True
    assert rows["Standard_D2s_v5"]["hourly"] == pytest.approx(0.096)
    assert rows["Standard_D2s_v5"]["monthly_730h"] == pytest.approx(0.096 * 730, rel=1e-3)
    assert rows["Standard_D4s_v5"]["hourly"] == pytest.approx(0.192)


def test_compare_skus_marks_missing_sku() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    with _install_mock_transport(handler):
        result = pricing.pricing_compare_skus(
            skus=["Standard_NotReal"], region="westeurope"
        )

    row = result["comparison"][0]
    assert row["found"] is False
    assert row["unit_price"] is None
    assert row["hourly"] is None
    assert row["monthly_730h"] is None


def test_compare_skus_size_cap() -> None:
    too_many = [f"Standard_X{i}" for i in range(11)]
    with pytest.raises(ValueError, match="cap"):
        pricing.pricing_compare_skus(skus=too_many, region="westeurope")


def test_compare_skus_empty_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        pricing.pricing_compare_skus(skus=[], region="westeurope")


def test_no_httpx_at_pricing_module_top() -> None:
    """The pricing module by itself must not pull httpx into sys.modules.

    Cold-start guard: httpx is only allowed to load when a tool is actually
    invoked from the pricing module, not when the module is imported. The
    server module separately depends on FastMCP, which transitively loads
    httpx; that is outside this module's control. Run in a subprocess so we
    do not perturb sys.modules in the current test session.
    """
    import subprocess

    code = (
        "import sys\n"
        "import mcp_server_azure_architect.pricing  # noqa: F401\n"
        "assert 'httpx' not in sys.modules, "
        "'httpx must not load at pricing module import time'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"subprocess failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_server_registers_pricing_tools() -> None:
    """The MCP server should expose both pricing tools with valid metadata."""
    from mcp_server_azure_architect.server import mcp as server_mcp

    tools = server_mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}

    assert "pricing_lookup_sku" in names
    assert "pricing_compare_skus" in names

    lookup_tool = next(t for t in tools if t.name == "pricing_lookup_sku")
    assert lookup_tool.description is not None
    assert "retail" in lookup_tool.description.lower()


def test_pricing_lookup_sku_via_server_tool() -> None:
    """Exercise the MCP-registered pricing_lookup_sku end to end."""
    from mcp_server_azure_architect.server import pricing_lookup_sku as server_tool

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"Items": [_make_item()], "NextPageLink": None}
        )

    with _install_mock_transport(handler):
        result = server_tool(sku="Standard_D2s_v5", region="westeurope")

    assert result["item_count"] == 1
    assert result["items"][0]["arm_sku_name"] == "Standard_D2s_v5"
