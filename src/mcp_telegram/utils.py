"""
Utility functions for the MCP Telegram module.
"""


def parse_entity_id(entity: str) -> int | str:
    """
    Convert a string entity ID to an integer if it represents a number
    (including negative numbers), otherwise return the original string.

    Args:
        entity (`str`): The entity which could be a numeric ID or a username/handle

    Returns:
        `int | str`: Integer if the input is a valid number, otherwise the original string
    """
    return int(entity) if entity.lstrip("-").isdigit() else entity
