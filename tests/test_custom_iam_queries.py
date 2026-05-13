"""Tests for custom IAM drift queries (issue #99, ADR-006)."""

from collections.abc import Iterator

import pytest

from mcp_server_azure_architect import alz_queries


CUSTOM_GUIDS = [
    "06f994c5-0074-437a-8fe7-76ad7270c02b",
    "464f1e97-148f-4250-a716-d22b289bac41",
    "bc5a2107-737a-4f9a-bd70-680c9ed28b8b",
    "decc6b2b-9a5b-4261-a2f7-eac632b550fe",
    "fe60141f-7d13-4ad5-90f0-cbf5d2ee249f",
]


@pytest.fixture(autouse=True)
def _reset_cache() -> Iterator[None]:
    alz_queries.reset_cache()
    yield
    alz_queries.reset_cache()


def test_custom_source_returns_all_five() -> None:
    result = alz_queries.list_queries(source="custom")
    assert result["count"] == 5
    assert {item["checklist_id"] for item in result["items"]} == set(CUSTOM_GUIDS)


def test_custom_queries_have_adr_006_provenance() -> None:
    for guid in CUSTOM_GUIDS:
        record = alz_queries.get_query(guid)
        assert record["source"] == "custom"
        assert record["source_commit"] == ""  # ADR-006 sentinel
        assert record["source_repo"] == "martinopedal/mcp-server-azure-architect"
        assert "issue #99" in record["citation"]
        assert "ADR-006" in record["citation"]


def test_custom_queries_load_kql_bodies() -> None:
    for guid in CUSTOM_GUIDS:
        record = alz_queries.get_query(guid)
        assert record["kql"], f"{guid} has empty KQL body"
        assert record["kql"].startswith("// Custom query authored")


def test_custom_queries_categorized_under_identity() -> None:
    for guid in CUSTOM_GUIDS:
        record = alz_queries.get_query(guid)
        assert record["category"] == "Identity and Access Management"
        assert record["queryable"] is True


def test_filter_by_identity_category_includes_custom() -> None:
    result = alz_queries.list_queries(category="Identity and Access Management")
    custom_in_result = [item for item in result["items"] if item["source"] == "custom"]
    assert len(custom_in_result) == 5
