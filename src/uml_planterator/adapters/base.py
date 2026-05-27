"""Adapter ABC for language-specific parsers.

Adapters translate (path, source) -> models.ModuleInfo and must be pure
and testable. Implementations should not perform I/O beyond using the
provided `source` string.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from uml_planterator import models


class AdapterError(RuntimeError):
    """Adapter-specific errors raised by adapters."""


class Adapter(ABC):
    """Abstract adapter interface for language parsers.

    Concrete adapters must at minimum implement `language`,
    `supported_extensions()` and `parse_source(...)`.
    """

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language identifier this adapter supports.

        Example: 'python', 'cpp', 'java'
        """

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return a list of file extensions this adapter handles.

        Example: ['.py']
        """

    @abstractmethod
    def parse_source(self, path: Path, source: str) -> models.ModuleInfo:
        """Parse `source` and return a `ModuleInfo`.

        Implementations must be pure and side-effect free. On failure
        implementations should raise `AdapterError` rather than return
        None to make error handling explicit and easier to test.
        """

    def parse_ast(self, path: Path, node) -> models.ModuleInfo | None:
        """Optional fast-path: parse from an AST node. Default raises
        AdapterError to indicate optional support.
        """
        raise AdapterError("parse_ast not implemented for this adapter")

    def compute_complexity(self, module: models.ModuleInfo) -> int:
        """Optional language-specific complexity calculation.

        Default falls back to `module.cc` if present.
        """
        return int(getattr(module, "cc", 1))
