"""Large model config for testing."""

from pydantic import BaseModel, Field


class LargeModelConfig(BaseModel):
    """Large model configuration."""

    size: int = Field(default=1000, description="Model size")
    layers: int = Field(default=10, description="Number of layers")
