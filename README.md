# PydraConf

Python-native hierarchical configuration management with Pydantic. Like Hydra, but for YAML-haters.

## Features

Three powerful override mechanisms work together:

1. **Variants** - Named configurations through inheritance (e.g., `QuickTest(TrainConfig)`)
2. **Groups** - Component swapping via type inheritance (e.g., `model=ViTConfig`)
3. **CLI Overrides** - Runtime field tweaks (e.g., `--epochs=50`)

Benefits:
- Pure Python - no YAML, no magic strings
- Type-safe with Pydantic validation
- IDE autocomplete and refactoring support
- Simple `@provide_config` decorator
- Type-driven architecture - groups are defined by class inheritance, not directory structure

## Installation

```bash
pip install pydraconf
```

## Quick Start

Create a simple config and use the decorator:

```python
from pydantic import BaseModel
from pydraconf import provide_config

class TrainConfig(BaseModel):
    epochs: int = 100
    batch_size: int = 32

class QuickTest(TrainConfig):
    epochs: int = 5

@provide_config()
def train(cfg: TrainConfig):
    print(f"Training for {cfg.epochs} epochs")

if __name__ == "__main__":
    train()
```

The decorator automatically infers the config class from the function's type annotation.

Run with different configurations:

```bash
# Default config
python train.py

# Use QuickTest variant
python train.py --config=QuickTest

# Override specific fields
python train.py --epochs=50 --batch_size=64

# Combine all three
python train.py --config=QuickTest --epochs=10
```

## How It Works

### 1. Variants - Named Configurations

Create named configuration variants by **subclassing your main config**:

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

Use with `--config=ClassName`:

```bash
python train.py --config=QuickTest   # Uses QuickTest
python train.py --config=Production  # Uses Production
```

**How it works:** PydraConf discovers all direct subclasses of your main config class (the one used in your `train` function) and registers them as variants.

### 2. Groups - Component Swapping

Create swappable components by **defining base types for nested fields**:

```python
# base.py
class ModelConfig(BaseModel):
    """Base type for model configs with sane defaults."""
    hidden_dim: int = 512
    num_layers: int = 6

class OptimizerConfig(BaseModel):
    """Base type for optimizer configs with sane defaults."""
    lr: float = 0.001

class TrainConfig(BaseModel):
    epochs: int = 100
    model: ModelConfig = Field(default_factory=ModelConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)

# model/vit.py
class ViTConfig(ModelConfig):
    hidden_dim: int = 768  # Override base
    num_heads: int = 12
    num_layers: int = 12  # Override base

# model/resnet50.py
class ResNet50Config(ModelConfig):
    hidden_dim: int = 2048  # Override base
    num_layers: int = 50  # Override base
    pretrained: bool = True

# optimizer/adam.py
class AdamConfig(OptimizerConfig):
    # Inherits lr=0.001 from base
    beta1: float = 0.9
    beta2: float = 0.999
```

Swap components at runtime using class names:

```bash
python train.py model=ViTConfig optimizer=AdamConfig
```

**How it works:** PydraConf identifies groups by examining the types of nested fields in your main config. Any class that inherits from a nested field's type becomes part of that field's group. The field name becomes the group name.

**Complete Example:**

```python
# configs/base.py
from pydantic import BaseModel, Field

# Define base types for groups with sane defaults
class ModelConfig(BaseModel):
    hidden_dim: int = 512
    num_layers: int = 6

class OptimizerConfig(BaseModel):
    lr: float = 0.001

# Main config
class TrainConfig(BaseModel):
    epochs: int = 100
    model: ModelConfig = Field(default_factory=ModelConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)

# Variants (subclass main config)
class QuickTest(TrainConfig):
    epochs: int = 5

# configs/model/vit.py
class ViTConfig(ModelConfig):  # Inherits from ModelConfig -> goes in "model" group
    hidden_dim: int = 768  # Override base
    num_heads: int = 12
    num_layers: int = 12  # Override base

# configs/optimizer/adam.py
class AdamConfig(OptimizerConfig):  # Inherits from OptimizerConfig -> goes in "optimizer" group
    # Inherits lr=0.001 from base
    beta1: float = 0.9
```

Now you can swap components by type:

```bash
python train.py model=ViTConfig optimizer=AdamConfig
```

### 3. CLI Overrides - Runtime Tweaks

Override any field from the command line:

```bash
python train.py --epochs=50 --model.hidden_dim=1024
```

Use exact field names including underscores (e.g., `batch_size` → `--batch_size`).

### Override Priority

When all three mechanisms are combined, priority is (from lowest to highest):

1. Base config defaults
2. Variant/subclass defaults
3. Config group selections (replaces entire sub-configs)
4. CLI field overrides

Example:

```bash
python train.py --config=quick-test model=ViTConfig --epochs=10
```

Results in:
- `epochs=10` (CLI override, highest priority)
- `model=ViTConfig(...)` (config group selection)
- Other fields from QuickTest variant defaults

## Configuration Directory

By default, PydraConf looks for configs in multiple locations with priority. You have three options to customize this:

### Option 1: Use the default

Just create a `configs/` directory in one of the default locations. No configuration needed:

```
my_project/
├── train.py
└── configs/
    ├── base.py
    └── model/
        ├── resnet.py
        └── vit.py
```

```python
@provide_config()  # Searches default locations
def train(cfg: TrainConfig):
    ...
```

By default, PydraConf searches in this order:
1. `$ROOT/configs` - Project root (directory with `pyproject.toml` or `.pydraconfrc`)
2. `$CWD/configs` - Current working directory
3. `configs` - Relative to the script directory

**Config discovery and shadowing**: PydraConf discovers configs from ALL existing directories. Configs in later directories (rightmost) override configs with the same name from earlier directories. For example, if both `$ROOT/configs` and`$CWD/configs`  have a `model/resnet.py`, the one from `$CWD/configs` (rightmost) wins.

### Option 2: Config files (recommended for projects)

Create a `.pydraconfrc` (JSON) or add to `pyproject.toml`:

**.pydraconfrc:**
```json
{
  "config_dirs": ["$ROOT/shared_configs", "$CWD/configs"]
}
```

**pyproject.toml:**
```toml
[tool.pydraconf]
config_dirs = ["$ROOT/shared_configs", "$CWD/configs"]
```

Then use the decorator without arguments:

```python
@provide_config()  # Reads from config file
def train(cfg: TrainConfig):
    ...
```

Config files are searched in current and parent directories, making this great for monorepos.

**Variable substitution:**
- `$CWD` - Current working directory
- `$ROOT` - Project root (directory with `pyproject.toml` or `.pydraconfrc`)

**Path resolution:**
- Relative paths (without variables) are resolved relative to the script directory
- Example: `"configs"` resolves to `{script_dir}/configs`

### Option 3: Explicit argument

Pass `config_dirs` directly to the decorator (single or multiple directories):

```python
# Single directory (relative to script)
@provide_config(config_dirs="my_configs")
def train(cfg: TrainConfig):
    ...

# Multiple directories with priority
@provide_config(config_dirs=["$ROOT/shared_configs", "$CWD/configs"])
def train(cfg: TrainConfig):
    ...
```

**Resolution priority:**
1. Explicit `config_dirs` argument (if provided)
2. `.pydraconfrc` in current/parent directories
3. `[tool.pydraconf]` in `pyproject.toml`
4. Default to `["$ROOT/configs", "$CWD/configs", "configs"]`

## Examples

See the [`examples/`](examples/) directory:

- [`examples/basic/`](examples/basic/) - Simple app configuration with variants
- [`examples/ml_training/`](examples/ml_training/) - ML training with all three override types

## API Reference

### `@provide_config`

Decorator to make a function config-driven. The config class is automatically inferred from the function's first parameter type annotation.

```python
@provide_config(
    config_dirs: str | list[str] | None = None   # Directory or directories to scan
)
def my_function(cfg: ConfigClass):
    ...
```

**Arguments:**

- `config_dirs`: Directory or list of directories containing config files. If `None`, searches for:
  1. `.pydraconfrc` (JSON) in current/parent directories
  2. `[tool.pydraconf]` section in `pyproject.toml`
  3. Defaults to `["$ROOT/configs", "$CWD/configs", "configs"]` if not found

  When multiple directories are provided, configs are discovered from ALL existing directories.
  Configs in later directories (rightmost) override configs with the same name from earlier directories.

  Supports variable substitution:
  - `$CWD` - Current working directory
  - `$ROOT` - Project root (directory with `pyproject.toml` or `.pydraconfrc`)

  Relative paths (without variables) are resolved relative to the script directory.

**The decorator:**
1. Resolves `config_dirs` from config files or arguments
2. Substitutes variables and resolves paths
3. Discovers all configs in the first existing directory
4. Parses CLI arguments
5. Builds the final config with all overrides applied
6. Calls your function with the configured instance

**Config File Format:**

`.pydraconfrc` (JSON):
```json
{
  "config_dirs": ["$ROOT/shared_configs", "$CWD/configs", "configs"]
}
```

`pyproject.toml`:
```toml
[tool.pydraconf]
config_dirs = ["$ROOT/shared_configs", "$CWD/configs", "configs"]
```

### `ConfigRegistry`

Low-level API for config discovery and management (optional, advanced usage).

```python
from pydraconf import ConfigRegistry

registry = ConfigRegistry()
registry.discover(Path("configs"), TrainConfig)  # Pass main config class

# List available options
print(registry.list_variants())  # ["QuickTest", "Production"]
print(registry.list_groups())    # {"model": ["ResNet50Config", "ViTConfig"], ...}

# Get specific configs
variant_cls = registry.get_variant("QuickTest")
model_cls = registry.get_group("model", "ViTConfig")
```

**Key points:**

- `discover()` requires the main config class to identify variants and groups
- **Variants** are direct subclasses of the main config
- **Groups** are subclasses of nested field types in the main config

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
