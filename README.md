# PydraConf

Python-native hierarchical configuration management with Pydantic. Like Hydra, but for YAML-haters.

**Key features** 🎯:

- Pure Python - no YAML, no magic strings
- Type-safe with Pydantic validation
- IDE autocomplete and refactoring support
- Run with a single `@with_config` decorator
- Type-driven architecture - groups are defined by class inheritance, not directory structure
- Built-in override tracking and config metadata

Three **powerful override mechanisms** work together 🍻:

1. **Variants** - Named configurations through inheritance (e.g., `QuickTest(TrainConfig)`)
2. **Groups** - Component swapping via type inheritance (e.g., `model=ViTConfig`)
3. **CLI Overrides** - Runtime field tweaks (e.g., `--epochs=50`)

<details>
<summary>Table of contents</summary>

- [PydraConf](#pydraconf)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [How It Works](#how-it-works)
    - [1. Variants - Named Configurations](#1-variants---named-configurations)
      - [Setting a Default Variant](#setting-a-default-variant)
    - [2. Groups - Component Swapping](#2-groups---component-swapping)
    - [3. CLI Overrides - Runtime Tweaks](#3-cli-overrides---runtime-tweaks)
    - [4. Override Priority](#4-override-priority)
  - [Configuration Directory](#configuration-directory)
    - [Option 1: Use the default](#option-1-use-the-default)
    - [Option 2: Config files (recommended for projects)](#option-2-config-files-recommended-for-projects)
    - [Option 3: Explicit argument](#option-3-explicit-argument)
  - [Examples](#examples)
  - [API Reference](#api-reference)
    - [`@with_config`](#with_config)
    - [`ConfigRegistry`](#configregistry)
    - [`PydraConfig`](#pydraconfig)
    - [`configure_logging`](#configure_logging)
  - [CLI Reference](#cli-reference)
  - [Development](#development)
  - [Comparison with Hydra](#comparison-with-hydra)
  - [License](#license)
  - [Contributing](#contributing)
  - [Credits](#credits)

</details>


## Installation

```bash
pip install pydraconf
```

## Quick Start

Create a simple config and use the decorator:

```python
from pydraconf import PydraConfig, with_config

# Use `PydraConfig` instead of Pydantic's `BaseModel` for your main configuration classes
# to get automatic override tracking and metadata features.
class TrainConfig(PydraConfig):
    epochs: int = 100
    batch_size: int = 32

class QuickTest(TrainConfig):
    epochs: int = 5

# The decorator automatically infers the config class from the function's type annotation.
@with_config()
def train(cfg: TrainConfig):
    # Prints applied configuration and overrides
    cfg.log_summary()

    # Your training logic here...

    # Export final config with metadata for reproducibility
    cfg.export_config("config.json")

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

Or set a different default variant:

```python
@with_config(config_cls=QuickTest)
def train(cfg: TrainConfig):
    ...
```

## How It Works

### 1. Variants - Named Configurations

Create named configuration variants by **subclassing your main config**:

```python
from pydraconf import PydraConfig

class TrainConfig(PydraConfig):
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

**How it works:** PydraConf discovers all subclassess of your main config class (the one used in your `train` function) and registers them as variants.

#### Setting a Default Variant

You can specify a default variant by passing `config_cls` to the decorator. This sets the default to use when no `--config` CLI flag is provided:

```python
# Use QuickTest as default variant
@with_config(config_cls=QuickTest)
def train(cfg: TrainConfig):
    print(f"Training for {cfg.epochs} epochs")

if __name__ == "__main__":
    train()  # Uses QuickTest by default (epochs=5)
```

**Important notes:**

- The `config_cls` must be a subclass of the function's type annotation. In the example above, `QuickTest` must be a subclass of `TrainConfig`.
- Discovery (variants, groups, CLI fields) is based on the **type annotation** (`TrainConfig`), not `config_cls`
- The `--config` CLI flag can still override `config_cls` to select a different variant
- CLI parameters are based on fields from the type annotation

**Use cases:**

- Set a default variant for production deployments
- Create multiple entry points with different default configurations
- Simplify testing by defaulting to test configurations

```python
# Different entry points with different configs
@with_config(config_cls=ProductionConfig)
def train_prod(cfg: TrainConfig):
    ...

@with_config(config_cls=QuickTest)
def train_dev(cfg: TrainConfig):
    ...
```

### 2. Groups - Component Swapping

Create swappable components by **defining base types for nested fields**:

```python
# configs/base.py
from pydantic import BaseModel, Field
from pydraconf import PydraConfig

# Define base types for groups with sane defaults
class ModelConfig(BaseModel):
    hidden_dim: int = 512
    num_layers: int = 6

class OptimizerConfig(BaseModel):
    lr: float = 0.001

# Main config
class TrainConfig(PydraConfig):
    epochs: int = 100
    model: ModelConfig = Field(default_factory=ModelConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)

# configs/model/vit.py
class ViTConfig(ModelConfig):  # Inherits from ModelConfig -> goes in "model" group
    hidden_dim: int = 768  # Override base
    num_heads: int = 12
    num_layers: int = 12  # Override base

# configs/model/resnet50.py
class ResNet50Config(ModelConfig):
    hidden_dim: int = 2048
    num_layers: int = 50
    pretrained: bool = True

# configs/optimizer/adam.py
class AdamConfig(OptimizerConfig):  # Inherits from OptimizerConfig -> goes in "optimizer" group
    # Inherits lr=0.001 from base
    beta1: float = 0.9
    beta2: float = 0.999
```

Swap components at runtime using class names:

```bash
python train.py model=ViTConfig optimizer=AdamConfig
```

**How it works:** PydraConf identifies groups by examining the types of nested fields in your main config. Any class that inherits from a nested field's type becomes part of that field's group. The field name becomes the group name.

### 3. CLI Overrides - Runtime Tweaks

Override any field from the command line:

```bash
python train.py --epochs=50 --model.hidden_dim=1024
```

Use exact field names including underscores (e.g., `batch_size` → `--batch_size`).

### 4. Override Priority

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
@with_config()  # Searches default locations
def train(cfg: TrainConfig):
    ...
```

By default, PydraConf searches in this order:

1. `$ROOT/configs` - Project root (directory with `pyproject.toml` or `.pydraconfrc`)
2. `$CWD/configs` - Current working directory
3. `configs` - Relative to the script directory

**Config discovery and shadowing**: PydraConf discovers configs from ALL existing directories. Configs in later directories (rightmost) override configs with the same name from earlier directories. For example, if both `$ROOT/configs` and`$CWD/configs`  have a `ResNetConfigProd`, the one from `$CWD/configs` (rightmost) wins.

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
@with_config()  # Reads from config file
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
@with_config(config_dirs="my_configs")
def train(cfg: TrainConfig):
    ...

# Multiple directories with priority
@with_config(config_dirs=["$ROOT/shared_configs", "$CWD/configs"])
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

- [`examples/ml_training/`](examples/ml_training/) - **Comprehensive example** demonstrating all features: variants, groups, CLI overrides, multiple entry points, multi-class files, and metadata tracking. Start here!
- [`examples/multi_dir_config/`](examples/multi_dir_config/) - Multiple config directories with shadowing for team collaboration and monorepo setups

## API Reference

### `@with_config`

Decorator to make a function config-driven. The config class is automatically inferred from the function's first parameter type annotation, or can be explicitly specified.

```python
@with_config(
    config_cls: Type[PydraConfig] | None = None,  # Optional explicit config class
    config_dirs: str | list[str] | None = None   # Directory or directories to scan
)
def my_function(cfg: ConfigClass):
    ...
```

**Arguments:**

- `config_cls`: Optional default config class. If provided, it must be a subclass of the function's first parameter type annotation. This is useful when you want to set a default config variant without requiring CLI arguments.

  **Important**: Discovery (variants, groups, CLI fields) is ALWAYS based on the type annotation, NOT on `config_cls`. The `config_cls` parameter only sets which config to instantiate by default when no `--config` flag is provided.

  **Selection priority**: CLI `--config` flag > `config_cls` parameter > type annotation

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
- **Variants** are subclassess of the main config
- **Groups** are subclasses of nested field types in the main config

### `PydraConfig`

Enhanced configuration base class that extends Pydantic's `BaseModel` with automatic override tracking and metadata capabilities.

**When to use:**

- Use `PydraConfig` for your main configuration classes (the ones passed to `@with_config`)
- Use Pydantic's `BaseModel` for nested config groups (optional, both work)

```python
from pydraconf import PydraConfig
from pydantic import BaseModel, Field

# Nested configs can use BaseModel
class ModelConfig(BaseModel):
    hidden_dim: int = 512

# Main config should use PydraConfig
class TrainConfig(PydraConfig):
    epochs: int = 100
    model: ModelConfig = Field(default_factory=ModelConfig)
```

**Methods:**

**`get_metadata() -> dict[str, Any]`**

Get metadata about the configuration and applied overrides.

```python
metadata = config.get_metadata()
print(metadata["config_name"])     # "TrainConfig"
print(metadata["variant_name"])    # "QuickTest" (if variant selected)
print(metadata["group_selections"]) # {"model": "ViTConfig"}
print(metadata["field_overrides"])  # {"epochs": 50}
print(metadata["config_dirs"])      # ["./configs"]
print(metadata["timestamp"])        # ISO timestamp
```

**`get_overrides_summary() -> list[str]`**

Get a human-readable list of all applied overrides.

```python
overrides = config.get_overrides_summary()
# Returns: ["variant: QuickTest", "model=ViTConfig", "epochs=50"]

for override in overrides:
    print(f"  - {override}")
```

**`export_config(filepath: str, *, include_metadata: bool = True, indent: int = 2) -> None`**

Export configuration to a JSON file with optional metadata.

```python
# Export with metadata (default)
config.export_config("config.json")

# Export only config values
config.export_config("config.json", include_metadata=False)
```

Exported JSON structure (with metadata):

```json
{
  "config": {
    "epochs": 50,
    "batch_size": 32,
    "model": {...}
  },
  "metadata": {
    "config_name": "TrainConfig",
    "variant_name": "QuickTest",
    "group_selections": {"model": "ViTConfig"},
    "field_overrides": {"epochs": 50},
    "config_dirs": ["./configs"],
    "timestamp": "2025-01-15T10:30:00.123456"
  }
}
```

**`to_json_with_metadata(*, indent: int = 2) -> str`**

Convert configuration to a JSON string with metadata.

```python
json_str = config.to_json_with_metadata()
print(json_str)
```

**`log_summary(level: str = "INFO") -> None`**

Log a summary of the configuration and applied overrides.

```python
# Configure logging once at startup
from pydraconf import configure_logging
configure_logging(level="INFO")

# Log summary (outputs to stdout by default)
config.log_summary()
```

Output:

```
INFO - pydraconf - Configuration: TrainConfig
INFO - pydraconf - Variant: QuickTest
INFO - pydraconf - Applied Overrides:
INFO - pydraconf -   - variant: QuickTest
INFO - pydraconf -   - model=ViTConfig
INFO - pydraconf -   - epochs=50
```

### `configure_logging`

Configure global logging for PydraConf.

```python
from pydraconf import configure_logging
import logging

# Basic setup - log to stdout (default)
configure_logging(level="DEBUG")

# Single handler with default format
file_handler = logging.FileHandler("config.log")
configure_logging(level="INFO", handlers=file_handler)

# Multiple handlers with different formats
file_handler = logging.FileHandler("config.log")
console_handler = logging.StreamHandler()
configure_logging(
    level="INFO",
    handlers=[
        (file_handler, "%(asctime)s - %(levelname)s - %(message)s"),
        (console_handler, "%(levelname)s - %(message)s"),
    ]
)

# Multiple handlers with same custom format
configure_logging(
    level="INFO",
    handlers=[
        (file_handler, "%(asctime)s - %(levelname)s - %(message)s"),
        (console_handler, "%(asctime)s - %(levelname)s - %(message)s"),
    ]
)

# Mix of default and custom formats
configure_logging(
    level="INFO",
    handlers=[
        (file_handler, None),  # Uses default format
        (console_handler, "%(levelname)s - %(message)s"),  # Custom format
    ]
)
```

**Arguments:**

- `level`: Log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
- `handlers`: Can be:
  - `None`: Uses default StreamHandler to stdout with default format
  - Single handler: Uses provided handler with default format
  - List of `(handler, format)` tuples: Each handler uses its own format (use `None` for default)

## CLI Reference

List available configuration options:

```bash
# Show all available variants
python train.py --list-variants

# Show all available groups and their configs
python train.py --list-groups
```

These commands display the available options and exit, making it easy to discover what configurations you can use.

## Development

```bash
# Clone and install
git clone https://github.com/yourusername/pydraconf.git
cd pydraconf
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install

# Linting and formatting
uv run pre-commit run --all-files

# Run tests
uv run pytest
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
