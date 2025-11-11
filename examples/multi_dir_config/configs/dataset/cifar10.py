"""CIFAR-10 dataset configuration."""

from pydantic import BaseModel, Field


class CIFAR10Config(BaseModel):
    """CIFAR-10 dataset configuration."""

    name: str = "CIFAR-10"
    batch_size: int = 128
    num_workers: int = Field(default=4, description="Number of data loading workers")
    augmentation: bool = Field(default=True, description="Use data augmentation")
