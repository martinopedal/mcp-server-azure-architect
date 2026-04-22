# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, report it responsibly using [GitHub Security Advisories](https://github.com/martinopedal/mcp-server-azure-architect/security/advisories/new).

Do not open a public issue. Public disclosure before a fix is in place puts users at risk.

The maintainer will acknowledge the report within 5 business days and aim to release a fix within 30 days for confirmed vulnerabilities.

## Supported Versions

Only the latest version on the `main` branch is supported with security updates.

## Scope

This is a **read-only** Model Context Protocol server. It exposes Azure architect tools (ALZ checklist queries, scorecard composition) over MCP. It must never make Azure write calls.

Relevant vulnerability classes include:

- Any code path that imports an Azure SDK client class with mutation methods (`Begin*`, `Create*`, `Update*`, `Delete*`)
- Tool input that lets a caller probe a subscription or tenant they are not logged into (confused-deputy)
- Token or secret leakage through tool output, error messages, or logs
- Workflow injection in GitHub Actions
- Supply chain issues in runtime dependencies or recommended companion MCP servers

## Companion MCP servers

This repo ships a curated `mcp-config.json` listing recommended companion servers (azure-mcp, microsoft-learn-mcp, github, mermaid-mcp, drawio-mcp, kubernetes-mcp, terraform-mcp). Each addition requires a Sage research note and a Sentinel supply chain review. Pinned versions in `mcp-config.json` are part of the security contract.

## Not in scope

This repo is **not an official Microsoft product**. It is a personal community tool that complements [`azure-mcp`](https://github.com/microsoft/azure-mcp), it does not replace it.
