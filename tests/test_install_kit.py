"""
Tests for scripts/install_kit.py.

Coverage:
- Prerequisites detection (mocked subprocess calls)
- Config file generation per client (golden structure checks)
- Config merge preserves existing entries
- Collision prompts work in interactive/non-interactive modes
- Dry-run mode doesn't touch disk
"""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import the installer module from scripts/ (not on sys.path by default)
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import install_kit  # noqa: E402, I001


def test_check_python_version() -> None:
    """Test Python version check returns correct status."""
    ok, msg = install_kit.check_python_version()
    assert ok is True
    assert "Python 3." in msg


def test_check_command_available_exists() -> None:
    """Test command check when command exists."""
    with (
        patch("shutil.which", return_value="/usr/bin/python"),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="Python 3.11.0\n")
        ok, version = install_kit.check_command_available("python")
        assert ok is True
        assert "Python" in version


def test_check_command_available_missing() -> None:
    """Test command check when command is missing."""
    with patch("shutil.which", return_value=None):
        ok, msg = install_kit.check_command_available("nonexistent")
        assert ok is False
        assert msg == "not found"


def test_check_prerequisites() -> None:
    """Test prerequisites check returns all required items."""
    results = install_kit.check_prerequisites()
    assert "python" in results
    assert "node" in results
    assert "docker" in results
    assert "gh" in results
    assert results["python"][0] is True


def test_get_config_path_copilot_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config path resolution for Copilot CLI."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = install_kit.get_config_path("copilot-cli")
    assert path == tmp_path / ".copilot" / "mcp-config.json"


def test_get_config_path_claude_desktop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config path resolution for Claude Desktop (OS-specific)."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with patch("platform.system", return_value="Windows"):
        path = install_kit.get_config_path("claude-desktop")
        assert path == tmp_path / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"

    with patch("platform.system", return_value="Darwin"):
        path = install_kit.get_config_path("claude-desktop")
        assert (
            path
            == tmp_path
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )

    with patch("platform.system", return_value="Linux"):
        path = install_kit.get_config_path("claude-desktop")
        assert path == tmp_path / ".config" / "Claude" / "claude_desktop_config.json"


def test_get_config_path_cursor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config path resolution for Cursor."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = install_kit.get_config_path("cursor")
    assert path == tmp_path / ".cursor" / "mcp-config.json"


def test_get_config_path_vscode_copilot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test config path resolution for VS Code Copilot (same as copilot-cli)."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = install_kit.get_config_path("vscode-copilot")
    assert path == tmp_path / ".copilot" / "mcp-config.json"


def test_load_existing_config_missing(tmp_path: Path) -> None:
    """Test loading config when file doesn't exist returns empty template."""
    config_path = tmp_path / "missing.json"
    config = install_kit.load_existing_config(config_path)
    assert config == {"$schema": "https://aka.ms/mcp-config-schema", "mcpServers": {}}


def test_load_existing_config_valid(tmp_path: Path) -> None:
    """Test loading valid existing config."""
    config_path = tmp_path / "config.json"
    existing = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"my-server": {"command": "npx", "args": ["-y", "my-server"]}},
    }
    config_path.write_text(json.dumps(existing), encoding="utf-8")

    config = install_kit.load_existing_config(config_path)
    assert config == existing


def test_load_existing_config_invalid_json(tmp_path: Path) -> None:
    """Test loading invalid JSON creates backup and returns template."""
    config_path = tmp_path / "invalid.json"
    config_path.write_text("{ invalid json }", encoding="utf-8")

    config = install_kit.load_existing_config(config_path)

    assert config["$schema"] == "https://aka.ms/mcp-config-schema"
    assert "mcpServers" in config

    backup_path = tmp_path / "invalid.json.backup"
    assert backup_path.exists()


def test_merge_configs_no_collision() -> None:
    """Test merging configs when no server name collision."""
    existing = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"existing-server": {"command": "existing"}},
    }
    curated = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"new-server": {"command": "new"}},
    }

    merged = install_kit.merge_configs(existing, curated, interactive=False)

    assert "existing-server" in merged["mcpServers"]
    assert "new-server" in merged["mcpServers"]
    assert len(merged["mcpServers"]) == 2


def test_merge_configs_collision_skip() -> None:
    """Test merging configs with collision in non-interactive mode skips."""
    existing = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "existing"}},
    }
    curated = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "curated"}},
    }

    merged = install_kit.merge_configs(existing, curated, interactive=False)

    assert merged["mcpServers"]["shared-server"]["command"] == "existing"


def test_merge_configs_collision_overwrite_yes() -> None:
    """Test merging configs with collision and user chooses overwrite."""
    existing = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "existing"}},
    }
    curated = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "curated"}},
    }

    with patch("builtins.input", return_value="y"):
        merged = install_kit.merge_configs(existing, curated, interactive=True)

    assert merged["mcpServers"]["shared-server"]["command"] == "curated"


def test_merge_configs_collision_overwrite_no() -> None:
    """Test merging configs with collision and user chooses keep existing."""
    existing = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "existing"}},
    }
    curated = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"shared-server": {"command": "curated"}},
    }

    with patch("builtins.input", return_value="n"):
        merged = install_kit.merge_configs(existing, curated, interactive=True)

    assert merged["mcpServers"]["shared-server"]["command"] == "existing"


def test_write_config_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test write_config in dry-run mode doesn't write to disk."""
    config_path = tmp_path / "test.json"
    config: dict[str, Any] = {"mcpServers": {}}

    install_kit.write_config(config_path, config, dry_run=True)

    assert not config_path.exists()
    captured = capsys.readouterr()
    assert "[DRY RUN]" in captured.out


def test_write_config_actually_writes(tmp_path: Path) -> None:
    """Test write_config actually writes to disk in normal mode."""
    config_path = tmp_path / "test.json"
    config = {
        "$schema": "https://aka.ms/mcp-config-schema",
        "mcpServers": {"test": {"command": "test"}},
    }

    install_kit.write_config(config_path, config, dry_run=False)

    assert config_path.exists()
    loaded = json.loads(config_path.read_text(encoding="utf-8"))
    assert loaded == config


def test_check_azure_auth_authenticated() -> None:
    """Test Azure auth check when authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="some account\n")
        ok, msg = install_kit.check_azure_auth()
        assert ok is True
        assert "authenticated" in msg


def test_check_azure_auth_not_authenticated() -> None:
    """Test Azure auth check when not authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        ok, msg = install_kit.check_azure_auth()
        assert ok is False
        assert "not authenticated" in msg


def test_check_github_auth_authenticated() -> None:
    """Test GitHub auth check when authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Logged in\n")
        ok, msg = install_kit.check_github_auth()
        assert ok is True
        assert "authenticated" in msg


def test_check_github_auth_not_authenticated() -> None:
    """Test GitHub auth check when not authenticated."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        ok, msg = install_kit.check_github_auth()
        assert ok is False
        assert "not authenticated" in msg


def test_detect_clients_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test client detection when none are installed."""
    with (
        patch("shutil.which", return_value=None),
        patch("pathlib.Path.exists", return_value=False),
    ):
        detected = install_kit.detect_clients()
        assert detected == []


def test_detect_clients_copilot_cli() -> None:
    """Test client detection finds Copilot CLI."""
    with patch(
        "shutil.which", side_effect=lambda cmd: "/usr/bin/copilot" if cmd == "copilot" else None
    ):
        detected = install_kit.detect_clients()
        assert "copilot-cli" in detected
