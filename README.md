# PydraConf

Python-native hierarchical configuration management with Pydantic. Like Hydra, but for YAML-haters.

## Features

Three powerful override mechanisms work together:

1. **Subclassing** - Named variants through Python inheritance (e.g., `QuickTest(BaseConfig)`)
2. **Config Groups** - Component swapping via directory structure (e.g., `model=vit`)
3. **CLI Overrides** - Runtime field tweaks (e.g., `--epochs=50`)

Benefits:
- Pure Python - no YAML, no magic strings
- Type-safe with Pydantic validation
- IDE autocomplete and refactoring support
- Simple `@provide_config` decorator
- Convention-over-configuration design

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

@provide_config(TrainConfig)
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
python train.py --config=QuickTest

# Override specific fields
python train.py --epochs=50 --batch_size=64

# Combine all three
python train.py --config=QuickTest --epochs=10
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

Use with `--config=ClassName`:

```bash
python train.py --config=QuickTest   # Uses QuickTest
python train.py --config=Production  # Uses Production
```

Variant names use the exact class name.

### 2. Config Groups - Component Swapping

Organize configs in subdirectories to create swappable components:

```
configs/
├── base.py           # Main config
├── model/
│   ├── resnet50.py   # Contains ResNet50Config class
│   └── vit.py        # Contains ViTConfig class
└── optimizer/
    ├── adam.py       # Contains AdamConfig class
    └── sgd.py        # Contains SGDConfig class
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

Swap components at runtime using class names:

```bash
python train.py model=ViTConfig optimizer=SGDConfig
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
@provide_config(TrainConfig)  # Searches default locations
def train(cfg):
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
@provide_config(TrainConfig)  # Reads from config file
def train(cfg):
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
@provide_config(TrainConfig, config_dirs="my_configs")
def train(cfg):
    ...

# Multiple directories with priority
@provide_config(TrainConfig, config_dirs=["$ROOT/shared_configs", "$CWD/configs"])
def train(cfg):
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

Decorator to make a function config-driven.

```python
@provide_config(
    config_cls: Type[BaseModel],                 # Base config class
    config_dirs: str | list[str] | None = None   # Directory or directories to scan
)
def my_function(cfg: ConfigClass):
    ...
```

**Arguments:**
- `config_cls`: Base configuration class (Pydantic BaseModel)
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
registry.discover(Path("configs"))

# List available options
print(registry.list_variants())  # ["QuickTest", "Production"]
print(registry.list_groups())    # {"model": ["ResNet50Config", "ViTConfig"], ...}

# Get specific configs
variant_cls = registry.get_variant("QuickTest")
model_cls = registry.get_group("model", "ViTConfig")
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
