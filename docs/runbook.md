# Operator Runbook

How to run and troubleshoot `mcp-server-azure-architect` in production and development workflows.

## Daily Operation

An architect's typical workflow:

1. **Pre-design checklist.** Before a design review:
   ```bash
   # List ALZ gaps for a subscription
   mcp-exec alz_query_list --source checklist | jq '.items[] | .checklist_id'
   
   # Run a quick scorecard to surface compliance posture
   mcp-exec alz_scorecard --subscription-id <sub-id>
   ```

2. **During-design queries.** When evaluating options:
   ```bash
   # Fetch a specific ALZ query to understand the check
   mcp-exec alz_query_by_id --checklist-id <id>
   
   # Compare pricing for sizing candidates
   mcp-exec pricing_compare_skus --skus Standard_D4s_v5,Standard_D8s_v5 --region eastus
   ```

3. **Post-decision documentation.** When recording decisions:
   - Use `alz_scorecard` to capture baseline before implementation.
   - Reference query citations (in tool response) in architecture decision records.
   - Link to `docs/companions/` for schema details on vendor-specific readiness.

## Authentication

The server uses Azure `DefaultAzureCredential` chain. Check credentials in this order:

| Environment | Credential Source | Setup |
|---|---|---|
| Local dev | `az login` | Run `az login` once, credentials cached in `~/.azure` |
| CI/CD (GitHub) | Workload Identity | Configure `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` in Actions secrets |
| Prod (Azure) | Managed Identity | Assign identity to the compute resource (VM, App Service, AKS) |
| Service principal | Environment variables | Set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET` |

**Troubleshooting `Unauthorized`:**
1. Check `az account show` outputs a valid subscription.
2. Verify the subscription ID in your query matches a subscription you have access to.
3. For service principal flows, confirm `AZURE_TENANT_ID` is set (not inferred).
4. For managed identity, inspect the Azure compute resource's "Identity" tab in the portal.

## Common Errors

### 1. `LookupError: query 'X' not found`

**Symptom:** `alz_query_by_id` fails with a lookup error.

**Root cause:** Checklist ID does not exist in the vendored ALZ snapshot.

**Fix:**
```bash
# Discover available IDs
mcp-exec alz_query_list | jq '.items[] | .checklist_id' | grep -i 'partial-match'
```

### 2. `httpx.HTTPStatusError: 429 Too Many Requests`

**Symptom:** `pricing_lookup_sku` or `pricing_compare_skus` returns 429.

**Root cause:** Azure Retail Prices API rate-limited (10 req/sec per IP).

**Fix:** Implement backoff. The tools do not retry internally.
```python
import time
for attempt in range(3):
    try:
        result = pricing_lookup_sku(sku, region)
        break
    except HTTPStatusError as e:
        if e.response.status_code == 429:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

### 3. `ClientAuthenticationError: AADSTS...`

**Symptom:** `alz_scorecard` fails with an AAD auth error.

**Root cause:** Azure credentials are missing or expired. `az login` token timed out (token lifetime ~24h).

**Fix:**
```bash
# Refresh credentials
az login
# Or set explicit tenant
export AZURE_TENANT_ID=<your-tenant-id>
az login --tenant <your-tenant-id>
```

### 4. `ResourceNotFound` from `alz_scorecard`

**Symptom:** "Subscription not found" or "Invalid subscription ID".

**Root cause:** `subscription_id` format error or insufficient permissions.

**Fix:**
- Verify format: `00000000-0000-0000-0000-000000000000` (GUID).
- List your subscriptions: `az account list -o table`.
- Confirm the identity (via `az account show`) has Reader role on the target subscription.

### 5. Cold-start hangs on Windows (8-10 seconds)

**Symptom:** First MCP tool call takes 8.5-9.0 seconds on Windows, normal on Linux.

**Root cause:** Python startup time + import graph (measured baseline in ADR-001).

**Fix:** None required. This is expected per ADR-001 cold-start budget (under 2000ms hard gate). Use MCP clients' caching (e.g., Claude Desktop caches results across conversations). If unacceptable, see [docs/perf/coldstart-investigation.md](perf/coldstart-investigation.md) for profiling instructions.

### 6. MCP client says "tool not found"

**Symptom:** Tool is not listed in the MCP client's UI or completions.

**Root cause:** Server is not in the client's `mcp-config.json`, or client did not re-index.

**Fix:**
1. Verify server in config:
   ```bash
   python scripts/mcp_smoke.py
   ```
   Should list all 6 tools and their JSON schemas.

2. Restart the MCP client (reload config).

3. Check the client's logs (e.g., Claude Desktop logs in `~/.claude/logs/`).

## Logging

The server is stateless and produces no log files by default. All state is held in memory.

**Token scrubbing policy:** Any logging must never include Azure tokens, subscription IDs, or query results (per [SECURITY.md](../SECURITY.md)).

**Verbose mode:** FastMCP does not expose a per-tool verbose flag yet. To debug, run with Python logging:
```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG); from mcp_server_azure_architect.server import mcp; mcp.run()"
```

**What NOT to log:**
- Azure credentials (DefaultAzureCredential tokens, managed identity tokens).
- Subscription IDs or resource names in structured logs.
- Scorecard results (may expose internal infrastructure details).

## Maintenance

### Bumping the ALZ Snapshot

The vendored ALZ queries come from two upstream repos:
- `martinopedal/alz-checklist-queries`
- `martinopedal/alz-graph-queries`

**Manual refresh (on-demand):**
```bash
# Trigger via GitHub Actions (requires push access)
gh workflow run refresh-alz-snapshot.yml -f force=true
```

**Automatic refresh (weekly, Mondays 0600 UTC):**
Configured in `.github/workflows/refresh-alz-snapshot.yml`. No action needed.

After the workflow completes:
1. A PR is opened with the updated snapshot.
2. CI runs. If tests pass and no breaking changes, merge.
3. Bump CHANGELOG.md and tag a patch release (per [docs/release.md](release.md) SemVer policy).

### Adding New Tools

See the [CONTRIBUTING.md](../CONTRIBUTING.md) docstring style guide. New tools must:
1. Be read-only (no Azure SDK `Begin*`, `Create*`, `Update*`, `Delete*`).
2. Have a docstring with Args, Returns, and Raises.
3. Have unit tests (pytest).
4. Register via `@mcp.tool()` decorator in `server.py`.
5. Update CHANGELOG.md and README.md tool count.

### Updating Companion Kit

Companion servers (azure-mcp, microsoft-learn, mermaid, drawio, kubernetes, terraform) are wired via `mcp-config.json`.

To update:
```bash
python scripts/install_kit.py --refresh
```

This re-detects your MCP clients and merges the latest companion config. See [docs/companions/README.md](companions/README.md) for per-server details.

## References

- Release procedure: [docs/release.md](release.md)
- Performance baseline: [docs/perf/coldstart-investigation.md](perf/coldstart-investigation.md)
- Security posture: [SECURITY.md](../SECURITY.md)
- Architecture decisions: [docs/adr/](adr/) (ADR-001 runtime, ADR-002 ALZ vendoring, ADR-003 read-only gate, ADR-004 companion bar, ADR-005 SemVer policy)
- MCP spec: [https://spec.modelcontextprotocol.io/](https://spec.modelcontextprotocol.io/)
