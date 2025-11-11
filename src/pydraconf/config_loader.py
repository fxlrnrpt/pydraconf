"""Configuration file loader for PydraConf settings."""

import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


def find_root_dir(start_path: Path) -> Path | None:
    """Find project root directory containing pyproject.toml or .pydraconfrc.

    Args:
        start_path: Starting directory for search

    Returns:
        Path to root directory or None if not found
    """
    current = start_path.resolve()
    while True:
        # Check for project markers
        if (current / "pyproject.toml").exists() or (current / ".pydraconfrc").exists():
            return current

        # Move up one directory
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None


def substitute_variables(path_str: str, cwd: Path, root: Path | None) -> str:
    """Substitute variables in path string.

    Supported variables:
    - $CWD: Current working directory
    - $ROOT: Project root (directory with pyproject.toml or .pydraconfrc)

    Relative paths without variables are treated as relative to the script directory.

    Args:
        path_str: Path string potentially containing variables
        cwd: Current working directory
        root: Project root directory (or None)

    Returns:
        Path with variables substituted
    """
    result = path_str
    result = result.replace("$CWD", str(cwd))
    if root:
        result = result.replace("$ROOT", str(root))
    return result


def load_config_dirs(start_path: Path | None = None) -> list[str] | None:
    """Load config_dirs setting from configuration files.

    Searches for configuration in this order:
    1. .pydraconfrc (JSON) in current directory or parent directories
    2. pyproject.toml [tool.pydraconf] section
    3. Returns None if not found

    Supports variable substitution: $CWD, $ROOT
    Relative paths (without variables) are treated as relative to the script.

    Args:
        start_path: Starting directory for search (defaults to current directory)

    Returns:
        List of config_dir paths or None if not found

    Example pyproject.toml:
        [tool.pydraconf]
        config_dirs = ["$ROOT/configs", "$CWD/configs", "configs"]

    Example .pydraconfrc:
        {
            "config_dirs": ["$ROOT/configs", "$CWD/configs", "configs"]
        }
    """
    if start_path is None:
        start_path = Path.cwd()

    # Search up the directory tree
    current = start_path.resolve()
    while True:
        # Try .pydraconfrc (JSON)
        rc_file = current / ".pydraconfrc"
        if rc_file.exists():
            try:
                with open(rc_file) as f:
                    data = json.load(f)
                    if "config_dirs" in data:
                        dirs = data["config_dirs"]
                        if isinstance(dirs, str):
                            return [dirs]
                        return list(dirs)
            except (json.JSONDecodeError, KeyError):
                pass

        # Try pyproject.toml
        pyproject = current / "pyproject.toml"
        pydraconf_config = None
        if pyproject.exists():
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "pydraconf" in data["tool"]:
                        pydraconf_config = data["tool"]["pydraconf"]
                        if "config_dirs" in pydraconf_config:
                            dirs = pydraconf_config["config_dirs"]
                            if isinstance(dirs, str):
                                return [dirs]
                            return list(dirs)
            except (tomllib.TOMLDecodeError, KeyError):
                pass

        if pydraconf_config or rc_file.exists():
            break

        # Move up one directory
        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return None
