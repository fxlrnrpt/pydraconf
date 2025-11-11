# Basic Example

This example demonstrates the three override mechanisms in PydraConf:

1. **Subclassing** - Named variants (DevConfig, ProdConfig)
2. **CLI Overrides** - Runtime tweaks (--port, --debug)

## Usage

### Default configuration
```bash
python main.py
# Uses AppConfig defaults: port=8000, debug=False, host=localhost
```

### Using variants (subclassing)
```bash
python main.py --config=dev-config
# Uses DevConfig: port=8080, debug=True

python main.py --config=prod-config
# Uses ProdConfig: host=0.0.0.0, debug=False
```

### CLI overrides
```bash
python main.py --port=9000 --debug=true
# Overrides specific fields

python main.py --config=dev-config --port=3000
# Combines variant + field override
```

## Available Configs

Run with `--help` to see all available options:
```bash
python main.py --help
```
