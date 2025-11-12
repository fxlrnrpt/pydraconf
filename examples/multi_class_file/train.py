#!/usr/bin/env python3
"""Example demonstrating multiple config classes in a single file.

This example shows how you can define multiple configuration classes
in one file (configs/model/variants.py) and use any of them via CLI.
"""

from configs.base import TrainConfig
from pydraconf import provide_config


@provide_config(TrainConfig, config_dirs="configs")
def train(cfg: TrainConfig):
    """Train a model with the given configuration."""
    print("=" * 60)
    print("Training Configuration")
    print("=" * 60)
    print(f"Epochs:        {cfg.epochs}")
    print(f"Batch Size:    {cfg.batch_size}")
    print(f"Learning Rate: {cfg.learning_rate}")
    print()
    print("Model Configuration")
    print("-" * 60)
    print(f"Type:          {cfg.model.__class__.__name__}")
    print(f"Hidden Dim:    {cfg.model.hidden_dim}")
    print(f"Layers:        {cfg.model.layers}")
    print(f"Dropout:       {cfg.model.dropout}")
    print("=" * 60)


if __name__ == "__main__":
    train()
