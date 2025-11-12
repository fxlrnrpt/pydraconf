# ML Training Example

This example demonstrates all three override mechanisms in PydraConf:

1. **Subclassing** - Named variants (QuickTest, FullTraining)
2. **Config Groups** - Component swapping using class names (model=ViTConfig, optimizer=AdamConfig)
3. **CLI Overrides** - Runtime tweaks (--epochs, --batch_size)

This example uses `.pydraconfrc` to specify the config directory, so the decorator doesn't need a `config_dir` argument.

## Usage

### Basic training with config groups
```bash
# ResNet50 with Adam optimizer
python train.py model=ResNet50Config optimizer=AdamConfig

# ViT with SGD optimizer
python train.py model=ViTConfig optimizer=SGDConfig
```

### Using variants (subclassing)
```bash
# Quick test run (5 epochs, batch_size=8)
python train.py --config=QuickTest model=ViTConfig optimizer=AdamConfig

# Full training (200 epochs, batch_size=64)
python train.py --config=FullTraining model=ResNet50Config optimizer=SGDConfig
```

### CLI overrides
```bash
# Override specific fields
python train.py model=ViTConfig optimizer=AdamConfig --epochs=50 --batch_size=128 --seed=123
```

### Combining all three
```bash
# Variant + Groups + Field overrides
python train.py --config=QuickTest model=ViTConfig optimizer=AdamConfig --epochs=10 --batch_size=16

# This demonstrates the override priority:
# 1. Start with QuickTest variant (epochs=5, batch_size=8)
# 2. Swap model to ViT and optimizer to Adam (config groups)
# 3. Override epochs=10 and batch_size=16 (CLI overrides)
```

## Available Configs

### Models (model=X)
- `ResNet50Config`: ResNet50 model
- `ViTConfig`: Vision Transformer

### Optimizers (optimizer=X)
- `AdamConfig`: Adam optimizer
- `SGDConfig`: SGD optimizer with momentum

### Variants (--config=X)
- `QuickTest`: 5 epochs, batch_size=8
- `FullTraining`: 200 epochs, batch_size=64

Run with `--help` to see all available options:
```bash
python train.py --help

# See available config groups
python train.py --help-groups
```

## Override Priority

When combining all three mechanisms, the priority is (from lowest to highest):
1. Base config defaults
2. Variant/subclass defaults
3. Config group selections (replaces entire sub-configs)
4. CLI field overrides

Example:
```bash
python train.py --config=QuickTest model=ViTConfig optimizer=AdamConfig --epochs=10
```
Results in:
- epochs=10 (CLI override)
- batch_size=8 (from QuickTest variant)
- model=ViT (config group selection)
- optimizer=Adam (config group selection)
