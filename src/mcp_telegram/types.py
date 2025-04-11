"""Types for MCP Telegram Server"""

import typing

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from telethon.tl import custom, types  # type: ignore


class Contact(BaseModel):
    """A contact with an entity."""

    id: int
    """The ID of the contact."""
    first_name: str | None = None
    """The first name of the contact."""
    last_name: str | None = None
    """The last name of the contact."""
    username: str | None = None
    """The username of the contact."""
    phone: str | None = None
    """The phone number of the contact."""


class DialogType(Enum):
    """The type of a dialog."""

    USER = "user"
    GROUP = "group"
    CHANNEL = "channel"
    BOT = "bot"


class Dialog(BaseModel):
    """A dialog with an entity."""

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
    def from_custom_dialog(dialog: custom.Dialog) -> "Dialog":
        """Convert a `telethon.tl.custom.Dialog` object to a `Dialog` object.

        Args:
            dialog (`telethon.tl.custom.Dialog`): The custom dialog to convert.

        Returns:
            `Dialog`: The converted Dialog object.
        """
        assert isinstance(dialog.id, int) and isinstance(dialog.unread_count, int)  # type: ignore
        assert isinstance(dialog.entity, (types.User | types.Chat | types.Channel))  # type: ignore

        dialog_type: DialogType
        if dialog.is_user:
            assert isinstance(dialog.entity, types.User)
            if dialog.entity.bot:
                dialog_type = DialogType.BOT
            else:
                dialog_type = DialogType.USER
        elif dialog.is_group:
            dialog_type = DialogType.GROUP
        else:
            dialog_type = DialogType.CHANNEL

        username: str | None = None
        if isinstance(dialog.entity, (types.User | types.Channel)):
            username = dialog.entity.username

        phone_number: str | None = None
        if isinstance(dialog.entity, types.User):
            phone_number = dialog.entity.phone

        return Dialog(
            id=dialog.id,
            title=dialog.name,
            type=dialog_type,
            username=username,
            phone_number=phone_number,
            unread_messages_count=dialog.unread_count,
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

            file_name = message.file.name if isinstance(message.file.name, str) else None

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


class Messages(BaseModel):
    """A list of messages from an entity and the dialog the messages belong to."""

    messages: list[Message]
    """The list of messages."""
    dialog: Dialog | None = None
    """The dialog the messages belong to."""
