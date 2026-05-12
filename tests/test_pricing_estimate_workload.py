"""Tests for pricing_estimate_workload tool."""

from __future__ import annotations

from decimal import Decimal
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


def test_estimate_workload_happy_path_vms_and_storage() -> None:
    """Mock 2 VMs + 1 disk; assert deterministic total and line items."""

    def handler(request: httpx.Request) -> httpx.Response:
        filter_param = request.url.params.get("$filter") or ""
        if "D2s_v5" in filter_param:
            return httpx.Response(
                200,
                json={
                    "Items": [_make_item("Standard_D2s_v5", price=0.096)],
                    "NextPageLink": None,
                },
            )
        if "D4s_v5" in filter_param:
            return httpx.Response(
                200,
                json={
                    "Items": [_make_item("Standard_D4s_v5", price=0.192)],
                    "NextPageLink": None,
                },
            )
        if "Premium_LRS" in filter_param or "PremiumLRS" in filter_param:
            return httpx.Response(
                200,
                json={
                    "Items": [
                        _make_item(
                            "Premium_LRS",
                            price=0.15,
                            uom="1 GB/Month",
                        )
                    ],
                    "NextPageLink": None,
                },
            )
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    spec = pricing.WorkloadSpec(
        region="westeurope",
        vms=[
            pricing.VmGroup(sku="Standard_D2s_v5", count=2, hours_per_month=730),
            pricing.VmGroup(sku="Standard_D4s_v5", count=1, hours_per_month=730),
        ],
        storage=[
            pricing.StorageItem(sku="Premium_LRS", capacity_gb=1024, region_override=None),
        ],
        currency="USD",
    )

    with _install_mock_transport(handler):
        result = pricing.pricing_estimate_workload(spec)

    assert result["currency"] == "USD"
    assert len(result["line_items"]) == 3

    line_items = result["line_items"]
    d2s_items = [li for li in line_items if li["sku"] == "Standard_D2s_v5"]
    d4s_items = [li for li in line_items if li["sku"] == "Standard_D4s_v5"]
    storage_items = [li for li in line_items if li["sku"] == "Premium_LRS"]

    assert len(d2s_items) == 1
    assert d2s_items[0]["region"] == "westeurope"
    assert d2s_items[0]["quantity"] == 2 * 730
    assert d2s_items[0]["unit_price"] == Decimal("0.096")
    assert d2s_items[0]["monthly_cost"] == Decimal("0.096") * 2 * 730

    assert len(d4s_items) == 1
    assert d4s_items[0]["monthly_cost"] == Decimal("0.192") * 1 * 730

    assert len(storage_items) == 1
    assert storage_items[0]["quantity"] == 1024
    assert storage_items[0]["unit_price"] == Decimal("0.15")
    assert storage_items[0]["monthly_cost"] == Decimal("0.15") * 1024

    expected_total = (
        Decimal("0.096") * 2 * 730 + Decimal("0.192") * 1 * 730 + Decimal("0.15") * 1024
    )
    assert result["total_monthly"] == expected_total

    assert len(result["assumptions"]) > 0
    assert any("hourly" in a.lower() for a in result["assumptions"])
    assert result["warnings"] == []


def test_estimate_workload_sku_not_found_warning() -> None:
    """If SKU not found, record warning and do not raise."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    spec = pricing.WorkloadSpec(
        region="westeurope",
        vms=[pricing.VmGroup(sku="Standard_NotReal", count=1, hours_per_month=730)],
        currency="USD",
    )

    with _install_mock_transport(handler):
        result = pricing.pricing_estimate_workload(spec)

    assert result["total_monthly"] == Decimal("0")
    assert result["line_items"] == []
    assert len(result["warnings"]) == 1
    assert "Standard_NotReal" in result["warnings"][0]
    assert "not found" in result["warnings"][0]


def test_estimate_workload_multi_region_storage() -> None:
    """Storage in different region than VMs via region_override."""

    def handler(request: httpx.Request) -> httpx.Response:
        filter_param = request.url.params.get("$filter") or ""
        if "westeurope" in filter_param:
            return httpx.Response(
                200,
                json={
                    "Items": [_make_item("Standard_D2s_v5", region="westeurope", price=0.096)],
                    "NextPageLink": None,
                },
            )
        if "eastus" in filter_param:
            return httpx.Response(
                200,
                json={
                    "Items": [
                        _make_item(
                            "Premium_LRS",
                            region="eastus",
                            price=0.10,
                            uom="1 GB/Month",
                        )
                    ],
                    "NextPageLink": None,
                },
            )
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    spec = pricing.WorkloadSpec(
        region="westeurope",
        vms=[pricing.VmGroup(sku="Standard_D2s_v5", count=1, hours_per_month=730)],
        storage=[pricing.StorageItem(sku="Premium_LRS", capacity_gb=512, region_override="eastus")],
        currency="USD",
    )

    with _install_mock_transport(handler):
        result = pricing.pricing_estimate_workload(spec)

    line_items = result["line_items"]
    vm_items = [li for li in line_items if li["sku"] == "Standard_D2s_v5"]
    storage_items = [li for li in line_items if li["sku"] == "Premium_LRS"]

    assert vm_items[0]["region"] == "westeurope"
    assert storage_items[0]["region"] == "eastus"


def test_estimate_workload_non_hourly_vm_warning() -> None:
    """If VM meter is not hourly, record warning and skip."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "Items": [_make_item("Standard_D2s_v5", price=0.096, uom="1 Month")],
                "NextPageLink": None,
            },
        )

    spec = pricing.WorkloadSpec(
        region="westeurope",
        vms=[pricing.VmGroup(sku="Standard_D2s_v5", count=1, hours_per_month=730)],
        currency="USD",
    )

    with _install_mock_transport(handler):
        result = pricing.pricing_estimate_workload(spec)

    assert result["total_monthly"] == Decimal("0")
    assert result["line_items"] == []
    assert len(result["warnings"]) == 1
    assert "not hourly" in result["warnings"][0]
    assert "1 Month" in result["warnings"][0]


def test_estimate_workload_empty_spec() -> None:
    """Empty spec (no VMs, no storage) produces zero total."""
    spec = pricing.WorkloadSpec(region="westeurope", currency="USD")

    result = pricing.pricing_estimate_workload(spec)

    assert result["total_monthly"] == Decimal("0")
    assert result["line_items"] == []
    assert result["assumptions"] == []
    assert result["warnings"] == []


def test_estimate_workload_storage_no_unit_price() -> None:
    """If storage API item has no unit_price, record warning and skip."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "Items": [
                    {
                        "currencyCode": "USD",
                        "armSkuName": "Premium_LRS",
                        "armRegionName": "westeurope",
                        "unitPrice": None,
                        "unitOfMeasure": "1 GB/Month",
                    }
                ],
                "NextPageLink": None,
            },
        )

    spec = pricing.WorkloadSpec(
        region="westeurope",
        storage=[pricing.StorageItem(sku="Premium_LRS", capacity_gb=1024, region_override=None)],
        currency="USD",
    )

    with _install_mock_transport(handler):
        result = pricing.pricing_estimate_workload(spec)

    assert result["total_monthly"] == Decimal("0")
    assert result["line_items"] == []
    assert len(result["warnings"]) == 1
    assert "no valid unit_price" in result["warnings"][0]


def test_estimate_workload_via_server_tool() -> None:
    """Exercise the MCP-registered pricing_estimate_workload end to end."""
    from mcp_server_azure_architect.server import (
        pricing_estimate_workload as server_tool,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "Items": [_make_item("Standard_D2s_v5", price=0.096)],
                "NextPageLink": None,
            },
        )

    spec_dict = {
        "region": "westeurope",
        "vms": [{"sku": "Standard_D2s_v5", "count": 1, "hours_per_month": 730}],
        "currency": "USD",
    }

    with _install_mock_transport(handler):
        result = server_tool(spec=spec_dict)

    assert result["currency"] == "USD"
    assert len(result["line_items"]) == 1
    assert result["line_items"][0]["sku"] == "Standard_D2s_v5"


def test_server_registers_pricing_estimate_workload() -> None:
    """The MCP server should expose pricing_estimate_workload with valid metadata."""
    from mcp_server_azure_architect.server import mcp as server_mcp

    tools = server_mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}

    assert "pricing_estimate_workload" in names

    estimate_tool = next(t for t in tools if t.name == "pricing_estimate_workload")
    assert estimate_tool.description is not None
    assert "workload" in estimate_tool.description.lower()
