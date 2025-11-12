# Base model config type (for group identification)
from pydantic import BaseModel, Field


class BaseModelConfig(BaseModel):
    """Base model configuration type."""

    size: int = Field(default=100, description="Model size")
    layers: int = Field(default=2, description="Number of layers")
