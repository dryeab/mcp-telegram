from pydantic import SecretStr
from pydantic_settings import BaseSettings
from telethon import TelegramClient
from telethon.tl.types.auth import SentCode
from xdg_base_dirs import xdg_state_home


class Settings(BaseSettings):
    api_id: int
    api_hash: SecretStr

    class Config:
        case_sensitive = False


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

    async def send_code(self, phone: str) -> SentCode:
        """
        Send a code to the given phone number.

        Args:
            phone (`str`): The phone number to send the code to.

        Returns:
            `telethon.tl.types.auth.SentCode`: The token.

        Examples:
            >>> await client.send_code("+1234567890")
        """
        return await self._client.send_code_request(phone)

    async def login(
        self, phone_code_hash: str, code: str, password: str | None = None
    ) -> None:
        """
        Login to the Telegram client.

        Args:
            phone_code_hash (`str`): The phone code hash to login to.
            code (`str`): The code to login to.
            password (`str`, optional): The 2FA password to login to.

        Examples:
            >>> await client.login("+1234567890", "123456")
            >>> await client.login("+1234567890", "123456", "123456")
        """
        self._client.start()
        if password:
            await self._client.sign_in(
                code=code, password=password, phone_code_hash=phone_code_hash
            )
        else:
            await self._client.sign_in(code=code, phone_code_hash=phone_code_hash)

        await self._client.send_message("me", "hey there")

    async def connect(self) -> None:
        """
        Connect to the Telegram client.
        """
        await self._client.connect()

    async def logout(self) -> bool:
        """
        Log out of the Telegram client.

        Examples:
            >>> await client.logout()
        """
        success = await self._client.log_out()

        return success
