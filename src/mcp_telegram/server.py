from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_telegram.telegram import Telegram
from mcp_telegram.types import Contact, Dialog, Message


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifespan manager for the app.

    This will connect to Telegram on startup and disconnect on shutdown.
    """
    try:
        tg.create_client()
        await tg.client.connect()
        yield
    finally:
        tg.client.disconnect()


instructions = """
You are a helpful assistant that can send messages and 
get messages from Telegram users, groups, and channels.
"""

tg = Telegram()
mcp = FastMCP(
    "mcp-telegram",
    lifespan=app_lifespan,
    instructions=instructions,
)


@mcp.tool()
async def send_message(recipient: str, message: str) -> str:
    """Send a message to a Telegram user, group, or channel.

    It allows sending text messages to any Telegram entity identified by `recipient`.

    Args:
        recipient (`str`):
            The identifier of where to send the message. This can be a Telegram
            chat ID, a username, a phone number (in format '+1234567890'), or a
            group/channel username. The special value "me" can be used to send
            a message to yourself.

        message (`str`):
            The text message to be sent. The message supports Markdown formatting
            including **bold**, __italic__, `monospace`, and [URL](links).

    Returns:
        `str`:
            A success message if sent, or an error message if failed.
    """

    try:
        await tg.send_message(recipient, message)
        return "Message sent"
    except Exception as e:
        return f"Error sending message: {e}"


@mcp.tool()
async def search_contacts(query: str | None = None) -> list[Contact]:
    """Search for contacts in the user's Telegram contacts list.

    Retrieves the user's contacts and filters them based on the provided query.
    The query performs a case-insensitive search against the contact's
    first name, last name, username, and phone number.

    Args:
        query (`str`, optional):
            A query string to filter the contacts. If provided, the search
            will return only contacts where the query string is found within
            their first name, last name, username, or phone number.
            If None or empty, all contacts are returned.

    Returns:
        `list[Contact]`:
            A list of contacts that match the query including the contact's
            id, first name, last name, username, and phone number.
    """

    return await tg.search_contacts(query)


@mcp.tool()
async def search_dialogs(query: str = "") -> list[Dialog]:
    """Search for dialogs in the user's Telegram dialogs list.

    Retrieves the user's dialogs and filters them based on the provided query.
    The query performs a case-insensitive search against the dialog's title and username.

    Args:
        query (`str`, optional):
            A query string to filter the dialogs. If provided, the search
            will return only dialogs where the query string is found within
            the dialog's title or username. If empty, all dialogs are returned.

    Returns:
        `list[Dialog]`:
            A list of dialogs that match the query including the dialog's
            id, title, username, type, and unread messages count.
    """

    return await tg.search_dialogs(query)


@mcp.tool()
async def get_draft(entity: str) -> str:
    """Get the draft message for a specific entity.

    Finds the draft message for an entity specified by username, chat_id,
    phone number, or 'me'.

    Args:
        entity (`str`):
            The identifier of the entity to get the draft message for.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

    Returns:
        `str`:
            The draft message for the specific entity.
    """

    return await tg.get_draft(entity)


@mcp.tool()
async def set_draft(entity: str, message: str) -> str:
    """Set a draft message for a specific entity.

    Sets a draft message for an entity specified by username, chat_id,
    phone number, or 'me'.

    Args:
        entity (`str`):
            The identifier of the entity to save the draft message for.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        message (`str`):
            The message to save as a draft.

    Returns:
        `str`:
            A success message if saved, or an error message if failed.
    """

    try:
        if await tg.set_draft(entity, message):
            return "Draft saved"
        return "Draft not saved"
    except Exception as e:
        return f"Error saving draft: {e}"


@mcp.tool()
async def get_messages(
    entity: str,
    limit: int = 20,
    unread: bool = False,
    mark_as_read: bool = False,
) -> list[Message]:
    """Get messages from a specific entity.

    Retrieves messages from an entity specified by username, chat_id,
    phone number, or 'me'.

    Args:
        entity (`str`):
            The identifier of the entity to get messages from.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        limit (`int`, optional):
            The maximum number of messages to retrieve.
            Defaults to 20.

        unread (`bool`, optional):
            Whether to get only unread messages.
            Defaults to False.

        mark_as_read (`bool`, optional):
            Whether to mark the messages as read.
            Defaults to False.

    Returns:
        `list[Message]`:
            A list of messages from the entity.
    """

    return await tg.get_messages(
        int(entity) if entity.lstrip("-").isdigit() else entity,
        limit,
        unread,
        mark_as_read,
    )
