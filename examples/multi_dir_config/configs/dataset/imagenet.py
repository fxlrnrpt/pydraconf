"""ImageNet dataset configuration."""

from pydantic import BaseModel, Field


class ImageNetConfig(BaseModel):
    """ImageNet dataset configuration."""

    name: str = "ImageNet"
    batch_size: int = 256
    num_workers: int = Field(default=8, description="Number of data loading workers")
    train_split: str = Field(default="train", description="Training split")
    val_split: str = Field(default="val", description="Validation split")
