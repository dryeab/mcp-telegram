"""Telegram client wrapper."""

# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false

from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient
from telethon.tl import custom, functions, types
from xdg_base_dirs import xdg_state_home

from mcp_telegram.types import Chat, ChatType, Contact


class Settings(BaseSettings):
    """Settings for the Telegram client."""

    api_id: int
    api_hash: SecretStr


class Telegram:
    """Wrapper around `telethon.TelegramClient` class."""

    def __init__(self):
        self._state_dir = xdg_state_home() / "mcp-telegram"
        self._state_dir.mkdir(parents=True, exist_ok=True)

        self._client: TelegramClient | None = None

    @property
    def client(self) -> TelegramClient:
        if self._client is None:
            raise RuntimeError("Client not created!")
        return self._client

    def create_client(
        self, api_id: int | None = None, api_hash: str | None = None
    ) -> TelegramClient:
        """Create a Telegram client.

        If `api_id` and `api_hash` are not provided, the client
        will use the default values from the `Settings` class.

        Args:
            api_id (`int`, optional): The API ID for the Telegram client.
            api_hash (`str`, optional): The API hash for the Telegram client.

        Returns:
            `telethon.TelegramClient`: The created Telegram client.

        Raises:
            `pydantic_core.ValidationError`: If `api_id` and `api_hash` are not provided.
        """
        if self._client is not None:
            return self._client

        settings: Settings
        if api_id is None or api_hash is None:
            settings = Settings()  # type: ignore
        else:
            settings = Settings(api_id=api_id, api_hash=SecretStr(api_hash))

        self._client = TelegramClient(
            session=self._state_dir / "session",
            api_id=settings.api_id,
            api_hash=settings.api_hash.get_secret_value(),
        )

        return self._client

    async def send_message(self, recipient: str, message: str) -> None:
        """Send a message to a Telegram user, group, or channel.

        Args:
            recipient (`str`): The recipient of the message.
            message (`str`): The message to send.
        """
        if self._client is None:
            raise RuntimeError("Client not created!")

        # If recipient is a string of digits, it is a chat id. Cast it to an integer.
        await self.client.send_message(
            int(recipient) if recipient.isdigit() else recipient, message
        )

    async def _list_contacts(self) -> types.contacts.Contacts:
        """List all contacts in the user's Telegram contacts list.

        Returns:
            `types.contacts.Contacts`: The contacts in the user's Telegram contacts list.
        """
        if self._client is None:
            raise RuntimeError("Client not created!")

        contacts: Any = await self.client(functions.contacts.GetContactsRequest(hash=0))

        assert isinstance(
            contacts, types.contacts.Contacts
        ), f"Expected types.contacts.Contacts, got {type(contacts).__name__}"

        return contacts

    async def search_contacts(self, query: str | None = None) -> list[Contact]:
        """Search for contacts in the user's Telegram contacts list.

        Args:
            query (`str`, optional):
                A query string to filter the contacts. If provided, the search will
                return only contacts that match the query.

        Returns:
            `list[Contact]`: A list of contacts that match the query.
        """

        contacts = await self._list_contacts()

        contact_ids = {contact.user_id for contact in contacts.contacts}
        contact_users = [
            user
            for user in contacts.users
            if user.id in contact_ids and isinstance(user, types.User)
        ]

        if not query:
            # No query provided, return all actual contacts
            return [
                Contact(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    username=user.username,
                    phone=user.phone,
                )
                for user in contact_users
            ]

        results: list[Contact] = []

        lower_query = query.lower()
        for user in contact_users:
            # Check relevant fields for the query (case-insensitive)
            match = (
                (user.first_name and lower_query in user.first_name.lower())
                or (user.last_name and lower_query in user.last_name.lower())
                or (user.username and lower_query in user.username.lower())
                or (user.phone and lower_query in user.phone.lower())
            )
            if match:
                results.append(
                    Contact(
                        id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        username=user.username,
                        phone=user.phone,
                    )
                )

        return results

    async def _list_chats(self) -> list[custom.Dialog]:
        """List all chats in the user's Telegram chats list.

        Returns:
            `list[custom.Dialog]`: A list of chats in the user's Telegram chats list.
        """
        if self._client is None:
            raise RuntimeError("Client not created!")

        return await self.client.iter_dialogs().collect()

    async def search_chats(self, query: str) -> list[Chat]:
        """Search for chats in the user's Telegram chats list.

        Args:
            query (`str`):
                A query string to filter the chats. If provided, the search will
                return only chats where the query string is found within
                the chat's title.

        Returns:
            `list[Chat]`: A list of chats that match the query.
        """

        dialogs = await self._list_chats()

        results: list[Chat] = []

        for dialog in dialogs:
            assert isinstance(dialog.entity, (types.User | types.Chat | types.Channel))

            chat_type: ChatType
            if dialog.is_user:
                assert isinstance(dialog.entity, types.User)
                if dialog.entity.bot:
                    chat_type = ChatType.BOT
                else:
                    chat_type = ChatType.USER
            elif dialog.is_group:
                chat_type = ChatType.GROUP
            else:
                chat_type = ChatType.CHANNEL

            username: str | None = None
            if isinstance(dialog.entity, types.User | types.Channel):
                username = dialog.entity.username

            lower_query = query.lower()

            match = True
            if query:
                match = lower_query in dialog.name.lower() or (
                    username and lower_query in username.lower()
                )

            assert isinstance(dialog.id, int) and isinstance(dialog.unread_count, int)

            if match:
                results.append(
                    Chat(
                        id=dialog.id,
                        title=dialog.name,
                        type=chat_type,
                        username=username,
                        unread_messages_count=dialog.unread_count,
                    )
                )

        return results
