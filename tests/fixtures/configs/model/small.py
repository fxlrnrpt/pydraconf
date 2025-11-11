"""Small model config for testing."""

from pydantic import BaseModel, Field


class SmallModelConfig(BaseModel):
    """Small model configuration."""

    size: int = Field(default=100, description="Model size")
    layers: int = Field(default=2, description="Number of layers")
