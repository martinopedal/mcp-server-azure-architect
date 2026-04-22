# Install mcp-server-azure-architect on Claude Desktop

Claude Desktop integrates MCP servers natively. This guide covers merging the architect's toolkit into your Claude Desktop config.

## Prerequisites

- **Claude Desktop** installed ([download](https://claude.ai/download))
- **Docker** (for `github-mcp` and `terraform-mcp`)
- (Optional) **Node.js 18+**

## Step 1: Locate Your Config

Claude Desktop stores its MCP config at:

```
Windows:   C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json
macOS:     ~/Library/Application Support/Claude/claude_desktop_config.json
Linux:     ~/.config/Claude/claude_desktop_config.json
```

If the file does not exist, create one with the template below.

## Step 2: Add the Companions

Open `claude_desktop_config.json` in your editor and add the servers from the curated config. A full example:

```json
{
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

If you use `github-mcp`, export your Personal Access Token:

**Windows (PowerShell):**

```powershell
[System.Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_xxxxxxxxxxxx", "User")
```

Then restart Claude Desktop for the variable to load.

**macOS / Linux:**

Add to `~/.zprofile` (macOS) or `~/.bashrc` (Linux):

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"
```

Source the file and restart Claude Desktop.

Generate a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with scopes: `repo`, `read:org`.

## Step 4: Restart Claude Desktop

Close and reopen Claude Desktop to load the updated config.

## Step 5: Verify Servers Loaded

In a Claude Desktop chat, type:

```
@azure-mcp list help
```

If the server is available, Claude will list its tools. Repeat for other servers. If a server fails to load, Claude will show an error. Check the config JSON syntax and environment variables.

## Step 6: Opt Out of Any Companion (Optional)

To disable a server, add `"disabled": true`:

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

Once configured, invoke servers in Claude Desktop by mentioning them by name:

```
@azure-mcp show resource groups

@mermaid create a diagram of an AKS ingress architecture

@drawio export the diagram to a PowerPoint slide

@github search for IaC examples in my org
```

See the main [README.md](../../README.md) for architecture-focused skills.

## Troubleshooting

### "TBD-pending-runtime-adr" Error

If `mcp-server-azure-architect` fails to load, the runtime is still being decided. Check [AGENTS.md](../../AGENTS.md) for updates.

### Servers Not Appearing

1. Verify the JSON is well-formed (use an online JSON validator).
2. Restart Claude Desktop completely.
3. Check the Claude Desktop logs for error messages (usually in the console if launched from terminal).

### Docker Error

Ensure Docker Desktop is running on Windows/macOS. On Linux, ensure the Docker daemon is active:

```bash
sudo systemctl start docker
```

### Node.js Not Found

Install Node.js from [nodejs.org](https://nodejs.org) or use the global install approach:

```bash
npm install -g mcp-mermaid@0.4.1
```

Then update the config to reference the global path instead of `npx`.

## Next Steps

- Read the [Companion Compatibility Matrix](compatibility-matrix.md) for tested versions and known issues.
- See the [Copilot CLI guide](copilot-cli.md) if you use that client too.
