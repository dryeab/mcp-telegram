"""MCP Telegram CLI."""

import asyncio
import importlib.metadata
import logging
import sys

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

import typer

from mcp.types import Tool
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_telegram.server import mcp
from mcp_telegram.telegram import Telegram

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = typer.Typer(
    name="mcp-telegram",
    help="MCP Server for Telegram",
    add_completion=False,
    no_args_is_help=True,
)

console = Console()


def async_command(
    func: Callable[..., Coroutine[Any, Any, None]],
) -> Callable[..., None]:
    """Decorator to handle async Typer commands.

    Args:
        func: An async function that will be wrapped to work with Typer.

    Returns:
        A synchronous function that can be used with Typer.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        asyncio.run(func(*args, **kwargs))

    return wrapper


@app.command()
def version() -> None:
    """Show the MCP Telegram version."""
    try:
        version = importlib.metadata.version("mcp-telegram")
        console.print(
            Panel.fit(
                f"[bold blue]MCP Telegram version {version}[/bold blue]",
                title="📦 Version",
                border_style="blue",
            )
        )
    except importlib.metadata.PackageNotFoundError:
        console.print(
            Panel.fit(
                "[bold red]MCP Telegram version unknown (package not installed)\
                    [/bold red]",
                title="❌ Error",
                border_style="red",
            )
        )
        sys.exit(1)


@app.command()
@async_command
async def login() -> None:
    """Login to Telegram."""
    console.print(
        Panel.fit(
            "[bold blue]Welcome to MCP Telegram![/bold blue]\n\n"
            "To proceed with login, you'll need your Telegram API credentials:\n"
            "1. Visit [link]https://my.telegram.org/apps[/link]\n"
            "2. Create a new application if you haven't already\n"
            "3. Copy your API ID and API Hash",
            title="🚀 Telegram Authentication",
            border_style="blue",
        )
    )

    tg = Telegram()

    console.print("\n[yellow]Please enter your credentials:[/yellow]")

    try:
        api_id = int(
            console.input(
                "\n[bold cyan]🔑 API ID[/bold cyan]\n"
                "[dim]Enter your Telegram API ID (found on my.telegram.org)[/dim]\n"
                "> ",
                password=True,
            )
        )

        api_hash = console.input(
            "\n[bold cyan]🔒 API Hash[/bold cyan]\n"
            "[dim]Enter your Telegram API hash (found on my.telegram.org)[/dim]\n"
            "> ",
            password=True,
        )

        phone = console.input(
            "\n[bold cyan]📱 Phone Number[/bold cyan]\n"
            "[dim]Enter your phone number in international format \
                (e.g., +1234567890)[/dim]\n"
            "> "
        )

        tg.create_client(api_id=api_id, api_hash=api_hash)

        with console.status("[bold green]Connecting to Telegram...", spinner="dots"):
            await tg.client.connect()
            console.print(
                "\n[bold green]✓[/bold green] [dim]Connected to Telegram[/dim]"
            )

        def code_callback() -> str:
            return console.input(
                "\n[bold cyan]🔢 Verification Code[/bold cyan]\n"
                "[dim]Enter the code sent to your Telegram[/dim]\n"
                "> "
            )

        def password_callback() -> str:
            return console.input(
                "\n[bold cyan]🔐 Two-Factor Authentication[/bold cyan]\n"
                "[dim]Enter your 2FA password[/dim]\n"
                "> ",
                password=True,
            )

        await tg.client.start(
            phone=phone,
            code_callback=code_callback,
            password=password_callback,
        )  # type: ignore

        console.print("\n[bold green]✓[/bold green] [dim]Successfully logged in[/dim]")

        user = await tg.client.get_me()

        console.print(
            Panel.fit(
                f"[bold green]Authentication successful![/bold green]\n"
                f"[dim]Welcome, {user.first_name}! You can now use \
                        MCP Telegram commands.[/dim]",
                title="🎉 Success",
                border_style="green",
            )
        )

    except ValueError:
        console.print(
            "\n[bold red]✗ Error:[/bold red] API ID must be a number", style="red"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {str(e)}", style="red")
        sys.exit(1)
    finally:
        if tg.client.is_connected():
            tg.client.disconnect()


@app.command()
def start() -> None:
    """Start the MCP Telegram server."""
    mcp.run()


def _format_parameters(schema: dict[str, Any]) -> str:
    """Formats the parameters from a tool's input schema for display."""
    if not schema.get("properties"):
        return "[dim]No parameters[/dim]"

    params: list[str] = []
    properties: dict[str, dict[str, Any]] = schema.get("properties", {})
    required_params: set[str] = set(schema.get("required", []))

    for name, details in properties.items():
        param_type: str = details.get("type", "any")
        description: str = details.get("description", "")
        param_str: str = f"[bold]{name}[/bold]: [italic]{param_type}[/italic]"
        if description:
            param_str += f" - [dim]{description}[/dim]"

        if name in required_params:
            params.append(f"[red]•[/red] {param_str} [bold red](required)[/bold red]")
        else:
            params.append(f"[dim]•[/dim] {param_str}")

    return "\n".join(params) if params else "[dim]No parameters[/dim]"


@app.command()
@async_command
async def tools() -> None:
    """List all available tools in a table format."""
    try:
        tools: list[Tool] = await mcp.list_tools()
    except Exception as e:
        console.print(f"[bold red]Error fetching tools:[/bold red] {e}")
        raise typer.Exit(code=1)

    if not tools:
        console.print("[yellow]No tools available.[/yellow]")
        return

    table = Table(
        title="🔧 Available Tools",
        box=ROUNDED,
        show_header=True,
        header_style="bold blue",
        show_lines=True,
        expand=True,
    )

    table.add_column("Name", style="cyan", width=20, overflow="fold")
    table.add_column("Description", style="dim", ratio=2, overflow="fold")
    table.add_column("Parameters", ratio=3, overflow="fold")

    for tool in tools:
        table.add_row(
            f"[bold]{tool.name}[/bold]",
            tool.description or "[dim]No description[/dim]",
            _format_parameters(tool.inputSchema),
        )

    console.print(table)
