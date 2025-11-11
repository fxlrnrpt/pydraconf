# PydraConf

Python-native hierarchical configuration management with Pydantic. Like Hydra, but YAML-haters.

## Features

Three powerful override mechanisms work together:

1. **Subclassing** - Named variants through Python inheritance (e.g., `QuickTest(BaseConfig)`)
2. **Config Groups** - Component swapping via directory structure (e.g., `model=vit`)
3. **CLI Overrides** - Runtime field tweaks (e.g., `--epochs=50`)

Benefits:
- Pure Python - no YAML, no magic strings
- Type-safe with Pydantic validation
- IDE autocomplete and refactoring support
- Simple `@config_main` decorator
- Convention-over-configuration design

## Installation

```bash
pip install pydraconf
```

## Quick Start

```python
from pydantic import BaseModel
from pydraconf import config_main

class TrainConfig(BaseModel):
    epochs: int = 100
    batch_size: int = 32

class QuickTest(TrainConfig):
    epochs: int = 5

@config_main(TrainConfig, config_dir="configs")
def train(cfg: TrainConfig):
    print(f"Training for {cfg.epochs} epochs")

if __name__ == "__main__":
    train()
```

Run with different configurations:

```bash
# Default config
python train.py

# Use QuickTest variant
python train.py --config=quick-test

# Override specific fields
python train.py --epochs=50 --batch-size=64

# Combine all three
python train.py --config=quick-test --epochs=10
```

## How It Works

### 1. Subclassing - Named Variants

Create named configuration variants by subclassing:

```python
class TrainConfig(BaseModel):
    epochs: int = 100
    batch_size: int = 32

class QuickTest(TrainConfig):
    epochs: int = 5  # Override defaults

class Production(TrainConfig):
    epochs: int = 200
    batch_size: int = 128
```

Use with `--config=variant-name`:

```bash
python train.py --config=quick-test  # Uses QuickTest
python train.py --config=production   # Uses Production
```

Variant names are automatically converted to kebab-case (QuickTest → quick-test).

### 2. Config Groups - Component Swapping

Organize configs in subdirectories to create swappable components:

```
configs/
├── base.py           # Main config
├── model/
│   ├── resnet50.py   # model=resnet50
│   └── vit.py        # model=vit
└── optimizer/
    ├── adam.py       # optimizer=adam
    └── sgd.py        # optimizer=sgd
```

```python
# base.py
class TrainConfig(BaseModel):
    epochs: int = 100
    model: ModelConfig = Field(default_factory=ResNet50Config)
    optimizer: OptimizerConfig = Field(default_factory=AdamConfig)

# model/vit.py
class ViTConfig(BaseModel):
    hidden_dim: int = 768
    num_heads: int = 12
```

Swap components at runtime:

```bash
python train.py model=vit optimizer=sgd
```

### 3. CLI Overrides - Runtime Tweaks

Override any field from the command line:

```bash
python train.py --epochs=50 --model.hidden-dim=1024
```

Field names with underscores accept kebab-case (`batch_size` → `--batch-size`).

### Override Priority

When all three mechanisms are combined, priority is (from lowest to highest):

1. Base config defaults
2. Variant/subclass defaults
3. Config group selections (replaces entire sub-configs)
4. CLI field overrides

Example:

```bash
python train.py --config=quick-test model=vit --epochs=10
```

Results in:
- `epochs=10` (CLI override, highest priority)
- `model=ViT(...)` (config group selection)
- Other fields from QuickTest variant defaults

## Examples

See the [`examples/`](examples/) directory:

- [`examples/basic/`](examples/basic/) - Simple app configuration with variants
- [`examples/ml_training/`](examples/ml_training/) - ML training with all three override types

## API Reference

### `@config_main`

Decorator to make a function config-driven.

```python
@config_main(
    config_cls: Type[BaseModel],  # Base config class
    config_dir: str = "configs"    # Directory to scan for configs
)
def my_function(cfg: ConfigClass):
    ...
```

The decorator:
1. Discovers all configs in `config_dir`
2. Parses CLI arguments
3. Builds the final config with all overrides applied
4. Calls your function with the configured instance

### `ConfigRegistry`

Low-level API for config discovery and management (optional, advanced usage).

```python
from pydraconf import ConfigRegistry

registry = ConfigRegistry()
registry.discover(Path("configs"))

# List available options
print(registry.list_variants())  # ["quick-test", "production"]
print(registry.list_groups())    # {"model": ["resnet50", "vit"], ...}

# Get specific configs
variant_cls = registry.get_variant("quick-test")
model_cls = registry.get_group("model", "vit")
```

## Development

```bash
# Clone and install
git clone https://github.com/yourusername/pydraconf.git
cd pydraconf
uv sync --dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/pydraconf --strict

# Linting
uv run ruff check src/pydraconf
```

## Comparison with Hydra

| Feature | PydraConf | Hydra |
|---------|-----------|-------|
| Language | Pure Python | YAML + Python |
| Type Safety | Full (Pydantic) | Partial (OmegaConf) |
| IDE Support | Excellent | Limited |
| Learning Curve | Gentle | Steep |
| Flexibility | Python inheritance | YAML composition |
| File Format | .py | .yaml |

PydraConf is ideal if you:
- Prefer Python over YAML
- Want full type safety and IDE support
- Need simple hierarchical configs
- Value convention over configuration

Consider Hydra if you need:
- Complex multi-run experiments
- Job launchers for clusters
- Extensive plugin ecosystem

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

## Credits

Inspired by [Hydra](https://hydra.cc/) by Facebook Research, with a focus on Python-first design and simplicity.
