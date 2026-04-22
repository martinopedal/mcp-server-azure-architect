# Install mcp-server-azure-architect on VS Code Copilot

VS Code Copilot uses the same MCP config format as other clients. This guide covers setup for the Copilot Chat extension in VS Code.

## Prerequisites

- **VS Code** with **Copilot Chat** extension installed ([marketplace](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat))
- **Docker** (for `github-mcp` and `terraform-mcp`)
- (Optional) **Node.js 18+**

## Step 1: Locate Your Config

VS Code Copilot reads MCP configs from the Copilot CLI location:

```
Windows:   C:\Users\<username>\.copilot\mcp-config.json
macOS:     ~/.copilot/mcp-config.json
Linux:     ~/.copilot/mcp-config.json
```

If the file does not exist, create an empty one with this template:

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {}
}
```

## Step 2: Add the Architect's Toolkit

Merge the companion servers from the `mcp-server-azure-architect` repository (`.copilot/mcp-config.json`) into your existing config:

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

## Step 3: Configure GitHub PAT (Optional)

If you plan to use `github-mcp`, export your GitHub Personal Access Token:

**Windows (PowerShell):**

```powershell
[System.Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_xxxxxxxxxxxx", "User")
```

Then restart VS Code.

**macOS / Linux:**

Add to your shell profile (`~/.zprofile` for macOS, `~/.bashrc` or `~/.zshrc` for Linux):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"
```

Then restart VS Code.

Generate a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with scopes: `repo`, `read:org`.

## Step 4: Restart VS Code

Close and reopen VS Code to load the MCP config.

## Step 5: Verify Servers Loaded

Open the Copilot Chat pane (Ctrl+Shift+L or Cmd+Shift+L) and type:

```
@azure-mcp help
```

If available, Copilot Chat will list the server's tools. Repeat for other servers to verify they loaded.

## Step 6: Opt Out of Any Companion (Optional)

To disable a server, add `"disabled": true` to its config entry:

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

Once configured, use the servers in Copilot Chat via the `@` mention:

```
@azure-mcp list all resource groups in my subscription

@mermaid create a diagram of an AKS cluster with ingress controller

@drawio save the diagram as a PowerPoint slide

@github search my organization for Bicep templates
```

Type `@` and a server name to see its available tools.

## Troubleshooting

### "TBD-pending-runtime-adr" Error

If `mcp-server-azure-architect` fails to load, the runtime decision is still pending. Check [AGENTS.md](../../AGENTS.md) for updates.

### Servers Not Appearing

1. Verify `.copilot/mcp-config.json` contains valid JSON (check syntax with an online validator).
2. Restart VS Code completely.
3. Check the Copilot Chat output pane for error messages.

### Docker Not Running

Ensure Docker is active:

**Windows/macOS:**

Start Docker Desktop application.

**Linux:**

```bash
sudo systemctl start docker
```

### Node.js Not Found

Install Node.js from [nodejs.org](https://nodejs.org). Or globally install companions:

```bash
npm install -g mcp-mermaid@0.4.1 drawio-mcp-server@2.0.4 kubernetes-mcp-server@0.0.53
```

Remove `npx` and `-y` from the args and reference the global path.

## Next Steps

- Read the [Companion Compatibility Matrix](compatibility-matrix.md) for tested versions and known issues.
- See the [Copilot CLI guide](copilot-cli.md) for the CLI version.
