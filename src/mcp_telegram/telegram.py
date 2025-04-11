"""Telegram client wrapper."""

# pyright: reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false

import itertools
import logging

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient
from telethon.tl import custom, functions, patched, types
from xdg_base_dirs import xdg_state_home

from mcp_telegram.types import Contact, Dialog, Message

logger = logging.getLogger(__name__)


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
        # If recipient is a string of digits, it is a chat id. Cast it to an integer.
        await self.client.send_message(
            int(recipient) if recipient.lstrip("-").isdigit() else recipient, message
        )

    async def _list_contacts(self) -> types.contacts.Contacts:
        """List all contacts in the user's Telegram contacts list.

        Returns:
            `types.contacts.Contacts`: The contacts in the user's Telegram contacts list.
        """
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

    async def _list_dialogs(self) -> list[custom.Dialog]:
        """List all dialogs in the user's Telegram dialogs list.

        Returns:
            `list[custom.Dialog]`: A list of dialogs in the user's Telegram dialogs list.
        """
        return await self.client.iter_dialogs().collect()

    async def search_dialogs(self, query: str) -> list[Dialog]:
        """Search for dialogs in the user's Telegram dialogs list.

        Args:
            query (`str`):
                A query string to filter the dialogs. If provided, the search will
                return only dialogs where the query string is found within
                the dialog's title.

        Returns:
            `list[Dialog]`: A list of dialogs that match the query.
        """

        dialogs = await self._list_dialogs()

        results: list[Dialog] = []

        for dialog in dialogs:
            assert isinstance(dialog.entity, (types.User | types.Chat | types.Channel))

            username: str | None = None
            if isinstance(dialog.entity, types.User | types.Channel):
                username = dialog.entity.username

            lower_query = query.lower()

            match = True
            if query:
                match = lower_query in dialog.name.lower() or (
                    username and lower_query in username.lower()
                )

            if match:
                results.append(Dialog.from_custom_dialog(dialog))

        return results

    async def get_draft(self, entity: str) -> str:
        """Get the draft message from a specific entity.

        Args:
            entity (`str`): The identifier of the entity to get the draft message from.

        Returns:
            `str`: The draft message from the specific entity.
        """

        draft = await self.client.get_drafts(
            int(entity) if entity.lstrip("-").isdigit() else entity
        )

        assert isinstance(
            draft, custom.Draft
        ), f"Expected custom.Draft, got {type(draft).__name__}"

        if isinstance(draft.text, str):
            return draft.text

        return ""

    async def set_draft(self, entity: str, message: str) -> Any:
        """Set a draft message for a specific entity.

        Args:
            entity (`str`): The identifier of the entity to save the draft message for.
            message (`str`): The message to save as a draft.

        Returns:
            `Any`: The result of the `set_message` method.
        """

        target_entity_peer_id = (
            int(entity)
            if entity.lstrip("-").isdigit()
            else (await self.client.get_peer_id(entity))
        )

        draft = await self.client.get_drafts(target_entity_peer_id)

        assert isinstance(
            draft, custom.Draft
        ), f"Expected custom.Draft, got {type(draft).__name__}"

        return await draft.set_message(message)  # type: ignore

    async def _get_dialog(self, entity: str | int) -> Dialog | None:
        """Get a dialog object from a specific entity.

        Args:
            entity (`str | int`): The entity to get the dialog from.

        Returns:
            `Dialog | None`: The dialog object for the specific entity,
                or `None` if the entity is not found.
        """

        input_peer = await self.client.get_input_entity(entity)

        result: Any = await self.client(
            functions.messages.GetPeerDialogsRequest(
                peers=[types.InputDialogPeer(peer=input_peer)]
            )
        )

        assert isinstance(
            result, types.messages.PeerDialogs
        ), f"Expected types.messages.PeerDialogs, got {type(result).__name__}"

        if result and result.dialogs and isinstance(result.dialogs[0], types.Dialog):
            entities: dict[int, types.User | types.Chat | types.Channel] = {}
            for x in itertools.chain(result.users, result.chats):
                if isinstance(x, (types.User | types.Chat | types.Channel)):
                    entities[x.id] = x

            return Dialog.from_custom_dialog(
                custom.Dialog(
                    client=self.client,
                    dialog=result.dialogs[0],
                    entities=entities,
                    message=None,
                )
            )

        return None

    async def get_messages(
        self,
        entity: str | int,
        limit: int = 20,
        start_date: datetime = datetime.now(timezone.utc) - timedelta(days=10),
        end_date: datetime = datetime.now(timezone.utc),
        unread: bool = False,
        mark_as_read: bool = False,
    ) -> list[Message]:
        """Get messages from a specific entity.

        Args:
            entity (`str | int`):
                The entity to get messages from.
            limit (`int`, optional):
                The maximum number of messages to get. Defaults to 20.
            start_date (`datetime`, optional):
                The start date of the messages to get. Defaults to 10 days ago.
            end_date (`datetime`, optional):
                The end date of the messages to get. Defaults to now.
            unread (`bool`, optional):
                Whether to get only unread messages. Defaults to False.
            mark_as_read (`bool`, optional):
                Whether to mark the messages as read. Defaults to False.

        Returns:
            `list[Message]`:
                A list of messages from the specific entity, ordered newest to oldest.
        """

        # Ensure dates are timezone-aware (assume UTC if naive)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        peer_id = await self.client.get_peer_id(entity)

        if unread:
            dialog = await self._get_dialog(entity)
            if not dialog or dialog.unread_messages_count == 0:
                return []
            limit = min(limit, dialog.unread_messages_count)

        results: list[Message] = []
        async for message in self.client.iter_messages(  # type: ignore
            peer_id,
            offset_date=end_date,  # fetching messages older than end_date
        ):
            if not isinstance(message, patched.Message):
                continue

            if message.date is None:
                continue

            if message.date < start_date:
                break

            if len(results) >= limit:
                break

            if mark_as_read:
                try:
                    await message.mark_read()
                except Exception as e:
                    logger.warning(f"Failed to mark message {message.id} as read: {e}")

            sender_id: int | None = None
            if message.from_id:
                try:
                    sender_peer = await self.client.get_peer_id(message.from_id)
                    sender_id = sender_peer
                except Exception as e:
                    logger.warning(f"Could not get peer ID for from_id {message.from_id}: {e}")

            if isinstance(message.text, str):
                results.append(
                    Message(
                        message_id=message.id,
                        sender_id=sender_id,
                        message=message.text,
                        outgoing=message.out,
                        date=message.date,
                    )
                )

        return results
