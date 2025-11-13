"""SGD optimizer configuration."""

from configs.base import OptimizerConfig  # pyrefly: ignore[missing-import]
from pydantic import Field


class SGDConfig(OptimizerConfig):
    """SGD optimizer configuration."""

    lr: float = Field(default=0.01, description="Learning rate")  # Override base
    momentum: float = Field(default=0.9, description="Momentum factor")
    weight_decay: float = Field(default=0.0001, description="Weight decay (L2 penalty)")
