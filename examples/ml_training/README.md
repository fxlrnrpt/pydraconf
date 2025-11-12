# ML Training - Comprehensive Example

This example demonstrates **all major PydraConf features** in a realistic ML training scenario. Think of it as a guided tour from simple to advanced usage.

## What You'll Learn

1. **Variants** - Named configurations (QuickTest, FullTraining)
2. **Groups** - Component swapping (model=X, optimizer=X)
3. **CLI Overrides** - Runtime field tweaks (--epochs, --batch_size)
4. **Multiple Entry Points** - Using `config_cls` for fixed defaults
5. **Multi-Class Files** - Organizing related configs in one file
6. **Metadata Tracking** - Config export and override logging

## Progressive Tutorial

### Level 1: Start Simple - Use Base Config

```bash
python train.py train
# Uses default TrainConfig: epochs=100, batch_size=32
# Default model: ModelConfig (base), optimizer: OptimizerConfig (base)
```

### Level 2: Use Variants for Named Configs

```bash
# Quick testing with fewer epochs
python train.py train --config=QuickTest
# Uses: epochs=5, batch_size=8

# Full production training
python train.py train --config=FullTraining
# Uses: epochs=200, batch_size=64
```

**What happened?** `QuickTest` and `FullTraining` are subclasses of `TrainConfig` that override default values. Perfect for common scenarios.

### Level 3: Swap Components with Groups

```bash
# Train with Vision Transformer + Adam
python train.py train model=ViTConfig optimizer=AdamConfig

# Train with ResNet50 + SGD
python train.py train model=ResNet50Config optimizer=SGDConfig

# Try tiny model for quick experiments
python train.py train model=TinyModel
```

**What happened?** Groups let you swap entire sub-configs (models, optimizers) by class name. PydraConf discovers these by looking at nested field types.

**💡 Bonus:** Check out [configs/model/variants.py](configs/model/variants.py) - it defines **4 model classes in one file** (TinyModel, SmallModel, ResNet50Config, ViTConfig). This is cleaner than separate files when configs are related.

### Level 4: Combine Variants + Groups

```bash
# Quick test with Vision Transformer
python train.py train --config=QuickTest model=ViTConfig optimizer=AdamConfig
# Result: 5 epochs, batch_size=8, ViT model, Adam optimizer

# Production training with ResNet50
python train.py train --config=FullTraining model=ResNet50Config optimizer=SGDConfig
# Result: 200 epochs, batch_size=64, ResNet50, SGD optimizer
```

**What happened?** Variants set baseline values, then groups swap components. This is powerful for experimentation!

### Level 5: Fine-Tune with CLI Overrides

```bash
# Override specific fields
python train.py train --config=QuickTest model=ViTConfig --epochs=10 --batch_size=16

# Override nested fields
python train.py train model=ViTConfig --model.num_heads=8 --optimizer.lr=0.0001
```

**What happened?** CLI overrides have the highest priority. Perfect for quick tweaks without changing code.

### Level 6: Use Entry Points for Convenience

Instead of always typing `--config=QuickTest`, use dedicated entry points:

```bash
# Development mode (always uses QuickTest)
python train.py train-dev
# Equivalent to: python train.py train --config=QuickTest

# Production mode (always uses FullTraining)
python train.py train-prod
# Equivalent to: python train.py train --config=FullTraining

# Entry points still support all other features!
python train.py train-dev model=TinyModel --epochs=3
python train.py train-prod model=ResNet50Config optimizer=AdamConfig --batch_size=128
```

**What happened?** The `config_cls` parameter in `@with_config()` sets a fixed default variant. Great for:
- CI/CD pipelines (ensure prod always uses prod config)
- Team workflows (devs use dev mode, ops use prod mode)
- Reproducibility (fixed baseline with optional tweaks)

## File Structure

```
ml_training/
├── configs/
│   ├── base.py              # TrainConfig + QuickTest/FullTraining variants
│   ├── model/
│   │   └── variants.py      # TinyModel, SmallModel, ResNet50Config, ViTConfig
│   └── optimizer/
│       ├── adam.py          # AdamConfig
│       └── sgd.py           # SGDConfig
├── train.py                 # Entry points: train, train-dev, train-prod
└── README.md                # This file
```

**Key insight:** [model/variants.py](configs/model/variants.py) demonstrates that you can define **multiple config classes in one file**. This is great for:
- Related size variants (Tiny/Small/Large)
- Preset combinations (Fast/Balanced/Accurate)
- Keeping related configs together

## Available Configurations

### Models (model=X)
All in [configs/model/variants.py](configs/model/variants.py):
- `TinyModel`: 128 hidden_dim, 2 layers (rapid prototyping)
- `SmallModel`: 256 hidden_dim, 6 layers (development)
- `ResNet50Config`: 2048 hidden_dim, 50 layers, pretrained (production)
- `ViTConfig`: 768 hidden_dim, 12 layers, 12 heads (transformers)

### Optimizers (optimizer=X)
- `AdamConfig`: Adam optimizer (lr=0.001, beta1=0.9, beta2=0.999)
- `SGDConfig`: SGD with momentum (lr=0.01, momentum=0.9)

### Variants (--config=X)
In [configs/base.py](configs/base.py):
- `QuickTest`: 5 epochs, batch_size=8 (fast iteration)
- `FullTraining`: 200 epochs, batch_size=64 (production runs)

### Entry Points
- `train`: Flexible, supports all variants and options
- `train-dev`: Always uses QuickTest (convenience)
- `train-prod`: Always uses FullTraining (safety)

## Override Priority

When you combine all mechanisms, priority is (lowest to highest):

1. **Base config defaults** - From TrainConfig/ModelConfig/OptimizerConfig
2. **Variant defaults** - From QuickTest/FullTraining (if using --config or entry point)
3. **Group selections** - From model=X, optimizer=X (replaces entire sub-config)
4. **CLI overrides** - From --epochs, --batch_size, etc. (highest priority)

Example:
```bash
python train.py train-dev model=ViTConfig --epochs=10 --model.num_heads=8
```

Results in:
- `epochs=10` (CLI override)
- `batch_size=8` (from QuickTest via train-dev)
- `model=ViTConfig` with `num_heads=8` (group + CLI override)
- Everything else from base defaults

## Help Commands

```bash
# See all CLI options
python train.py train --help

# See available config groups
python train.py train --help-groups
```

## Next Steps

- Try [multi_dir_config](../multi_dir_config/) to learn about team collaboration patterns with multiple config directories
- Read the [main README](../../README.md) for complete API reference
- Check [configs/model/variants.py](configs/model/variants.py) to see how multiple classes work in one file
