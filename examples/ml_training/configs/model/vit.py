"""Vision Transformer (ViT) model configuration."""

from pydantic import BaseModel, Field


class ViTConfig(BaseModel):
    """Vision Transformer configuration."""

    hidden_dim: int = Field(default=768, description="Hidden dimension size")
    num_heads: int = Field(default=12, description="Number of attention heads")
    num_layers: int = Field(default=12, description="Number of transformer layers")
    patch_size: int = Field(default=16, description="Patch size for image splitting")
    num_classes: int = Field(default=1000, description="Number of output classes")
