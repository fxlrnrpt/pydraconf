"""Base configuration class with override tracking and metadata support."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .logger import LogLevel, logger


class PydraConfig(BaseModel):
    """
    Base configuration class that extends Pydantic BaseModel with override tracking
    and metadata output capabilities.

    This class automatically tracks all overrides applied to the configuration,
    including variant selection, group selections, and field overrides.

    Example:
        ```python
        from pydraconf import PydraConfig

        class TrainConfig(PydraConfig):
            epochs: int = 100
            batch_size: int = 32

        class QuickTest(TrainConfig):
            epochs: int = 5

        @with_config()
        def train(cfg: TrainConfig):
            # Access metadata
            metadata = cfg.get_metadata()
            print(metadata["config_name"])  # "QuickTest"
            print(metadata["overrides"])    # {"field_overrides": {...}, ...}

            # Export to JSON with metadata
            cfg.export_config("config_snapshot.json")

            # Log configuration summary
            cfg.log_summary()
        ```
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    # Private fields to store metadata (excluded from serialization by default)
    _config_metadata: dict[str, Any] = {}

    def set_metadata(
        self,
        *,
        config_name: str | None = None,
        variant_name: str | None = None,
        group_selections: dict[str, str] | None = None,
        field_overrides: dict[str, Any] | None = None,
        config_dirs: list[str] | None = None,
    ) -> None:
        """
        Set metadata about the configuration and its overrides.

        This method is called internally by the @with_config decorator.

        Args:
            config_name: Name of the config class being used
            variant_name: Name of the variant selected (if any)
            group_selections: Dictionary of group selections {group_name: class_name}
            field_overrides: Dictionary of field overrides {field_path: value}
            config_dirs: List of config directories searched
        """
        self._config_metadata = {
            "config_name": config_name or self.__class__.__name__,
            "variant_name": variant_name,
            "group_selections": group_selections or {},
            "field_overrides": field_overrides or {},
            "config_dirs": config_dirs or [],
            "timestamp": datetime.now().isoformat(),
        }

    def get_metadata(self) -> dict[str, Any]:
        """
        Get metadata about the configuration and applied overrides.

        Returns:
            Dictionary containing:
                - config_name: Name of the config class
                - variant_name: Name of the variant (if selected)
                - group_selections: Dictionary of group selections
                - field_overrides: Dictionary of field overrides
                - config_dirs: List of config directories
                - timestamp: ISO format timestamp when config was created

        Example:
            ```python
            metadata = config.get_metadata()
            print(f"Using config: {metadata['config_name']}")
            print(f"Overrides: {metadata['field_overrides']}")
            ```
        """
        # Return a copy to prevent external modification
        return self._config_metadata.copy()

    def get_overrides_summary(self) -> list[str]:
        """
        Get a human-readable list of all overrides applied to this config.

        Returns:
            List of override descriptions in the format:
                - "variant: VariantName" (if variant was selected)
                - "group.field_name=ClassName" (for each group selection)
                - "field.path=value" (for each field override)

        Example:
            ```python
            overrides = config.get_overrides_summary()
            print("Applied overrides:")
            for override in overrides:
                print(f"  - {override}")
            ```
        """
        overrides = []

        # Add variant if present
        if self._config_metadata.get("variant_name"):
            overrides.append(f"variant: {self._config_metadata['variant_name']}")

        # Add group selections
        for group_name, class_name in self._config_metadata.get("group_selections", {}).items():
            overrides.append(f"{group_name}={class_name}")

        # Add field overrides
        for field_path, value in self._config_metadata.get("field_overrides", {}).items():
            overrides.append(f"{field_path}={value}")

        return overrides

    def export_config(
        self,
        filepath: str,
        *,
        include_metadata: bool = True,
        indent: int = 2,
    ) -> None:
        """
        Export the configuration to a JSON file with optional metadata.

        Args:
            filepath: Path to the output JSON file
            include_metadata: Whether to include metadata about overrides
            indent: Number of spaces for JSON indentation

        Example:
            ```python
            # Export with metadata (default)
            config.export_config("config.json")

            # Export only the config values
            config.export_config("config.json", include_metadata=False)
            ```

        The exported JSON structure (with metadata) looks like:
            ```json
            {
                "config": {
                    "epochs": 50,
                    "batch_size": 32,
                    ...
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
        """
        output: dict[str, Any] = {}

        if include_metadata:
            output["config"] = self.model_dump()
            output["metadata"] = self.get_metadata()
        else:
            output = self.model_dump()

        with open(filepath, "w") as f:
            json.dump(output, f, indent=indent, default=str)

        logger.info(f"Configuration exported to {filepath}")

    def to_json_with_metadata(self, *, indent: int = 2) -> str:
        """
        Convert the configuration to a JSON string with metadata.

        Args:
            indent: Number of spaces for JSON indentation

        Returns:
            JSON string containing both config and metadata

        Example:
            ```python
            json_str = config.to_json_with_metadata()
            print(json_str)
            ```
        """
        output = {
            "config": self.model_dump(),
            "metadata": self.get_metadata(),
        }
        return json.dumps(output, indent=indent, default=str)

    def log_summary(self, level: LogLevel = "INFO") -> None:
        """
        Log a summary of the configuration and applied overrides.

        Args:
            level: Log level to use for the summary

        Example:
            ```python
            # Configure logging first (once at startup)
            from pydraconf import configure_logging
            configure_logging(level="INFO")

            # Log summary (outputs to stdout by default)
            config.log_summary()
            # Output:
            # INFO - pydraconf - Configuration: TrainConfig
            # INFO - pydraconf - Variant: QuickTest
            # INFO - pydraconf - Applied Overrides:
            # INFO - pydraconf -   - variant: QuickTest
            # INFO - pydraconf -   - model=ViTConfig
            # INFO - pydraconf -   - epochs=50
            ```
        """
        log_fn = getattr(logger, level.lower())
        metadata = self.get_metadata()

        log_fn(f"Configuration: {metadata.get('config_name', 'Unknown')}")

        if metadata.get("variant_name"):
            log_fn(f"Variant: {metadata['variant_name']}")

        overrides = self.get_overrides_summary()
        if overrides:
            log_fn("Applied Overrides:")
            for override in overrides:
                log_fn(f"  - {override}")
        else:
            log_fn("No overrides applied (using defaults)")

        if metadata.get("config_dirs"):
            log_fn(f"Config directories: {', '.join(metadata['config_dirs'])}")

        log_fn(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
