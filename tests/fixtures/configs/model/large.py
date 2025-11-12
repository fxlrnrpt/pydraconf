"""Large model config for testing."""

from pydantic import Field

from tests.fixtures.configs.model.base import BaseModelConfig


class LargeModelConfig(BaseModelConfig):
    """Large model configuration."""

    size: int = Field(default=1000, description="Model size")
    layers: int = Field(default=10, description="Number of layers")
