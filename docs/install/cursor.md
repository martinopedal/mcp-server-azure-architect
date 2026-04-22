# Install mcp-server-azure-architect on Cursor

Cursor integrates MCP servers for inline tool access. This guide covers setting up the architect's toolkit with Cursor.

## Prerequisites

- **Cursor** installed ([download](https://cursor.com))
- **Docker** (for `github-mcp` and `terraform-mcp`)
- (Optional) **Node.js 18+**

## Step 1: Locate Your Config

Cursor stores its MCP config at:

```
Windows:   C:\Users\<username>\.cursor\mcp-config.json
macOS:     ~/.cursor/mcp-config.json
Linux:     ~/.cursor/mcp-config.json
```

If the file does not exist, create an empty one:

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {}
}
```

## Step 2: Merge the Curated Config

Use the companion list from the `mcp-server-azure-architect` repository (`.copilot/mcp-config.json`). Add each server to your `.cursor/mcp-config.json`:

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {
    "azure-mcp": {
      "command": "npx",
      "args": ["-y", "@azure/mcp@2.0.1"]
    },
    "microsoft-learn": {
      "url": "https://learn.microsoft.com/api/mcp"
    },
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server:latest"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "mermaid": {
      "command": "npx",
      "args": ["-y", "mcp-mermaid@0.4.1"]
    },
    "drawio": {
      "command": "npx",
      "args": ["-y", "drawio-mcp-server@2.0.4"]
    },
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubernetes-mcp-server@0.0.53"]
    },
    "terraform": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hashicorp/terraform-mcp-server:v0.5.1"]
    },
    "mcp-server-azure-architect": {
      "command": "TBD-pending-runtime-adr",
      "args": []
    }
  }
}
```

## Step 3: Set GitHub PAT Environment Variable (Optional)

If using `github-mcp`, export your GitHub Personal Access Token:

**Windows (PowerShell):**

```powershell
[System.Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_xxxxxxxxxxxx", "User")
```

Then restart Cursor.

**macOS / Linux:**

Add to `~/.zprofile` (macOS) or `~/.bashrc` (Linux):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"
```

Restart Cursor for the environment variable to take effect.

Generate a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with scopes: `repo`, `read:org`.

## Step 4: Restart Cursor

Close and reopen Cursor to load the updated MCP config.

## Step 5: Verify Servers Loaded

Open the Cursor settings (Cmd+, or Ctrl+,) and check the MCP Servers section. All configured servers should appear with a green checkmark if loaded successfully.

## Step 6: Opt Out of Any Companion (Optional)

To disable a server without removing it, add `"disabled": true`:

```json
{
  "mermaid": {
    "disabled": true,
    "command": "npx",
    "args": ["-y", "mcp-mermaid@0.4.1"]
  }
}
```

## Usage

Once configured, use the servers in Cursor via Cmd+K (Mac) or Ctrl+K (Windows/Linux) chat:

```
@azure-mcp get resource groups in my subscription

@mermaid draw an AKS networking diagram

@drawio export to PowerPoint

@github search repos for Bicep infrastructure
```

Use `@` to mention any available server and Claude will list its tools.

## Troubleshooting

### "TBD-pending-runtime-adr" Error

If `mcp-server-azure-architect` fails to load, the runtime decision is pending. Check [AGENTS.md](../../AGENTS.md) for status updates.

### Servers Not Appearing in Chat

1. Verify `.cursor/mcp-config.json` is valid JSON.
2. Restart Cursor completely.
3. Check Cursor logs for errors (usually accessible via Help > Toggle Developer Tools).

### Docker Not Found

Ensure Docker is running:

**Windows/macOS:**

Start Docker Desktop application.

**Linux:**

```bash
sudo systemctl start docker
```

### Node.js Not Installed

Install Node.js from [nodejs.org](https://nodejs.org). Or install companions globally:

```bash
npm install -g mcp-mermaid@0.4.1 drawio-mcp-server@2.0.4 kubernetes-mcp-server@0.0.53
```

Then reference them without `npx` in the config.

## Next Steps

- Read the [Companion Compatibility Matrix](compatibility-matrix.md) for tested versions.
- See the [Copilot CLI guide](copilot-cli.md) if you use multiple clients.
