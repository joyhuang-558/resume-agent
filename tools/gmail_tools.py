"""
Gmail toolkit helpers for integrating Agno GmailTools with this project.
"""
import logging
from typing import Optional, Sequence

logger = logging.getLogger(__name__)

# Read-only functions that are safe for resume screening workflows.
READ_ONLY_GMAIL_FUNCTIONS = [
    "get_latest_emails",
    "get_emails_from_user",
    "get_unread_emails",
    "get_starred_emails",
    "get_emails_by_context",
    "get_emails_by_date",
    "get_emails_by_thread",
    "search_emails",
    "list_custom_labels",
]

# Mutating functions we intentionally block.
MUTATING_GMAIL_FUNCTIONS = [
    "create_draft_email",
    "send_email",
    "send_email_reply",
    "mark_email_as_read",
    "mark_email_as_unread",
    "apply_label",
    "remove_label",
    "delete_custom_label",
]


def create_readonly_gmail_tools(
    credentials_path: Optional[str] = None,
    token_path: Optional[str] = None,
    scopes: Optional[Sequence[str]] = None,
    port: Optional[int] = None,
):
    """
    Create a GmailTools toolkit limited to read-only functions whenever possible.
    """
    try:
        from agno.tools.gmail import GmailTools
    except ImportError as exc:
        raise ImportError(
            "GmailTools is unavailable. Install Gmail dependencies and ensure "
            "the current agno version includes agno.tools.gmail."
        ) from exc

    base_kwargs = {}
    if credentials_path:
        base_kwargs["credentials_path"] = credentials_path
    if token_path:
        base_kwargs["token_path"] = token_path
    if scopes:
        base_kwargs["scopes"] = list(scopes)
    if port is not None:
        base_kwargs["port"] = port

    # Prefer allow-listing read-only functions.
    try:
        return GmailTools(include_tools=READ_ONLY_GMAIL_FUNCTIONS, **base_kwargs)
    except TypeError:
        logger.debug("GmailTools does not support include_tools; trying exclude_tools fallback.")

    # Fallback to deny-listing mutating functions.
    try:
        return GmailTools(exclude_tools=MUTATING_GMAIL_FUNCTIONS, **base_kwargs)
    except TypeError:
        logger.warning(
            "GmailTools could not be restricted to read-only mode with include/exclude filters. "
            "Tool is enabled without function-level restrictions."
        )
        return GmailTools(**base_kwargs)
