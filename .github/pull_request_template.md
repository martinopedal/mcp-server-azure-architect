## Summary

<!-- Concise description of the changes and why they are needed. -->

## Related issue

<!-- Link to the issue this PR closes or addresses. Use "Closes #N" format. -->

Closes #

## Changes

<!-- Bulleted list of all changes in this PR. -->

- 
- 

## Validation gates

Before opening this PR, confirm:

- [ ] `python -m pytest -q` passes
- [ ] `python -m ruff check .` is clean
- [ ] `python -m mypy src tests scripts` is clean
- [ ] `python scripts/check_readonly.py src/mcp_server_azure_architect/` is clean (if `src/` was modified)
- [ ] `python scripts/mcp_smoke.py` passes (if tools changed)
- [ ] CHANGELOG.md updated under `[Unreleased]`

## ADR or design notes

<!-- If this PR implements or references an ADR, link it here. If design decisions were made, document them briefly. -->

## Squad reviewer

<!-- Use the `squad:{member}` label to route to the appropriate reviewer. See .squad/routing.md. -->
