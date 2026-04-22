# Sage: Research and Documentation History

## Learnings

### 2026-04-22: ADR-001 Runtime Choice

**Decision:** Recommended Python with FastMCP for the MCP server runtime.

**Key Citations:**
- MCP Specification, Tool Definition Schema: [modelcontextprotocol.io/specification/tools#tool-definition-schema](https://modelcontextprotocol.io/specification/tools#tool-definition-schema)
- MCP SDKs Overview: [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)
- All three candidate runtimes (Python, TypeScript, .NET) are Tier 1 MCP SDKs with official support from Linux Foundation (Python, TS) or Microsoft (.NET).
- Cold start benchmarks: Python FastMCP 200-800ms, TypeScript 300-700ms, .NET 300-1500ms (optimized <500ms with AOT).
- Azure SDK quality: .NET is gold standard (10/10), Python is mature (8/10), TypeScript is solid (7/10).

**Gotchas Discovered:**
1. **Cold start is measurable but not always documented.** FastMCP does not publish official cold start metrics. Had to infer from multi-language benchmarks and typical Python import times.
2. **MCP Inspector compatibility is a CI gate.** All three SDKs pass, but this is non-negotiable. Must validate in CI on every PR.
3. **JSON Schema generation varies by runtime.** FastMCP auto-generates from type hints (easiest). TypeScript requires `typescript-json-schema` (predictable). .NET uses reflection with `NJsonSchema` (enterprise-friendly).
4. **Distribution story matters.** uvx (Python), npx (TypeScript), dotnet tool (.NET) all work, but uvx and npx are ephemeral-first, while dotnet tool requires explicit install. For a tool, ephemeral is better.
5. **Contributor friction is not just language familiarity.** Build steps, type system strictness, and ecosystem norms all factor in. Python wins on no-build-step, TypeScript loses on tsc requirement, .NET loses on enterprise-heavy perception.

**Weighted Decision Criteria:**
- Scored on 8 criteria: MCP SDK maturity, Azure SDK quality, cold start, install/distribution, JSON Schema tooling, ecosystem fit, contributor friction, MCP Inspector compatibility.
- Python: 247, TypeScript: 229, .NET: 222.
- Cold start (weight 5) and contributor friction (weight 4) tipped the scale toward Python.

**Skill Extraction Candidate:**
- MCP SDK comparison rubric (8 criteria, weights, scoring guide). Could be generalized for any MCP server runtime decision. Will write `.squad/skills/mcp-runtime-evaluation/SKILL.md` if pattern reuse is needed.

---

### 2026-04-22: Cold-Start Performance Investigation (Incoming)

**Incoming issue:** "perf: Investigate cold-start overhead (target <800ms)" — assigned squad:sage.

Forge measured 1048ms on cold start (48ms over ADR-001 target). Lead approved with nits and opened this investigation for you. Scope: profile `mcp[cli]` import cost vs minimal `mcp` dependency, test lazy imports for azure-identity, confirm Python 3.11 baseline (dev machine appeared to be running 3.14). Goal: bring measured cold start under 800ms or update ADR with revised expectation and citation.
