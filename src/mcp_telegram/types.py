from enum import Enum

from pydantic import BaseModel


class ChatType(Enum):
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


class Chat(BaseModel):
    id: int
    title: str
    username: str | None = None
    type: ChatType
    unread_messages_count: int
