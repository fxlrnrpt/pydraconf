"""Integration tests for end-to-end config building."""

from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel, Field

from pydraconf.cli import ConfigCLIParser
from pydraconf.decorators import _build_config
from pydraconf.registry import ConfigRegistry
from tests.test_registry import SmallModelConfig


class ModelConfig(BaseModel):
    """Base model config."""

    size: int = Field(default=100, description="Model size")


class OptimizerConfig(BaseModel):
    """Base optimizer config."""

    lr: float = Field(default=0.001, description="Learning rate")


class TrainConfig(BaseModel):
    """Training configuration."""

    epochs: int = Field(default=100, description="Number of epochs")
    model: ModelConfig = Field(default_factory=ModelConfig, description="Model config")
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig, description="Optimizer config")


class QuickTest(TrainConfig):
    """Quick test variant."""

    epochs: int = 5


class TestIntegration:
    """Integration tests for full config building pipeline."""

    @pytest.fixture
    def fixtures_path(self):
        """Path to test fixtures."""
        return Path(__file__).parent / "fixtures" / "configs"

    @pytest.fixture
    def registry(self, fixtures_path):
        """Create and populate registry."""
        reg = ConfigRegistry()
        reg.discover(fixtures_path)
        return reg

    def test_base_config_only(self, registry):
        """Test building config with no overrides."""
        config = _build_config(TrainConfig, registry, {}, {})

        assert isinstance(config, TrainConfig)
        assert config.epochs == 100
        assert isinstance(config.model, ModelConfig)
        assert config.model.size == 100

    def test_variant_selection(self, registry):
        """Test building config with variant selection."""
        variant_cls = QuickTest
        config = _build_config(variant_cls, registry, {}, {})

        assert isinstance(config, QuickTest)
        assert config.epochs == 5

    def test_group_selection(self, registry):
        """Test building config with group selection."""
        config = _build_config(TrainConfig, registry, {"model": "SmallModelConfig"}, {})

        assert isinstance(config, TrainConfig)
        # Model should be swapped to SmallModelConfig
        assert config.model.__class__.__name__ == "SmallModelConfig"
        assert isinstance(config.model, SmallModelConfig)
        assert config.model.size == 100
        assert config.model.layers == 2

    def test_field_overrides(self, registry):
        """Test building config with field overrides."""
        config = _build_config(TrainConfig, registry, {}, {"epochs": 50})

        assert isinstance(config, TrainConfig)
        assert config.epochs == 50

    def test_nested_field_overrides(self, registry):
        """Test building config with nested field overrides."""
        config = _build_config(TrainConfig, registry, {}, {"model.size": 500})

        assert isinstance(config, TrainConfig)
        assert config.model.size == 500

    def test_all_three_override_types(self, registry):
        """Test building config with variant + groups + overrides."""
        variant_cls = QuickTest
        groups = {"model": "LargeModelConfig"}
        overrides = {"epochs": 10, "model.size": 2000}

        config = _build_config(variant_cls, registry, groups, overrides)

        # Should be QuickTest variant
        assert isinstance(config, QuickTest)

        # epochs should be overridden (override priority: CLI > group > variant > base)
        assert config.epochs == 10

        # Model should be LargeModelConfig (group selection)
        assert config.model.__class__.__name__ == "LargeModelConfig"

        # Model size should be overridden
        assert config.model.size == 2000

    def test_override_priority(self, registry):
        """Test correct override priority: CLI > groups > variant > base."""

        # Base: epochs=100
        # Variant (QuickTest): epochs=5
        # Group: model=SmallModelConfig (size=100, layers=2)
        # CLI: epochs=15, model.layers=5

        config = cast(
            QuickTest, _build_config(QuickTest, registry, {"model": "SmallModelConfig"}, {"epochs": 15, "model.layers": 5})
        )

        # epochs from CLI override (highest priority)
        assert config.epochs == 15

        # model from group selection
        assert config.model.__class__.__name__ == "SmallModelConfig"

        # model.size from group default
        assert config.model.size == 100

        # model.layers from CLI override
        assert config.model.layers == 5  # pyright: ignore[reportAttributeAccessIssue]

    def test_multiple_group_swaps(self, registry):
        """Test swapping multiple config groups."""

        class FullConfig(BaseModel):
            model: BaseModel = Field(default_factory=ModelConfig)
            optimizer: BaseModel = Field(default_factory=OptimizerConfig)

        # Register optimizer group
        registry.register_group("optimizer", "OptimizerConfig", OptimizerConfig)

        config = cast(FullConfig, _build_config(FullConfig, registry, {"model": "SmallModelConfig", "optimizer": "OptimizerConfig"}, {}))

        assert isinstance(config.model, SmallModelConfig)
        assert config.model.__class__.__name__ == "SmallModelConfig"
        # Note: OptimizerConfig has no variants in fixtures, so it stays as is
        # In a real scenario with different optimizer configs, this would change

    def test_end_to_end_with_cli_parser(self, registry):
        """Test complete end-to-end flow with CLI parser."""
        parser = ConfigCLIParser(TrainConfig, registry)
        variant_name, groups, overrides = parser.parse(["--epochs=50", "model=SmallModelConfig"])

        # variant_name should be None (no --config specified)
        assert variant_name is None

        # Build config
        config = cast(TrainConfig, _build_config(TrainConfig, registry, groups, overrides))

        assert config.epochs == 50
        assert config.model.__class__.__name__ == "SmallModelConfig"
