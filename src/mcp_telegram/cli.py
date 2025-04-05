"""MCP Telegram CLI."""

import importlib.metadata
import sys

from typer import Typer

app = Typer(
    name="mcp-telegram",
    help="MCP Server for Telegram",
    add_completion=False,
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show the MCP Telegram version."""
    try:
        version = importlib.metadata.version("mcp-telegram")
        print(f"MCP Telegram version {version}")
    except importlib.metadata.PackageNotFoundError:
        print("MCP Telegram version unknown (package not installed)")
        sys.exit(1)
