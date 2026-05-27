"""Python adapter implementing the Adapter ABC using existing parsers."""

from __future__ import annotations

from pathlib import Path

from uml_planterator import parsers
from uml_planterator.adapters.base import Adapter


class PythonAdapter(Adapter):
    """Adapter that parses Python source into ModuleInfo objects."""

    @property
    def language(self) -> str:
        return "python"

    def supported_extensions(self) -> list[str]:
        return [".py"]

    def parse_source(self, path: Path, source: str):
        return parsers.parse_module_from_source(path, source, path.parent)

    def compute_complexity(self, module):
        return int(getattr(module, "cc", 1))
