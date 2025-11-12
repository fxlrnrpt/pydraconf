"""Tests for utility functions."""

import pytest

from pydraconf.utils import get_nested_value, set_nested_value


class TestSetNestedValue:
    """Tests for set_nested_value function."""

    def test_single_level(self):
        """Test setting value at single level."""
        d = {}
        set_nested_value(d, ["key"], "value")
        assert d == {"key": "value"}

    def test_nested_levels(self):
        """Test setting value at nested levels."""
        d = {}
        set_nested_value(d, ["a", "b", "c"], 42)
        assert d == {"a": {"b": {"c": 42}}}

    def test_update_existing(self):
        """Test updating existing nested value."""
        d = {"a": {"b": {"c": 1}}}
        set_nested_value(d, ["a", "b", "c"], 42)
        assert d == {"a": {"b": {"c": 42}}}

    def test_partial_path_exists(self):
        """Test setting value when partial path exists."""
        d = {"a": {"b": 1}}
        set_nested_value(d, ["a", "c", "d"], 42)
        assert d == {"a": {"b": 1, "c": {"d": 42}}}


class TestGetNestedValue:
    """Tests for get_nested_value function."""

    def test_single_level(self):
        """Test getting value at single level."""
        d = {"key": "value"}
        assert get_nested_value(d, ["key"]) == "value"

    def test_nested_levels(self):
        """Test getting value at nested levels."""
        d = {"a": {"b": {"c": 42}}}
        assert get_nested_value(d, ["a", "b", "c"]) == 42

    def test_missing_key(self):
        """Test getting non-existent key raises KeyError."""
        d = {"a": {"b": 1}}
        with pytest.raises(KeyError):
            get_nested_value(d, ["a", "c"])

    def test_missing_nested_key(self):
        """Test getting non-existent nested key raises TypeError."""
        d = {"a": 1}
        with pytest.raises(TypeError):
            get_nested_value(d, ["a", "b"])
