"""Types for MCP Telegram Server"""

import typing

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from telethon import hints, types, utils  # type: ignore
from telethon.tl import custom, patched  # type: ignore


class DialogType(Enum):
    """The type of a dialog."""

    USER = "user"
    GROUP = "group"
    CHANNEL = "channel"
    BOT = "bot"


class Dialog(BaseModel):
    id: int
    """The ID of the dialog."""
    title: str
    """The title of the dialog."""
    username: str | None = None
    """The username of the dialog."""
    phone_number: str | None = None
    """The phone number of the dialog."""
    type: DialogType
    """The type of the dialog."""
    unread_messages_count: int
    """The number of unread messages in the dialog."""

    @staticmethod
    def get_dialog_type(entity: hints.Entity) -> "DialogType":
        """Get the type of a dialog from a telethon entity."""
        if isinstance(entity, types.User):
            if entity.bot:
                return DialogType.BOT
            else:
                return DialogType.USER
        elif isinstance(entity, types.Chat):
            return DialogType.GROUP
        else:
            if entity.megagroup:
                return DialogType.GROUP
            else:
                return DialogType.CHANNEL

    @staticmethod
    def from_entity(entity: hints.Entity) -> "Dialog":
        """Convert a `telethon.hints.Entity` object to a `Dialog` object.

        Args:
            entity (`telethon.hints.Entity`): The entity to convert.

        Returns:
            `Dialog`: The converted Dialog object.
        """

        id: int = utils.get_peer_id(entity)  # type: ignore
        title = utils.get_display_name(entity)  # type: ignore
        type: DialogType = Dialog.get_dialog_type(entity)
        username = entity.username if not isinstance(entity, types.Chat) else None
        phone_number = entity.phone if isinstance(entity, types.User) else None

        return Dialog(
            id=id,  # type: ignore
            title=title,
            type=type,
            username=username,
            phone_number=phone_number,
            unread_messages_count=0,
        )


class Media(BaseModel):
    """A media object."""

    media_id: int
    """The ID of the media."""
    mime_type: str | None = None
    """The MIME type of the media."""
    file_name: str | None = None
    """The name of the file."""
    file_size: int | None = None
    """The size of the file."""

    @staticmethod
    def from_message(message: custom.Message) -> typing.Union["Media", None]:
        """Convert a `telethon.tl.custom.Message` object to a `Media` object.

        Args:
            message (`telethon.tl.custom.Message`): The message to convert.

        Returns:
            `Media`: The converted Media object.
        """

        if message.media and message.file:
            media_id: int
            if message.photo:
                media_id = message.photo.id
            elif message.document:
                media_id = message.document.id
            else:
                # Fallback to message ID if no specific media ID is available
                media_id = message.id

            file_name = (
                message.file.name if isinstance(message.file.name, str) else None
            )

            return Media(
                media_id=media_id,
                mime_type=message.file.mime_type,
                file_name=file_name,
                file_size=message.file.size,
            )

        return None


class DownloadedMedia(BaseModel):
    """A downloaded media object."""

    path: str
    """The path to the downloaded media."""
    media: Media
    """The media object."""


class Message(BaseModel):
    """A single message from an entity."""

    message_id: int
    """The ID of the message."""
    sender_id: int | None = None
    """The ID of the user who sent the message."""
    message: str | None = None
    """The message text."""
    outgoing: bool
    """Whether the message is outgoing."""
    date: datetime | None = None
    """The date and time the message was sent."""
    media: Media | None = None
    """The media associated with the message."""
    reply_to: int | None = None
    """The message ID that this message is replying to."""

    @staticmethod
    def from_message(message: patched.Message) -> "Message":
        """Convert a `telethon.tl.patched.Message` object to a `Message` object.

        Args:
            message (`telethon.tl.patched.Message`): The message to convert.

        Returns:
            `Message`: The converted Message object.
        """

        sender_id: int | None = None
        if message.from_id:
            sender_id = int(utils.get_peer_id(message.from_id))  # type: ignore
        media = Media.from_message(message)
        message_text: str | None = (
            message.text if isinstance(message.text, str) else None  # type: ignore
        )
        reply_to: int | None = None
        if message.reply_to and isinstance(message.reply_to, types.MessageReplyHeader):
            try:
                reply_to = (
                    int(message.reply_to.reply_to_msg_id)
                    if message.reply_to.reply_to_msg_id
                    else None
                )
            except (AttributeError, TypeError, ValueError):
                reply_to = None

        return Message(
            message_id=message.id,
            sender_id=sender_id,
            message=message_text,
            outgoing=message.out,
            date=message.date,
            media=media,
            reply_to=reply_to,
        )


class Messages(BaseModel):
    """A list of messages from an entity and the dialog the messages belong to."""

    messages: list[Message]
    """The list of messages."""
    dialog: Dialog | None = None
    """The dialog the messages belong to."""
