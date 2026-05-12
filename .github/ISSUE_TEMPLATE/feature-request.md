---
name: Feature request
description: Propose a new MCP tool or skill
title: "feat: "
labels: ["feat", "squad"]
---

## Goal

<!-- What architect workflow does this feature enable? Describe the gap or use case. -->

## Proposed surface

**Tool name:**
<!-- e.g., alz_query_graph -->

**Signature:**
<!-- e.g., alz_query_graph(checklist_id: str, subscription_id: str) -> dict -->

**Returns:**
<!-- e.g., { 'results': [...], 'manifest_commit': str } -->

## Justification

<!-- Why should this be a native tool in this server vs. a companion server?

See docs/adr/0004-companion-server-bar.md (ADR-004) for the decision framework:
- Does native or companion implementation best serve architect workflows?
- Are there upstream tools in azure-mcp or other companions that duplicate this?
- What is the supply chain and auth boundary?

If companion, justify why we should add it to mcp-config.json instead of building native. -->

## Acceptance criteria

- [ ] Tool is read-only (no Azure write calls)
- [ ] Tool signature and returns are documented
- [ ] Tool has unit tests (mocked Azure SDK responses)
- [ ] Tool has TypedDict return schema
- [ ] Tool includes provenance comment for any hard-coded identifiers
- [ ] CHANGELOG.md updated under `[Unreleased]`

## Related ADRs

<!-- Link to relevant ADRs, e.g., ADR-001 (runtime), ADR-002 (vendoring), ADR-003 (read-only), ADR-004 (companion bar) -->

- ADR-004: Companion Server Selection Bar
