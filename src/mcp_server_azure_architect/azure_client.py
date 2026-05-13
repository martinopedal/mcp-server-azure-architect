"""Azure client helpers with lazy credential initialization."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

_credential: DefaultAzureCredential | None = None
_authorized_subscriptions: dict[int, set[str]] = {}


def get_credential() -> DefaultAzureCredential:
    """Lazily construct and return a DefaultAzureCredential.

    This defers credential initialization until first use to minimize cold start time.
    The azure.identity import happens inside this function to avoid ~435ms import cost
    at module load time (perf: issue #67).

    Returns:
        Azure DefaultAzureCredential instance.
    """
    global _credential
    if _credential is None:
        from azure.identity import DefaultAzureCredential

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


def scrub_subscription_id(subscription_id: str) -> str:
    """Redact most of a subscription ID for safe logging.

    Args:
        subscription_id: Azure subscription ID (GUID format).

    Returns:
        Redacted subscription ID (e.g., 12345678-****-****-****-************).
    """
    if len(subscription_id) < 36:
        return subscription_id[:8] + "-****-****-****-************"
    return subscription_id[:8] + "-****-****-****-************"


def validate_caller_scope(subscription_id: str, credential: DefaultAzureCredential) -> bool:
    """Validate that subscription_id is in the caller's authorized scope.

    Queries Azure Resource Manager to enumerate subscriptions accessible by the
    credential, then checks if the requested subscription_id is in that list.
    Results are cached per credential instance to avoid repeated ARM calls.

    This defends against confused-deputy attacks where an AI agent is tricked
    into probing subscriptions outside the caller's scope (Threat S1, issue #57).

    Args:
        subscription_id: Azure subscription ID to validate.
        credential: DefaultAzureCredential instance.

    Returns:
        True if subscription_id is in the caller's scope, False otherwise.

    Raises:
        Exception: If ARM call to list subscriptions fails.
    """
    cred_id = id(credential)

    # Check cache
    if cred_id not in _authorized_subscriptions:
        # Lazy import to minimize cold-start overhead
        from azure.mgmt.subscription import SubscriptionClient

        logger.info("Enumerating authorized subscriptions for scope validation")
        client = SubscriptionClient(credential=credential)

        try:
            # List all subscriptions accessible to this credential
            subs = client.subscriptions.list()
            sub_ids: set[str] = set()
            for sub in subs:
                if sub.subscription_id is not None:
                    sub_ids.add(sub.subscription_id)
            _authorized_subscriptions[cred_id] = sub_ids
            logger.info(f"Cached {len(sub_ids)} authorized subscription(s)")
        except Exception as e:
            scrubbed_error = token_scrub(str(e))
            logger.error(f"Failed to enumerate subscriptions: {scrubbed_error}")
            raise

    authorized = _authorized_subscriptions[cred_id]
    is_valid = subscription_id in authorized

    if not is_valid:
        scrubbed_id = scrub_subscription_id(subscription_id)
        logger.warning(f"Subscription ID validation failed: {scrubbed_id} is not in caller's scope")

    return is_valid
