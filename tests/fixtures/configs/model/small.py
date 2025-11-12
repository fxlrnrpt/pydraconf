"""Small model config for testing."""

from pydantic import Field

from tests.fixtures.configs.model.base import BaseModelConfig


class SmallModelConfig(BaseModelConfig):
    """Small model configuration."""

    size: int = Field(default=50, description="Model size")
    layers: int = Field(default=1, description="Number of layers")
