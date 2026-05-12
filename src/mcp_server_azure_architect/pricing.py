# READ-ONLY: this module performs HTTP GET against the public Azure Retail Prices API;
# no auth, no Azure SDK, no writes.
"""Native Azure retail pricing lookup tools.

Calls the public Azure Retail Prices API (https://prices.azure.com/api/retail/prices).
No authentication required. OData filter syntax. Paginated via NextPageLink.

Read-only by design (ADR-003): only HTTP GET against a public Microsoft endpoint.

Caveats surfaced in tool docstrings:
- Retail prices only. No EA, CSP, or private rate cards.
- USD default currency. The currencyCode parameter is forwarded to the API.
- No real-time freshness SLA from Microsoft.
- Reservation discounts only where Microsoft publishes them in the meter.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import httpx

PRICING_ENDPOINT = "https://prices.azure.com/api/retail/prices"

# 24-hour TTL per issue #39 spec. Key = OData filter string. Value = (expiry_ts, items).
_CACHE_TTL_SECONDS = 24 * 60 * 60
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

# Defensive cap: max pages followed via NextPageLink. Each page is up to 1000 items.
# Five pages tolerates 5000 SKU rows for a single filter, which is well above any
# realistic single-SKU lookup. Higher values risk runaway requests on broad filters.
_MAX_PAGES = 5

# Soft cap on number of SKUs that pricing_compare_skus accepts in one call.
_COMPARE_MAX_SKUS = 10


def _get_client() -> httpx.Client:
    """Lazily import httpx and construct a Client.

    Lazy import keeps cold-start budget clean: httpx is not loaded at server module
    import time, only when a pricing tool is actually invoked.
    """
    import httpx

    return httpx.Client(timeout=30.0, follow_redirects=True)


def _escape_odata_value(value: str) -> str:
    """Escape a string for safe inclusion inside an OData single-quoted literal.

    OData escapes single quotes by doubling them. Reference:
    https://learn.microsoft.com/odata/concepts/uri-conventions#literals
    """
    # readonly-allow: string method, not Azure SDK mutation
    return value.replace("'", "''")


def _normalize_term(term: str) -> tuple[str, str | None]:
    """Map a friendly term ('ondemand', '1yr', '3yr') to API filter values.

    Returns:
        (price_type, reservation_term) where reservation_term is None for ondemand.
    """
    t = term.lower().strip()
    if t in ("ondemand", "consumption", "payg", "on-demand"):
        return "Consumption", None
    if t in ("1yr", "1y", "1year", "1 year"):
        return "Reservation", "1 Year"
    if t in ("3yr", "3y", "3year", "3 years", "3 year"):
        return "Reservation", "3 Years"
    raise ValueError(
        f"Unknown term '{term}'. Expected one of: 'ondemand', '1yr', '3yr'."
    )


def _build_filter(sku: str, region: str, term: str) -> str:
    """Build an OData $filter string for a single-SKU lookup.

    The Retail Prices API is permissive about whether `sku` is the friendly
    `skuName` ('D2s v5') or the ARM-style `armSkuName` ('Standard_D2s_v5'). Match
    on `armSkuName` first because it is unambiguous; if the caller supplies a
    friendly name without the 'Standard_' prefix, also try `skuName` via OR.
    """
    sku_esc = _escape_odata_value(sku)
    region_esc = _escape_odata_value(region)
    price_type, reservation_term = _normalize_term(term)

    sku_clause = (
        f"(armSkuName eq '{sku_esc}' or skuName eq '{sku_esc}')"
    )
    parts = [
        sku_clause,
        f"armRegionName eq '{region_esc}'",
        f"priceType eq '{price_type}'",
    ]
    if reservation_term is not None:
        rt_esc = _escape_odata_value(reservation_term)
        parts.append(f"reservationTerm eq '{rt_esc}'")

    return " and ".join(parts)


def _cache_key(odata_filter: str, currency: str) -> str:
    return f"{currency}|{odata_filter}"


def _cache_get(key: str) -> list[dict[str, Any]] | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    expiry, items = entry
    if time.time() >= expiry:
        _CACHE.pop(key, None)
        return None
    return items


def _cache_put(key: str, items: list[dict[str, Any]]) -> None:
    _CACHE[key] = (time.time() + _CACHE_TTL_SECONDS, items)


def _fetch_all_pages(odata_filter: str, currency: str) -> list[dict[str, Any]]:
    """Fetch every page of results for the given filter, capped at _MAX_PAGES.

    Returns combined Items across pages.
    """
    items: list[dict[str, Any]] = []
    params: dict[str, str] | None = {
        "$filter": odata_filter,
        "currencyCode": currency,
    }
    url: str = PRICING_ENDPOINT
    pages = 0

    with _get_client() as client:
        while url and pages < _MAX_PAGES:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            page_items = payload.get("Items", []) or []
            items.extend(page_items)
            next_link = payload.get("NextPageLink")
            if not next_link:
                break
            url = next_link
            params = None
            pages += 1

    return items


def _fetch_with_cache(odata_filter: str, currency: str) -> list[dict[str, Any]]:
    key = _cache_key(odata_filter, currency)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    items = _fetch_all_pages(odata_filter, currency)
    _cache_put(key, items)
    return items


def _shape_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Project the raw API record into a stable, documented shape."""
    return {
        "retail_price": raw.get("retailPrice"),
        "unit_price": raw.get("unitPrice"),
        "currency_code": raw.get("currencyCode"),
        "unit_of_measure": raw.get("unitOfMeasure"),
        "meter_id": raw.get("meterId"),
        "meter_name": raw.get("meterName"),
        "product_name": raw.get("productName"),
        "service_name": raw.get("serviceName"),
        "service_family": raw.get("serviceFamily"),
        "arm_sku_name": raw.get("armSkuName"),
        "sku_name": raw.get("skuName"),
        "arm_region_name": raw.get("armRegionName"),
        "location": raw.get("location"),
        "price_type": raw.get("type") or raw.get("priceType"),
        "reservation_term": raw.get("reservationTerm"),
        "effective_start_date": raw.get("effectiveStartDate"),
    }


def pricing_lookup_sku(
    sku: str,
    region: str,
    term: Literal["ondemand", "1yr", "3yr"] = "ondemand",
    currency: str = "USD",
) -> dict[str, Any]:
    """Look up retail pricing for a single Azure SKU in a region.

    Calls the public Azure Retail Prices API. No authentication is used and no
    Azure SDK call is made. Read-only by design (ADR-003).

    Args:
        sku: SKU name. Either ARM form ('Standard_D2s_v5') or friendly form
            ('D2s v5'). The filter matches both.
        region: ARM region name, lower-case ('westeurope', 'eastus2', etc.).
        term: Pricing term. 'ondemand' for Consumption (PAYG). '1yr' or '3yr'
            for Reservation pricing where Microsoft publishes it.
        currency: ISO currency code. Defaults to 'USD'. Forwarded to the API
            via the currencyCode query parameter.

    Returns:
        Dict with the original inputs plus an ``items`` list of pricing rows.
        Each item exposes retail_price, unit_price, unit_of_measure, meter_id,
        and other fields documented in the API reference. Empty ``items`` means
        the SKU was not found for the region/term combination; this is not an
        error.

    Caveats:
        - Retail prices only. EA, CSP, and private rate cards are not exposed.
        - USD default. Pass ``currency`` for other ISO codes supported by the API.
        - No real-time freshness SLA from Microsoft. Results are cached for 24h.
        - Reservation rows appear only where Microsoft publishes them in the meter.

    Reference:
        https://learn.microsoft.com/rest/api/cost-management/retail-prices/azure-retail-prices
    """
    odata_filter = _build_filter(sku, region, term)
    raw_items = _fetch_with_cache(odata_filter, currency)
    items = [_shape_item(r) for r in raw_items]
    source_url = f"{PRICING_ENDPOINT}?$filter={odata_filter}&currencyCode={currency}"
    return {
        "sku": sku,
        "region": region,
        "term": term,
        "currency": currency,
        "items": items,
        "item_count": len(items),
        "cached_at": int(time.time()),
        "source_url": source_url,
    }


def _hourly_from_unit(unit_price: Any, unit_of_measure: str | None) -> float | None:
    """Best-effort conversion of a metered unit price to an hourly rate.

    Many compute SKUs are metered as '1 Hour'. Some are '100 Hours' or '10 Hours'.
    Storage and most other meters are not hourly and return None. The caller
    should display unit_of_measure alongside any derived hourly figure so the
    user can sanity-check.
    """
    if unit_price is None or unit_of_measure is None:
        return None
    uom = unit_of_measure.strip().lower()
    try:
        price = float(unit_price)
    except (TypeError, ValueError):
        return None
    if uom in ("1 hour", "hour"):
        return price
    if uom == "100 hours":
        return price / 100.0
    if uom == "10 hours":
        return price / 10.0
    if uom == "1000 hours":
        return price / 1000.0
    return None


def pricing_compare_skus(
    skus: list[str],
    region: str,
    term: str = "ondemand",
    currency: str = "USD",
) -> dict[str, Any]:
    """Compare retail pricing for multiple SKUs side by side in one region.

    Calls ``pricing_lookup_sku`` per SKU and assembles a comparison table.
    Designed for sizing trade-off review and for the future design-review skill
    to compare candidate options in a single response.

    Args:
        skus: SKU names to compare. Capped at 10 entries to bound the API
            response size. Pass fewer than 10 for typical sizing review.
        region: ARM region name, lower-case.
        term: 'ondemand', '1yr', or '3yr'. See ``pricing_lookup_sku``.
        currency: ISO currency code. Defaults to 'USD'.

    Returns:
        Dict with region, term, currency, and a ``comparison`` list. Each entry
        carries the SKU, a representative item (cheapest unit_price seen for
        that SKU/region/term), and a derived ``hourly`` and ``monthly_730h``
        figure where the meter is hourly. Items whose meter is not hourly
        report hourly/monthly as None and the caller should consult
        unit_of_measure.

    Raises:
        ValueError: If ``skus`` is empty or exceeds the 10-SKU cap.
    """
    if not skus:
        raise ValueError("skus must contain at least one entry.")
    if len(skus) > _COMPARE_MAX_SKUS:
        raise ValueError(
            f"skus exceeds the {_COMPARE_MAX_SKUS}-entry cap (got {len(skus)}). "
            f"Split the request to keep responses bounded."
        )

    comparison: list[dict[str, Any]] = []
    for sku in skus:
        result = pricing_lookup_sku(
            sku=sku,
            region=region,
            term=term,  # type: ignore[arg-type]
            currency=currency,
        )
        items = result["items"]
        cheapest: dict[str, Any] | None = None
        for item in items:
            price = item.get("unit_price")
            if price is None:
                continue
            if cheapest is None or float(price) < float(cheapest["unit_price"]):
                cheapest = item

        hourly = (
            _hourly_from_unit(cheapest["unit_price"], cheapest.get("unit_of_measure"))
            if cheapest is not None
            else None
        )
        monthly = round(hourly * 730.0, 4) if hourly is not None else None

        comparison.append(
            {
                "sku": sku,
                "found": cheapest is not None,
                "unit_price": cheapest["unit_price"] if cheapest else None,
                "unit_of_measure": cheapest.get("unit_of_measure") if cheapest else None,
                "currency_code": cheapest.get("currency_code") if cheapest else currency,
                "meter_id": cheapest.get("meter_id") if cheapest else None,
                "product_name": cheapest.get("product_name") if cheapest else None,
                "hourly": hourly,
                "monthly_730h": monthly,
                "item_count": len(items),
            }
        )

    return {
        "region": region,
        "term": term,
        "currency": currency,
        "comparison": comparison,
        "notes": (
            "monthly_730h uses the standard 730-hour month convention. "
            "Items whose meter is not hourly report hourly/monthly as null; "
            "consult unit_of_measure. Retail prices only (no EA/CSP)."
        ),
    }


def _clear_cache_for_tests() -> None:
    """Test helper. Not exported as an MCP tool."""
    _CACHE.clear()
