"""Utility helpers used across the package."""

from __future__ import annotations

import ast
import re

# Module-level id map for deterministic safe ids during a run.
_id_map: dict[str, str] = {}


def safe_id(name: str) -> str:
    """Return a PlantUML-safe deterministic identifier for `name`.

    Keeps letters, digits and underscores; prefixes leading digits. Collisions
    are resolved by appending numeric suffixes. Deterministic within a run.
    """
    if name in _id_map:
        return _id_map[name]

    base = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    if not base:
        base = "id"
    if base[0].isdigit():
        base = f"id_{base}"

    alias = base
    i = 1
    existing = set(_id_map.values())
    while alias in existing:
        i += 1
        alias = f"{base}_{i}"

    _id_map[name] = alias
    return alias


def up(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def vis(name: str) -> str:
    """UML visibility from Python naming conventions.

    - names starting with "__" (but not ending with "__") are private
    - names starting with "_" are protected
    - otherwise public
    """
    if name.startswith("__") and not name.endswith("__"):
        return "-"
    if name.startswith("_"):
        return "#"
    return "+"


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def reset_id_map() -> None:
    """Clear the id map between generator runs to prevent cross-run pollution."""
    _id_map.clear()
