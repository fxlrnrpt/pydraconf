"""User-specific EfficientNet configuration."""

from pydantic import BaseModel, Field


class EfficientNetConfig(BaseModel):
    """EfficientNet model configuration - user's custom config."""

    name: str = "EfficientNet-B0"
    num_classes: int = 1000
    width_coefficient: float = Field(default=1.0, description="Width scaling")
    depth_coefficient: float = Field(default=1.0, description="Depth scaling")
    dropout_rate: float = Field(default=0.2, description="Dropout rate")
