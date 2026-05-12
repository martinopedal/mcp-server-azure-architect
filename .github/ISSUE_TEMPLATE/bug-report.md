---
name: Bug report
description: Report a bug or unexpected behavior
title: "bug: "
labels: ["bug", "squad"]
---

## Summary

<!-- One-line description of the bug. -->

## Reproduction steps

<!-- Step-by-step instructions to reproduce the issue. Be as specific as possible. -->

1. 
2. 
3. 

## Expected vs actual behavior

**Expected:**
<!-- What did you expect to happen? -->

**Actual:**
<!-- What actually happened? -->

## Environment

- Python version: <!-- e.g., 3.11, 3.12 -->
- Operating system: <!-- e.g., Windows, macOS, Linux -->
- MCP client used: <!-- e.g., Claude Desktop, Copilot CLI, VS Code -->
- Server version: <!-- e.g., v0.1.0, or commit SHA if from source -->

## Logs

<!-- Paste relevant error messages or logs here. IMPORTANT: Redact any credentials, tokens, subscription IDs, or personal data before pasting. -->

```
<!-- Logs go here -->
```

## Pre-checks

- [ ] I have tried running `python scripts/mcp_smoke.py` to confirm the server starts and tools enumerate
- [ ] I have tried running the server with `--verbose` flag to see detailed logs
- [ ] I have searched existing issues for similar reports
