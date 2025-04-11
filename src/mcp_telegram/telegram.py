"""Telegram client wrapper."""

import itertools
import logging

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient  # type: ignore
from telethon.tl import custom, functions, patched, types  # type: ignore
from xdg_base_dirs import xdg_state_home

from mcp_telegram.types import (
    Contact,
    Dialog,
    DownloadedMedia,
    Media,
    Message,
    Messages,
)
from mcp_telegram.utils import get_unique_filename, parse_telegram_url

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

        self._downloads_dir = self._state_dir / "downloads"
        self._downloads_dir.mkdir(parents=True, exist_ok=True)

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

    async def send_message(self, entity: str | int, message: str) -> None:
        """Send a message to a Telegram user, group, or channel.

        Args:
            entity (`str | int`): The recipient of the message.
            message (`str`): The message to send.
        """
        await self.client.send_message(entity, message)

    async def search_contacts(self, query: str | None = None) -> list[Contact]:
        """Search for contacts in the user's Telegram contacts list.

        Args:
            query (`str`, optional):
                A query string to filter the contacts. If provided, the search will
                return only contacts that match the query.

        Returns:
            `list[Contact]`: A list of contacts that match the query.
        """

        contacts: Any = await self.client(functions.contacts.GetContactsRequest(hash=0))

        assert isinstance(
            contacts, types.contacts.Contacts
        ), f"Expected types.contacts.Contacts, got {type(contacts).__name__}"

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

        dialogs = [
            dialog
            for dialog in await self.client.iter_dialogs().collect()  # type: ignore
            if isinstance(dialog, custom.Dialog)
        ]

        results: list[Dialog] = []

        for dialog in dialogs:
            assert isinstance(dialog.entity, (types.User | types.Chat | types.Channel))  # type: ignore

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

    async def get_draft(self, entity: str | int) -> str:
        """Get the draft message from a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.

        Returns:
            `str`: The draft message from the specific entity.
        """
        draft = await self.client.get_drafts(entity)

        assert isinstance(
            draft, custom.Draft
        ), f"Expected custom.Draft, got {type(draft).__name__}"

        if isinstance(draft.text, str):  # type: ignore
            return draft.text

        return ""

    async def set_draft(self, entity: str | int, message: str) -> Any:
        """Set a draft message for a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.
            message (`str`): The message to save as a draft.

        Returns:
            `Any`: The result of the `set_message` method.
        """

        peer_id = await self.client.get_peer_id(entity)
        draft = await self.client.get_drafts(peer_id)

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
    ) -> Messages:
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
        dialog = await self._get_dialog(entity)

        if unread:
            if not dialog or dialog.unread_messages_count == 0:
                return Messages(messages=[], dialog=dialog)
            limit = min(limit, dialog.unread_messages_count)

        results: list[Message] = []
        async for message in self.client.iter_messages(  # type: ignore
            peer_id,
            offset_date=end_date,  # fetching messages older than end_date
        ):
            assert isinstance(message, patched.Message)

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

            media = Media.from_message(message)
            message_text: str | None = (
                message.text if isinstance(message.text, str) else None  # type: ignore
            )

            results.append(
                Message(
                    message_id=message.id,
                    sender_id=sender_id,
                    message=message_text,
                    outgoing=message.out,
                    date=message.date,
                    media=media,
                )
            )

        return Messages(messages=results, dialog=dialog)

    async def download_media(
        self, entity: str | int, message_id: int
    ) -> DownloadedMedia | None:
        """Download media attached to a specific message to a unique local file.

        Args:
            entity (`str | int`): The chat/user where the message exists.
            message_id (`int`): The ID of the message containing the media.

        Returns:
            `DownloadedMedia | None`: An object containing the absolute path
                                     and media details of the downloaded file,
                                     or None if download fails.
        """
        try:
            logger.debug(
                f"Attempting to download media from message {message_id} in entity {entity}"
            )
            # Fetch the specific message
            message = await self.client.get_messages(entity, ids=message_id)  # type: ignore

            if not message or not isinstance(message, patched.Message):
                logger.warning(
                    f"Message {message_id} not found or invalid in entity {entity}."
                )
                return None

            media = Media.from_message(message)
            if not media:
                logger.warning(
                    f"Message {message_id} in entity {entity} does not contain \
                        downloadable media."
                )
                return None

            filename = get_unique_filename(message)

            filepath = self._downloads_dir / filename

            # Attempt to download the media to the specified file path
            try:
                # download_media returns the path where the file was saved
                downloaded_path = await message.download_media(file=filepath)  # type: ignore
            except Exception as e:
                logger.error(
                    f"Error during media download for message {message_id} "
                    f"in entity {entity}: {e}",
                    exc_info=True,
                )
                return None

            if downloaded_path and isinstance(downloaded_path, str):
                # Make path absolute for clarity if it's not already
                absolute_path = str(Path(downloaded_path).resolve())
                logger.info(
                    f"Successfully downloaded media for message {message_id} \
                        to {absolute_path}."
                )
                return DownloadedMedia(path=absolute_path, media=media)
            else:
                logger.error(
                    f"Failed to download media for message {message_id}. "
                    f"download_media returned: {downloaded_path}"
                )
                return None

        except Exception as e:
            logger.error(
                f"General error processing media download for message {message_id} in entity "
                f"{entity}: {e}",
                exc_info=True,
            )
            return None

    async def message_from_link(self, link: str) -> Message | None:
        """Get a message from a link.

        Args:
            link (`str`): The link to get the message from.

        Returns:
            `Message | None`: The message from the link, or None if not found or invalid.
        """
        try:
            # Parse the link to get the entity and message ID
            parsed_result = parse_telegram_url(link)

            if parsed_result is None:
                logger.warning(f"Could not parse valid entity/message ID from link: {link}")
                return None

            # Unpack the result now that we know it's not None
            entity, message_id = parsed_result

            # Fetch the specific message using the parsed entity and ID
            # Use client.get_messages with ids parameter
            message = await self.client.get_messages(entity, ids=message_id)  # type: ignore

            if not message or not isinstance(message, patched.Message):
                logger.warning(
                    f"Could not retrieve message {message_id} from entity {entity} \
                        (parsed from link: {link})"
                )
                return None

            # Construct the Message object, similar to get_messages
            sender_id: int | None = None
            if message.from_id:
                try:
                    # Use get_peer_id for consistency and potential user/channel resolution
                    sender_peer = await self.client.get_peer_id(message.from_id)
                    sender_id = sender_peer
                except Exception as e:
                    logger.warning(
                        f"Could not get peer ID for from_id {message.from_id} "
                        f"(message {message_id} from link {link}): {e}"
                    )
                    # Continue without sender_id if resolution fails

            media = Media.from_message(message)
            message_text: str | None = (
                message.text if isinstance(message.text, str) else None  # type: ignore
            )

            # Ensure date is valid
            if not isinstance(message.date, datetime):
                logger.warning(
                    f"Message {message_id} from link {link} has invalid date: {message.date}"
                )
                return None

            return Message(
                message_id=message.id,
                sender_id=sender_id,
                message=message_text,
                outgoing=message.out,
                date=message.date,
                media=media,
            )

        except (
            ValueError
        ) as e:  # Handle invalid link format specifically from parse_telegram_url
            logger.warning(f"Invalid Telegram link format: {link} - {e}")
            return None
        except (
            TypeError
        ) as e:  # Handle potential errors from parse_telegram_url returning unexpected types
            logger.error(f"Error parsing Telegram link {link}: {e}", exc_info=True)
            return None
        except (
            Exception
        ) as e:  # Catch other potential errors (e.g., network issues, permissions)
            logger.error(f"Error fetching message from link {link}: {e}", exc_info=True)
            return None
