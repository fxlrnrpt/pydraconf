"""Base training configuration."""

from pydantic import BaseModel, Field


# Import default configs - we'll use BaseModel as placeholder type
# The actual type will be determined at runtime through config groups
class ModelConfig(BaseModel):
    """Base model config placeholder."""
    pass


class OptimizerConfig(BaseModel):
    """Base optimizer config placeholder."""
    pass


class TrainConfig(BaseModel):
    """Main training configuration."""

    epochs: int = Field(default=100, description="Number of training epochs")
    batch_size: int = Field(default=32, description="Training batch size")
    model: BaseModel = Field(default_factory=ModelConfig, description="Model configuration")
    optimizer: BaseModel = Field(default_factory=OptimizerConfig, description="Optimizer configuration")
    seed: int = Field(default=42, description="Random seed")


class QuickTest(TrainConfig):
    """Quick test configuration variant."""

    epochs: int = 5
    batch_size: int = 8


class FullTraining(TrainConfig):
    """Full training configuration variant."""

    epochs: int = 200
    batch_size: int = 64
