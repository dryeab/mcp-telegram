"""Telegram client wrapper."""

import itertools
import logging

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient, hints, types  # type: ignore
from telethon.tl import custom, functions, patched  # type: ignore
from xdg_base_dirs import xdg_state_home

from mcp_telegram.types import (
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

    api_id: str
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
        self, api_id: str | None = None, api_hash: str | None = None
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
            `pydantic_core.ValidationError`: If `api_id` and `api_hash`
            are not provided.
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
            api_id=int(settings.api_id),
            api_hash=settings.api_hash.get_secret_value(),
        )

        return self._client

    async def send_message(
        self,
        entity: str | int,
        message: str = "",
        file_path: list[str] | None = None,
        reply_to: int | None = None,
    ) -> None:
        """Send a message to a Telegram user, group, or channel.

        Args:
            entity (`str | int`): The recipient of the message.
            message (`str`, optional): The message to send.
            file_path (`list[str]`, optional): The list of paths to the files
                to be sent.
            reply_to (`int`, optional): The message ID to reply to.

        Raises:
            `FileNotFoundError`: If a file does not exist or is not a file.
        """

        if file_path:
            for path in file_path:
                _path = Path(path)
                if not _path.exists() or not _path.is_file():
                    logger.error(f"File {path} does not exist or is not a file.")
                    raise FileNotFoundError(
                        f"File {path} does not exist or is not a file."
                    )

        await self.client.send_message(
            entity,
            message,
            file=file_path,  # type: ignore
            reply_to=reply_to,  # type: ignore
        )

    async def edit_message(
        self, entity: str | int, message_id: int, message: str
    ) -> None:
        """Edit a message from a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.
            message_id (`int`): The ID of the message to edit.
            message (`str`): The message to edit the message to.
        """
        await self.client.edit_message(entity, message_id, message)

    async def delete_message(self, entity: str | int, message_ids: list[int]) -> None:
        """Delete a message from a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.
            message_ids (`list[int]`): The IDs of the messages to delete.
        """
        await self.client.delete_messages(entity, message_ids)

    async def get_draft(self, entity: str | int) -> str:
        """Get the draft message from a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.

        Returns:
            `str`: The draft message from the specific entity.
        """
        draft = await self.client.get_drafts(entity)

        assert isinstance(draft, custom.Draft)

        if isinstance(draft.text, str):  # type: ignore
            return draft.text

        return ""

    async def set_draft(self, entity: str | int, message: str) -> None:
        """Set a draft message for a specific entity.

        Args:
            entity (`str | int`): The identifier of the entity.
            message (`str`): The message to save as a draft.
        """

        peer_id = await self.client.get_peer_id(entity)
        draft = await self.client.get_drafts(peer_id)

        assert isinstance(draft, custom.Draft)

        await draft.set_message(message)  # type: ignore

    async def get_messages(
        self,
        entity: str | int,
        limit: int = 20,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
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
                The start date of the messages to get.
            end_date (`datetime`, optional):
                The end date of the messages to get.
            unread (`bool`, optional):
                Whether to get only unread messages. Defaults to False.
            mark_as_read (`bool`, optional):
                Whether to mark the messages as read. Defaults to False.

        Returns:
            `list[Message]`:
                A list of messages from the specific entity, ordered newest to oldest.
        """

        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # make it very old if start_date is not provided
        if start_date is None:
            start_date = end_date - timedelta(days=10000)

        # make sure the dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        _entity = await self.client.get_entity(entity)
        assert isinstance(_entity, hints.Entity)
        dialog = Dialog.from_entity(_entity)

        if unread:
            if not dialog or dialog.unread_messages_count == 0:
                return Messages(messages=[], dialog=dialog)
            limit = min(limit, dialog.unread_messages_count)

        results: list[Message] = []
        async for message in self.client.iter_messages(  # type: ignore
            _entity,
            offset_date=end_date,  # fetching messages older than end_date
        ):
            # Skip service messages and empty messages immediately
            if not isinstance(message, patched.Message) or isinstance(
                message, patched.MessageService | patched.MessageEmpty
            ):
                continue

            if message.date is None:
                continue

            if message.date < start_date or len(results) >= limit:
                break

            if mark_as_read:
                try:
                    await message.mark_read()
                except Exception as e:
                    logger.warning(f"Failed to mark message {message.id} as read: {e}")

            results.append(Message.from_message(message))

        return Messages(messages=results, dialog=dialog)

    async def download_media(
        self, entity: str | int, message_id: int, path: str | None = None
    ) -> DownloadedMedia:
        """Download media attached to a specific message to a unique local file.

        Args:
            entity (`str | int`): The chat/user where the message exists.
            message_id (`int`): The ID of the message containing the media.

        Returns:
            `DownloadedMedia`: An object containing the absolute path
                             and media details of the downloaded file.
        """

        # Fetch the specific message
        message = await self.client.get_messages(entity, ids=message_id)  # type: ignore

        if not message or not isinstance(message, patched.Message):
            raise ValueError(
                f"Message {message_id} not found or invalid in entity {entity}."
            )

        media = Media.from_message(message)
        if not media:
            raise ValueError(
                f"Message {message_id} in entity {entity} does not contain \
                    downloadable media."
            )

        filename = get_unique_filename(message)
        if path:
            filepath = Path(path) / filename
        else:
            filepath = self._downloads_dir / filename

        # Attempt to download the media to the specified file path
        try:
            downloaded_path = await message.download_media(file=filepath)  # type: ignore
        except Exception as e:
            logger.error(
                f"Error during media download for message {message_id} "
                f"in entity {entity}: {e}",
                exc_info=True,
            )
            raise e

        if downloaded_path and isinstance(downloaded_path, str):
            absolute_path = str(Path(downloaded_path).resolve())
            logger.info(
                f"Successfully downloaded media for message {message_id} \
                    to {absolute_path}."
            )
            return DownloadedMedia(path=absolute_path, media=media)

        raise ValueError(
            f"Failed to download media for message {message_id}. "
            f"download_media returned: {downloaded_path}"
        )

    async def message_from_link(self, link: str) -> Message:
        """Get a message from a link.

        Args:
            link (`str`): The link to get the message from.

        Returns:
            `Message`: The message from the link.

        Raises:
            `ValueError`: If the link is not a valid Telegram link.
        """

        # Parse the link to get the entity and message ID
        parsed_result = parse_telegram_url(link)

        if parsed_result is None:
            raise ValueError(
                f"Could not parse valid entity/message ID from link: {link}"
            )

        entity, message_id = parsed_result

        # Fetch the specific message using the parsed entity and ID
        message = await self.client.get_messages(entity, ids=message_id)  # type: ignore

        if not message or not isinstance(message, patched.Message):
            raise ValueError(
                f"Could not retrieve message {message_id} from entity {entity} \
                    (parsed from link: {link})"
            )

        return Message.from_message(message)

    async def _can_send_message(self, entity: hints.Entity) -> bool:
        """Check if the logged-in account can send messages to an entity.

        Args:
            entity (`hints.Entity`): The entity to check.

        Returns:
            `bool`: Whether the account can send messages to the entity.
        """

        if isinstance(entity, types.User):
            return True
        else:
            try:
                permissions = await self.client.get_permissions(entity, "me")
                assert isinstance(permissions, custom.ParticipantPermissions)

                if permissions.is_creator or (
                    permissions.is_admin and permissions.post_messages
                ):
                    return True

                if isinstance(entity, types.Channel) and entity.broadcast:
                    return False  # Regular members can't send to broadcast channels

                if permissions.is_banned:
                    assert isinstance(
                        permissions.participant, types.ChannelParticipantBanned  # type: ignore
                    )
                    return not permissions.participant.banned_rights.send_messages

                banned_rights = await self.client.get_permissions(entity)
                assert isinstance(banned_rights, types.ChatBannedRights)

                return not banned_rights.send_messages

            except Exception as e:
                logger.warning(f"Failed to get permissions for entity {entity}: {e}")
                return False

    async def search_dialogs(
        self, query: str, limit: int, global_search: bool = False
    ) -> list[Dialog]:
        """Search for users, groups, and channels globally.

        Args:
            query (`str`): The search query.
            limit (`int`): Maximum number of results to return.
            global_search (`bool`, optional): Whether to search globally. Defaults to False.

        Returns:
            `list[Dialog]`: A list of Dialog objects representing the search results.

        Raises:
            `ValueError`: If the query is empty or the limit is not greater than 0.
        """
        if not query:
            raise ValueError("Query cannot be empty!")

        if limit <= 0:
            raise ValueError("Limit must be greater than 0!")

        response: Any = await self.client(
            functions.contacts.SearchRequest(
                q=query,
                limit=limit,
            )
        )

        assert isinstance(response, types.contacts.Found)

        priority: dict[int, int] = {}
        for i, peer in enumerate(
            itertools.chain(response.my_results, response.results)
            if global_search
            else response.my_results
        ):
            peer_id = await self.client.get_peer_id(peer)
            priority[peer_id] = i

        result: list[Dialog] = []
        for x in itertools.chain(response.users, response.chats):
            if isinstance(x, hints.Entity):
                peer_id = await self.client.get_peer_id(x)
                if peer_id in priority:
                    can_send_message = await self._can_send_message(x)
                    try:
                        dialog = Dialog.from_entity(x, can_send_message)
                        result.append(dialog)
                    except Exception as e:
                        logger.warning(f"Failed to get dialog for entity {x.id}: {e}")

        # Sort results based on priority
        result.sort(key=lambda x: priority.get(x.id))  # type: ignore

        return result
