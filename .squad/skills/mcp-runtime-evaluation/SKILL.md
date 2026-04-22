# SKILL: MCP Runtime Evaluation

## Purpose

Evaluate and compare runtime options (Python, TypeScript, .NET, Go, Rust, etc.) for an MCP server implementation using a structured rubric. This skill provides a reusable decision framework for any MCP server project.

## When to Use

- Starting a new MCP server project and need to choose a runtime.
- Re-evaluating an existing MCP server runtime due to performance, contributor friction, or ecosystem changes.
- Documenting a runtime decision in an ADR.

## Evaluation Criteria

### 1. MCP SDK Maturity (Weight: 3)
- Is there an official MCP SDK for this runtime?
- Is it Tier 1 (Linux Foundation or Microsoft backing)?
- Does it support client and server roles?
- Is it actively maintained with recent commits?
- **Scoring:** 10 = official Tier 1, 7 = community-supported, 4 = unofficial, 1 = none.

### 2. Azure SDK Quality (Weight: 4)
- Does the runtime have GA Azure SDKs for Resource Graph, Key Vault, Storage, Identity?
- Is DefaultAzureCredential supported?
- Is the SDK actively maintained by Microsoft?
- **Scoring:** 10 = gold standard (.NET), 8 = mature (Python), 7 = solid (TypeScript), 4 = experimental, 1 = none.

### 3. Cold Start Performance (Weight: 5)
- Measure time from process start to first tool invocation.
- Requirement: typically <1 second for CLI tools, <500ms for serverless.
- **Scoring:** 10 = <200ms, 9 = 200-500ms, 8 = 500-1000ms, 6 = 1-2s, 3 = >2s.

### 4. Install/Distribution (Weight: 3)
- How easy is it to distribute the MCP server as a tool?
- Does the ecosystem support ephemeral runs (uvx, npx) or require global install (dotnet tool, cargo install)?
- **Scoring:** 10 = ephemeral (npx, uvx), 8 = global tool with manifest (dotnet tool), 6 = manual install, 3 = complex.

### 5. JSON Schema Tooling (Weight: 3)
- How easy is it to generate JSON Schema from type definitions?
- Per MCP spec ([modelcontextprotocol.io/specification/tools#tool-definition-schema](https://modelcontextprotocol.io/specification/tools#tool-definition-schema)), inputSchema must be JSON Schema.
- **Scoring:** 10 = auto-generated from types, 8 = library-assisted, 6 = manual, 3 = verbose.

### 6. Ecosystem Fit (Weight: 2)
- Does the runtime align with the project's target audience (ops, data, enterprise, web)?
- Are companion MCP servers in this runtime?
- **Scoring:** 10 = perfect fit, 7 = good fit, 4 = neutral, 1 = mismatch.

### 7. Contributor Friction (Weight: 4)
- How easy is it for contributors to get started?
- Does the runtime require a build step?
- Is the language ubiquitous or niche?
- **Scoring:** 10 = ubiquitous + no build (Python), 8 = common + build (TypeScript, Go), 6 = enterprise-heavy (C#, Java), 3 = niche (Rust, Kotlin).

### 8. MCP Inspector Compatibility (Weight: 5)
- Does the MCP SDK ship with inspector-compatible tool listings?
- Can the server be tested with MCP Inspector in CI?
- **Scoring:** 10 = yes (all Tier 1 SDKs), 5 = partial, 1 = no.

## Decision Process

1. Score each runtime on all 8 criteria (1-10).
2. Multiply score by weight.
3. Sum weighted scores for each runtime.
4. Recommend the highest-scoring runtime.
5. Document in an ADR with references to MCP spec, SDK repos, and Microsoft Learn (for Azure SDKs).

## Example Scorecard (from ADR-001)

| Criterion | Weight | Python | TypeScript | .NET |
|-----------|--------|--------|------------|------|
| MCP SDK Maturity | 3 | 9 | 9 | 9 |
| Azure SDK Quality | 4 | 8 | 7 | 10 |
| Cold Start (<1s) | 5 | 9 | 8 | 7 |
| Install/Distribution | 3 | 8 | 9 | 8 |
| JSON Schema Tooling | 3 | 8 | 9 | 8 |
| Ecosystem Fit | 2 | 9 | 7 | 6 |
| Contributor Friction | 4 | 9 | 7 | 6 |
| MCP Inspector | 5 | 10 | 10 | 10 |
| **Weighted Total** | | **247** | **229** | **222** |

**Result:** Python wins on cold start (weight 5) and contributor friction (weight 4).

## References

- MCP Specification, Tool Definition Schema: [modelcontextprotocol.io/specification/tools#tool-definition-schema](https://modelcontextprotocol.io/specification/tools#tool-definition-schema)
- MCP SDKs Overview: [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)
- Python SDK: [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- TypeScript SDK: [github.com/modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk)
- C# SDK: [github.com/modelcontextprotocol/csharp-sdk](https://github.com/modelcontextprotocol/csharp-sdk)
- Microsoft Learn, Azure SDKs: [learn.microsoft.com/azure](https://learn.microsoft.com/azure)

## Maintenance

Update this skill when:
- New MCP SDKs reach Tier 1 (e.g., Go, Rust).
- Cold start benchmarks change (e.g., .NET AOT improves).
- Distribution tools evolve (e.g., new package managers).
