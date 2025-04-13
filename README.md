<div align="center">
  <img src="logo.png" alt="MCP Telegram Logo" width="150"/>
  <h2 style="padding: 0px; margin: 0">Enable LLMs to control your Telegram</h2>
</div>

---

[![GitHub stars](https://img.shields.io/github/stars/dryeab/mcp-telegram?style=social)](https://github.com/gregpr07/browser-use/stargazers) [![PyPI version](https://badge.fury.io/py/mcp-telegram.svg)](https://badge.fury.io/py/mcp-telegram) [![Twitter Follow](https://img.shields.io/twitter/follow/dryeab?style=social)](https://twitter.com/dryeab)

**Connect Large Language Models to Telegram via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction).**

Built with [Telethon](https://github.com/LonamiWebs/Telethon), this server allows AI agents to interact with Telegram, enabling features like sending/editing/deleting messages, searching chats, managing drafts, downloading media, and more using the [MTProto](https://core.telegram.org/mtproto).

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- [`uv`](https://github.com/astral-sh/uv)  Install via the [official uv guide](https://github.com/astral-sh/uv#installation).

### Installation

Install the `mcp-telegram` CLI tool:

```bash
uv tool install mcp-telegram
```


## ⚙️ Usage

> [!IMPORTANT]
> Please ensure you have read and understood Telegram's [ToS](https://telegram.org/tos) before using this tool. Misuse of this tool may result in account restrictions.

The `mcp-telegram` command-line tool is your entry point.

```bash
mcp-telegram --help # See all commands
```

#### Login

First, authenticate with your Telegram account:

```bash
mcp-telegram login
```

<details>
<summary>Login Process</summary>

This interactive command will prompt you for:

- API ID & API Hash: Obtain these from [my.telegram.org/apps](https://my.telegram.org/apps).
- Phone Number: Your Telegram-registered phone number (international format, e.g., `+1234567890`).
- Verification Code: Sent to your Telegram account upon first login.
- 2FA Password: If you have Two-Factor Authentication enabled.

Your credentials are securely stored in the session file for future use.

> [!WARNING]
> Keep your API credentials private and never share them publicly

</details>

#### Connect to the MCP server

To use MCP Telegram with MCP clients like Claude Desktop or Cursor, you'll need to configure the MCP server. The configuration process varies by client and operating system.

For detailed setup instructions, please refer to:
- [Claude Desktop MCP Setup Guide](https://modelcontextprotocol.io/quickstart/user)
- [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol)

##### Quick Configuration Reference

The configuration file should contain:
```json
{
  "mcpServers": {
      "mcp-telegram": {
          "command": "mcp-telegram",
          "args": ["start"],
          "env": {
              "API_ID": "<your_api_id>",
              "API_HASH": "<your_api_hash>"
          }
      }
  }
}
```

> [!Note]
> Configuration paths vary by OS and client. For example:
> - macOS: `~/Library/Application Support/Claude/` or `~/.cursor/`
> - Windows: `%APPDATA%\Claude\` or `%APPDATA%\Cursor\`

After saving the configuration file, restart your application.

## 🧰 Tools

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

## 🛠️ Troubleshooting

### Database Locked Errors

Running multiple `mcp-telegram` instances using the *same session file* can cause `database is locked` errors due to Telethon's SQLite session storage. Ensure only one instance uses a session file at a time.

<details>
<summary>Force-Stopping Existing Processes</summary>

If you need to stop potentially stuck processes:

*   **macOS / Linux:** `pkill -f "mcp-telegram"`
*   **Windows:** `taskkill /F /IM mcp-telegram.exe /T` (Check Task Manager for the exact process name)

</details>

## 🤝 Contributing

We welcome contributions! If you'd like to help improve MCP Telegram, please feel free to submit issues, feature requests, or pull requests. Your feedback and contributions help make this project better for everyone.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ by <a href="https://x.com/dryeab">Yeabsira Driba</a></p>
</div>

