"""MCP Telegram Server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from mcp.server.fastmcp import FastMCP

from mcp_telegram.telegram import Telegram
from mcp_telegram.types import Dialog, DownloadedMedia, Message, Messages
from mcp_telegram.utils import parse_entity


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
        await tg.client.disconnect()  # type: ignore


tg = Telegram()
mcp = FastMCP(
    "mcp-telegram",
    lifespan=app_lifespan,
)


@mcp.tool()
async def send_message(entity: str, message: str) -> str:
    """Send a message to a Telegram user, group, or channel.

    It allows sending text messages to any Telegram entity identified by `entity`.

    Args:
        entity (`str`):
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
        await tg.send_message(parse_entity(entity), message)
        return "Message sent"
    except Exception as e:
        return f"Error sending message: {e}"


@mcp.tool()
async def search_dialogs(query: str, limit: int = 10) -> list[Dialog]:
    """Search for users, groups, and channels.

    Retrieves users, groups, and channels and filters them based
    on the provided query. The query performs a case-insensitive search.

    Args:
        query (`str`): A query string to filter the dialogs.
            The search will return only dialogs where the query string is
            found within the dialog's title or username.

        limit (`int`, optional): The maximum number of dialogs to return.
            Defaults to 10.

    Returns:
        `list[Dialog]`: A list of dialogs that match the query.
    """

    return await tg.search_dialogs(query, limit)


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

    return await tg.get_draft(parse_entity(entity))


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
        if await tg.set_draft(parse_entity(entity), message):
            return "Draft saved"
        return "Draft not saved"
    except Exception as e:
        return f"Error saving draft: {e}"


@mcp.tool()
async def get_messages(
    entity: str,
    limit: int = 10,
    start_date: datetime = datetime.now(timezone.utc) - timedelta(days=10),
    end_date: datetime = datetime.now(timezone.utc),
    unread: bool = False,
    mark_as_read: bool = False,
) -> Messages:
    """Get messages from a specific entity.

    Retrieves messages from an entity specified by username, chat_id,
    phone number, or 'me'.

    Args:
        entity (`str`):
            The identifier of the entity to get messages from.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        limit (`int`, optional):
            The maximum number of messages to retrieve.
            Defaults to 10.

        start_date (`datetime`, optional):
            The start date of the messages to retrieve.
            Defaults to 10 days ago.

        end_date (`datetime`, optional):
            The end date of the messages to retrieve.
            Defaults to now.

        unread (`bool`, optional):
            Whether to get only unread messages.
            Defaults to False.

        mark_as_read (`bool`, optional):
            Whether to mark the messages as read.
            Defaults to False.

    Returns:
        `Messages`:
            A list of messages from the entity and the dialog the messages belong to.
    """

    return await tg.get_messages(
        parse_entity(entity),
        limit,
        start_date,
        end_date,
        unread,
        mark_as_read,
    )


@mcp.tool()
async def media_download(entity: str, message_id: int) -> DownloadedMedia | None:
    """Download media from a specific message to a unique local file.

    Retrieves media from an entity specified by username, chat_id,
    phone number, or 'me' and saves it to a local directory with a unique name.

    Args:
        entity (`str`):
            The identifier of the entity where the message exists.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        message_id (`int`):
            The ID of the message containing the media to download.

    Returns:
        `DownloadedMedia | None`:
            An object containing the absolute path and media details
            of the downloaded file if successful, or None otherwise.
            The object has `path` (str) and `media` (Media) attributes.
    """
    return await tg.download_media(parse_entity(entity), message_id)


@mcp.tool()
async def message_from_link(link: str) -> Message | None:
    """Get a message from a link.

    Retrieves a message from a link.

    Args:
        link (`str`):
            The link to the message.

    Returns:
        `Message | None`:
            The message from the link if successful, or None otherwise.
    """
    return await tg.message_from_link(link)
