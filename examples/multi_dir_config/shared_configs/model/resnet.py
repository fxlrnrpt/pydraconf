"""Shared ResNet configuration."""

from pydantic import BaseModel, Field


class ResNetConfig(BaseModel):
    """ResNet model configuration - shared with team."""

    name: str = "ResNet50"
    num_classes: int = 1000
    depth: int = Field(default=50, description="ResNet depth (18, 34, 50, 101, 152)")
    pretrained: bool = Field(default=True, description="Use pretrained weights")
