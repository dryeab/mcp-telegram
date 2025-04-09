from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_telegram.telegram import Telegram
from mcp_telegram.types import Chat, Contact

# TODO (Yeabsira): Some clients don't support Context.
# @dataclass
# class AppContext:
#     tg: Telegram


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


tg = Telegram()
mcp = FastMCP("mcp-telegram", lifespan=app_lifespan)


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
async def search_chats(query: str = "") -> list[Chat]:
    """Search for chats in the user's Telegram chats list.

    Retrieves the user's chats and filters them based on the provided query.
    The query performs a case-insensitive search against the chat's title and username.

    Args:
        query (`str`, optional):
            A query string to filter the chats. If provided, the search
            will return only chats where the query string is found within
            the chat's title or username. If empty, all chats are returned.

    Returns:
        `list[Chat]`:
            A list of chats that match the query including the chat's
            id, title, username, type, and unread messages count.
    """

    return await tg.search_chats(query)
