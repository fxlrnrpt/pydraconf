"""Command-line interface parser for hierarchical configs."""

import argparse
import json
from enum import Enum
from typing import Any, Type, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from .base_config import PydraConfig
from .registry import ConfigRegistry


class ConfigCLIParser:
    """Parser for config CLI arguments.

    Supports three types of arguments:
    1. --config=VariantClassName (select named variant using class name)
    2. group=ClassName (swap config group using class name, e.g., model=ViTConfig)
    3. --field.nested=value (override specific fields using exact field names)
    """

    def __init__(self, config_cls: Type[PydraConfig], registry: ConfigRegistry) -> None:
        """Initialize parser.

        Args:
            config_cls: Base config class to build parser from
            registry: Config registry with available groups and variants
        """
        self.config_cls = config_cls
        self.registry = registry
        self.parser = argparse.ArgumentParser(
            description=f"Configure {config_cls.__name__}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self._build_parser()

    def _build_parser(self) -> None:
        """Build argument parser with all config options."""
        variants = self.registry.list_variants()

        self.parser.add_argument(
            "--config",
            type=str,
            choices=variants,
            help="Select config variant",
        )

        self.parser.add_argument(
            "--list-groups",
            action="store_true",
            help="Show available config groups",
        )

        self.parser.add_argument(
            "--list-variants",
            action="store_true",
            help="Show available config variants",
        )

        # Add field arguments recursively
        self._add_field_arguments(self.config_cls, prefix="")

    def _add_field_arguments(self, model: Type[BaseModel], prefix: str) -> None:
        """Recursively add arguments for model fields.

        Args:
            model: PydraConfig to extract fields from
            prefix: Prefix for nested fields (e.g., "model.")
        """
        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            arg_name = f"{prefix}{field_name}"

            # Handle nested BaseModel
            origin = get_origin(field_type)
            if origin is None and isinstance(field_type, type) and issubclass(field_type, BaseModel):
                # Recurse into nested model
                self._add_field_arguments(field_type, f"{prefix}{field_name}.")
            else:
                # Add argument for simple field
                self.parser.add_argument(
                    f"--{arg_name}",
                    type=self._infer_type(field_type, field_info),
                    help=field_info.description or f"Override {arg_name}",
                )

    def _infer_type(self, field_type: Any, field_info: FieldInfo) -> type:
        """Infer argument type from Pydantic field type.

        Args:
            field_type: Pydantic field annotation
            field_info: Field information

        Returns:
            Type callable for argparse
        """
        # Handle Optional types
        origin = get_origin(field_type)
        if origin is not None:
            args = get_args(field_type)
            if len(args) > 0:
                # Use first non-None type
                field_type = next((arg for arg in args if arg is not type(None)), args[0])

        # Handle Enum
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return str  # Will validate against enum values later

        # Handle basic types
        if field_type in (int, float, str, bool):
            if field_type is bool:
                # For bool, we need special handling
                return self._bool_type  # pyright: ignore[reportReturnType]
            return field_type

        # For complex types (list, dict, etc.), parse as JSON
        return self._json_type  # pyright: ignore[reportReturnType]

    def _bool_type(self, value: str) -> bool:
        """Parse boolean from string.

        Args:
            value: String value

        Returns:
            Boolean value

        Raises:
            argparse.ArgumentTypeError: If value is not a valid boolean
        """
        if value.lower() in ("true", "1", "yes", "y"):
            return True
        elif value.lower() in ("false", "0", "no", "n"):
            return False
        else:
            raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")

    def _json_type(self, value: str) -> Any:
        """Parse JSON from string.

        Args:
            value: JSON string

        Returns:
            Parsed value

        Raises:
            argparse.ArgumentTypeError: If JSON is invalid
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise argparse.ArgumentTypeError(f"Invalid JSON: {e}")

    def parse(self, args: list[str] | None = None) -> tuple[str | None, dict[str, str], dict[str, Any]]:
        """Parse command-line arguments.

        Args:
            args: Arguments to parse (defaults to sys.argv)

        Returns:
            Tuple of (config_variant, group_selections, field_overrides)
            - config_variant: Selected variant name (--config=VariantClassName)
            - group_selections: Component swaps using class names {"model": "ViTConfig"}
            - field_overrides: Field changes {"epochs": 50, "model.hidden_dim": 1024}
        """
        # Separate group selections from regular args
        group_args: list[str] = []
        regular_args: list[str] = []

        if args is None:
            import sys

            args = sys.argv[1:]

        i = 0
        while i < len(args):
            arg = args[i]
            # Check for group selection (group=name format without --)
            if "=" in arg and not arg.startswith("-"):
                group_args.append(arg)
            else:
                regular_args.append(arg)
            i += 1

        # Parse regular arguments
        parsed = self.parser.parse_args(regular_args)

        # Handle --list-variants
        if hasattr(parsed, "list_variants") and parsed.list_variants:
            variants = self.registry.list_variants()
            print("Available config variants:")
            for variant in variants:
                print(f"  {variant}")
            if not variants:
                print("  None")
            import sys

            sys.exit(0)

        # Handle --list-groups
        if hasattr(parsed, "list_groups") and parsed.list_groups:
            groups = self.registry.list_groups()
            print("Available config groups:")
            for group, configs in groups.items():
                print(f"  {group}: {', '.join(configs)}")
            if not groups:
                print("  None")
            import sys

            sys.exit(0)

        # Extract config variant
        config_variant = getattr(parsed, "config", None)

        # Parse group selections
        group_selections: dict[str, str] = {}
        for group_arg in group_args:
            group, name = group_arg.split("=", 1)
            group_selections[group] = name

        # Extract field overrides
        field_overrides: dict[str, Any] = {}
        for key, value in vars(parsed).items():
            if key in ("config", "list_groups", "list_variants") or value is None:
                continue
            # Store with dot notation for nested fields (key already has correct format)
            field_overrides[key] = value

        return config_variant, group_selections, field_overrides
