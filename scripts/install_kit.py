#!/usr/bin/env python3
"""
Kit installer for mcp-server-azure-architect.

Walks an architect through:
1. Prerequisites check (Python, Node, Docker, gh CLI)
2. Installing this MCP server
3. Detecting target MCP client(s)
4. Merging curated kit config into client config file(s)
5. Auth smoke tests
6. Next steps summary

Usage:
    python scripts/install_kit.py [--dry-run] [--clients copilot-cli,claude-desktop]
    python scripts/install_kit.py --help

Design:
    - Language: Python (stdlib only) to match project stack
    - Merge strategy: Preserve existing servers, prompt on name collision
    - Distribution: Run from repo clone for v0.1 (no console_script yet)
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def check_python_version() -> tuple[bool, str]:
    """Check if Python 3.11+ is available."""
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and minor >= 11:
        return True, f"Python {major}.{minor}"
    return False, f"Python {major}.{minor} (requires 3.11+)"


def check_command_available(cmd: str) -> tuple[bool, str]:
    """Check if a command is available on PATH."""
    if shutil.which(cmd):
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            version = result.stdout.strip().split("\n")[0] if result.returncode == 0 else "unknown"
            return True, version
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True, "found"
    return False, "not found"


def check_prerequisites() -> dict[str, tuple[bool, str]]:
    """Check all prerequisites and return status dict."""
    results = {
        "python": check_python_version(),
        "node": check_command_available("node"),
        "docker": check_command_available("docker"),
        "gh": check_command_available("gh"),
    }
    return results


def get_config_path(client: str) -> Path | None:
    """Get config file path for a given MCP client."""
    system = platform.system()
    home = Path.home()

    if client == "copilot-cli":
        if system == "Windows":
            return home / ".copilot" / "mcp-config.json"
        else:
            return home / ".copilot" / "mcp-config.json"

    elif client == "claude-desktop":
        if system == "Windows":
            return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif system == "Darwin":
            return (
                home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
            )
        else:
            return home / ".config" / "Claude" / "claude_desktop_config.json"

    elif client == "cursor":
        if system == "Windows":
            return home / ".cursor" / "mcp-config.json"
        else:
            return home / ".cursor" / "mcp-config.json"

    elif client == "vscode-copilot":
        # VS Code Copilot uses the Copilot CLI config location
        if system == "Windows":
            return home / ".copilot" / "mcp-config.json"
        else:
            return home / ".copilot" / "mcp-config.json"

    return None


def load_curated_config() -> dict[str, Any]:
    """Load the curated mcp-config.json from repo."""
    repo_root = Path(__file__).parent.parent
    curated_path = repo_root / ".copilot" / "mcp-config.json"

    if not curated_path.exists():
        print(f"Error: Curated config not found at {curated_path}")
        sys.exit(1)

    with open(curated_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def load_existing_config(path: Path) -> dict[str, Any]:
    """Load existing config file, or return empty template if missing."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data
        except json.JSONDecodeError as e:
            print(f"Warning: Existing config at {path} is invalid JSON: {e}")
            print("Creating backup and starting fresh.")
            backup_path = path.with_suffix(path.suffix + ".backup")
            shutil.copy2(path, backup_path)
            print(f"Backup saved to {backup_path}")

    return {"$schema": "https://aka.ms/mcp-config-schema", "mcpServers": {}}


def merge_configs(
    existing: dict[str, Any], curated: dict[str, Any], interactive: bool = True
) -> dict[str, Any]:
    """
    Merge curated config into existing, preserving existing servers.

    If a server name collision occurs, prompt user (if interactive) or skip (if not).
    """
    merged = existing.copy()

    if "mcpServers" not in merged:
        merged["mcpServers"] = {}

    curated_servers = curated.get("mcpServers", {})

    for server_name, server_config in curated_servers.items():
        if server_name in merged["mcpServers"]:
            if interactive:
                print(f"\nServer '{server_name}' already exists in config.")
                print(f"Existing: {json.dumps(merged['mcpServers'][server_name], indent=2)}")
                print(f"Curated:  {json.dumps(server_config, indent=2)}")
                response = input("Overwrite with curated version? (y/N): ").strip().lower()
                if response == "y":
                    merged["mcpServers"][server_name] = server_config
                    print(f"Overwrote '{server_name}'.")
                else:
                    print(f"Kept existing '{server_name}'.")
            else:
                print(f"Skipping '{server_name}' (already exists, non-interactive mode).")
        else:
            merged["mcpServers"][server_name] = server_config

    return merged


def write_config(path: Path, config: dict[str, Any], dry_run: bool = False) -> None:
    """Write merged config to disk (or print if dry_run)."""
    if dry_run:
        print(f"\n[DRY RUN] Would write to {path}:")
        print(json.dumps(config, indent=2))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"Wrote config to {path}")


def check_azure_auth() -> tuple[bool, str]:
    """Check if Azure CLI is authenticated."""
    try:
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return True, "az CLI authenticated"
        else:
            return False, "az CLI not authenticated (run 'az login')"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "az CLI not found"


def check_github_auth() -> tuple[bool, str]:
    """Check if GitHub CLI is authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return True, "gh CLI authenticated"
        else:
            return False, "gh CLI not authenticated (run 'gh auth login')"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, "gh CLI not found"


def detect_clients() -> list[str]:
    """Auto-detect which MCP clients are installed."""
    detected = []

    # Check Copilot CLI
    if shutil.which("copilot"):
        detected.append("copilot-cli")

    # Check Claude Desktop by config path existence
    claude_path = get_config_path("claude-desktop")
    if claude_path and claude_path.parent.exists():
        detected.append("claude-desktop")

    # Check Cursor
    cursor_path = get_config_path("cursor")
    if cursor_path and cursor_path.parent.exists():
        detected.append("cursor")

    # Check VS Code (look for code command)
    if shutil.which("code"):
        detected.append("vscode-copilot")

    return detected


def prompt_clients(detected: list[str]) -> list[str]:
    """Prompt user to select which clients to configure."""
    all_clients = ["copilot-cli", "claude-desktop", "cursor", "vscode-copilot"]

    print("\nDetected clients:")
    for client in detected:
        print(f"  - {client}")

    print("\nAvailable clients:")
    for idx, client in enumerate(all_clients, 1):
        marker = "✓" if client in detected else " "
        print(f"  {idx}. [{marker}] {client}")

    print(
        "\nEnter client numbers to configure (comma-separated, e.g., '1,2,4'), or 'all': ", end=""
    )
    response = input().strip().lower()

    if response == "all":
        return all_clients

    try:
        indices = [int(x.strip()) for x in response.split(",")]
        selected = [all_clients[i - 1] for i in indices if 1 <= i <= len(all_clients)]
        return selected
    except (ValueError, IndexError):
        print("Invalid selection, using detected clients only.")
        return detected


def main() -> int:
    """Main installer flow."""
    parser = argparse.ArgumentParser(
        description="Install mcp-server-azure-architect kit and configure MCP clients.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without modifying files",
    )
    parser.add_argument(
        "--clients",
        type=str,
        help="Comma-separated list of clients to configure (copilot-cli,claude-desktop,cursor,vscode-copilot)",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Skip all prompts (use with --clients for automation)",
    )
    args = parser.parse_args()

    print("=== mcp-server-azure-architect Kit Installer ===\n")

    # Step 1: Check prerequisites
    print("Step 1: Checking prerequisites...")
    prereqs = check_prerequisites()

    for name, (available, info) in prereqs.items():
        status = "✓" if available else "✗"
        print(f"  {status} {name}: {info}")

    if not prereqs["python"][0]:
        print("\nError: Python 3.11+ is required.")
        return 1

    if not prereqs["node"][0]:
        print(
            "\nWarning: Node.js not found. npx-based companions (azure-mcp, mermaid, drawio, kubernetes) will not work."
        )
        print("Install from https://nodejs.org")

    if not prereqs["docker"][0]:
        print(
            "\nWarning: Docker not found. Docker-based companions (github, terraform) will not work."
        )
        print("Install Docker Desktop from https://docker.com")

    # Step 2: Install this server
    print("\nStep 2: Install mcp-server-azure-architect")
    print("This installer assumes you have already installed the server via:")
    print("  pip install -e .    (for dev)")
    print("  uvx mcp-server-azure-architect    (for end users)")
    print("If not, please install first, then re-run this installer.")

    if not args.non_interactive:
        response = input("\nContinue? (Y/n): ").strip().lower()
        if response == "n":
            print("Aborted.")
            return 0

    # Step 3: Detect and prompt for clients
    print("\nStep 3: Detecting MCP clients...")

    if args.clients:
        selected_clients = [c.strip() for c in args.clients.split(",")]
    elif args.non_interactive:
        selected_clients = detect_clients()
        if not selected_clients:
            print("No clients detected and --non-interactive specified. Nothing to do.")
            return 0
    else:
        detected = detect_clients()
        if detected:
            selected_clients = prompt_clients(detected)
        else:
            print("No MCP clients detected.")
            print("You can still configure manually. Select clients to set up:")
            selected_clients = prompt_clients([])

    if not selected_clients:
        print("No clients selected. Exiting.")
        return 0

    print(f"\nConfiguring clients: {', '.join(selected_clients)}")

    # Step 4: Load curated config and merge
    print("\nStep 4: Merging curated config into client configs...")
    curated = load_curated_config()

    for client in selected_clients:
        config_path = get_config_path(client)
        if not config_path:
            print(f"Warning: Unknown client '{client}', skipping.")
            continue

        print(f"\n  Configuring {client} at {config_path}")
        existing = load_existing_config(config_path)
        merged = merge_configs(existing, curated, interactive=not args.non_interactive)
        write_config(config_path, merged, dry_run=args.dry_run)

    # Step 5: Auth smoke tests
    print("\nStep 5: Authentication checks...")

    az_ok, az_msg = check_azure_auth()
    gh_ok, gh_msg = check_github_auth()

    status_az = "✓" if az_ok else "✗"
    status_gh = "✓" if gh_ok else "✗"

    print(f"  {status_az} Azure: {az_msg}")
    print(f"  {status_gh} GitHub: {gh_msg}")

    if not az_ok:
        print(
            "\nWarning: Azure CLI not authenticated. Run 'az login' before using azure-mcp or this server."
        )

    if not gh_ok:
        print("\nWarning: GitHub CLI not authenticated. The 'github' companion will not work.")
        print("Run 'gh auth login' if you plan to use it.")

    # Step 6: Next steps
    print("\n=== Installation Complete ===\n")
    print("Next steps:")

    if "copilot-cli" in selected_clients or "vscode-copilot" in selected_clients:
        print("  - Restart Copilot CLI or VS Code to load the new config.")
        print("  - Run: copilot mcp servers")

    if "claude-desktop" in selected_clients:
        print("  - Restart Claude Desktop to load the new config.")

    if "cursor" in selected_clients:
        print("  - Restart Cursor to load the new config.")
        print("  - Check Settings > MCP Servers to verify.")

    print("\nFor more info:")
    print("  - Docs: docs/install/installer.md")
    print("  - Compatibility: docs/install/compatibility-matrix.md")
    print("  - Skills: See README.md")

    if args.dry_run:
        print("\n(DRY RUN: No files were modified)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
