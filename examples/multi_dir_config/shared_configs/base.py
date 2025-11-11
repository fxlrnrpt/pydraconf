"""Shared base configuration used across the team."""

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model configuration."""

    name: str = "base"
    num_classes: int = Field(default=1000, description="Number of output classes")


class DatasetConfig(BaseModel):
    """Dataset configuration."""

    name: str = "base"
    batch_size: int = Field(default=32, description="Batch size")


class TrainConfig(BaseModel):
    """Shared training configuration."""

    epochs: int = Field(default=100, description="Number of epochs")
    learning_rate: float = Field(default=0.001, description="Learning rate")
    model: ModelConfig = Field(default_factory=ModelConfig, description="Model config")
    dataset: DatasetConfig = Field(default_factory=DatasetConfig, description="Dataset config")


class QuickTest(TrainConfig):
    """Quick test variant - shared across team."""

    epochs: int = 5
    learning_rate: float = 0.01
