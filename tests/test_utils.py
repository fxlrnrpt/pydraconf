"""Tests for utility functions."""

import pytest

from pydraconf.utils import camel_to_kebab, get_nested_value, kebab_to_snake, set_nested_value


class TestCamelToKebab:
    """Tests for camel_to_kebab function."""

    def test_simple_camel_case(self):
        """Test simple CamelCase conversion."""
        assert camel_to_kebab("QuickTest") == "quick-test"
        assert camel_to_kebab("DevConfig") == "dev-config"

    def test_multiple_capitals(self):
        """Test multiple consecutive capitals."""
        assert camel_to_kebab("MLTrainingConfig") == "ml-training-config"
        assert camel_to_kebab("HTTPServer") == "http-server"

    def test_single_word(self):
        """Test single word."""
        assert camel_to_kebab("Config") == "config"

    def test_already_lowercase(self):
        """Test already lowercase string."""
        assert camel_to_kebab("config") == "config"


class TestKebabToSnake:
    """Tests for kebab_to_snake function."""

    def test_basic_conversion(self):
        """Test basic kebab to snake conversion."""
        assert kebab_to_snake("hidden-dim") == "hidden_dim"
        assert kebab_to_snake("pool-size") == "pool_size"

    def test_no_hyphens(self):
        """Test string without hyphens."""
        assert kebab_to_snake("config") == "config"


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
