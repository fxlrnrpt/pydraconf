"""ML training example - comprehensive demonstration of PydraConf features.

This example demonstrates:
1. Variants - Named configurations (QuickTest, FullTraining)
2. Groups - Component swapping (model=X, optimizer=X)
3. CLI Overrides - Runtime tweaks (--epochs, --batch_size)
4. Multiple entry points - Using config_cls parameter
5. Multi-class files - Multiple configs in one file (model/variants.py)
6. Metadata tracking - log_summary() and export_config()

Usage:
    # Standard usage with flexibility
    python train.py train                           # Uses base config
    python train.py train --config=QuickTest        # Select variant
    python train.py train model=ViTConfig           # Swap components
    python train.py train --config=QuickTest model=TinyModel --epochs=3

    # Entry points with fixed defaults (great for workflows)
    python train.py train-dev                       # Always QuickTest
    python train.py train-prod                      # Always FullTraining
    python train.py train-dev --epochs=10           # Can still override
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from configs.base import FullTraining, QuickTest, TrainConfig

from pydraconf import with_config


def run_training(cfg: TrainConfig) -> None:
    """Core training logic (shared by all entry points).

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

    # Display metadata about applied overrides
    overrides = cfg.get_overrides_summary()
    if overrides:
        print("Applied Overrides:")
        for override in overrides:
            print(f"  - {override}")
        print()

    print("Starting training...")
    print(f"  Training {cfg.model.__class__.__name__} for {cfg.epochs} epochs")
    print(f"  Using {cfg.optimizer.__class__.__name__} optimizer")
    print()
    print("(This is a demo - no actual training happens)")

    # Optionally export config with metadata
    # cfg.export_config("training_config.json")


@with_config()  # config_dirs read from .pydraconfrc
def train(cfg: TrainConfig) -> None:
    """Standard training entry point - flexible configuration.

    Supports all variants via --config flag and component swapping.
    Use this for maximum flexibility in experimentation.

    Args:
        cfg: Training configuration
    """
    run_training(cfg)


@with_config(config_cls=QuickTest)
def train_dev(cfg: TrainConfig) -> None:
    """Development entry point - always uses QuickTest config.

    Perfect for rapid iteration during development.
    Still supports CLI overrides for fine-tuning.

    Args:
        cfg: Training configuration (QuickTest by default)
    """
    print("\n🔧 DEVELOPMENT MODE - Using QuickTest defaults")
    run_training(cfg)


@with_config(config_cls=FullTraining)
def train_prod(cfg: TrainConfig) -> None:
    """Production entry point - always uses FullTraining config.

    Ensures production runs use production settings by default.
    CLI overrides still work for emergency adjustments.

    Args:
        cfg: Training configuration (FullTraining by default)
    """
    print("\n🚀 PRODUCTION MODE - Using FullTraining defaults")
    run_training(cfg)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python train.py train [--config=VARIANT] [OPTIONS]")
        print("  python train.py train-dev [OPTIONS]")
        print("  python train.py train-prod [OPTIONS]")
        print("\nExamples:")
        print("  python train.py train")
        print("  python train.py train --config=QuickTest")
        print("  python train.py train model=ViTConfig optimizer=AdamConfig")
        print("  python train.py train --config=QuickTest model=TinyModel --epochs=3")
        print("  python train.py train-dev")
        print("  python train.py train-dev model=SmallModel --epochs=10")
        print("  python train.py train-prod model=ResNet50Config optimizer=AdamConfig")
        print("\nFor more help:")
        print("  python train.py train --help")
        sys.exit(1)

    # Remove the command from argv before calling the function
    command = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]

    if command == "train":
        train()
    elif command == "train-dev":
        train_dev()
    elif command == "train-prod":
        train_prod()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: train, train-dev, train-prod")
        sys.exit(1)
