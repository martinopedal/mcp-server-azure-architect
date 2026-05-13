# Deployment Guide

Guidance for deploying `mcp-server-azure-architect` to development, staging, and production environments.

## Audit Logging Configuration

The MCP server logs all tool invocations to an audit log for security monitoring and compliance. This implements threat R1 (unauthorized access detection).

### Default Configuration

By default, audit logs are written to:

```
~/.mcp-server-azure-architect/logs/audit.log
```

The log directory and files are created with restricted permissions:
- Directory: `0700` (owner read/write/execute only)
- Log file: `0600` (owner read/write only)

This prevents other users on the system from reading sensitive information in the logs (threat I3 mitigation).

### Log Location Override

To specify a custom log directory, set the environment variable:

```bash
export MCP_AZURE_ARCHITECT_LOG_DIR=/path/to/custom/logs
```

Or in Windows:

```powershell
$env:MCP_AZURE_ARCHITECT_LOG_DIR = "C:\path\to\custom\logs"
```

### Log Rotation

Audit logs use Python's `RotatingFileHandler` with the following settings:
- Maximum file size: 10 MB
- Backup count: 5 files
- Total storage: up to 60 MB (current + 5 backups)

When the current log file reaches 10 MB, it is rotated to `audit.log.1`, and older backups are shifted accordingly. The oldest backup (`.5`) is deleted.

### Log Format

Logs are written in JSON format for machine parsing:

```json
{"timestamp": "2026-04-22T14:30:00+0000", "level": "INFO", "message": {"event": "tool_invocation", "tool": "alz_scorecard", "params": {"subscription_id": "12345678-****-****-****-************", "source": "checklist"}, "caller": "unknown"}}
```

Key fields:
- `event`: Event type (`tool_invocation`, `tool_result`, `tool_error`)
- `tool`: Name of the MCP tool invoked
- `params`: Tool parameters (sensitive values redacted)
- `caller`: Caller identity (currently `unknown` as MCP protocol does not surface this)

### Sensitive Data Redaction

All logged parameters are scrubbed to remove:
- Azure subscription IDs (GUIDs): `aaaaaaaa-****-****-****-************`
- Tenant IDs (GUIDs): redacted in same format
- JWT tokens: replaced with `[REDACTED_TOKEN]`
- API keys (long base64 strings): replaced with `[REDACTED_KEY]`
- Bearer tokens: replaced with `Bearer [REDACTED_TOKEN]`

Query results are **not logged** to avoid leaking sensitive resource data. Only result summaries (e.g., `result_size=N items`, `status=ok|error`) are recorded.

### Immutable Log Storage Upgrade Path

For production environments requiring tamper-proof logs, consider these options:

1. **Forward to syslog**: Configure a syslog forwarder (e.g., `rsyslog`) to send audit logs to a centralized logging system with immutable storage.

2. **Azure Monitor Integration**: Stream logs to Azure Monitor Logs (Log Analytics workspace) for long-term retention and alerting. Use Azure's built-in immutability features.

3. **WORM Storage**: Mount the log directory on write-once-read-many (WORM) storage or use file integrity monitoring (FIM) tools.

Example syslog forwarding (Linux):

```bash
# /etc/rsyslog.d/mcp-audit.conf
module(load="imfile")
input(type="imfile"
      File="/home/username/.mcp-server-azure-architect/logs/audit.log"
      Tag="mcp-audit"
      Severity="info"
      Facility="local0")
local0.* @@central-syslog-server:514
```

### Monitoring and Alerting

Key events to monitor:
- `tool_error`: Tool invocation failures (may indicate misconfigurations or attacks)
- High volume of `tool_invocation` events from unknown callers
- Repeated access to subscription IDs outside approved scope (requires correlation with allowlist)

### Security Considerations

- **Log file permissions**: On startup, the server checks log directory permissions and warns if they are too permissive (e.g., world-readable).
- **Caller identity**: The current MCP protocol implementation does not surface the calling process or user identity. Logs record `caller=unknown`. For attribution, deploy the server behind a proxy that injects identity into tool contexts.
- **Log tampering**: Local file-based logs can be modified by the owner. For tamper-proof audit trails, forward logs to an immutable remote sink.

### Troubleshooting

**Issue**: Logs not appearing in custom directory.

**Solution**: Verify `MCP_AZURE_ARCHITECT_LOG_DIR` is set before starting the server. Check directory permissions allow owner write access.

**Issue**: Warning "audit log directory has permissive permissions".

**Solution**: On POSIX systems, run `chmod 700 /path/to/logs` to restrict access to owner only.

**Issue**: Windows ACL errors.

**Solution**: Ensure the current user has full control over the log directory. The server uses `icacls` to set ACLs automatically, but this requires local admin rights in some configurations.

## Log Tampering Mitigation (Threat R2)

Audit logs are a critical control for compliance audits (SOC 2, ISO 27001, HIPAA). To prevent tampering or deletion, make logs append-only and forward them to a trusted central repository.

### Linux: Append-Only via `chattr`

On Linux, use the `chattr` immutable flag to prevent log deletion or modification:

```bash
# Make audit log append-only
sudo chattr +a /var/log/mcp-server-azure-architect/audit.log

# Verify the attribute
lsattr /var/log/mcp-server-azure-architect/audit.log
# Output: -----a----------- /var/log/mcp-server-azure-architect/audit.log
```

Only `root` can remove the append-only flag. The `+a` flag allows writing new log entries but prevents truncation or overwrite.

### Windows: Audit Policy via Group Policy

On Windows, enforce log integrity via audit event forwarding to a centralized Windows Event Log collector:

1. **Enable audit policy for process creation:**
   ```
   gpedit.msc > Computer Configuration > Windows Settings > Security Settings
   > Event Log > Application > Properties > Retention method: Overwrite as needed
   ```

2. **Forward events to a remote Event Log collector:**
   ```
   wecutil.exe ss EventCollector /c:http://collector-hostname:5985/wsman/SubscriptionManager/WEC
   ```

   This ensures logs are written to a remote server that the local administrator cannot tamper with.

3. **Use Windows Audit Policy to protect the server's own Event Log:**
   ```powershell
   auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
   ```

### Cloud: Azure Monitor Logs (Recommended for Production)

For production deployments, forward audit logs to Azure Monitor Logs (Log Analytics workspace) or an enterprise syslog ingestion service.

**Azure Monitor Logs:**

1. Create a Log Analytics workspace in the Azure portal.
2. Configure the MCP server to send logs to the workspace via Azure Monitor agent or direct HTTP ingestion:

   ```python
   # In future versions, a dedicated tool will abstract this.
   # For now, use the Azure Monitor SDK or a syslog forwarder.
   import logging
   from azure.monitor.opentelemetry import configure_azure_monitor

   configure_azure_monitor(
       connection_string="InstrumentationKey=<your-key>"
   )
   logging.getLogger("mcp_server_azure_architect").addHandler(
       # Azure Monitor handler
   )
   ```

3. Set the workspace retention policy to 90+ days (see Log Retention section below).

**Enterprise Syslog (rsyslog, Splunk, Datadog):**

Forward audit logs via syslog to an enterprise log aggregator:

```bash
# /etc/rsyslog.d/99-mcp-audit.conf
:programname, isequal, "mcp-server-azure-architect" @@syslog-collector.example.com:514
& stop
```

Restart rsyslog:

```bash
sudo systemctl restart rsyslog
```

The double `@@` indicates TCP (reliable). For UDP, use single `@`. Ensure the syslog server is outside your organization's network boundary or runs on a hardened, dedicated host.

## Log Retention

Compliance frameworks require audit log retention for a minimum of 90 days. Many standards (SOC 2 Type II, ISO 27001, HIPAA, GDPR) mandate 90+ day retention to support breach investigations and regulatory audits.

### Self-Hosted Log Rotation

If logs are stored locally, use `logrotate` to compress and archive older logs while retaining them:

```bash
# /etc/logrotate.d/mcp-server-azure-architect
/var/log/mcp-server-azure-architect/audit.log {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 0600 mcp-audit mcp-audit
    postrotate
        systemctl reload mcp-server-azure-architect > /dev/null 2>&1 || true
    endscript
}
```

This keeps 90 days of compressed logs on disk. For long-term retention (e.g., 7 years), archive compressed logs to cloud object storage (Azure Blob Storage, S3).

### Cloud Log Retention

- **Azure Monitor Logs:** Set retention in the workspace to 90 days (default is 30; can extend to 2 years for additional cost).
- **Splunk/Datadog:** Configure data retention policy at the ingestion tier.
- **Cloud Storage (archive):** Use Azure Blob Storage lifecycle policies to move old logs to archive tier after 90 days.

## Security Best Practices

### Run as Non-Privileged User

Never run the MCP server as `root` (Linux) or `Administrator` (Windows). Create a dedicated service user:

```bash
# Linux
sudo useradd -r -s /bin/false -d /var/lib/mcp-server-azure-architect mcp-audit

# Ensure server runs under this user
sudo chown -R mcp-audit:mcp-audit /var/log/mcp-server-azure-architect
sudo chmod 750 /var/log/mcp-server-azure-architect
```

```powershell
# Windows (optional; service wrapper handles this)
# Create a service account with minimal permissions:
# Rights: Log on as a service, Read event log, Network access
```

### Restrict Configuration and Cache Directories

The server stores API credentials, cached query results, and client configuration in `~/.mcp-server-azure-architect/`.

Restrict file permissions to prevent other users from reading cached data:

```bash
# Linux
chmod 700 ~/.mcp-server-azure-architect
chmod 600 ~/.mcp-server-azure-architect/*

# Verify
ls -la ~/.mcp-server-azure-architect/
# drwx------ ... .mcp-server-azure-architect
# -rw------- ... audit.log
```

On Windows, NTFS ACLs are inherited. Verify the directory grants `Full Control` to the service user only:

```powershell
icacls C:\Users\$USER\.mcp-server-azure-architect /grant:r "$USER`:F"
```

### Network Isolation

Restrict egress from the server host to Azure ARM endpoints and configured log collectors only:

```
Egress allowed:
  management.azure.com (ARM)
  graph.microsoft.com (Azure AD, if using Entra for multi-tenant queries)
  <syslog-collector-hostname>:514 (if using syslog)
  <azure-monitor-endpoint> (if using Azure Monitor Logs)

Egress blocked:
  All other destinations (especially public internet, P2P networks)
```

Use network policy (Linux), Windows Firewall rules (Windows), or cloud network ACLs to enforce this.

### Credential Management

The server uses Azure `DefaultAzureCredential` chain (environment variables, managed identity, `az cli`). Never store credentials in configuration files.

For production:

1. Use **Managed Identity** (Azure VMs, App Service, AKS): no credential management required.
2. Use **Workload Identity** (GitHub Actions, external CI/CD): configure `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_FEDERATED_TOKEN_FILE` in the runtime environment only.
3. Use **`az cli` or Environment Variables** for local dev: authenticate once via `az login` and let the server read the token from `~/.azure/`.

Never embed or commit credentials in code, config files, or container images.

See `docs/runbook.md` for detailed authentication troubleshooting.
