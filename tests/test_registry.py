"""Tests for ConfigRegistry."""

from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel

from pydraconf.base_config import PydraConfig
from pydraconf.registry import ConfigRegistry
from tests.fixtures.configs.base import BaseTestConfig, ChildConfig, ComplexConfig
from tests.fixtures.configs.model.small import SmallModelConfig


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
        """Test discovering variant configs (subclasses of main config)."""
        # BaseTestConfig is the main config - should find its subclassess
        registry.discover(fixtures_path, BaseTestConfig)
        variants = registry.list_variants()

        # Should find ChildConfig (direct subclass of BaseTestConfig)
        assert "ChildConfig" in variants
        # ComplexVariant is a subclass of ComplexConfig, not BaseTestConfig
        assert "ComplexVariant" not in variants

        # If we use ComplexConfig as main, should find ComplexVariant
        registry2 = ConfigRegistry()
        registry2.discover(fixtures_path, ComplexConfig)
        variants2 = registry2.list_variants()
        assert "ComplexVariant" in variants2

    def test_discover_groups(self, registry, fixtures_path):
        """Test discovering config groups (subclasses of nested field types)."""
        # BaseTestConfig has a 'model' field of type ModelConfig
        # SmallModelConfig and LargeModelConfig are subclasses of ModelConfig
        registry.discover(fixtures_path, BaseTestConfig)
        groups = registry.list_groups()

        assert "model" in groups
        assert "SmallModelConfig" in groups["model"]
        assert "LargeModelConfig" in groups["model"]

    def test_get_variant(self, registry, fixtures_path):
        """Test retrieving a variant config."""
        registry.discover(fixtures_path, BaseTestConfig)
        variant_cls = registry.get_variant("ChildConfig")

        assert variant_cls is not None
        assert issubclass(variant_cls, BaseModel)

        # Test instantiation
        instance = cast(ChildConfig, variant_cls())
        assert instance.value == 20
        assert instance.name == "child"

    def test_get_group(self, registry, fixtures_path):
        """Test retrieving a config from a group."""
        registry.discover(fixtures_path, BaseTestConfig)
        model_cls = registry.get_group("model", "SmallModelConfig")

        assert model_cls is not None
        assert issubclass(model_cls, BaseModel)

        # Test instantiation
        instance = cast(SmallModelConfig, model_cls())
        assert instance.size == 50  # SmallModelConfig overrides base default
        assert instance.layers == 1

    def test_get_nonexistent_variant(self, registry: ConfigRegistry, fixtures_path: Path):
        """Test getting non-existent variant raises KeyError."""
        registry.discover(fixtures_path, BaseTestConfig)
        with pytest.raises(KeyError, match="Config variant 'nonexistent' not found"):
            registry.get_variant("nonexistent")

    def test_get_nonexistent_group(self, registry: ConfigRegistry, fixtures_path: Path):
        """Test getting non-existent group raises KeyError."""
        registry.discover(fixtures_path, BaseTestConfig)
        with pytest.raises(KeyError, match="Config group 'nonexistent' not found"):
            registry.get_group("nonexistent", "small")

    def test_get_nonexistent_config_in_group(self, registry: ConfigRegistry, fixtures_path: Path):
        """Test getting non-existent config in existing group raises KeyError."""
        registry.discover(fixtures_path, BaseTestConfig)
        with pytest.raises(KeyError, match="Config 'nonexistent' not found in group 'model'"):
            registry.get_group("model", "nonexistent")

    def test_register_variant_manually(self, registry: ConfigRegistry):
        """Test manually registering a variant."""

        class TestVariant(PydraConfig):
            value: int = 42

        registry.register_variant("TestVariant", TestVariant)
        assert "TestVariant" in registry.list_variants()

        retrieved = registry.get_variant("TestVariant")
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
        registry.discover(Path("/nonexistent/path"), BaseTestConfig)
        assert registry.list_groups() == {}
        assert registry.list_variants() == []

    def test_multiple_classes_in_one_file(self, registry, tmp_path):
        """Test discovering multiple config classes from a single file."""
        # Create a config directory with one file containing multiple classes
        config_dir = tmp_path / "configs"
        config_dir.mkdir(parents=True)

        # Write base config with ModelConfig field type
        base_file = config_dir / "base.py"
        base_file.write_text('''
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Base model config type."""
    pass

class MainConfig(BaseModel):
    """Main configuration."""
    model: ModelConfig = Field(default_factory=ModelConfig)
''')

        # Write a file with multiple model config classes that inherit from ModelConfig
        variants_file = config_dir / "variants.py"
        variants_file.write_text("""
from base import ModelConfig

class SmallModel(ModelConfig):
    hidden_dim: int = 256
    layers: int = 4

class MediumModel(ModelConfig):
    hidden_dim: int = 512
    layers: int = 8

class LargeModel(ModelConfig):
    hidden_dim: int = 1024
    layers: int = 16
""")

        # Need to import MainConfig to pass to discover
        import sys

        sys.path.insert(0, str(config_dir))
        from base import MainConfig  # pyrefly: ignore[missing-import]

        # Discover configs
        registry.discover(config_dir, MainConfig)
        groups = registry.list_groups()

        # All three classes should be registered in the "model" group
        assert "model" in groups
        assert "SmallModel" in groups["model"]
        assert "MediumModel" in groups["model"]
        assert "LargeModel" in groups["model"]

        # Verify we can retrieve each class
        small = registry.get_group("model", "SmallModel")
        medium = registry.get_group("model", "MediumModel")
        large = registry.get_group("model", "LargeModel")

        # Test instantiation
        small_instance = small()
        assert small_instance.hidden_dim == 256
        assert small_instance.layers == 4

        medium_instance = medium()
        assert medium_instance.hidden_dim == 512
        assert medium_instance.layers == 8

        large_instance = large()
        assert large_instance.hidden_dim == 1024
        assert large_instance.layers == 16

        # Clean up sys.path
        sys.path.remove(str(config_dir))
