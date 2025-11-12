"""Tests for the provide_config decorator."""

import sys
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from pydraconf.decorators import provide_config


class BaseConfig(BaseModel):
    """Base configuration."""

    value: int = Field(default=10, description="Base value")


class DerivedConfig(BaseConfig):
    """Derived configuration - subclass of BaseConfig."""

    value: int = 20
    extra_value: int = 30


class UnrelatedConfig(BaseModel):
    """Unrelated configuration - not a subclass of BaseConfig."""

    other_value: str = "test"


class TestProvideConfigDecorator:
    """Test the provide_config decorator."""

    def test_decorator_infers_config_from_type_annotation(self, tmp_path):
        """Test that decorator infers config class from function parameter."""

        @provide_config(config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, BaseConfig)
        assert result.value == 10

    def test_decorator_with_explicit_config_cls(self, tmp_path):
        """Test providing explicit config_cls parameter."""

        @provide_config(config_cls=DerivedConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, DerivedConfig)
        assert result.value == 20
        assert result.extra_value == 30

    def test_explicit_config_cls_must_be_subclass(self, tmp_path):
        """Test that explicit config_cls must be subclass of type annotation."""
        with pytest.raises(TypeError, match="must be a subclass of"):

            @provide_config(config_cls=UnrelatedConfig, config_dirs=str(tmp_path))
            def my_func(cfg: BaseConfig):
                return cfg

    def test_config_cls_validates_at_decoration_time(self, tmp_path):
        """Test that config_cls validation happens when decorator is applied."""
        # Should raise immediately when decorator is applied, not when function is called
        with pytest.raises(TypeError, match="must be a subclass of"):

            @provide_config(config_cls=UnrelatedConfig, config_dirs=str(tmp_path))
            def my_func(cfg: BaseConfig):
                return cfg

            # Should not reach here
            my_func()

    def test_explicit_config_cls_with_cli_overrides(self, tmp_path):
        """Test that CLI overrides work with explicit config_cls."""

        @provide_config(config_cls=DerivedConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py", "--value=100"]):
            result = my_func()

        assert isinstance(result, DerivedConfig)
        assert result.value == 100  # CLI override
        assert result.extra_value == 30  # Default from DerivedConfig

    def test_none_config_cls_uses_type_annotation(self, tmp_path):
        """Test that config_cls=None (default) uses type annotation."""

        @provide_config(config_cls=None, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, BaseConfig)
        assert result.value == 10

    def test_config_cls_does_not_prevent_cli_overrides(self, tmp_path):
        """Test that CLI overrides still work with explicit config_cls."""

        @provide_config(config_cls=DerivedConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        # CLI overrides should still work for fields in the type annotation
        # Note: Only fields from BaseConfig (type annotation) are available via CLI
        with patch.object(sys, "argv", ["test.py", "--value=999"]):
            result = my_func()

        # Should use DerivedConfig as the base
        assert isinstance(result, DerivedConfig)
        assert result.value == 999  # CLI override
        assert result.extra_value == 30  # Default from DerivedConfig

    def test_discovery_uses_type_annotation_not_config_cls(self, tmp_path):
        """Test that discovery uses type annotation, not explicit config_cls.

        This ensures that:
        1. Variants are discovered based on the type annotation
        2. Groups are discovered based on the type annotation's nested fields
        3. CLI parameters are based on the type annotation's fields
        """

        @provide_config(config_cls=DerivedConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        # Without config_cls, we should use the type annotation (BaseConfig)
        # BaseConfig only has 'value' field
        # DerivedConfig has both 'value' and 'extra_value' fields
        # Since discovery uses BaseConfig, only 'value' should be available in CLI
        with patch.object(sys, "argv", ["test.py", "--value=777"]):
            result = my_func()

        # Should use DerivedConfig as the base (from config_cls parameter)
        assert isinstance(result, DerivedConfig)
        # But CLI should only allow BaseConfig fields
        assert result.value == 777  # CLI override worked
        assert result.extra_value == 30  # Default from DerivedConfig (not overridable via CLI)

    def test_missing_type_annotation_raises_error(self, tmp_path):
        """Test that missing type annotation raises TypeError."""
        with pytest.raises(TypeError, match="must have type hints for its first parameter"):

            @provide_config(config_dirs=str(tmp_path))
            def my_func(cfg):  # No type hint
                return cfg

    def test_non_basemodel_type_annotation_raises_error(self, tmp_path):
        """Test that non-BaseModel type annotation raises TypeError."""
        with pytest.raises(TypeError, match="must be a Pydantic BaseModel"):

            @provide_config(config_dirs=str(tmp_path))  # pyright: ignore[reportArgumentType]
            def my_func(cfg: int):  # Not a BaseModel
                return cfg

    def test_config_cls_parameter_order(self, tmp_path):
        """Test that config_cls is the first parameter."""

        # Should work with positional argument
        @provide_config(DerivedConfig, str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, DerivedConfig)
        assert result.value == 20

    def test_config_dirs_still_works_as_keyword(self, tmp_path):
        """Test that config_dirs can still be used as keyword argument."""

        @provide_config(config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, BaseConfig)
        assert result.value == 10

    def test_both_parameters_as_keywords(self, tmp_path):
        """Test using both parameters as keyword arguments."""

        @provide_config(config_cls=DerivedConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, DerivedConfig)
        assert result.value == 20


class TestConfigClsWithNestedFields:
    """Test config_cls parameter with nested field overrides."""

    def test_explicit_config_cls_with_nested_overrides(self, tmp_path):
        """Test that nested field overrides work with explicit config_cls."""

        class ModelConfig(BaseModel):
            size: int = 100

        class TrainConfig(BaseModel):
            epochs: int = 100
            model: ModelConfig = Field(default_factory=ModelConfig)

        class FastTrain(TrainConfig):
            epochs: int = 10

        @provide_config(config_cls=FastTrain, config_dirs=str(tmp_path))
        def train(cfg: TrainConfig):
            return cfg

        # Test nested field overrides with explicit config_cls
        with patch.object(sys, "argv", ["test.py", "--model.size=500"]):
            result = train()

        assert isinstance(result, FastTrain)
        assert result.epochs == 10  # From FastTrain
        assert result.model.size == 500  # CLI override


class TestConfigClsInheritance:
    """Test that config_cls properly validates inheritance."""

    def test_exact_type_is_valid_subclass(self, tmp_path):
        """Test that using the exact same type as annotation is valid."""

        @provide_config(config_cls=BaseConfig, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, BaseConfig)
        assert result.value == 10

    def test_multi_level_inheritance(self, tmp_path):
        """Test that multi-level inheritance is properly validated."""

        class Level2Config(DerivedConfig):
            """Second level of inheritance."""

            level2_value: int = 40

        # Should work - Level2Config is subclass of DerivedConfig which is subclass of BaseConfig
        @provide_config(config_cls=Level2Config, config_dirs=str(tmp_path))
        def my_func(cfg: BaseConfig):
            return cfg

        with patch.object(sys, "argv", ["test.py"]):
            result = my_func()

        assert isinstance(result, Level2Config)
        assert result.value == 20  # From DerivedConfig
        assert result.extra_value == 30  # From DerivedConfig
        assert result.level2_value == 40  # From Level2Config
