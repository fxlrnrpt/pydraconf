# Multiple Classes Per File Example

This example demonstrates that you can define **multiple configuration classes in a single file**, and each will be registered separately by its class name.

## File Structure

```
multi_class_file/
├── configs/
│   ├── base.py           # Main config with variants
│   └── model/
│       └── variants.py   # Multiple model configs in ONE file
└── train.py
```

## Key Feature: Multiple Classes in One File

Instead of creating separate files for each model size:

```
❌ Old approach (one class per file):
model/
├── tiny.py      → TinyModel
├── small.py     → SmallModel
├── medium.py    → MediumModel
└── large.py     → LargeModel
```

You can now group related configs together:

```
✅ New approach (multiple classes per file):
model/
└── variants.py  → TinyModel, SmallModel, MediumModel, LargeModel
```

## How It Works

**[configs/model/variants.py](configs/model/variants.py)** defines four model classes:

```python
class TinyModel(BaseModel):
    hidden_dim: int = 128
    layers: int = 2
    dropout: float = 0.1

class SmallModel(BaseModel):
    hidden_dim: int = 256
    layers: int = 4
    dropout: float = 0.1

class MediumModel(BaseModel):
    hidden_dim: int = 512
    layers: int = 8
    dropout: float = 0.2

class LargeModel(BaseModel):
    hidden_dim: int = 1024
    layers: int = 16
    dropout: float = 0.3
```

The registry discovers **all BaseModel classes** in each file and registers them by their class name.

## Usage

### Default (MediumModel)
```bash
python train.py
```

### Switch to any model using class name
```bash
# Tiny model for rapid prototyping
python train.py model=TinyModel

# Small model for development
python train.py model=SmallModel

# Medium model (default)
python train.py model=MediumModel

# Large model for production
python train.py model=LargeModel
```

### Combine with variants
```bash
# Quick test with tiny model
python train.py --config=QuickTest model=TinyModel

# Full training with large model
python train.py --config=FullTraining model=LargeModel
```

### Override model parameters
```bash
# Use small model but customize its parameters
python train.py model=SmallModel --model.hidden_dim=384 --model.layers=6
```

## Available Configs

### Model Sizes (model=X)
All defined in `configs/model/variants.py`:
- `TinyModel`: 128 hidden_dim, 2 layers (rapid prototyping)
- `SmallModel`: 256 hidden_dim, 4 layers (development)
- `MediumModel`: 512 hidden_dim, 8 layers (production baseline)
- `LargeModel`: 1024 hidden_dim, 16 layers (maximum performance)

### Training Variants (--config=X)
Defined in `configs/base.py`:
- `QuickTest`: 5 epochs, batch_size=8
- `FullTraining`: 200 epochs, batch_size=128

## Benefits

1. **Better Organization**: Group related configs together
2. **Less Boilerplate**: No need for separate files for simple variants
3. **Easier Maintenance**: Related configs are co-located
4. **Flexibility**: Still reference by class name for clarity

## When to Use Multiple Classes Per File

✅ **Good use cases:**
- Size variants (Tiny/Small/Medium/Large)
- Preset combinations (Fast/Balanced/Accurate)
- Environment configs (Dev/Staging/Prod)
- Related variations of the same concept

❌ **When to use separate files:**
- Completely different architectures (ResNet vs ViT)
- Configs with different purposes (Model vs Optimizer)
- Large, complex configs with many fields
- Configs that need separate documentation
