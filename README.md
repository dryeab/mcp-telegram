<div align="center">
  <img src="logo.png" alt="MCP Telegram Logo" width="150"/>
  <h2 style="padding: 0px; margin-top: 0">Enable LLMs to control your Telegram</h2>
</div>

<div align="center">
  [![PyPI version](https://badge.fury.io/py/mcp-telegram.svg)](https://badge.fury.io/py/mcp-telegram) [![Twitter Follow](https://img.shields.io/twitter/follow/dryeab?style=social)](https://twitter.com/dryeab)
</div>

---

**Connect Language Models to Telegram via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).**

Built with [Telethon](https://github.com/LonamiWebs/Telethon), this server allows AI agents to interact with Telegram, enabling features like sending/editing/deleting messages, searching chats, managing drafts, downloading media, and more using the MTProto API.

## 🚀 Getting Started

### 📦 Installation

Published on PyPI as `mcp-telegram`.

**Requires [`uv`](https://github.com/astral-sh/uv) for installation.**

```bash
# Create & activate a virtual environment (optional but recommended)
uv venv
. .venv/bin/activate 

# Install the package
uv pip install mcp-telegram
```

This installs the server and the `mcp-telegram` CLI.

## ⚙️ Usage

The `mcp-telegram` command-line tool is your entry point.

```bash
mcp-telegram --help # See all commands
```

### 1. Login

First, authenticate with your Telegram account:

```bash
mcp-telegram login
```

<details>
<summary>Login Process Details</summary>

This interactive command will prompt you for:

1.  **API ID & API Hash:** Obtain these from [my.telegram.org/apps](https://my.telegram.org/apps).
2.  **Phone Number:** Your Telegram-registered phone number (international format, e.g., `+1234567890`).
3.  **Verification Code:** Sent to your Telegram account upon first login.
4.  **2FA Password:** If you have Two-Factor Authentication enabled.

Your credentials are securely stored in the session file (see below) for future use.

</details>

### 2. Start Server

Run the MCP server:

```bash
mcp-telegram start
```

The server will listen for incoming MCP client connections.

### Other Commands

*   `mcp-telegram tools`: List available MCP tools with descriptions and parameters.
*   `mcp-telegram version`: Show the installed package version.

## 📁 Configuration & Data

*   **Session File:** Securely stores your login session.
*   **Media Downloads:** Default location for files downloaded via the `media_download` tool.

<details>
<summary>Default File Paths</summary>

Locations follow standard user directories:

*   **Linux/macOS:**
    *   Session: `$XDG_STATE_HOME/mcp-telegram/session` (usually `~/.local/state/mcp-telegram/session`)
    *   Downloads: `$XDG_STATE_HOME/mcp-telegram/downloads/`
*   **Windows:**
    *   Session: `%LOCALAPPDATA%\mcp-telegram\mcp-telegram\session`
    *   Downloads: `%LOCALAPPDATA%\mcp-telegram\mcp-telegram\downloads\`

*(Note: The `media_download` tool allows specifying a custom download path.)*

</details>

## ⚠️ Concurrency & Locking

Running multiple `mcp-telegram` instances using the *same session file* can cause `database is locked` errors due to Telethon's SQLite session storage. Ensure only one instance uses a session file at a time.

<details>
<summary>Force-Stopping Existing Processes</summary>

If you need to stop potentially stuck processes:

*   **macOS / Linux:** `pkill -f "mcp-telegram"`
*   **Windows:** `taskkill /F /IM mcp-telegram.exe /T` (Check Task Manager for the exact process name)

</details>

## 🛡️ Security Notes & Disclaimer

*   **API Credentials:** **NEVER** share your `API ID` and `API Hash` publicly. They are handled securely during the interactive `login` and stored within the encrypted session file.
*   **Account Safety:** Automation via APIs carries inherent risks. This project **does not guarantee the safety of your Telegram account**.
*   **Terms of Service:** Using this tool might conflict with Telegram's Terms of Service depending on usage. **You are solely responsible for compliance.** Misuse could lead to account restrictions. Use responsibly.

## 🧰 MCP Server Tools

The following tools are available via MCP:

| Name                | Description                                                             |
| :------------------ | :---------------------------------------------------------------------- |
| `send_message`      | Sends a text message or file to a user, group, or channel.              |
| `edit_message`      | Edits a previously sent message.                                        |
| `delete_message`    | Deletes one or more messages.                                           |
| `search_dialogs`    | Searches for users, groups, and channels by name or username.           |
| `get_draft`         | Retrieves the current message draft for a specific chat.                |
| `set_draft`         | Sets or clears the message draft for a specific chat.                   |
| `get_messages`      | Retrieves message history from a chat, with filtering options.          |
| `media_download`    | Downloads media (photos, videos, documents) attached to a message.      |
| `message_from_link` | Retrieves a specific message using its public or private Telegram link. |

*Use `mcp-telegram tools` for detailed parameter information and example use cases.*

## 🌐 Learn More about MCP

*   **MCP Documentation:** [modelcontextprotocol.io/introduction](https://modelcontextprotocol.io/introduction)

## 🙏 Acknowledgements

*   Built upon the excellent [**Telethon**](https://github.com/LonamiWebs/Telethon) library.

## 📄 License

MIT License. See the `LICENSE` file.
