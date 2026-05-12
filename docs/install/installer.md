# Kit Installer

Cross-platform installer for mcp-server-azure-architect and its curated companion kit.

## What it does

The installer automates the setup flow for Azure architects:

1. **Prerequisites check:** Python 3.11+, Node.js 18+ (optional), Docker (optional), GitHub CLI (optional)
2. **Server installation reminder:** Ensures you have installed `mcp-server-azure-architect` via pip or uvx
3. **Client detection:** Auto-detects which MCP clients are present (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot)
4. **Config merge:** Adds the curated companion kit to each client's config file, preserving your existing servers
5. **Auth smoke test:** Checks `az account show` and `gh auth status` to verify you're ready to use the tools
6. **Next steps:** Shows copy-pasteable commands for verifying the setup

## Usage

### Interactive (recommended)

```bash
python scripts/install_kit.py
```

The installer will:
- Check prerequisites and warn if any are missing
- Auto-detect your MCP clients
- Prompt you to select which ones to configure
- Merge the curated config into each client's config file
- Check Azure and GitHub auth status
- Print next steps

### Non-interactive (CI or automation)

```bash
python scripts/install_kit.py --clients copilot-cli,claude-desktop --non-interactive
```

Use `--clients` to specify which clients to configure (comma-separated). Use `--non-interactive` to skip all prompts. If a server name collision is detected, the installer will preserve the existing entry.

### Dry-run (preview changes)

```bash
python scripts/install_kit.py --dry-run
```

Prints the JSON that would be written to each config file without modifying any files.

## Supported clients

| Client | Config location (Windows) | Config location (macOS) | Config location (Linux) |
|--------|---------------------------|-------------------------|-------------------------|
| Copilot CLI | `C:\Users\<user>\.copilot\mcp-config.json` | `~/.copilot/mcp-config.json` | `~/.copilot/mcp-config.json` |
| Claude Desktop | `C:\Users\<user>\AppData\Roaming\Claude\claude_desktop_config.json` | `~/Library/Application Support/Claude/claude_desktop_config.json` | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | `C:\Users\<user>\.cursor\mcp-config.json` | `~/.cursor/mcp-config.json` | `~/.cursor/mcp-config.json` |
| VS Code Copilot | Same as Copilot CLI | Same as Copilot CLI | Same as Copilot CLI |

## Config merge behavior

The installer **merges** the curated kit into your existing config. It does NOT overwrite your config file.

- **No collision:** New servers are added to your existing config.
- **Name collision (interactive):** The installer prompts you to choose: keep existing or overwrite with curated.
- **Name collision (non-interactive):** The installer preserves your existing entry and skips the curated one.

If the installer detects invalid JSON in your existing config, it creates a `.backup` file and starts fresh.

## Prerequisites

### Required

- **Python 3.11+** (the project minimum)

### Optional

- **Node.js 18+:** Required for npx-based companions (azure-mcp, mermaid, drawio, kubernetes). Without Node, these companions will not work.
- **Docker:** Required for Docker-based companions (github, terraform). Without Docker, these companions will not work.
- **GitHub CLI (`gh`):** Required only if you plan to use the `github` companion and need to check auth status.

The installer checks all of these and warns if any are missing, but it does not fail unless Python 3.11+ is missing.

## Authentication

The curated kit assumes:

- **Azure:** You have run `az login` and have an active Azure CLI session. The `azure-mcp` companion and this server use `DefaultAzureCredential`, which reads your az CLI credentials.
- **GitHub:** (Optional) If you use the `github` companion, export `GITHUB_PERSONAL_ACCESS_TOKEN` (see [copilot-cli.md](copilot-cli.md) for details) OR run `gh auth login`.

The installer runs `az account show` and `gh auth status` as smoke tests and warns if either fails. It does not fail the install if auth is missing, you can set it up later.

## Design decisions

### Language: Python (stdlib only)

**Chosen:** Python 3.11+ with stdlib only (no external dependencies).

**Rationale:**
- Matches the project stack (Python 3.11+, already required)
- Cross-platform without needing both PowerShell and Bash scripts
- Can import `mcp_server_azure_architect` if needed in future versions
- Everyone installing this already has Python 3.11+

**Not chosen:** PowerShell + Bash pair. Would require maintaining two scripts with identical logic.

### Config merge strategy: Preserve existing servers

**Chosen:** MERGE new servers into existing config. On name collision, prompt (interactive) or skip (non-interactive).

**Rationale:**
- Architects may already have other MCP servers configured.
- Overwriting the config file would delete their work.
- Interactive prompt gives control when names collide.
- Non-interactive mode is safe for automation (preserves existing).

**Not chosen:** Overwrite entire config. Too destructive.

### Distribution: Run from repo clone

**Chosen:** `python scripts/install_kit.py` (run from a clone). No `pyproject.toml` entry point yet.

**Rationale:**
- v0.1 minimum viable installer for architects who already cloned the repo.
- Avoids premature public API commitment.
- Future: publish to PyPI as `mcp-server-azure-architect-installer` or add a console_script entry, once we have user feedback.

**Not chosen:** Console script in `pyproject.toml`. Premature for v0.1.

### Per-client paths: Hardcoded by OS

**Chosen:** Hardcode canonical config paths per OS (per existing per-client docs).

**Rationale:**
- MCP clients have fixed config locations per OS.
- No environment variable overrides exist (as of 2026-05-12).
- Hardcoding matches the per-client install docs we already shipped.

**Not chosen:** Allow `--config-path` override. Not needed yet; all clients use standard locations.

## Examples

### Example 1: First-time setup on Windows

```powershell
# Clone the repo
git clone https://github.com/martinopedal/mcp-server-azure-architect.git
cd mcp-server-azure-architect

# Install the server (dev mode)
pip install -e .

# Run the installer
python scripts/install_kit.py
```

Installer output:

```
=== mcp-server-azure-architect Kit Installer ===

Step 1: Checking prerequisites...
  ✅ python: Python 3.12
  ✅ node: v20.11.0
  ✅ docker: Docker version 24.0.7
  ❌ gh: not found

Warning: GitHub CLI not found. The 'github' companion will not work.

Step 2: Install mcp-server-azure-architect
This installer assumes you have already installed the server via:
  pip install -e .    (for dev)
  uvx mcp-server-azure-architect    (for end users)
If not, please install first, then re-run this installer.

Continue? (Y/n): y

Step 3: Detecting MCP clients...

Detected clients:
  - copilot-cli

Available clients:
  1. [✅] copilot-cli
  2. [ ] claude-desktop
  3. [ ] cursor
  4. [ ] vscode-copilot

Enter client numbers to configure (comma-separated, e.g., '1,2,4'), or 'all': 1

Configuring clients: copilot-cli

Step 4: Merging curated config into client configs...

  Configuring copilot-cli at C:\Users\martin\.copilot\mcp-config.json
Wrote config to C:\Users\martin\.copilot\mcp-config.json

Step 5: Authentication checks...
  ✅ Azure: az CLI authenticated
  ❌ GitHub: gh CLI not found

Warning: GitHub CLI not authenticated. The 'github' companion will not work.
Run 'gh auth login' if you plan to use it.

=== Installation Complete ===

Next steps:
  - Restart Copilot CLI or VS Code to load the new config.
  - Run: copilot mcp servers

For more info:
  - Docs: docs/install/installer.md
  - Compatibility: docs/install/compatibility-matrix.md
  - Skills: See README.md
```

### Example 2: Dry-run to preview changes

```bash
python scripts/install_kit.py --dry-run --clients copilot-cli --non-interactive
```

Output includes:

```
[DRY RUN] Would write to /home/martin/.copilot/mcp-config.json:
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {
    "azure-mcp": {
      "_purpose": "Official Microsoft Azure MCP...",
      "command": "npx",
      "args": ["-y", "@azure/mcp@2.0.1"]
    },
    ...
  }
}

(DRY RUN: No files were modified)
```

### Example 3: Automation (CI pipeline)

```bash
# In a CI script
python scripts/install_kit.py \
  --clients copilot-cli \
  --non-interactive
```

No prompts, exits cleanly with status 0 if successful.

## Troubleshooting

### "Error: Python 3.11+ is required."

You are running Python 3.10 or older. Upgrade to Python 3.11 or newer.

### "Curated config not found"

You are running the installer from the wrong directory. Change to the repo root:

```bash
cd /path/to/mcp-server-azure-architect
python scripts/install_kit.py
```

### "Warning: Existing config is invalid JSON"

Your existing config file has a syntax error. The installer creates a backup (`.backup` suffix) and starts fresh. Review the backup to see what was wrong, then re-add any servers you need.

### "Skipping '<server>' (already exists, non-interactive mode)."

In non-interactive mode, the installer will not overwrite servers that already exist in your config. If you want to overwrite, either:
- Run interactively and choose "y" when prompted, or
- Manually remove the conflicting server from your config first

### Installer runs but client doesn't load servers

1. **Restart the client.** MCP clients only read config on startup.
2. **Check the config file path.** Run the installer with `--dry-run` to see the path it's writing to, and verify that matches your client's expected location.
3. **Validate JSON syntax.** Use an online JSON validator or `jq` (Linux/macOS) / `ConvertFrom-Json` (PowerShell) to check for syntax errors.
4. **Check client logs.** Most MCP clients log errors when loading servers. See the per-client install docs for log locations.

## See also

- [Copilot CLI install guide](copilot-cli.md) (manual setup if you prefer not to use the installer)
- [Claude Desktop install guide](claude-desktop.md)
- [Cursor install guide](cursor.md)
- [VS Code Copilot install guide](vscode-copilot.md)
- [Companion compatibility matrix](compatibility-matrix.md) (tested versions, known issues)
