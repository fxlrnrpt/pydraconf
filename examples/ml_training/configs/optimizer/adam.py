"""Adam optimizer configuration."""

from pydantic import Field

from configs.base import OptimizerConfig


class AdamConfig(OptimizerConfig):
    """Adam optimizer configuration."""

    # Inherits lr from base
    beta1: float = Field(default=0.9, description="Beta1 parameter")
    beta2: float = Field(default=0.999, description="Beta2 parameter")
    weight_decay: float = Field(default=0.0, description="Weight decay (L2 penalty)")
