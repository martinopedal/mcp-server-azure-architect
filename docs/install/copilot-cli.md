# Install mcp-server-azure-architect on Copilot CLI

Copilot CLI integrates MCP servers to expand tool capabilities. This guide walks you through merging `mcp-server-azure-architect` and its companion toolkit into your Copilot CLI config.

## Prerequisites

- **Copilot CLI** installed ([install guide](https://github.com/github/gh-copilot))
- **Docker** available on PATH (for `github-mcp` and `terraform-mcp`)
- (Optional) **Node.js 18+** (for faster npm installs; falls back to `npx` otherwise)

## Step 1: Locate Your Config

Copilot CLI stores its MCP config at:

```
Windows:   C:\Users\<username>\.copilot\mcp-config.json
macOS:     ~/.copilot/mcp-config.json
Linux:     ~/.copilot/mcp-config.json
```

If the file does not exist, create an empty one:

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {}
}
```

## Step 2: Merge the Curated Config

Download or copy the `mcp-config.json` from the `mcp-server-azure-architect` repository (`.copilot/mcp-config.json`).

Merge its `mcpServers` into your Copilot CLI config. For example:

**Before (your existing config):**

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {
    "my-custom-server": {
      "command": "npx",
      "args": ["-y", "my-custom-mcp"]
    }
  }
}
```

**After (merged with mcp-server-azure-architect):**

```json
{
  "$schema": "https://aka.ms/mcp-config-schema",
  "mcpServers": {
    "my-custom-server": {
      "command": "npx",
      "args": ["-y", "my-custom-mcp"]
    },
    "azure-mcp": { ... },
    "microsoft-learn": { ... },
    "github": { ... },
    "mermaid": { ... },
    "drawio": { ... },
    "kubernetes": { ... },
    "terraform": { ... },
    "mcp-server-azure-architect": { ... }
  }
}
```

## Step 3: Configure GitHub PAT (if using github-mcp)

The `github` server requires a GitHub Personal Access Token (PAT). Export it before running Copilot CLI:

```bash
# Windows (PowerShell)
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_xxxxxxxxxxxx"

# macOS / Linux
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"
```

Generate a PAT at [github.com/settings/tokens](https://github.com/settings/tokens) with scopes: `repo`, `read:org`.

## Step 4: Verify the Servers Loaded

Run:

```bash
copilot mcp servers
```

Expected output includes:

```
✓ azure-mcp
✓ microsoft-learn
✓ github
✓ mermaid
✓ drawio
✓ kubernetes
✓ terraform
✓ mcp-server-azure-architect
```

If any fail to load, check the error message. Common issues:
- **Docker not found:** Install Docker Desktop or Docker CLI.
- **Node.js missing:** Install Node.js or rely on `npx` (slower).
- **GitHub PAT not set:** Export `GITHUB_PERSONAL_ACCESS_TOKEN` before running Copilot CLI.

## Step 5: Opt Out of Any Companion (Optional)

To disable a companion server without removing it from the config, add `"disabled": true`:

```json
{
  "mermaid": {
    "_purpose": "Render architecture diagrams inline in design reviews.",
    "disabled": true,
    "command": "npx",
    "args": ["-y", "mcp-mermaid@0.4.1"]
  }
}
```

The server will not load but remains documented in your config for future re-enabling.

## Step 6: Use the Tools

Once loaded, use Copilot CLI normally:

```bash
copilot /design-review -a my-architecture.json
copilot /alz-gap-check --subscription <sub-id>
```

See the main [README.md](../../README.md) for skill documentation.

## Troubleshooting

### "TBD-pending-runtime-adr" Error

If `mcp-server-azure-architect` fails to load with this message, the runtime decision is still pending. Check [AGENTS.md](../../AGENTS.md) for status.

### "Docker daemon not responding"

Ensure Docker Desktop is running (Windows/macOS) or Docker daemon is active (Linux). Restart if needed.

### "npx: command not found"

Install Node.js 16+ from [nodejs.org](https://nodejs.org). Or install companions globally with `npm install -g <package>` and reference them without `npx`.

### Config Not Loading

Validate the JSON file:

```bash
# Linux / macOS
jq . ~/.copilot/mcp-config.json

# Windows (PowerShell)
Get-Content -Path "C:\Users\<username>\.copilot\mcp-config.json" | ConvertFrom-Json | ConvertTo-Json
```

If invalid JSON is reported, fix the syntax and retry.

## Next Steps

- Read the [Companion Compatibility Matrix](compatibility-matrix.md) for known issues and tested versions.
- See the main [README.md](../../README.md) for architecture-focused skills and examples.
