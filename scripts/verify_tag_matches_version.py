#!/usr/bin/env python3
"""Ensure a git tag matches the version declared in pyproject.toml."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:  # pragma: no cover
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "tomllib/tomli is required to parse pyproject.toml"
        ) from exc


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"


def load_project_version() -> str:
    content = PYPROJECT.read_bytes()
    data = tomllib.loads(content.decode("utf-8"))
    return data["project"]["version"]


def requested_tag(argv: list[str]) -> str | None:
    if len(argv) > 1:
        return argv[1]
    return os.environ.get("GITHUB_REF_NAME") or os.environ.get("GITHUB_REF")


def normalize_tag(tag: str) -> str:
    tag = tag.strip()
    if tag.startswith("refs/tags/"):
        tag = tag.removeprefix("refs/tags/")
    return tag[1:] if tag.startswith("v") else tag


def main(argv: list[str]) -> int:
    raw_tag = requested_tag(argv)
    if not raw_tag:
        print("No tag provided. Pass it as an argument or via GITHUB_REF_NAME.")
        return 1

    version = load_project_version()
    normalized_tag = normalize_tag(raw_tag)

    if normalized_tag != version:
        print(
            f"Tag mismatch: normalized tag '{normalized_tag}' does not equal "
            f"pyproject version '{version}'."
        )
        return 1

    print(f"Tag '{raw_tag}' matches project version {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
