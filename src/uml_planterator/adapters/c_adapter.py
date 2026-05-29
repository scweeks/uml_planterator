"""Minimal C adapter using regex to extract typedef'd structs as classes."""

from __future__ import annotations

import re
from pathlib import Path

from uml_planterator import models
from uml_planterator.adapters.base import Adapter


class CAdapter(Adapter):
    STRUCT_RE = re.compile(r"typedef\s+struct\s+(\w+)\s*\{")

    @property
    def language(self) -> str:
        return "c"

    def supported_extensions(self) -> list[str]:
        return [".c", ".h"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo:
        module_name = path.stem
        rel = str(path.relative_to(path.parent))
        classes = []
        for m in self.STRUCT_RE.finditer(source):
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
