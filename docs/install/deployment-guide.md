# Deployment Guide

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
{"timestamp": "2026-04-22T14:30:00+0000", "level": "INFO", "message": {"event": "tool_invocation", "tool": "alz_scorecard", "params": {"subscription_id": "12345678-****-****-****-************", "pillar": "checklist"}, "caller": "unknown"}}
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
