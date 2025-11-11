"""Training script demonstrating multiple config directories."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from shared_configs.base import TrainConfig

from pydraconf import provide_config


@provide_config(TrainConfig)  # config_dirs read from .pydraconfrc
def train(cfg: TrainConfig) -> None:
    """Run training with the given config.

    This example demonstrates config directory priority:
    1. configs/ (local, highest priority)
    2. user_configs/ (user-specific)
    3. shared_configs/ (team-wide, lowest priority)

    Args:
        cfg: Training configuration
    """
    print("=" * 80)
    print(f"Training Configuration: {cfg.__class__.__name__}")
    print("=" * 80)
    print()
    print("Training Settings:")
    print(f"  Epochs: {cfg.epochs}")
    print(f"  Learning Rate: {cfg.learning_rate}")
    print()
    print("Model Configuration:")
    print(f"  Model: {cfg.model.name} ({cfg.model.__class__.__name__})")
    print(f"  Num Classes: {cfg.model.num_classes}")
    if hasattr(cfg.model, "depth"):
        print(f"  Depth: {cfg.model.depth}")
        print(f"  Pretrained: {cfg.model.pretrained}")
    elif hasattr(cfg.model, "patch_size"):
        print(f"  Patch Size: {cfg.model.patch_size}")
        print(f"  Hidden Dim: {cfg.model.hidden_dim}")
        print(f"  Num Heads: {cfg.model.num_heads}")
    elif hasattr(cfg.model, "width_coefficient"):
        print(f"  Width Coefficient: {cfg.model.width_coefficient}")
        print(f"  Depth Coefficient: {cfg.model.depth_coefficient}")
        print(f"  Dropout Rate: {cfg.model.dropout_rate}")
    print()
    print("Dataset Configuration:")
    print(f"  Dataset: {cfg.dataset.name} ({cfg.dataset.__class__.__name__})")
    print(f"  Batch Size: {cfg.dataset.batch_size}")
    if hasattr(cfg.dataset, "num_workers"):
        print(f"  Num Workers: {cfg.dataset.num_workers}")
    print()
    print("Config Source Explanation:")
    print("  - Base config loaded from: shared_configs/base.py")
    print(f"  - Model config loaded from: {_get_config_source(cfg.model.__class__.__name__)}")
    print(f"  - Dataset config loaded from: {_get_config_source(cfg.dataset.__class__.__name__)}")
    print()
    print("Starting training...")
    print("(This is a demo - no actual training happens)")


def _get_config_source(class_name: str) -> str:
    """Helper to explain where config was loaded from."""
    mapping = {
        "ResNetConfig": "shared_configs/model/resnet.py (shared)",
        "EfficientNetConfig": "user_configs/model/efficient_net.py (user-specific)",
        "ViTConfig": "configs/model/vit.py (local)",
        "ImageNetConfig": "configs/dataset/imagenet.py (local)",
        "CIFAR10Config": "configs/dataset/cifar10.py (local)",
        "ModelConfig": "shared_configs/base.py (default)",
        "DatasetConfig": "shared_configs/base.py (default)",
    }
    return mapping.get(class_name, "unknown")


if __name__ == "__main__":
    train()
