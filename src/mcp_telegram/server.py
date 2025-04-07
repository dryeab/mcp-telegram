from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_telegram.telegram import Telegram

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
        str: A success message if sent, or an error message if failed.
    """

    try:
        # If recipient is a string of digits, it is a chat id. Cast it to an integer.
        await tg.client.send_message(
            int(recipient) if recipient.isdigit() else recipient, message
        )
        return "Message sent"
    except Exception as e:
        return f"Error sending message: {e}"
