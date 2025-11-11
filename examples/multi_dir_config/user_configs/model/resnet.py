"""User-specific ResNet configuration - overrides shared ResNet."""

from pydantic import BaseModel, Field


class ResNetConfig(BaseModel):
    """ResNet model configuration - USER OVERRIDE with different settings."""

    name: str = "ResNet101-Custom"
    num_classes: int = 1000
    depth: int = Field(default=101, description="ResNet depth (USER: using 101 instead of 50)")
    pretrained: bool = Field(default=False, description="Use pretrained weights (USER: False)")
    custom_setting: str = Field(default="user-override", description="This field only exists in user config")
