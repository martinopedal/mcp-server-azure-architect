"""Tests for audit logging functionality."""

import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_server_azure_architect.audit import (
    audit_log_tool,
    setup_audit_logging,
    token_scrub,
)


def test_token_scrub_subscription_id() -> None:
    """Test that subscription_id GUIDs are redacted."""
    input_text = "subscription_id: abc12345-6789-1234-5678-123456789012"
    result = token_scrub(input_text)
    assert "abc12345-****-****-****-************" in result
    assert "6789" not in result


def test_token_scrub_tenant_id() -> None:
    """Test that tenant_id GUIDs are redacted."""
    input_text = "tenant_id=def98765-4321-9876-5432-098765432109"
    result = token_scrub(input_text)
    assert "def98765-****-****-****-************" in result
    assert "4321" not in result


def test_token_scrub_jwt_token() -> None:
    """Test that JWT tokens are redacted."""
    input_text = "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkw.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    result = token_scrub(input_text)
    assert "[REDACTED_TOKEN]" in result
    assert "eyJhbGciOiJSUzI1NiIsInR5cCI" not in result


def test_token_scrub_base64_key() -> None:
    """Test that long base64 keys are redacted."""
    input_text = "key: dGhpc2lzYXZlcnlsb25nYmFzZTY0ZW5jb2RlZGtleXRoYXRzaG91bGRiZXJlZGFjdGVk"
    result = token_scrub(input_text)
    assert "[REDACTED_KEY]" in result
    assert "dGhpc2lzYXZlcnlsb25nYmFzZTY0ZW5jb2RlZGtleXRoYXRzaG91bGRiZXJlZGFjdGVk" not in result


def test_token_scrub_bearer_token() -> None:
    """Test that Bearer tokens are redacted."""
    input_text = "Authorization: Bearer abc123xyz456"
    result = token_scrub(input_text)
    assert "Bearer [REDACTED_TOKEN]" in result
    assert "abc123xyz456" not in result


def test_token_scrub_dict() -> None:
    """Test that token scrubbing works on dictionaries."""
    input_dict = {
        "subscription_id": "12345678-1234-1234-1234-123456789012",
        "name": "my-resource",
        "tenant_id": "87654321-4321-4321-4321-210987654321",
    }
    result = token_scrub(input_dict)
    assert result["subscription_id"] == "12345678-****-****-****-************"
    assert result["name"] == "my-resource"
    assert result["tenant_id"] == "87654321-****-****-****-************"


def test_token_scrub_list() -> None:
    """Test that token scrubbing works on lists."""
    input_list = [
        "sub: 11111111-2222-3333-4444-555555555555",
        "normal text",
    ]
    result = token_scrub(input_list)
    assert result[0] == "sub: 11111111-****-****-****-************"
    assert result[1] == "normal text"


def test_audit_log_tool_sync() -> None:
    """Test audit logging decorator on synchronous function."""

    @audit_log_tool
    def sample_tool(name: str, count: int) -> dict[str, str]:
        return {"result": f"{name}_{count}"}

    with patch("mcp_server_azure_architect.audit.get_audit_logger") as mock_logger:
        mock_info = mock_logger.return_value.info
        result = sample_tool("test", 42)

        assert result == {"result": "test_42"}
        # Verify logger was called (info for invocation + info for result)
        assert mock_info.call_count == 2


@pytest.mark.asyncio
async def test_audit_log_tool_async() -> None:
    """Test audit logging decorator on async function."""

    @audit_log_tool
    async def sample_async_tool(name: str) -> dict[str, str]:
        return {"result": name}

    with patch("mcp_server_azure_architect.audit.get_audit_logger") as mock_logger:
        mock_info = mock_logger.return_value.info
        result = await sample_async_tool("async_test")

        assert result == {"result": "async_test"}
        assert mock_info.call_count == 2


def test_audit_log_tool_with_redaction() -> None:
    """Test that audit logging redacts sensitive parameters."""

    @audit_log_tool
    def tool_with_sensitive_params(subscription_id: str, name: str) -> dict[str, str]:
        return {"status": "ok"}

    with patch("mcp_server_azure_architect.audit.get_audit_logger") as mock_logger:
        logger_instance = logging.getLogger("test")
        mock_logger.return_value = logger_instance

        # Capture logged messages
        logged_messages: list[str] = []

        def capture_info(msg: str) -> None:
            logged_messages.append(msg)

        # Use type ignore for method assignment in test
        logger_instance.info = capture_info  # type: ignore[method-assign]

        result = tool_with_sensitive_params(
            subscription_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            name="test-resource",
        )

        assert result == {"status": "ok"}
        assert len(logged_messages) == 2

        # Check that subscription_id was redacted in the invocation log
        invocation_log = json.loads(logged_messages[0])
        assert "aaaaaaaa-****-****-****-************" in invocation_log["params"]["subscription_id"]
        assert "bbbb" not in invocation_log["params"]["subscription_id"]


def test_audit_log_tool_error_handling() -> None:
    """Test that audit logging captures errors."""

    @audit_log_tool
    def failing_tool(name: str) -> dict[str, str]:
        raise ValueError("Test error")

    with patch("mcp_server_azure_architect.audit.get_audit_logger") as mock_logger:
        mock_error = mock_logger.return_value.error

        with pytest.raises(ValueError, match="Test error"):
            failing_tool("test")

        # Verify error was logged
        assert mock_error.call_count == 1


def test_setup_audit_logging_creates_directory(tmp_path: Path) -> None:
    """Test that setup_audit_logging creates log directory."""
    log_dir = tmp_path / "test_logs"

    with patch.dict(os.environ, {"MCP_AZURE_ARCHITECT_LOG_DIR": str(log_dir)}):
        # Reset global logger
        import mcp_server_azure_architect.audit
        mcp_server_azure_architect.audit._AUDIT_LOGGER = None

        setup_audit_logging()

        assert log_dir.exists()
        assert (log_dir / "audit.log").exists()


def test_setup_audit_logging_respects_env_var(tmp_path: Path) -> None:
    """Test that log directory can be overridden via environment variable."""
    custom_log_dir = tmp_path / "custom_logs"

    with patch.dict(os.environ, {"MCP_AZURE_ARCHITECT_LOG_DIR": str(custom_log_dir)}):
        import mcp_server_azure_architect.audit
        mcp_server_azure_architect.audit._AUDIT_LOGGER = None

        setup_audit_logging()

        assert custom_log_dir.exists()
        assert (custom_log_dir / "audit.log").exists()
