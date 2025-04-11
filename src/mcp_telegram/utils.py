"""
Utility functions for the MCP Telegram module.
"""

import re
import uuid

from pathlib import Path

from telethon.tl import patched  # type: ignore


def parse_entity(entity: str) -> int | str:
    """
    Parse a string entity identifier as an integer ID.

    If the string represents a valid integer (potentially negative), it's
    returned as an `int`. Otherwise, the original string (assumed to be
    a username or phone number) is returned.

    Args:
        entity (`str`): The entity (ID, username, phone number, or "me").

    Returns:
        `int | str`: The parsed integer ID or the original string identifier.
    """
    return int(entity) if entity.lstrip("-").isdigit() else entity


def get_unique_filename(message: patched.Message) -> str:
    """Generate a unique filename for a message media.

    Args:
        message (`patched.Message`): The message to generate a filename for.

    Returns:
        `str`: The unique filename.
    """

    unique_prefix = str(uuid.uuid4())

    original_filename = None
    original_suffix = ""

    if message.file and isinstance(message.file.name, str):
        original_filename = Path(message.file.name).stem
        original_suffix = Path(message.file.name).suffix

    if original_filename:
        filename = f"{original_filename}_{unique_prefix}{original_suffix}"
    else:
        # Fallback if no original name (use message_id and media type if possible)
        fallback_name = f"download_{message.id}_{unique_prefix}"
        if message.file and isinstance(message.file.mime_type, str):
            # Try to get extension from mime type (basic implementation)
            parts = message.file.mime_type.split("/")
            if len(parts) == 2 and parts[1]:
                filename = f"{fallback_name}.{parts[1]}"
            else:
                filename = fallback_name
        else:
            filename = fallback_name

    return filename


def parse_telegram_url(url: str) -> tuple[str | int, int] | None:
    """Parse a Telegram message URL to extract the entity and message ID.

    Handles common formats like:
    - `https://t.me/username/123`
    - `t.me/username/123`
    - `https://telegram.me/username/123`
    - `telegram.me/username/123`
    - `https://t.me/c/1234567890/123`

    Args:
        url (`str`): The Telegram URL to parse.

    Returns:
        `tuple[str | int, int] | None`: A tuple containing the entity
                                      (username string or channel_id integer
                                      in -100... format) and the message ID integer,
                                      or None if the URL format is not recognized.
    """
    # Regex to capture the entity (username or channel_id) and message ID
    pattern = r"(?:https?://)?t(?:elegram)?\.me/c/(\d+)/(\d+)"

    match = re.match(pattern, url)

    if match:
        try:
            entity = parse_entity(match.group(1))
            message_id = int(match.group(2))
        except Exception:
            return None

        return entity, message_id

    return None
