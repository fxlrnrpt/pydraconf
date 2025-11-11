"""Configuration registry for discovering and managing config classes."""

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from .utils import camel_to_kebab


class ConfigRegistry:
    """Registry for configuration classes and variants.

    Manages two types of configs:
    1. Groups: Configs organized in subdirectories (e.g., configs/model/resnet.py)
    2. Variants: Named config subclasses (e.g., class QuickTest(BaseConfig))
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._groups: dict[str, dict[str, Type[BaseModel]]] = {}
        self._variants: dict[str, Type[BaseModel]] = {}

    def discover(self, root_dir: Path) -> None:
        """Discover and register configs from directory.

        Discovery rules:
        - Files in subdirectories become config groups (model/resnet.py → group="model", name="resnet")
        - Subclasses of other configs become variants (QuickTest(BaseConfig) → variant="quick-test")

        Args:
            root_dir: Root directory to scan for configs
        """
        if not root_dir.exists():
            return

        for py_file in root_dir.rglob("*.py"):
            # Skip private modules
            if py_file.stem.startswith("_"):
                continue

            # Import the module
            module = self._import_module(py_file)
            if module is None:
                continue

            # Find all BaseModel subclasses
            for name, obj in inspect.getmembers(module):
                if not self._is_config_class(obj):
                    continue

                # Check if it's in a subdirectory (config group)
                if py_file.parent != root_dir:
                    group = py_file.parent.name
                    config_name = py_file.stem
                    self.register_group(group, config_name, obj)

                # Check if it's a variant (subclasses another config)
                if self._is_variant(obj):
                    variant_name = camel_to_kebab(obj.__name__)
                    self.register_variant(variant_name, obj)

    def register_group(self, group: str, name: str, cls: Type[BaseModel]) -> None:
        """Register a config class in a group.

        Args:
            group: Group name (e.g., "model", "optimizer")
            name: Config name within group (e.g., "resnet", "vit")
            cls: Config class
        """
        if group not in self._groups:
            self._groups[group] = {}
        self._groups[group][name] = cls

    def register_variant(self, name: str, cls: Type[BaseModel]) -> None:
        """Register a named config variant.

        Args:
            name: Variant name (kebab-case)
            cls: Config class
        """
        self._variants[name] = cls

    def get_group(self, group: str, name: str) -> Type[BaseModel]:
        """Get a config class from a group.

        Args:
            group: Group name
            name: Config name within group

        Returns:
            Config class

        Raises:
            KeyError: If group or config not found
        """
        if group not in self._groups:
            raise KeyError(f"Config group '{group}' not found. Available groups: {list(self._groups.keys())}")
        if name not in self._groups[group]:
            available = list(self._groups[group].keys())
            raise KeyError(f"Config '{name}' not found in group '{group}'. Available: {available}")
        return self._groups[group][name]

    def get_variant(self, name: str) -> Type[BaseModel]:
        """Get a named config variant.

        Args:
            name: Variant name (kebab-case)

        Returns:
            Config class

        Raises:
            KeyError: If variant not found
        """
        if name not in self._variants:
            raise KeyError(f"Config variant '{name}' not found. Available variants: {list(self._variants.keys())}")
        return self._variants[name]

    def list_groups(self) -> dict[str, list[str]]:
        """List all available config groups and their configs.

        Returns:
            Dictionary mapping group names to lists of config names
        """
        return {group: list(configs.keys()) for group, configs in self._groups.items()}

    def list_variants(self) -> list[str]:
        """List all available config variants.

        Returns:
            List of variant names
        """
        return list(self._variants.keys())

    def _import_module(self, py_file: Path) -> Any:
        """Import a Python module from file path.

        Args:
            py_file: Path to Python file

        Returns:
            Imported module or None if import fails
        """
        try:
            # Create unique module name based on file path
            module_name = f"pydraconf_config_{py_file.stem}_{id(py_file)}"

            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            # Silently skip files that fail to import
            return None

    def _is_config_class(self, obj: Any) -> bool:
        """Check if object is a valid config class.

        Args:
            obj: Object to check

        Returns:
            True if obj is a BaseModel subclass (but not BaseModel itself)
        """
        return (
            inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
        )

    def _is_variant(self, cls: Type[BaseModel]) -> bool:
        """Check if config class is a variant (subclasses another config).

        Args:
            cls: Config class to check

        Returns:
            True if cls subclasses another config (not just BaseModel)
        """
        for base in cls.__bases__:
            if base is not BaseModel and inspect.isclass(base) and issubclass(base, BaseModel):
                return True
        return False
