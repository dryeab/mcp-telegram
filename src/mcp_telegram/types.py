"""Types for MCP Telegram Server"""

# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from telethon.tl import custom, types


class DialogType(Enum):
    USER = "user"
    GROUP = "group"
    CHANNEL = "channel"
    BOT = "bot"


class Contact(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None


class Dialog(BaseModel):
    id: int
    title: str
    username: str | None = None
    phone_number: str | None = None
    type: DialogType
    unread_messages_count: int

    @staticmethod
    def from_custom_dialog(dialog: custom.Dialog) -> "Dialog":
        """Convert a `telethon.tl.custom.Dialog` object to a `Dialog` object.

        Args:
            dialog (`telethon.tl.custom.Dialog`): The custom dialog to convert.

        Returns:
            `Dialog`: The converted Dialog object.
        """
        assert isinstance(dialog.id, int) and isinstance(dialog.unread_count, int)
        assert isinstance(dialog.entity, (types.User | types.Chat | types.Channel))

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


class Message(BaseModel):
    message_id: int
    sender_id: int | None = None
    message: str | None = None
    outgoing: bool
    date: datetime | None = None
