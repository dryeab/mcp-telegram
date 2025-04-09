from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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
    type: DialogType
    unread_messages_count: int


class Message(BaseModel):
    message_id: int
    sender_id: int | None = None
    message: str | None = None
    outgoing: bool
    date: datetime | None = None
