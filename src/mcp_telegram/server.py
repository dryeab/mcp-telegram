"""MCP Telegram Server."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

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
async def send_message(
    entity: str,
    message: str = "",
    file_path: list[str] | None = None,
    reply_to: int | None = None,
) -> str:
    """Send a message to a Telegram user, group, or channel.

    It allows sending text messages to any Telegram entity identified by `entity`.

    !IMPORTANT: If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`): The identifier of where to send the message.
            This can be a Telegram chat ID, a username, a phone number
            (in format '+1234567890'), or a group/channel username. The special
            value "me" can be used to send a message to yourself.

        message (`str`, optional): The text message to be sent.
            The message supports Markdown formatting including **bold**, __italic__,
            `monospace`, and [URL](links). The maximum length for a message is 35,000
            bytes or 4,096 characters.

        file_path (`list[str]`, optional): The list of paths to the files to be sent.

        reply_to (`int`, optional): The message ID to reply to.

    Returns:
        `str`:
            A success message if sent, or an error message if failed.
    """

    _entity = parse_entity(entity)

    await tg.send_message(
        _entity,
        message,
        file_path=file_path,
        reply_to=reply_to,
    )

    return f"Message sent to {entity}"


@mcp.tool()
async def edit_message(entity: str, message_id: int, message: str) -> str:
    """Edit a message from a specific entity.

    Edits a message from a specific entity.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`): The identifier of the entity.
        message_id (`int`): The ID of the message to edit.
        message (`str`): The message to edit the message to.

    Returns:
        `str`:
            A success message if edited, or an error message if failed.
    """

    _entity = parse_entity(entity)

    await tg.edit_message(_entity, message_id, message)

    return f"Message edited in {entity}"


@mcp.tool()
async def delete_message(entity: str, message_ids: list[int]) -> str:
    """Delete a message from a specific entity.

    Deletes a message from a specific entity.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`): The identifier of the entity.
        message_ids (`list[int]`): The IDs of the messages to delete.

    Returns:
        `str`:
            A success message if deleted, or an error message if failed.
    """

    _entity = parse_entity(entity)

    await tg.delete_message(_entity, message_ids)

    return f"Messages deleted from {entity}"


@mcp.tool()
async def search_dialogs(query: str, limit: int = 10) -> list[Dialog]:
    """Search for users, groups, and channels.

    Retrieves users, groups, and channels and filters them based
    on the provided query. The query performs a case-insensitive search.

    !IMPORTANT: If the query doesn't return the correct results, it means that
    the query is not specific enough. Try to be more specific with the query or
    use a different query.

    Args:
        query (`str`): A query string to filter the dialogs.
            The search will return only dialogs where the query string is
            found within the dialog's title or username.

        limit (`int`, optional): The maximum number of dialogs to return.
            Defaults to 10. The limit must be greater than 0.

    Returns:
        `list[Dialog]`: A list of dialogs that match the query if successful,
            or an error message if request failed.
    """

    return await tg.search_dialogs(query, limit)


@mcp.tool()
async def get_draft(entity: str) -> str:
    """Get the draft message for a specific entity.

    Finds the draft message for an entity specified by username, chat_id,
    phone number, or 'me'.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`):
            The identifier of the entity to get the draft message for.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

    Returns:
        `str`:
            The draft message (empty string if no draft) for the specific entity
            or an error message if request failed.
    """

    _entity = parse_entity(entity)

    return await tg.get_draft(_entity)


@mcp.tool()
async def set_draft(entity: str, message: str) -> str:
    """Set a draft message for a specific entity.

    Sets a draft message for an entity specified by username, chat_id,
    phone number, or 'me'.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

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

    _entity = parse_entity(entity)

    await tg.set_draft(_entity, message)

    return f"Draft saved for {_entity}"


@mcp.tool()
async def get_messages(
    entity: str,
    limit: int = 10,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    unread: bool = False,
    mark_as_read: bool = False,
) -> Messages:
    """Get messages from a specific entity.

    Retrieves messages from an entity specified by username, chat_id,
    phone number, or 'me'.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`):
            The identifier of the entity to get messages from.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        limit (`int`, optional):
            The maximum number of messages to retrieve.
            Defaults to 10.

        start_date (`datetime`, optional):
            The start date of the messages to retrieve.

        end_date (`datetime`, optional):
            The end date of the messages to retrieve.

        unread (`bool`, optional):
            Whether to get only unread messages.
            Defaults to False.

        mark_as_read (`bool`, optional):
            Whether to mark the messages as read.
            Defaults to False.

    Returns:
        `Messages`:
            A list of messages from the entity and the dialog the messages
            belong to if successful, or an error message if request failed.
    """

    _entity = parse_entity(entity)

    return await tg.get_messages(
        _entity,
        limit,
        start_date,
        end_date,
        unread,
        mark_as_read,
    )


@mcp.tool()
async def media_download(
    entity: str, message_id: int, path: str | None = None
) -> DownloadedMedia:
    """Download media from a specific message to a unique local file.

    Retrieves media from an entity specified by username, chat_id,
    phone number, or 'me' and saves it to a local directory with a unique name.

    !IMPORTANT: If the entity is not found, it will return an error message.
    If you are not sure about the entity, use the `search_dialogs`
    tool and ask the user to select the correct entity from the list.

    Args:
        entity (`str`):
            The identifier of the entity where the message exists.
            This can be a Telegram chat ID, a username, a phone number, or 'me'.

        message_id (`int`):
            The ID of the message containing the media to download.

        path (`str`, optional):
            The path to save the downloaded media.
            Defaults to a Path corresponding to `XDG_STATE_HOME`.

    Returns:
        `DownloadedMedia`:
            An object containing the absolute path and media details
            of the downloaded file if successful or an error message.
    """
    _entity = parse_entity(entity)

    return await tg.download_media(_entity, message_id, path)


@mcp.tool()
async def message_from_link(link: str) -> Message:
    """Get a message from a link.

    Retrieves a message from a link.

    !IMPORTANT: If the link is not a valid Telegram message link, or the account
    is not authorized to access the message, it will return an error message.

    Args:
        link (`str`): The link to the message.

    Returns:
        `Message`: The message from the link if successful, or an error message.
    """

    return await tg.message_from_link(link)
