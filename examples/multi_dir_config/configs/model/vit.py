"""Local Vision Transformer configuration."""

from pydantic import BaseModel, Field


class ViTConfig(BaseModel):
    """Vision Transformer model configuration - local to this project."""

    name: str = "ViT-Base"
    num_classes: int = 1000
    patch_size: int = Field(default=16, description="Patch size")
    hidden_dim: int = Field(default=768, description="Hidden dimension")
    num_heads: int = Field(default=12, description="Number of attention heads")
    num_layers: int = Field(default=12, description="Number of transformer layers")
