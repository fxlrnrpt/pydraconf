"""Tests for ConfigCLIParser."""

import pytest
from pydantic import BaseModel, Field

from pydraconf.cli import ConfigCLIParser
from pydraconf.registry import ConfigRegistry


class SimpleConfig(BaseModel):
    """Simple config for testing."""

    value: int = Field(default=10, description="A test value")
    name: str = Field(default="test", description="A test name")
    enabled: bool = Field(default=False, description="Enable flag")


class NestedConfig(BaseModel):
    """Nested config for testing."""

    inner: int = Field(default=5, description="Inner value")


class ConfigWithNested(BaseModel):
    """Config with nested field."""

    top: int = Field(default=100, description="Top value")
    nested: NestedConfig = Field(default_factory=NestedConfig, description="Nested config")


class TestConfigCLIParser:
    """Tests for ConfigCLIParser class."""

    @pytest.fixture
    def registry(self):
        """Create a registry with some test data."""
        reg = ConfigRegistry()
        reg.register_variant("variant1", SimpleConfig)
        reg.register_variant("variant2", SimpleConfig)
        return reg

    def test_parse_no_args(self, registry):
        """Test parsing with no arguments."""
        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse([])

        assert variant is None
        assert groups == {}
        assert overrides == {}

    def test_parse_variant_selection(self, registry):
        """Test parsing variant selection."""
        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(["--config=variant1"])

        assert variant == "variant1"
        assert groups == {}
        assert overrides == {}

    def test_parse_field_overrides(self, registry):
        """Test parsing field overrides."""
        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(["--value=42", "--name=test123"])

        assert variant is None
        assert groups == {}
        assert "value" in overrides
        assert overrides["value"] == 42
        assert "name" in overrides
        assert overrides["name"] == "test123"

    def test_parse_boolean_field(self, registry):
        """Test parsing boolean fields."""
        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(["--enabled=true"])

        assert overrides["enabled"] is True

        variant, groups, overrides = parser.parse(["--enabled=false"])
        assert overrides["enabled"] is False

    def test_parse_group_selection(self, registry):
        """Test parsing group selection."""
        registry.register_group("model", "small", SimpleConfig)
        registry.register_group("model", "large", SimpleConfig)

        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(["model=small"])

        assert variant is None
        assert groups == {"model": "small"}
        assert overrides == {}

    def test_parse_multiple_groups(self, registry):
        """Test parsing multiple group selections."""
        registry.register_group("model", "small", SimpleConfig)
        registry.register_group("optimizer", "adam", SimpleConfig)

        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(["model=small", "optimizer=adam"])

        assert groups == {"model": "small", "optimizer": "adam"}

    def test_parse_all_three_types(self, registry):
        """Test parsing all three override types together."""
        registry.register_group("model", "small", SimpleConfig)

        parser = ConfigCLIParser(SimpleConfig, registry)
        variant, groups, overrides = parser.parse(
            ["--config=variant1", "model=small", "--value=42"]
        )

        assert variant == "variant1"
        assert groups == {"model": "small"}
        assert overrides["value"] == 42

    def test_nested_field_arguments(self, registry):
        """Test that nested fields generate proper arguments."""
        parser = ConfigCLIParser(ConfigWithNested, registry)
        variant, groups, overrides = parser.parse(["--top=200", "--nested.inner=10"])

        assert overrides["top"] == 200
        assert overrides["nested.inner"] == 10  # Stored with dot notation

    def test_kebab_case_conversion(self, registry):
        """Test that underscored fields accept kebab-case."""

        class ConfigWithUnderscores(BaseModel):
            batch_size: int = 32
            learning_rate: float = 0.001

        parser = ConfigCLIParser(ConfigWithUnderscores, registry)
        variant, groups, overrides = parser.parse(["--batch-size=64", "--learning-rate=0.01"])

        assert overrides["batch_size"] == 64
        assert overrides["learning_rate"] == 0.01
