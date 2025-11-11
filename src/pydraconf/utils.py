"""Utility functions for PydraConf."""

import re
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


def camel_to_kebab(name: str) -> str:
    """Convert CamelCase to kebab-case.

    Args:
        name: CamelCase string

    Returns:
        kebab-case string

    Example:
        >>> camel_to_kebab("QuickTest")
        "quick-test"
        >>> camel_to_kebab("MLTrainingConfig")
        "ml-training-config"
    """
    # Insert hyphen before uppercase letters (except at start)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    # Insert hyphen before uppercase followed by lowercase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    return s2.lower()


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case to snake_case.

    Args:
        name: kebab-case string

    Returns:
        snake_case string

    Example:
        >>> kebab_to_snake("hidden-dim")
        "hidden_dim"
    """
    return name.replace("-", "_")
