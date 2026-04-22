"""Azure client helpers with lazy credential initialization."""

import re

from azure.identity import DefaultAzureCredential

_credential: DefaultAzureCredential | None = None


def get_credential() -> DefaultAzureCredential:
    """Lazily construct and return a DefaultAzureCredential.

    This defers credential initialization until first use to minimize cold start time.

    Returns:
        Azure DefaultAzureCredential instance.
    """
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def token_scrub(text: str) -> str:
    """Remove potential Azure tokens from text for safe logging.

    Args:
        text: Input text that may contain tokens.

    Returns:
        Text with tokens replaced by [REDACTED].
    """
    # Pattern for Azure AD tokens (JWT format: xxx.yyy.zzz)
    jwt_pattern = r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+"

    # Pattern for potential access keys (base64-like strings of 40+ chars)
    key_pattern = r"[A-Za-z0-9+/]{40,}={0,2}"

    text = re.sub(jwt_pattern, "[REDACTED_TOKEN]", text)
    text = re.sub(key_pattern, "[REDACTED_KEY]", text)

    return text
