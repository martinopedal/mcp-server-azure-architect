"""Tests for log file permissions."""

import os
import platform
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_server_azure_architect.audit import (
    _check_directory_permissions,
    _set_file_permissions_0600,
    setup_audit_logging,
)


@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only test")
def test_set_file_permissions_0600_posix(tmp_path: Path) -> None:
    """Test that file permissions are set to 0600 on POSIX systems."""
    test_file = tmp_path / "test.log"
    test_file.touch()

    # Set permissions
    _set_file_permissions_0600(test_file)

    # Check permissions
    file_stat = os.stat(test_file)
    file_mode = stat.S_IMODE(file_stat.st_mode)

    assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-only test")
def test_set_file_permissions_0600_windows(tmp_path: Path) -> None:
    """Test that file permissions are restricted on Windows (smoke test)."""
    test_file = tmp_path / "test.log"
    test_file.touch()

    # This is a smoke test - on Windows we just verify the function doesn't crash
    # Actual ACL verification would require pywin32 or parsing icacls output
    _set_file_permissions_0600(test_file)

    # File should still exist
    assert test_file.exists()


@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only test")
def test_check_directory_permissions_warns_on_permissive(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that warning is logged for permissive directory permissions."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Set permissive permissions (0777)
    os.chmod(test_dir, 0o777)

    with caplog.at_level("WARNING"):
        _check_directory_permissions(test_dir)

    assert "has permissive permissions" in caplog.text


@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only test")
def test_check_directory_permissions_no_warn_on_0700(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Test that no warning is logged for secure directory permissions."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()

    # Set secure permissions (0700)
    os.chmod(test_dir, 0o700)

    with caplog.at_level("WARNING"):
        _check_directory_permissions(test_dir)

    assert "has permissive permissions" not in caplog.text


@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only test")
def test_setup_audit_logging_creates_secure_directory(tmp_path: Path) -> None:
    """Test that audit log directory is created with 0700 permissions."""
    log_dir = tmp_path / "secure_logs"

    with patch.dict(os.environ, {"MCP_AZURE_ARCHITECT_LOG_DIR": str(log_dir)}):
        # Reset global logger
        import mcp_server_azure_architect.audit
        mcp_server_azure_architect.audit._AUDIT_LOGGER = None

        setup_audit_logging()

        # Check directory permissions
        dir_stat = os.stat(log_dir)
        dir_mode = stat.S_IMODE(dir_stat.st_mode)

        assert dir_mode == 0o700, f"Expected 0700, got {oct(dir_mode)}"


@pytest.mark.skipif(platform.system() == "Windows", reason="POSIX-only test")
def test_setup_audit_logging_creates_secure_file(tmp_path: Path) -> None:
    """Test that audit log file is created with 0600 permissions."""
    log_dir = tmp_path / "secure_logs"

    with patch.dict(os.environ, {"MCP_AZURE_ARCHITECT_LOG_DIR": str(log_dir)}):
        # Reset global logger
        import mcp_server_azure_architect.audit
        mcp_server_azure_architect.audit._AUDIT_LOGGER = None

        setup_audit_logging()

        # Check file permissions
        log_file = log_dir / "audit.log"
        file_stat = os.stat(log_file)
        file_mode = stat.S_IMODE(file_stat.st_mode)

        assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"


def test_setup_audit_logging_windows_smoke(tmp_path: Path) -> None:
    """Test that audit logging setup works on Windows (smoke test)."""
    log_dir = tmp_path / "logs"

    with patch.dict(os.environ, {"MCP_AZURE_ARCHITECT_LOG_DIR": str(log_dir)}):
        # Reset global logger
        import mcp_server_azure_architect.audit
        mcp_server_azure_architect.audit._AUDIT_LOGGER = None

        setup_audit_logging()

        # Verify files exist (actual permission checking would require icacls parsing)
        assert log_dir.exists()
        assert (log_dir / "audit.log").exists()
