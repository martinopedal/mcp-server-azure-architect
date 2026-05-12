# Usage Guide

Guidance for end users invoking `mcp-server-azure-architect` tools via MCP clients (Claude Desktop, Copilot CLI, VS Code Copilot, others).

## Who This Guide Is For

You are an architect, infrastructure engineer, or cloud operations lead who uses the MCP server via a client (Claude Desktop, Copilot CLI, or third-party tools). This guide explains how to safely invoke tools and handle results without exposing sensitive data.

For **operators** deploying and maintaining the server, see `docs/runbook.md` and `docs/install/deployment-guide.md`.

## Sensitive Data in Query Results

Query results from `alz_scorecard`, `alz_query_by_id`, and `alz_query_list` may contain **sensitive data** that should not be logged, shared publicly, or persisted without review.

### Examples of Sensitive Data

- **Connection strings** in resource configurations (e.g., database passwords, API keys in app settings)
- **Resource tags** containing secrets or internal metadata (e.g., `env=prod`, `cost-center=12345`, custom tags with private info)
- **Private IP addresses** of internal VNets, subnets, and compute resources
- **Managed identity object IDs** that can be used to enumerate Entra ID directory
- **Diagnostic settings** revealing data sink destinations and retention policies
- **Role assignments** showing who has elevated permissions on sensitive scopes

Example: A scorecard result may include tag names from resources evaluated by the ALZ checklist. If your tags contain business-sensitive metadata (budget codes, project names), those become part of the result and should be treated as sensitive.

### Treatment of Results

Always assume query results are **sensitive** and:

- **Do not paste results into shared documents, wikis, or public issue trackers** without reviewing for secrets, tags, or internal metadata.
- **Do not log results to stdout, application logs, or cloud logging services** without redaction. Logs are often indexed and searchable by other team members.
- **Do not share results via unencrypted email, Slack, or Teams.** If sharing is necessary, use your organization's secure file transfer or communication channel (VPN, encrypted email, etc.).
- **Redact identifiable information** before including results in architecture decision records, compliance documentation, or incident reports. For example, replace actual subscription IDs with placeholder names (Sub-001, Sub-002, etc.) and redact resource names if they reveal business logic.

If you need to share a query result with a colleague, download it, review it locally, redact as needed, then share the redacted version via a secure channel.

## Scope Guidance

To minimize the blast radius of a query and reduce the risk of exposing unrelated sensitive data, prefer **narrow scopes** over broad ones.

### Resource Group > Subscription

Always specify a **resource group** when possible, rather than evaluating an entire subscription:

```
Good: Query resource group "rg-prod-web" (scoped, focused)
Less ideal: Query subscription "prod" (large, may include many teams' resources)
```

The ALZ checklist queries support resource group scopes via the ARG `where subscriptionId == "..." and resourceGroup == "..."` filter. Some tools may not expose this parameter; in those cases, run the scorecard at the subscription level but document the scope in your findings.

### One Subscription Per Call

Evaluation tools (`alz_scorecard`) process one subscription at a time. If you need to evaluate multiple subscriptions, make separate calls:

```
One call: alz_scorecard(subscription_id="12345...")
Two subscriptions: Call alz_scorecard twice, once for each subscription.
```

Do not attempt to combine results from multiple subscriptions in a single query. Combining shifts the context and can lead to incorrect analysis (e.g., comparing prod and non-prod resource counts as if they were peers).

### Understand Your Audience

Before running a query, consider:

- **Who will see the results?** If the results will be shared with the broader team, choose a narrower scope or abstract away identifiable metadata.
- **What is the compliance impact?** If you are generating evidence for a compliance audit (SOC 2, HIPAA, PCI DSS), results are audit artifacts and must be retained securely. Follow your organization's audit evidence retention policy.
- **Is there a reason to keep these results?** Transient queries (one-time design reviews) can be discarded. Long-term evidence (compliance audits, breach investigations) must be archived with appropriate access controls.

## Result Handling Best Practices

### Local Processing Only

Run queries and process results locally on your trusted workstation or a secure CI/CD environment, not on shared systems (chat bots, shared VMs, development servers).

### Redaction Before Sharing

Before sharing any result outside your immediate team:

1. Export the result to a JSON file.
2. Redact sensitive fields (subscription IDs, resource names, IP addresses) using a text editor or script.
3. Share the redacted version via your organization's secure channel.

Example redaction:

```json
{
  "subscription_id": "SUB-001",           // was "12345678-1234-1234-1234-123456789abc"
  "results": [
    {
      "checklist_id": "reliability-001",
      "status": "pass",
      "message": "Tags present on <resource-type> [REDACTED]"
    }
  ]
}
```

### Archive with Access Controls

If you are archiving results for compliance:

1. Store results in a secure location with restricted access (e.g., Azure Blob Storage with managed identity, an encrypted file share, a password-protected document repository).
2. Document the retention period and destruction date in your organization's records.
3. Enforce a formal access control process (e.g., ticket-based approval for viewing audit evidence).

## Organizational Policy Template

Your organization should establish a **data handling policy** for tool results. This template can be adapted to your governance model:

---

### **Azure Architect Tool Results Policy**

**Scope:** All results from `mcp-server-azure-architect` query tools (ALZ scorecard, compliance checks, pricing lookups).

**Classification:** All query results are `[INTERNAL / CONFIDENTIAL / TOP SECRET]` depending on the subscription. Queries may expose resource names, configurations, and metadata that reveal business logic or security posture.

**Permitted Uses:**

- Architecture design reviews (confidential to architecture team).
- Compliance audits and evidence generation (confidential to audit team, retained per regulatory requirement).
- Incident response and root cause analysis (confidential to incident commander and team, destroyed per incident retention policy).
- Performance or cost optimization studies (shared with finance and operations teams).

**Prohibited Uses:**

- Pasting results into public issue trackers, wikis, or documentation.
- Sharing via unencrypted email or chat (Teams, Slack, Discord) without redaction.
- Logging results to central log aggregators (Splunk, Datadog, Application Insights) without redaction.
- Committing results to source control repositories.
- Using results to train external ML models or LLMs without explicit data handling agreement.

**Handling:**

- Store results locally during analysis. Archive long-term results in secure cloud storage (Azure Blob with RBAC, SharePoint with restricted access).
- Redact resource names, subscription IDs, and custom tags before sharing.
- Document the query parameters, result date, and intended retention period.
- Destroy results after use unless a regulatory or contractual requirement mandates retention.

**Audit Trail:**

- Log query invocations in the MCP server's audit log (see `docs/install/deployment-guide.md`).
- Retain audit logs for 90+ days per compliance requirements.

**Contact:** Data Office / Compliance Team

---

Adapt the classifications, permitted uses, and contact details to match your organization's data governance framework. Share this policy with all teams using the MCP server.

## Links

- **Deployment and Operations:** `docs/install/deployment-guide.md`
- **Operator Runbook:** `docs/runbook.md`
- **Threat Model and Security Considerations:** `docs/threat-model.md` (if available)
- **Compliance Guidance:** Contact your organization's Data Office or Compliance team
