# SKILL: Wave Plan Synthesis from Deferred Backlog

**Confidence:** Low (2 observations: v0.2 synthesis from Wave 9, v0.3 synthesis from Wave 13)
**Author:** Lead
**Last updated:** 2026-05-17

## When to use

When a batch of deferred issues needs to be organized into a versioned release plan. Triggered by: accumulated `go:needs-research` issues, version milestone planning, or coordinator request for synthesis.

## Steps

1. **Verify issue state first.** Run `gh issue list --state all --label <label>` before reading any derived tables (now.md, task prompts, prior plans). Derived tables lag. GitHub is the source of truth.

2. **Check disk for implementations.** For each issue, grep for the implementation artifacts (source files, tests, docs, CI steps) described in the issue's DoD. Verify CHANGELOG entries match.

3. **Group by implementation shape.** Cluster issues by what they require (code change, docs-only, CI gate, design decision), not by threat severity or issue number. This reveals natural sequencing: CI gates first, parallel code fan-out, docs last.

4. **Identify dependency chains.** Look for explicit "depends on" relationships (e.g., #61 log permissions depends on #58 audit logging). Also look for implicit ones (e.g., pagination changes break tool signatures, requiring SemVer consideration).

5. **Match v0.2 plan shape exactly.** Use the same document structure: Goal, Scope (In) with sub-themes, Out of Scope, Sequencing, Open Questions. Per-issue bullets include: title, owner, effort (S/M/L), MCP-shape rationale, dependencies, acceptance criteria.

6. **Name trade-offs explicitly.** Every architectural call (theme choice, what to defer, what to close) gets a named trade-off. "We could X, but Y. We chose Z because W."

7. **Escalate, don't decide.** Release timing, version numbering, and scope additions are Martin's calls. The plan proposes and names trade-offs; Martin decides.

## Observations

### v0.2 synthesis (Wave 9, 2026-05-13)
- Input: 20-item N1-N20 roadmap from Wave 9 research. 10 already closed, 2 in-flight.
- Output: 5 items scoped, 3 skill items deferred, all security/perf marked as closed.
- Key learning: out-of-scope section is as valuable as in-scope.

### v0.3 synthesis (Wave 13, 2026-05-17)
- Input: 9 issues labeled `go:needs-research`. All 9 already closed.
- Output: verification document, no new scope.
- Key learning: always verify issue state before planning. Stale data in derived tables caused the entire synthesis request to be based on a false premise.
