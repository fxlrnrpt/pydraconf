"""Tests for ConfigRegistry."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from pydraconf.registry import ConfigRegistry


class TestConfigRegistry:
    """Tests for ConfigRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return ConfigRegistry()

    @pytest.fixture
    def fixtures_path(self):
        """Path to test fixtures."""
        return Path(__file__).parent / "fixtures" / "configs"

    def test_empty_registry(self, registry):
        """Test newly created registry is empty."""
        assert registry.list_groups() == {}
        assert registry.list_variants() == []

    def test_discover_variants(self, registry, fixtures_path):
        """Test discovering variant configs (subclasses)."""
        registry.discover(fixtures_path)
        variants = registry.list_variants()

        # Should find ChildConfig and ComplexVariant
        assert "child-config" in variants
        assert "complex-variant" in variants

    def test_discover_groups(self, registry, fixtures_path):
        """Test discovering config groups (subdirectories)."""
        registry.discover(fixtures_path)
        groups = registry.list_groups()

        assert "model" in groups
        assert "small" in groups["model"]
        assert "large" in groups["model"]

    def test_get_variant(self, registry, fixtures_path):
        """Test retrieving a variant config."""
        registry.discover(fixtures_path)
        variant_cls = registry.get_variant("child-config")

        assert variant_cls is not None
        assert issubclass(variant_cls, BaseModel)

        # Test instantiation
        instance = variant_cls()
        assert instance.value == 20
        assert instance.name == "child"

    def test_get_group(self, registry, fixtures_path):
        """Test retrieving a config from a group."""
        registry.discover(fixtures_path)
        model_cls = registry.get_group("model", "small")

        assert model_cls is not None
        assert issubclass(model_cls, BaseModel)

        # Test instantiation
        instance = model_cls()
        assert instance.size == 100
        assert instance.layers == 2

    def test_get_nonexistent_variant(self, registry, fixtures_path):
        """Test getting non-existent variant raises KeyError."""
        registry.discover(fixtures_path)
        with pytest.raises(KeyError, match="Config variant 'nonexistent' not found"):
            registry.get_variant("nonexistent")

    def test_get_nonexistent_group(self, registry, fixtures_path):
        """Test getting non-existent group raises KeyError."""
        registry.discover(fixtures_path)
        with pytest.raises(KeyError, match="Config group 'nonexistent' not found"):
            registry.get_group("nonexistent", "small")

    def test_get_nonexistent_config_in_group(self, registry, fixtures_path):
        """Test getting non-existent config in existing group raises KeyError."""
        registry.discover(fixtures_path)
        with pytest.raises(KeyError, match="Config 'nonexistent' not found in group 'model'"):
            registry.get_group("model", "nonexistent")

    def test_register_variant_manually(self, registry):
        """Test manually registering a variant."""

        class TestVariant(BaseModel):
            value: int = 42

        registry.register_variant("test-variant", TestVariant)
        assert "test-variant" in registry.list_variants()

        retrieved = registry.get_variant("test-variant")
        assert retrieved == TestVariant

    def test_register_group_manually(self, registry):
        """Test manually registering a config group."""

        class TestConfig(BaseModel):
            value: int = 42

        registry.register_group("testgroup", "testconfig", TestConfig)
        groups = registry.list_groups()

        assert "testgroup" in groups
        assert "testconfig" in groups["testgroup"]

        retrieved = registry.get_group("testgroup", "testconfig")
        assert retrieved == TestConfig

    def test_discover_nonexistent_directory(self, registry):
        """Test discovering from non-existent directory doesn't crash."""
        registry.discover(Path("/nonexistent/path"))
        assert registry.list_groups() == {}
        assert registry.list_variants() == []
