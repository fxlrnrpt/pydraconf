"""ResNet50 model configuration."""

from pydantic import BaseModel, Field


class ResNet50Config(BaseModel):
    """ResNet50 model configuration."""

    layers: int = Field(default=50, description="Number of layers")
    pretrained: bool = Field(default=True, description="Use pretrained weights")
    num_classes: int = Field(default=1000, description="Number of output classes")
