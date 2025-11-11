"""ML training example demonstrating PydraConf config groups."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pydraconf import config_main
from configs.base import TrainConfig


@config_main(TrainConfig, config_dir="configs")
def train(cfg: TrainConfig) -> None:
    """Run training with the given config.

    Args:
        cfg: Training configuration
    """
    print("=" * 70)
    print(f"Training Configuration: {cfg.__class__.__name__}")
    print("=" * 70)
    print(f"Epochs: {cfg.epochs}")
    print(f"Batch Size: {cfg.batch_size}")
    print(f"Random Seed: {cfg.seed}")
    print()
    print(f"Model: {cfg.model.__class__.__name__}")
    print(f"  {cfg.model}")
    print()
    print(f"Optimizer: {cfg.optimizer.__class__.__name__}")
    print(f"  {cfg.optimizer}")
    print("=" * 70)
    print()
    print("Starting training...")
    print(f"  Training {cfg.model.__class__.__name__} for {cfg.epochs} epochs")
    print(f"  Using {cfg.optimizer.__class__.__name__} optimizer")
    print()
    print("(This is a demo - no actual training happens)")


if __name__ == "__main__":
    train()
