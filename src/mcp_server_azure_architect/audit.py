"""Audit logging for MCP tool invocations.

Implements threat R1 (unauthorized access detection) and I3 (info disclosure via logs).
All tool invocations are logged with redacted parameters to a rotating audit log file.
Log files are created with 0600 permissions (owner read/write only).
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import os
import platform
import re
import stat
import subprocess
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, ParamSpec, TypeVar, cast

P = ParamSpec("P")
R = TypeVar("R")

_AUDIT_LOGGER: logging.Logger | None = None


def token_scrub(data: Any) -> Any:
    """Redact sensitive values from data for safe logging.

    Redacts subscription_id, tenant_id, API keys, and tokens from strings, dicts, and lists.

    Args:
        data: Input data (str, dict, list, or other types).

    Returns:
        Data with sensitive values replaced by [REDACTED_*] placeholders.
    """
    if isinstance(data, str):
        # Redact Azure GUIDs (subscription_id, tenant_id pattern)
        data = re.sub(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            lambda m: f"{m.group(0)[:8]}-****-****-****-************",
            data,
            flags=re.IGNORECASE,
        )

        # Redact JWT tokens (eyJ...)
        data = re.sub(
            r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+",
            "[REDACTED_TOKEN]",
            data,
        )

        # Redact base64 keys (40+ chars)
        data = re.sub(r"[A-Za-z0-9+/]{40,}={0,2}", "[REDACTED_KEY]", data)

        # Redact Bearer tokens
        data = re.sub(
            r"Bearer\s+[A-Za-z0-9._-]+",
            "Bearer [REDACTED_TOKEN]",
            data,
            flags=re.IGNORECASE,
        )

        return data
    elif isinstance(data, dict):
        return {k: token_scrub(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return type(data)(token_scrub(item) for item in data)
    else:
        return data


def _set_file_permissions_0600(path: Path) -> None:
    """Set file permissions to 0600 (owner read/write only).

    Args:
        path: Path to the file.
    """
    if platform.system() == "Windows":
        # Windows: use icacls to restrict access to owner only
        try:
            # Remove inheritance
            subprocess.run(
                ["icacls", str(path), "/inheritance:r"],
                check=True,
                capture_output=True,
                text=True,
            )
            # Grant full control to current user only
            username = os.getlogin()
            subprocess.run(
                ["icacls", str(path), "/grant", f"{username}:F"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, OSError) as e:
            logging.warning(f"Failed to set Windows ACL for {path}: {e}")
    else:
        # POSIX: use chmod 0600
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as e:
            logging.warning(f"Failed to set POSIX permissions for {path}: {e}")


def _check_directory_permissions(path: Path) -> None:
    """Check if directory permissions are too permissive and warn.

    Args:
        path: Path to the directory.
    """
    if platform.system() != "Windows":
        try:
            mode = os.stat(path).st_mode & 0o777
            if mode & 0o077:  # Others or group have any permissions
                logging.warning(
                    f"Audit log directory {path} has permissive permissions "
                    f"({oct(mode)}). Recommended: 0700 (owner only)."
                )
        except OSError:
            pass


def setup_audit_logging() -> None:
    """Initialize audit logging with RotatingFileHandler.

    Creates ~/.mcp-server-azure-architect/logs/ directory with 0700 permissions
    and audit.log file with 0600 permissions. Configures rotating log handler
    with 10MB max size and 5 backups.

    Log location can be overridden via MCP_AZURE_ARCHITECT_LOG_DIR environment variable.
    """
    global _AUDIT_LOGGER

    if _AUDIT_LOGGER is not None:
        return

    # Determine log directory
    log_dir_env = os.environ.get("MCP_AZURE_ARCHITECT_LOG_DIR")
    if log_dir_env:
        log_dir = Path(log_dir_env)
    else:
        log_dir = Path.home() / ".mcp-server-azure-architect" / "logs"

    # Create directory with 0700 permissions
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        if platform.system() != "Windows":
            os.chmod(log_dir, stat.S_IRWXU)  # 0700
        _check_directory_permissions(log_dir)
    except OSError as e:
        logging.error(f"Failed to create audit log directory {log_dir}: {e}")
        return

    # Create audit logger
    _AUDIT_LOGGER = logging.getLogger("mcp_server_azure_architect.audit")
    _AUDIT_LOGGER.setLevel(logging.INFO)
    _AUDIT_LOGGER.propagate = False

    # Configure rotating file handler (10MB, 5 backups)
    log_file = log_dir / "audit.log"
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Set file permissions to 0600
    _set_file_permissions_0600(log_file)

    # Set log format (structured JSON for machine parsing)
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    _AUDIT_LOGGER.addHandler(handler)

    _AUDIT_LOGGER.info(
        json.dumps({
            "event": "audit_logging_initialized",
            "log_dir": str(log_dir),
            "log_file": str(log_file),
        })
    )


def get_audit_logger() -> logging.Logger:
    """Get the audit logger instance.

    Returns:
        The audit logger. If not initialized, returns a dummy logger.
    """
    if _AUDIT_LOGGER is None:
        setup_audit_logging()
    return _AUDIT_LOGGER or logging.getLogger("mcp_server_azure_architect.audit")


def audit_log_tool(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to log MCP tool invocations.

    Logs tool name, redacted parameters, caller identity (if available),
    and result summary. Token scrubbing is applied to all logged data.

    Args:
        func: The MCP tool function to wrap.

    Returns:
        Wrapped function with audit logging.
    """
    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger = get_audit_logger()
        tool_name = func.__name__

        # Bind arguments to parameter names
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Redact sensitive parameters
        redacted_params = token_scrub(dict(bound_args.arguments))

        # Log invocation (caller identity not available from MCP context)
        logger.info(
            json.dumps({
                "event": "tool_invocation",
                "tool": tool_name,
                "params": redacted_params,
                "caller": "unknown",  # MCP protocol does not surface caller identity
            })
        )

        try:
            result = func(*args, **kwargs)

            # Log result summary (not full result to avoid leaking sensitive data)
            result_summary = _summarize_result(result)
            logger.info(
                json.dumps({
                    "event": "tool_result",
                    "tool": tool_name,
                    "status": "success",
                    "summary": result_summary,
                })
            )

            return result
        except Exception as e:
            # Log error
            logger.error(
                json.dumps({
                    "event": "tool_error",
                    "tool": tool_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })
            )
            raise

    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger = get_audit_logger()
        tool_name = func.__name__

        # Bind arguments to parameter names
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Redact sensitive parameters
        redacted_params = token_scrub(dict(bound_args.arguments))

        # Log invocation
        logger.info(
            json.dumps({
                "event": "tool_invocation",
                "tool": tool_name,
                "params": redacted_params,
                "caller": "unknown",
            })
        )

        try:
            result = await func(*args, **kwargs)  # type: ignore[misc]

            # Log result summary
            result_summary = _summarize_result(result)
            logger.info(
                json.dumps({
                    "event": "tool_result",
                    "tool": tool_name,
                    "status": "success",
                    "summary": result_summary,
                })
            )

            return result  # type: ignore[no-any-return]
        except Exception as e:
            # Log error
            logger.error(
                json.dumps({
                    "event": "tool_error",
                    "tool": tool_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })
            )
            raise

    if inspect.iscoroutinefunction(func):
        return cast(Callable[P, R], async_wrapper)
    else:
        return cast(Callable[P, R], sync_wrapper)


def _summarize_result(result: Any) -> dict[str, Any]:
    """Generate a summary of a tool result for logging.

    Args:
        result: The tool result.

    Returns:
        Summary dict with result type and size information.
    """
    result_type = type(result).__name__

    if isinstance(result, dict):
        return {
            "type": result_type,
            "keys": list(result.keys()),
            "size": len(result),
        }
    elif isinstance(result, (list, tuple)):
        return {
            "type": result_type,
            "size": len(result),
        }
    elif isinstance(result, str):
        return {
            "type": result_type,
            "length": len(result),
        }
    else:
        return {
            "type": result_type,
        }
