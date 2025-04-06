from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient
from xdg_base_dirs import xdg_state_home


class Settings(BaseSettings):
    api_id: int
    api_hash: SecretStr


class Telegram:
    """
    A class for interacting with the Telegram API.
    Wrapper around `telethon.TelegramClient` class.
    """

    def __init__(self, api_id: int | None = None, api_hash: str | None = None):
        """
        Initialize the Telegram client.

        If `api_id` and `api_hash` are not provided, the client
        will use the default values from the `Settings` class.

        Args:
            api_id (`int`, optional): The API ID for the Telegram client.
            api_hash (`str`, optional): The API hash for the Telegram client.

        Raises:
            pydantic_core.ValidationError: If `api_id` and `api_hash` are not provided.
        """
        self._state_dir = xdg_state_home() / "mcp-telegram"
        self._state_dir.mkdir(parents=True, exist_ok=True)

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

    @property
    def client(self) -> TelegramClient:
        return self._client
