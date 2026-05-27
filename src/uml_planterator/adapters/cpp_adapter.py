"""Minimal C++ adapter (best-effort) using regex-based extraction.

This is intentionally a lightweight implementation to provide basic
class/function discovery for C++ files. For full language support we
recommend a Tree-sitter or LSP-based adapter later.
"""

from __future__ import annotations

import re
from pathlib import Path

from uml_planterator import models
from uml_planterator.adapters.base import Adapter


class CppAdapter(Adapter):
    """Best-effort C++ adapter extracting class names via regex."""

    CLASS_RE = re.compile(r"\bclass\s+(\w+)\b")

    @property
    def language(self) -> str:
        return "cpp"

    def supported_extensions(self) -> list[str]:
        return [".cpp", ".hpp", ".cc", ".h"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo | None:
        module_name = path.stem
        rel = str(path.relative_to(path.parent))
        classes = []
        for m in self.CLASS_RE.finditer(source):
            cname = m.group(1)
            classes.append(models.ClassInfo(name=cname))

        return models.ModuleInfo(
            name=module_name,
            package=path.parent.name,
            rel_path=rel,
            classes=classes,
            top_level_functions=[],
            imports=[],
            internal_imports=[],
            has_main=False,
            has_cli=False,
            is_init=False,
            public_exports=[],
            cc=1,
        )

    def compute_complexity(self, module):
        return int(getattr(module, "cc", 1))
