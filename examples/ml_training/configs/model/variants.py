"""Model configuration variants - demonstrating multiple classes in one file."""

from configs.base import ModelConfig  # pyrefly: ignore[missing-import]
from pydantic import Field


class TinyModel(ModelConfig):
    """Tiny model for rapid prototyping."""

    hidden_dim: int = Field(default=128, description="Hidden dimension size")
    num_layers: int = Field(default=2, description="Number of layers")


class SmallModel(ModelConfig):
    """Small model for development and testing."""

    hidden_dim: int = Field(default=256, description="Hidden dimension size")
    num_layers: int = Field(default=6, description="Number of layers")


class ResNet50Config(ModelConfig):
    """ResNet50 model configuration."""

    hidden_dim: int = Field(default=2048, description="Hidden dimension size")
    num_layers: int = Field(default=50, description="Number of layers")
    pretrained: bool = Field(default=True, description="Use pretrained weights")
    num_classes: int = Field(default=1000, description="Number of output classes")


class ViTConfig(ModelConfig):
    """Vision Transformer configuration."""

    hidden_dim: int = Field(default=768, description="Hidden dimension size")
    num_heads: int = Field(default=12, description="Number of attention heads")
    num_layers: int = Field(default=12, description="Number of transformer layers")
    patch_size: int = Field(default=16, description="Patch size for image splitting")
    num_classes: int = Field(default=1000, description="Number of output classes")
