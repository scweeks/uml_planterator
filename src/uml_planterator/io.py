"""File I/O helpers for writing .puml files."""

from __future__ import annotations

from pathlib import Path


def write_puml(content: str, path: Path, verbose: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if verbose:
        print(f"  wrote: {path}")
