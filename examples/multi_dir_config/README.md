# Multiple Config Directories Example

This example demonstrates how to use multiple config directories with **shadowing/override** behavior. This is useful for:

- **Layered configs** - Base configs with team/user/local overrides
- **Monorepos** - Share configs across projects with project-specific overrides
- **Multi-environment** - Shared defaults with environment-specific overrides

## How Multiple Config Directories Work

PydraConf discovers configs from **ALL** existing directories in the list. Configs in **later** directories (rightmost) override configs with the same name from earlier directories:

```json
{
  "config_dirs": [
    "shared_configs",    // 1. Base configs (lowest priority)
    "user_configs",      // 2. User overrides (medium priority)
    "configs"            // 3. Local overrides (highest priority)
  ]
}
```

**Shadowing behavior**:
- If `model/resnet.py` exists in all three directories, the one from `configs` (rightmost) is used
- If `model/vit.py` only exists in `configs`, it's used
- If `model/efficient_net.py` only exists in `user_configs`, it's used
- All three configs are available, with rightmost taking precedence for conflicts

## Example Structure

```
examples/multi_dir_config/
├── .pydraconfrc              # Specifies directory priority
├── train.py                  # Training script
├── shared_configs/           # Base configs (priority: 1)
│   ├── base.py              #   - Team defaults
│   └── model/
│       └── resnet.py        #   - Shared ResNet50
├── user_configs/            # User overrides (priority: 2)
│   └── model/
│       ├── resnet.py        #   - Overrides shared ResNet (uses ResNet101)
│       └── efficient_net.py #   - User's custom model
└── configs/                 # Local overrides (priority: 3)
    ├── model/
    │   └── vit.py           #   - Local ViT config
    └── dataset/
        ├── imagenet.py      #   - Local datasets
        └── cifar10.py
```

## Priority Example

With the structure above:

| Config | Location | Priority | Why? |
|--------|----------|----------|------|
| `model=resnet` | `user_configs/model/resnet.py` | Medium | User config shadows shared |
| `model=efficient_net` | `user_configs/model/efficient_net.py` | Medium | Only exists in user_configs |
| `model=vit` | `configs/model/vit.py` | Highest | Only exists in configs |
| `dataset=imagenet` | `configs/dataset/imagenet.py` | Highest | Only exists in configs |

## Usage

### Basic usage
```bash
# Uses ResNet from user_configs (overrides shared_configs version)
python train.py model=resnet dataset=imagenet

# Uses EfficientNet from user_configs (only exists there)
python train.py model=efficient_net dataset=cifar10

# Uses ViT from configs (only exists there)
python train.py model=vit dataset=imagenet
```

### See available configs
```bash
python train.py --help-groups
# Shows: model: vit, efficient_net, resnet
# (all three from different directories, resnet from user_configs overrides shared one)
```

### Override priority demonstration
```bash
# Notice ResNet uses depth=101 (user override) not depth=50 (shared default)
python train.py model=resnet
```

## Benefits

1. **Layered configuration** - Start with shared defaults, override selectively
2. **No duplication** - Only override what you need to change
3. **Team collaboration** - Share base configs, allow personal customization
4. **Clear precedence** - Rightmost directory always wins

## Common Use Cases

### Use Case 1: Team Defaults + Personal Overrides
```json
{
  "config_dirs": [
    "$ROOT/team_configs",    // Team defaults (in git)
    "$HOME/.my_project/configs"  // Personal overrides (local only)
  ]
}
```

Each developer can override team defaults without modifying shared files.

### Use Case 2: Monorepo with Shared Configs
```json
{
  "config_dirs": [
    "$ROOT/shared/configs",           // Cross-project shared configs
    "$ROOT/services/my-service/configs"  // Service-specific overrides
  ]
}
```

Services inherit from shared configs but can override specific ones.

### Use Case 3: Environment-Specific Configs
```json
{
  "config_dirs": [
    "configs/base",         // Base configs
    "configs/production"    // Production overrides
  ]
}
```

Production overrides specific configs (like using smaller batch sizes, different models, etc).

## Variable Substitution

All the usual variables work:
- `$CWD` - Current working directory
- `$ROOT` - Project root (directory with `pyproject.toml` or `.pydraconfrc`)
- Relative paths - Resolved relative to the script directory

Example:
```json
{
  "config_dirs": [
    "$ROOT/shared_configs",      // Absolute path from root
    "$CWD/experiment_configs",   // Absolute path from CWD
    "local_configs"              // Relative to script
  ]
}
```

## Tips

1. **Order matters**: Always put base configs first, overrides last
2. **Name consistently**: Use the same names for configs you want to override
3. **Document overrides**: Comment why you're overriding in the override file
4. **Test priority**: Use `--help-groups` to see which configs are actually loaded
