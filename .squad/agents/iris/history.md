# Iris: Copilot Skills Author — History

## 2026-04-22T13:15:00Z — First Skill Landed: alz-gap-check

Branch: `feat/iris-skill-alz-gap-check-v2`  
PR: (pending creation)

Authored the first Copilot CLI extension for the project: `alz-gap-check`. This skill orchestrates ALZ checklist gap analysis by composing this server's `alz_query_by_id` tool (owned by Atlas) with optional `microsoft-learn-mcp` remediation lookups. Deliverables include:

- `.github/extensions/alz-gap-check/extension.mjs` — the extension itself
- `tests/skills/test_alz_gap_check_replay.md` — replay scenario doc
- `docs/skills/catalog.md` — skill catalog, first entry
- `.squad/agents/iris/history.md` — this file

**v0 behavior:** Returns an honest prerequisite message if `alz_query_by_id` tool is not available. The extension is wired and ready, automatically activating once Atlas's tool lands. No fake data, no `Math.random()`, no guessed remediation URLs.

**Corrections applied:**
1. Removed `Math.random()` fake failure data. v0 returns a clear prerequisite message instead.
2. Removed guessed Microsoft Learn URLs. v1 will add remediation via `microsoft-learn-mcp` search.
3. Added terminology section to catalog.md explaining "skill" vs "extension".
4. Verified decision record exists locally at `.squad/decisions/inbox/iris-skill-catalog-v0.md` (gitignored inbox, Scribe merges post-PR).
