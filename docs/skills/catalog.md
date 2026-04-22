# Copilot CLI Skills Catalog

Orchestration skills for Azure architects. Each skill composes MCP tools from this server and companion servers to deliver a cohesive architect workflow.

## Terminology

Project docs use "skill" as the conceptual term for orchestration workflows. Copilot CLI's execution format is called an "extension" and lives in `.github/extensions/`. We use "skill" in design conversation and "extension" when referring to the on-disk artifact.

**Naming convention:**
- Conceptual: "alz-gap-check skill" (user-facing, documentation)
- Implementation: `.github/extensions/alz-gap-check/extension.mjs` (on-disk artifact)
- Tool name: `alz_gap_check` (registered in Copilot CLI, snake_case per MCP conventions)

## Skills

### alz-gap-check

**Status:** v0 (shipped)  
**Owner:** Iris  
**Type:** Copilot CLI Extension  
**Path:** `.github/extensions/alz-gap-check/extension.mjs`

**Trigger phrases:**
- "ALZ gap check"
- "check my landing zone for ALZ gaps"
- "alz-gap-check on subscription X"

**Outcome:**  
Returns a ranked list of ALZ checklist items the target subscription or management group fails, with source query ID and remediation pointer.

**Inputs:**
- `scope` (required): Azure subscription ID or management group ID
- `design_area` (optional): Filter to a specific ALZ design area
- `severity_threshold` (optional): Minimum severity to surface. Defaults to Medium.
- `top_n` (optional): Return only the top N failures. Defaults to 10.
- `include_remediation` (optional): Reserved for v1. Defaults to false in v0.

**Dependencies:**
- **MCP tools:** `alz_query_by_id` (from this server, shipped by Atlas)
- **Companion servers:** `microsoft-learn-mcp` (optional, for v1 remediation lookups)

**Behavior:**
1. **v0 (current):** Returns a prerequisite message if `alz_query_by_id` tool is not available. The extension is wired and ready, automatically activating once Atlas's tool lands.
2. **v1 (future):** Invokes `alz_query_by_id` for each query in parallel, aggregates failures, returns ranked table.
3. **v2 (future):** Add remediation guidance column via `microsoft-learn-mcp` search.

**Boundaries:**
- Read-only. Never proposes a mutation.
- If `alz_query_by_id` is not yet available, returns an honest degraded-behavior message.

**Testing:**
- Replay scenario: `tests/skills/test_alz_gap_check_replay.md`

---

## Roadmap

Future skills: design-review, runner-sizing, ingress-migration-plan, quota-plan, policy-as-code-suggest.
