# AI Governance

This repository uses AI-assisted development tools including GitHub Copilot and Squad by Brady Gaster, and itself **ships an MCP server** consumed by AI agents.

## Principles

1. **AI can draft; CI decides.** All code, whether human or AI-authored, must pass the same automated quality and security checks.
2. **Human accountability.** The maintainer reviews and owns every merge. AI output is a draft, not a decision.
3. **Verify, don't trust.** Non-obvious claims, configurations, and architecture decisions must be verified against authoritative sources (Microsoft Learn, MCP spec, upstream `azure-mcp`).
4. **Transparency.** Pull requests must disclose meaningful AI assistance.
5. **No secrets.** AI tools must never be given access to credentials, PATs, real subscription IDs, or tenant IDs in prompts or code.

## What this means in practice

- Every PR runs CI (build/lint/test for the chosen runtime, gitleaks, CodeQL, dependency-review, MCP Inspector smoke test) before merge.
- Branch protection prevents direct pushes to `main`.
- Dependabot scans GitHub Actions weekly (and the runtime ecosystem once the runtime ADR lands).
- gitleaks runs on every PR with a config that blocks real-looking GUIDs in non-doc paths.
- The `provenance` rule in [CONTRIBUTING.md](CONTRIBUTING.md) requires every hard-coded Azure identifier (policy ID, initiative ID, role definition ID, ALZ checklist item ID) to be tagged `public-builtin`, `public-source <url>`, or `must-not-ship`.
- Co-authored-by trailers (`Copilot <223556219+Copilot@users.noreply.github.com>`) record AI co-authorship.

## Special obligations as an MCP server

This server is consumed **by other AI agents**. That raises the bar:

- **Read-only enforcement is a security gate**, not a guideline. A static analysis test in CI proves no Azure SDK mutation method (`Begin*`, `Create*`, `Update*`, `Delete*`) exists in the call graph. Failing this gate blocks merge.
- **Token-scrub all logging**. Tool output, error messages, and diagnostic logs route through a scrubber before leaving the process.
- **Confused-deputy defense**. Every tool that accepts a `subscription_id` or `tenant_id` parameter validates the input against the caller's logged-in scope before issuing the underlying ARG/Azure call.
- **Companion server inclusion bar** (see [CONTRIBUTING.md](CONTRIBUTING.md)): signed releases, supply chain check, version pin, Sage research note, Sentinel review.
- **JSON Schemas on every tool**. Per MCP spec, tools must declare and validate input.

## AI tools used in this project

- [GitHub Copilot](https://github.com/features/copilot) for code generation and review.
- [Squad](https://github.com/bradygaster/squad) by Brady Gaster for agentic AI team orchestration. Team charter and routing live in [`.squad/`](.squad/).
- [Model Context Protocol](https://modelcontextprotocol.io/) servers used during authoring (`azure-mcp`, `microsoft-learn`, `github`).

## Reporting concerns

If you believe AI-generated content in this repository is inaccurate, insecure, or violates attribution requirements, please open an issue or use the [security reporting process](SECURITY.md).
