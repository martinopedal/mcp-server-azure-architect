"""Tests for azure_client helpers including scope validation."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from mcp_server_azure_architect.azure_client import (
    scrub_subscription_id,
    token_scrub,
    validate_caller_scope,
)


def test_token_scrub_removes_jwt() -> None:
    """JWT tokens are redacted."""
    text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    scrubbed = token_scrub(text)
    assert "[REDACTED_TOKEN]" in scrubbed
    assert "eyJ" not in scrubbed


def test_token_scrub_removes_long_base64() -> None:
    """Long base64-like strings (potential keys) are redacted."""
    text = "Key: ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=="
    scrubbed = token_scrub(text)
    assert "[REDACTED_KEY]" in scrubbed
    assert "ABCDEFGHIJKLMNOP" not in scrubbed


def test_scrub_subscription_id_redacts_most_of_guid() -> None:
    """Subscription ID is partially redacted for safe logging."""
    sub_id = "12345678-abcd-ef12-3456-abcdefabcdef"
    scrubbed = scrub_subscription_id(sub_id)
    assert scrubbed == "12345678-****-****-****-************"


def test_scrub_subscription_id_short_string() -> None:
    """Short strings are handled gracefully."""
    scrubbed = scrub_subscription_id("short")
    assert "****" in scrubbed


def test_validate_caller_scope_accepts_valid_subscription() -> None:
    """Subscription in the authorized list passes validation."""
    mock_credential = Mock()

    # Mock SubscriptionClient.subscriptions.list()
    mock_sub1 = Mock()
    mock_sub1.subscription_id = "valid-sub-1"
    mock_sub2 = Mock()
    mock_sub2.subscription_id = "valid-sub-2"

    with patch("azure.mgmt.subscription.SubscriptionClient") as mock_client_class:
        mock_client = Mock()
        mock_client.subscriptions.list.return_value = [mock_sub1, mock_sub2]
        mock_client_class.return_value = mock_client

        # Clear cache to ensure fresh enumeration
        from mcp_server_azure_architect.azure_client import _authorized_subscriptions

        _authorized_subscriptions.clear()

        result = validate_caller_scope("valid-sub-1", mock_credential)
        assert result is True

        # Verify subscription list was called
        mock_client.subscriptions.list.assert_called_once()


def test_validate_caller_scope_rejects_invalid_subscription() -> None:
    """Subscription not in the authorized list fails validation."""
    mock_credential = Mock()

    mock_sub1 = Mock()
    mock_sub1.subscription_id = "valid-sub-1"

    with patch("azure.mgmt.subscription.SubscriptionClient") as mock_client_class:
        mock_client = Mock()
        mock_client.subscriptions.list.return_value = [mock_sub1]
        mock_client_class.return_value = mock_client

        from mcp_server_azure_architect.azure_client import _authorized_subscriptions

        _authorized_subscriptions.clear()

        result = validate_caller_scope("invalid-sub-xyz", mock_credential)
        assert result is False


def test_validate_caller_scope_caches_subscription_list() -> None:
    """Subscription list is cached per credential to avoid repeated ARM calls."""
    mock_credential = Mock()

    mock_sub1 = Mock()
    mock_sub1.subscription_id = "valid-sub-1"

    with patch("azure.mgmt.subscription.SubscriptionClient") as mock_client_class:
        mock_client = Mock()
        mock_client.subscriptions.list.return_value = [mock_sub1]
        mock_client_class.return_value = mock_client

        from mcp_server_azure_architect.azure_client import _authorized_subscriptions

        _authorized_subscriptions.clear()

        # First call: should query ARM
        result1 = validate_caller_scope("valid-sub-1", mock_credential)
        assert result1 is True
        assert mock_client.subscriptions.list.call_count == 1

        # Second call with same credential: should use cache
        result2 = validate_caller_scope("valid-sub-1", mock_credential)
        assert result2 is True
        assert mock_client.subscriptions.list.call_count == 1  # Not called again


def test_validate_caller_scope_propagates_arm_errors() -> None:
    """ARM API errors are propagated to the caller."""
    mock_credential = Mock()

    with patch("azure.mgmt.subscription.SubscriptionClient") as mock_client_class:
        mock_client = Mock()
        mock_client.subscriptions.list.side_effect = Exception("ARM API unavailable")
        mock_client_class.return_value = mock_client

        from mcp_server_azure_architect.azure_client import _authorized_subscriptions

        _authorized_subscriptions.clear()

        with pytest.raises(Exception) as excinfo:
            validate_caller_scope("any-sub", mock_credential)

        assert "ARM API unavailable" in str(excinfo.value)


def test_validate_caller_scope_handles_none_subscription_ids() -> None:
    """Subscriptions with None ID are handled gracefully."""
    mock_credential = Mock()

    mock_sub1 = Mock()
    mock_sub1.subscription_id = "valid-sub-1"
    mock_sub2 = Mock()
    mock_sub2.subscription_id = None  # ARM can return subscriptions with no ID

    with patch("azure.mgmt.subscription.SubscriptionClient") as mock_client_class:
        mock_client = Mock()
        mock_client.subscriptions.list.return_value = [mock_sub1, mock_sub2]
        mock_client_class.return_value = mock_client

        from mcp_server_azure_architect.azure_client import _authorized_subscriptions

        _authorized_subscriptions.clear()

        result = validate_caller_scope("valid-sub-1", mock_credential)
        assert result is True
