"""SGD optimizer configuration."""

from pydantic import BaseModel, Field


class SGDConfig(BaseModel):
    """SGD optimizer configuration."""

    lr: float = Field(default=0.01, description="Learning rate")
    momentum: float = Field(default=0.9, description="Momentum factor")
    weight_decay: float = Field(default=0.0001, description="Weight decay (L2 penalty)")
