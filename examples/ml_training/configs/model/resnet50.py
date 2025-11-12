"""ResNet50 model configuration."""

from pydantic import Field

from configs.base import ModelConfig


class ResNet50Config(ModelConfig):
    """ResNet50 model configuration."""

    hidden_dim: int = Field(default=2048, description="Hidden dimension size")  # Override base
    num_layers: int = Field(default=50, description="Number of layers")  # Override base
    pretrained: bool = Field(default=True, description="Use pretrained weights")
    num_classes: int = Field(default=1000, description="Number of output classes")
