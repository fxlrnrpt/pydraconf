"""Model size variants - multiple configs in a single file.

This demonstrates that you can define multiple configuration classes
in one file, and each will be registered separately by its class name.
"""

from pydantic import BaseModel, Field


class TinyModel(BaseModel):
    """Tiny model for rapid prototyping."""

    hidden_dim: int = Field(default=128, description="Hidden dimension size")
    layers: int = Field(default=2, description="Number of layers")
    dropout: float = Field(default=0.1, description="Dropout rate")


class SmallModel(BaseModel):
    """Small model for development and testing."""

    hidden_dim: int = Field(default=256, description="Hidden dimension size")
    layers: int = Field(default=4, description="Number of layers")
    dropout: float = Field(default=0.1, description="Dropout rate")


class MediumModel(BaseModel):
    """Medium model for production use."""

    hidden_dim: int = Field(default=512, description="Hidden dimension size")
    layers: int = Field(default=8, description="Number of layers")
    dropout: float = Field(default=0.2, description="Dropout rate")


class LargeModel(BaseModel):
    """Large model for maximum performance."""

    hidden_dim: int = Field(default=1024, description="Hidden dimension size")
    layers: int = Field(default=16, description="Number of layers")
    dropout: float = Field(default=0.3, description="Dropout rate")
