"""Configuration registry for discovering and managing config classes."""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from .base_config import PydraConfig


class ConfigRegistry:
    """Registry for configuration classes and variants.

    Manages two types of configs:
    1. Groups: Configs organized in subdirectories, identified by class name (e.g., configs/model/resnet.py with ResNet50Config class)
    2. Variants: Named config subclasses (e.g., class QuickTest(PydraConfig))
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._groups: dict[str, dict[str, Type[BaseModel]]] = {}
        self._variants: dict[str, Type[PydraConfig]] = {}

    def discover(self, root_dir: Path, main_config_cls: Type[PydraConfig]) -> None:
        """Discover and register configs from directory.

        Discovery rules:
        - Subclasses of main_config_cls become variants (QuickTest(TrainConfig) → variant="QuickTest")
        - Subclasses of nested field types become groups (ResNet50Config(ModelConfig) → group="model", name="ResNet50Config")

        Args:
            root_dir: Root directory to scan for configs
            main_config_cls: The main config class (e.g., TrainConfig from train function parameter)
        """
        if not root_dir.exists():
            return

        # Get nested field types from main config to identify groups
        nested_field_types = self._get_nested_field_types(main_config_cls)

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

                # Check if it's a variant (direct subclass of main config)
                if self._is_variant_of(obj, main_config_cls):
                    self.register_variant(obj.__name__, obj)

                # Check if it's a group config (subclass of nested field type)
                for field_name, field_type in nested_field_types.items():
                    if self._is_variant_of(obj, field_type) and obj is not field_type:
                        self.register_group(field_name, obj.__name__, obj)

    def register_group(self, group: str, name: str, cls: Type[BaseModel]) -> None:
        """Register a config class in a group by class name.

        Args:
            group: Group name (e.g., "model", "optimizer")
            name: Config class name (e.g., "ResNet50Config", "ViTConfig")
            cls: Config class
        """
        if group not in self._groups:
            self._groups[group] = {}
        self._groups[group][name] = cls

    def register_variant(self, name: str, cls: Type[PydraConfig]) -> None:
        """Register a named config variant.

        Args:
            name: Variant name (class name)
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

    def get_variant(self, name: str) -> Type[PydraConfig]:
        """Get a named config variant.

        Args:
            name: Variant name (class name)

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
        # First check if any module in sys.modules already points to this file
        # This ensures we reuse existing imports and avoid duplicate class objects
        try:
            file_path_resolved = py_file.resolve()
            for module_name, module in list(sys.modules.items()):
                if module is None:
                    continue
                try:
                    module_file = getattr(module, "__file__", None)
                    if module_file and Path(module_file).resolve() == file_path_resolved:
                        return module
                except (OSError, ValueError):
                    continue
        except OSError:
            pass

        # Try to import module via the canonical Python module name so that
        # discovered classes match existing imports (avoids duplicate types).
        module_name = self._derive_module_name(py_file)
        if module_name:
            try:
                return importlib.import_module(module_name)
            except ModuleNotFoundError:
                # Fall back to loading from file path when module import fails
                pass

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

    def _derive_module_name(self, py_file: Path) -> str | None:
        """Attempt to derive the canonical module path for a Python file."""
        try:
            file_path = py_file.resolve()
        except OSError:
            return None

        best_candidate: tuple[str, int] | None = None
        for entry in sys.path:
            entry_path = Path(entry or ".")
            try:
                entry_resolved = entry_path.resolve()
            except OSError:
                continue

            try:
                relative = file_path.relative_to(entry_resolved)
            except ValueError:
                continue

            parts = relative.with_suffix("").parts
            if not parts or not all(part.isidentifier() for part in parts):
                continue

            candidate = ".".join(parts)
            depth = len(parts)
            if best_candidate is None or depth > best_candidate[1]:
                best_candidate = (candidate, depth)

        return best_candidate[0] if best_candidate else None

    def _is_config_class(self, obj: Any) -> bool:
        """Check if object is a valid config class.

        Args:
            obj: Object to check

        Returns:
            True if obj is a BaseModel subclass (but not BaseModel itself)
        """
        return inspect.isclass(obj) and issubclass(obj, BaseModel) and obj is not BaseModel

    def _get_nested_field_types(self, config_cls: Type[BaseModel]) -> dict[str, Type[BaseModel]]:
        """Extract nested BaseModel field types from a config class.

        Args:
            config_cls: Config class to extract field types from

        Returns:
            Dictionary mapping field names to their BaseModel types
        """
        nested_types = {}
        for field_name, field_info in config_cls.model_fields.items():
            field_type = field_info.annotation
            # Check if it's a BaseModel subclass (but not BaseModel itself)
            if isinstance(field_type, type) and issubclass(field_type, BaseModel) and field_type is not BaseModel:
                nested_types[field_name] = field_type
        return nested_types

    def _is_variant_of(self, cls: Type[BaseModel], parent_cls: Type[BaseModel]) -> bool:
        """Check if a config class is a direct subclass of parent_cls.

        Args:
            cls: Config class to check
            parent_cls: Parent class to check against

        Returns:
            True if cls is a direct subclass of parent_cls
        """
        return parent_cls in cls.__bases__
