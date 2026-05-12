"""Regression test for issue #88 - OData-escape currency parameter."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from mcp_server_azure_architect import pricing


@pytest.fixture(autouse=True)
def _clear_pricing_cache() -> None:
    pricing._clear_cache_for_tests()


def _install_mock_transport(
    handler: Any,
) -> Any:
    """Patch pricing._get_client to return an httpx.Client backed by MockTransport."""
    transport = httpx.MockTransport(handler)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport)

    return patch.object(pricing, "_get_client", _factory)


def test_currency_escaped_in_source_url() -> None:
    """Currency parameter must be OData-escaped when interpolated into source_url.

    Regression test for issue #88. The source_url returned by pricing_lookup_sku
    interpolates the currency parameter directly. If the currency contains a single
    quote, it must be doubled per OData URI conventions for consistency with how
    other parameters (sku, region) are escaped.
    """
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"Items": [], "NextPageLink": None})

    with _install_mock_transport(handler):
        result = pricing.pricing_lookup_sku(
            sku="Standard_D2s_v5",
            region="westeurope",
            currency="USD'OR 1=1",
        )

    # The source_url in the result should have the escaped currency
    assert "currencyCode=USD''OR 1=1" in result["source_url"], (
        f"Expected escaped currency in source_url. Got: {result['source_url']}"
    )
