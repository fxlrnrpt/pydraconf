"""Decorators for config-driven applications."""

from functools import wraps
from pathlib import Path
from typing import Any, Callable, Type, TypeVar, get_type_hints

from pydantic import BaseModel

from .base_config import PydraConfig
from .cli import ConfigCLIParser
from .config_loader import find_root_dir, load_config_dirs, substitute_variables
from .registry import ConfigRegistry
from .utils import set_nested_value

T = TypeVar("T", bound=PydraConfig)


def _build_config(
    config_cls: Type[PydraConfig],
    registry: ConfigRegistry,
    group_selections: dict[str, str],
    field_overrides: dict[str, Any],
    variant_name: str | None = None,
    config_dirs: list[str] | None = None,
) -> PydraConfig:
    """Build config instance with all overrides applied.

    Override priority (from lowest to highest):
    1. Base config defaults
    2. Group selections (swap entire sub-configs)
    3. Field overrides (modify specific fields)

    Args:
        config_cls: Base config class (may be a variant)
        registry: Config registry
        group_selections: Component swaps {"model": "vit"}
        field_overrides: Field changes {"epochs": 50, "model.hidden_dim": 1024}
        variant_name: Name of the variant selected (for metadata)
        config_dirs: List of config directories (for metadata)

    Returns:
        Configured instance with all overrides applied

    Example:
        config_cls = QuickTest  # epochs=5
        group_selections = {"model": "vit"}
        field_overrides = {"model.hidden_dim": 1024}
        Result: QuickTest(epochs=5, model=ViT(hidden_dim=1024))
    """
    # Start with base config values
    config_dict = config_cls().model_dump()

    # Apply group selections (replace entire sub-configs)
    # We need to instantiate new configs for groups, not just dump their dicts
    group_instances = {}
    for group, variant in group_selections.items():
        new_cls = registry.get_group(group, variant)
        group_instances[group] = new_cls()
        config_dict[group] = group_instances[group].model_dump()

    # Apply field overrides
    for path, value in field_overrides.items():
        # Handle nested paths with dots
        keys = path.split(".")
        set_nested_value(config_dict, keys, value)

    # For group instances that were swapped, we need to update them with overrides
    for group, instance in group_instances.items():
        if group in config_dict:
            # Re-create instance with overrides applied
            group_instances[group] = type(instance)(**config_dict[group])

    # Build final config using model_construct to bypass validation
    # This allows swapping config groups with different types
    final_dict = config_cls().model_dump()
    final_dict.update(config_dict)

    # Replace group dicts with actual instances (for swapped configs)
    for group, instance in group_instances.items():
        final_dict[group] = instance

    # For non-swapped nested PydraConfig fields, we need to reconstruct them
    # Otherwise they stay as dicts when using model_construct
    for field_name, field_info in config_cls.model_fields.items():
        if field_name not in group_instances and field_name in final_dict:
            field_type = field_info.annotation
            # Check if it's a BaseModel field (but not BaseModel itself)
            if isinstance(field_type, type) and issubclass(field_type, BaseModel) and field_type is not BaseModel:
                if isinstance(final_dict[field_name], dict):
                    # Reconstruct the nested model from dict
                    final_dict[field_name] = field_type(**final_dict[field_name])

    # Use model_construct to bypass field type validation
    config = config_cls.model_construct(**final_dict)

    config.set_metadata(
        config_name=config_cls.__name__,
        variant_name=variant_name,
        group_selections=group_selections,
        field_overrides=field_overrides,
        config_dirs=config_dirs or [],
    )

    return config


def with_config(
    config_cls: Type[T] | None = None,
    config_dirs: str | list[str] | None = None,
) -> Callable[[Callable[[T], Any]], Callable[[], Any]]:
    """Decorator to make a function config-driven.

    Discovers configs, parses CLI arguments, builds config, and calls function.
    The config class is inferred from the function's first parameter type annotation.

    Args:
        config_cls: Optional config class to use as the default. If provided, it must be
                   a subclass of the function's first parameter type annotation.

                   Important: Discovery (variants, groups, CLI fields) is ALWAYS based on
                   the type annotation, NOT on config_cls. The config_cls only determines
                   which config to instantiate when no --config flag is provided.

                   Priority: CLI --config flag > config_cls parameter > type annotation

        config_dirs: Directory or list of directories to scan for configs.
                    If None, will search for config_dirs in:
                    1. .pydraconfrc (JSON) in current/parent directories
                    2. pyproject.toml [tool.pydraconf] section
                    3. Defaults to ["$ROOT/configs", "$CWD/configs", "configs"]

                    Supports variable substitution:
                    - $CWD: Current working directory
                    - $ROOT: Project root (dir with pyproject.toml or .pydraconfrc)

                    Relative paths (without variables) are treated as relative to the script.

    Returns:
        Decorated function

    Example:
        # With explicit config_dirs
        @with_config(config_dirs="configs")
        def train(cfg: TrainConfig):
            print(f"Training for {cfg.epochs} epochs")

        # With multiple directories
        @with_config(config_dirs=["$CWD/configs", "configs"])
        def train(cfg: TrainConfig):
            print(f"Training for {cfg.epochs} epochs")

        # Using config file (.pydraconfrc or pyproject.toml)
        @with_config()
        def train(cfg: TrainConfig):
            print(f"Training for {cfg.epochs} epochs")

        # With explicit config class (must be subclass of type annotation)
        @with_config(config_cls=QuickTestConfig)
        def train(cfg: TrainConfig):  # QuickTestConfig must be subclass of TrainConfig
            print(f"Training for {cfg.epochs} epochs")
    """

    def decorator(func: Callable[[T], Any]) -> Callable[[], Any]:
        # Infer default config class from function's first parameter type hint
        type_hints = get_type_hints(func)
        if not type_hints:
            msg = f"Function '{func.__name__}' must have type hints for its first parameter"
            raise TypeError(msg)

        # Get the first parameter's type
        first_param_name = next(iter(func.__code__.co_varnames[: func.__code__.co_argcount]))
        if first_param_name not in type_hints:
            msg = f"First parameter '{first_param_name}' of function '{func.__name__}' must have a type hint"
            raise TypeError(msg)

        annotated_config_cls = type_hints[first_param_name]

        # Validate it's a PydraConfig subclass
        if not (isinstance(annotated_config_cls, type) and issubclass(annotated_config_cls, PydraConfig)):
            msg = f"First parameter type of '{func.__name__}' must be a Pydraconf's PydraConfig, got {annotated_config_cls}"
            raise TypeError(msg)

        # Validate config_cls if provided
        if config_cls is not None:
            # Validate that provided config_cls is a subclass of the type annotation
            if not (isinstance(config_cls, type) and issubclass(config_cls, annotated_config_cls)):
                msg = f"Provided config_cls '{config_cls.__name__}' must be a subclass of '{annotated_config_cls.__name__}'"
                raise TypeError(msg)

        @wraps(func)
        def wrapper() -> Any:
            # Get the directory of the calling script
            import inspect
            import os

            frame = inspect.stack()[1]
            script_dir = Path(os.path.dirname(os.path.abspath(frame.filename)))
            cwd = Path.cwd()

            # Find project root
            root = find_root_dir(cwd)

            # Determine config directories
            resolved_config_dirs: list[str]
            if config_dirs is not None:
                # Explicit config_dirs provided
                if isinstance(config_dirs, str):
                    resolved_config_dirs = [config_dirs]
                else:
                    resolved_config_dirs = list(config_dirs)
            else:
                # Try to load from config files
                loaded_dirs = load_config_dirs(cwd)
                if loaded_dirs:
                    resolved_config_dirs = loaded_dirs
                else:
                    # Default: try ROOT first, then CWD, then relative to script
                    resolved_config_dirs = ["$ROOT/configs", "$CWD/configs", "configs"]

            # Substitute variables and resolve paths
            resolved_paths: list[Path] = []
            for dir_str in resolved_config_dirs:
                # Substitute variables
                substituted = substitute_variables(dir_str, cwd, root)
                path = Path(substituted)

                # Make path absolute if relative (relative paths are relative to script)
                if not path.is_absolute():
                    path = script_dir / path

                resolved_paths.append(path)

            # 1. Discover configs from all directories
            # Later directories override earlier ones (rightmost has highest priority)
            # Always use the type annotation for discovery
            registry = ConfigRegistry()
            for config_path in resolved_paths:
                if config_path.exists():
                    registry.discover(config_path, annotated_config_cls)

            # 2. Parse CLI
            parser = ConfigCLIParser(annotated_config_cls, registry)
            variant_name, group_selections, field_overrides = parser.parse()

            # 3. Select config class (variant, explicit config_cls, or base)
            # Priority: CLI --config flag > explicit config_cls parameter > type annotation
            if variant_name:
                # CLI --config flag has highest priority
                final_cls = registry.get_variant(variant_name)
            elif config_cls is not None:
                # Explicit config_cls parameter is second priority
                final_cls = config_cls
            else:
                # Type annotation is default
                final_cls = annotated_config_cls

            # 4. Build config with all overrides
            config = _build_config(
                final_cls,
                registry,
                group_selections,
                field_overrides,
                variant_name=variant_name,
                config_dirs=[str(p) for p in resolved_paths],
            )

            # 5. Call user function
            return func(config) # pyrefly: ignore[bad-argument-type]

        return wrapper

    return decorator
