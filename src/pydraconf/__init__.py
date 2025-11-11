"""PydraConf - Pure Python Hierarchical Configuration.

A lightweight library for hierarchical configuration management using pure Python + Pydantic.
Supports three override mechanisms:
1. Subclassing - Named variants (e.g., QuickTest(BaseConfig))
2. Config Groups - Component swapping (e.g., model=vit)
3. CLI Overrides - Runtime tweaks (e.g., --epochs=50)

Example:
    from pydantic import BaseModel
    from pydraconf import config_main

    class TrainConfig(BaseModel):
        epochs: int = 100

    class QuickTest(TrainConfig):
        epochs: int = 5

    @config_main(TrainConfig, config_dir="configs")
    def train(cfg: TrainConfig):
        print(f"Training for {cfg.epochs} epochs")

    # CLI: python train.py --config=quick-test --epochs=10
"""

from .decorators import config_main
from .registry import ConfigRegistry

__version__ = "0.1.0"

__all__ = [
    "config_main",
    "ConfigRegistry",
]
