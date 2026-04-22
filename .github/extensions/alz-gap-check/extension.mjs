import { joinSession } from "@github/copilot-sdk/extension";

/**
 * ALZ Gap Check Extension
 * 
 * Composes this server's alz_query_by_id tool with optional microsoft-learn lookups
 * to surface ALZ checklist gaps in a ranked, remediation-ready table.
 * 
 * Trigger phrases:
 * - "ALZ gap check"
 * - "check my landing zone for ALZ gaps"
 * - "alz-gap-check on subscription X"
 * 
 * Outcome: Returns a ranked list of ALZ checklist items the target subscription
 * or management group fails, with source query ID and remediation pointer.
 */

const session = await joinSession({
    tools: [
        {
            name: "alz_gap_check",
            description: `Run an Azure Landing Zone (ALZ) checklist gap analysis against a subscription or management group.
Returns a ranked list of failed ALZ checklist items with severity, failed resource count, source query ID, and remediation guidance.

This tool orchestrates calls to the MCP server's 'alz_query_by_id' tool (one per checklist query) and optionally fetches remediation docs from the microsoft-learn-mcp companion server.

Read-only. Never proposes mutations, only suggests Bicep/Terraform follow-ups.`,
            parameters: {
                type: "object",
                properties: {
                    scope: {
                        type: "string",
                        description: "Azure subscription ID or management group ID to analyze. Examples: 'a1b2c3d4-...' (subscription GUID) or 'mg-prod' (management group)."
                    },
                    design_area: {
                        type: "string",
                        enum: ["Identity", "Network", "Security", "Management", "Governance", "Platform", "LandingZones"],
                        description: "Optional filter: only run queries for this ALZ design area. Omit to check all areas."
                    },
                    severity_threshold: {
                        type: "string",
                        enum: ["Critical", "High", "Medium", "Low"],
                        description: "Optional filter: only surface failures at or above this severity. Defaults to 'Medium'."
                    },
                    top_n: {
                        type: "number",
                        description: "Return only the top N failures ranked by severity and count. Defaults to 10."
                    },
                    include_remediation: {
                        type: "boolean",
                        description: "Reserved for v1. Whether to fetch remediation guidance from microsoft-learn-mcp. Defaults to false in v0."
                    }
                },
                required: ["scope"]
            },
            handler: async (args, invocation) => {
                const {
                    scope,
                    design_area,
                    severity_threshold = "Medium",
                    top_n = 10,
                    include_remediation = false
                } = args;

                await session.log(`Starting ALZ gap check for scope: ${scope}`);

                // v0 prerequisite check: Does the client have alz_query_by_id tool?
                // This extension requires the MCP server's alz_query_by_id tool (Atlas's PR)
                // Since we cannot inspect available tools at runtime in this SDK version,
                // we document the prerequisite and return a clear message if it's missing.
                
                // TODO: Once the Copilot CLI SDK exposes tool introspection, detect availability automatically
                // For now, we return a prerequisite message directing the user to Atlas's PR
                
                const prerequisiteMessage = `# ALZ Gap Check: Prerequisite Tool Missing

**alz-gap-check** requires the \`alz_query_by_id\` tool from the \`mcp-server-azure-architect\` MCP server.

**Status:** This extension is wired and ready. The upstream tool is being shipped by Atlas in a parallel PR.

**Next steps:**
1. Wait for Atlas's \`alz_query_by_id\` tool to merge (tracked in the mcp-server-azure-architect repository)
2. Ensure your \`.copilot/mcp-config.json\` includes the \`mcp-server-azure-architect\` server entry
3. Reload MCP servers with \`mcp_reload\`
4. Re-run this gap check

**What this tool will do once the prerequisite lands:**
- Invoke \`alz_query_by_id\` in parallel for each relevant ALZ checklist query
- Aggregate failures and rank by severity (Critical > High > Medium > Low) and count
- Return a markdown table with columns: Checklist ID, Design Area, Severity, Failed Count, Description, Source Query
- v1: Optionally fetch remediation guidance from \`microsoft-learn-mcp\` (requires \`include_remediation=true\`)

**Requested scope:** \`${scope}\`
**Design area filter:** ${design_area || "All"}
**Severity threshold:** ${severity_threshold}
**Top N:** ${top_n}

For implementation details, see: \`.github/extensions/alz-gap-check/extension.mjs\``;

                await session.log("Prerequisite check: alz_query_by_id tool not yet available");

                return {
                    textResultForLlm: prerequisiteMessage,
                    resultType: "success"
                };
            }
        }
    ]
});

await session.log("alz-gap-check extension loaded");
