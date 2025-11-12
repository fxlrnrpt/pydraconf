"""Utility functions for PydraConf."""

from typing import Any


def set_nested_value(d: dict, path: list[str], value: Any) -> None:
    """Set value at nested path in dictionary.

    Args:
        d: Dictionary to modify in place
        path: List of keys representing path (e.g., ["a", "b", "c"])
        value: Value to set at the path

    Example:
        >>> d = {}
        >>> set_nested_value(d, ["a", "b", "c"], 42)
        >>> d
        {"a": {"b": {"c": 42}}}
    """
    for key in path[:-1]:
        d = d.setdefault(key, {})
    d[path[-1]] = value


def get_nested_value(d: dict, path: list[str]) -> Any:
    """Get value at nested path in dictionary.

    Args:
        d: Dictionary to read from
        path: List of keys representing path

    Returns:
        Value at the specified path

    Raises:
        KeyError: If path doesn't exist

    Example:
        >>> d = {"a": {"b": {"c": 42}}}
        >>> get_nested_value(d, ["a", "b", "c"])
        42
    """
    result = d
    for key in path:
        result = result[key]
    return result
