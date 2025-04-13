# MCP Telegram Server 🚀

[![PyPI version](https://badge.fury.io/py/mcp-telegram.svg)](https://badge.fury.io/py/mcp-telegram)

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/introduction) server for interacting with Telegram. Built with [Telethon](https://github.com/LonamiWebs/Telethon), allowing large language models to connect to and control a Telegram account via the MTProto API.

This server enables functionalities like sending, editing, and deleting messages, retrieving message history, searching chats, managing drafts, and downloading media.


## 📦 Installation

This package is published on PyPI as `mcp-telegram`.

**We strongly recommend using [`uv`](https://github.com/astral-sh/uv) for installation.**

```bash
uv pip install mcp-telegram
```

This will install the server and the `mcp-telegram` CLI tool.

## 🔧 CLI Tool (`mcp-telegram`)

The `mcp-telegram` command-line tool helps you manage the server and your Telegram session.

```bash
mcp-telegram --help
```

### Available Commands:

- **`login`**: Authenticate with your Telegram account.

  ```bash
  mcp-telegram login
  ```

  This interactive command will prompt you for:

  1.  **API ID & API Hash:** Obtain these from [my.telegram.org/apps](https://my.telegram.org/apps).
  2.  **Phone Number:** Your Telegram-registered phone number (international format, e.g., `+1234567890`).
  3.  **Verification Code:** Sent to your Telegram account upon first login.
  4.  **2FA Password:** If you have Two-Factor Authentication enabled.

- **`start`**: Start the MCP Telegram server.

  ```bash
  mcp-telegram start
  ```

- **`tools`**: List the available MCP tools provided by the server.

  ```bash
  mcp-telegram tools
  ```

  Displays a table with tool names, descriptions, and parameters.

- **`version`**: Show the installed version of `mcp-telegram`.
  ```bash
  mcp-telegram version
  ```

## 📁 Session and File Paths

- **Session File:** Your Telegram session data (allowing persistent login) is stored securely in the standard user state directory.
  - **Linux/macOS:** `$XDG_STATE_HOME/mcp-telegram/session` (usually `~/.local/state/mcp-telegram/session`)
  - **Windows:** `%LOCALAPPDATA%\mcp-telegram\mcp-telegram\session` (usually `C:\Users\<YourUsername>\AppData\Local\mcp-telegram\mcp-telegram\session`)
- **Media Downloads:** By default, media files downloaded via the `media_download` tool are saved to:
  - **Linux/macOS:** `$XDG_STATE_HOME/mcp-telegram/downloads/`
  - **Windows:** `%LOCALAPPDATA%\mcp-telegram\mcp-telegram\downloads\`
    You can specify a custom path when calling the `media_download` tool.

## 🛠️ Multi-client Locking

Running multiple `mcp-telegram` server instances using the _same session file_ simultaneously can lead to database locking issues, especially with Telethon's default SQLite session storage.

If you encounter locking errors (`database is locked`), ensure only one instance is running against a specific session file.

**Force-Stopping Existing Processes:**

- **macOS / Linux:**
  ```bash
  pkill -f "mcp-telegram"
  # Or, if the above is too broad:
  # pkill -f "/path/to/your/venv/bin/mcp-telegram"
  ```
- **Windows (Command Prompt / PowerShell):**
  ```powershell
  taskkill /F /IM mcp-telegram.exe /T
  # Note: The exact process name might vary depending on how it's run.
  # Use Task Manager (Ctrl+Shift+Esc) to find the correct process name if needed.
  ```

Consider running multiple instances only if they use separate session files (e.g., by setting the `XDG_STATE_HOME` environment variable differently for each instance or by modifying the code to support distinct session names).

## 🛡️ Security Notes & Disclaimer

- **API Credentials:** **NEVER** share your `API ID` and `API Hash` publicly. The `login` command prompts for them interactively and they are stored securely within the Telethon session file, not in plain text configuration files by this package.
- **Terms of Service:** Using this tool may potentially violate Telegram's Terms of Service, depending on your usage patterns. **You are solely responsible for complying with Telegram's ToS.** Excessive or abusive usage could lead to your account being flagged or banned by Telegram. Use this tool responsibly.

## 🧰 MCP Server Tools

The following tools are available through the MCP server:

| Name                | Description                                                             | Example Use Case                                                                 |
| :------------------ | :---------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| `send_message`      | Sends a text message or file to a user, group, or channel.              | Sending "Hello there!" to a friend (`@username`) or a group chat (`-100123...`). |
| `edit_message`      | Edits a previously sent message.                                        | Correcting a typo in a message sent to "me" (Saved Messages).                    |
| `delete_message`    | Deletes one or more messages.                                           | Removing accidentally sent messages from a chat.                                 |
| `search_dialogs`    | Searches for users, groups, and channels by name or username.           | Finding the chat ID for "Project Group" to send a message there.                 |
| `get_draft`         | Retrieves the current message draft for a specific chat.                | Checking if you left an unfinished message in a chat with `@colleague`.          |
| `set_draft`         | Sets or clears the message draft for a specific chat.                   | Saving a reminder message as a draft in "me" (Saved Messages).                   |
| `get_messages`      | Retrieves message history from a chat, with filtering options.          | Getting the last 5 unread messages from a specific channel.                      |
| `media_download`    | Downloads media (photos, videos, documents) attached to a message.      | Saving an important PDF document received in a group chat.                       |
| `message_from_link` | Retrieves a specific message using its public or private Telegram link. | Fetching the content of a message referenced by a `t.me/c/...` link.             |

_Use the `mcp-telegram tools` CLI command for detailed parameter information._

## 🌐 Learn More about MCP

- **MCP Documentation:** [modelcontextprotocol.io/introduction](https://modelcontextprotocol.io/introduction)

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
