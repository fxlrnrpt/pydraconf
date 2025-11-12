"""PydraConf - Pure Python Hierarchical Configuration.

A lightweight library for hierarchical configuration management using pure Python + Pydantic.
Supports three override mechanisms:
1. Subclassing - Named variants (e.g., QuickTest(PydraConfig))
2. Config Groups - Component swapping (e.g., model=vit)
3. CLI Overrides - Runtime tweaks (e.g., --epochs=50)

Example:
    from pydraconf import PydraConfig, with_config

    class TrainConfig(PydraConfig):
        epochs: int = 100

    class QuickTest(TrainConfig):
        epochs: int = 5

    @with_config(config_dirs="configs")
    def train(cfg: TrainConfig):
        print(f"Training for {cfg.epochs} epochs")
"""

from .base_config import PydraConfig
from .decorators import with_config
from .logger import configure_logging
from .registry import ConfigRegistry

__version__ = "0.1.0"

__all__ = [
    "PydraConfig",
    "with_config",
    "ConfigRegistry",
    "configure_logging",
]
