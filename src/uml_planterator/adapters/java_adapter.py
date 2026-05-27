"""Minimal Java adapter using regex-based extraction.

Lightweight starter adapter to enable Java support for tests. Replace with
Tree-sitter or LSP-based adapter for production-grade parsing.
"""

from __future__ import annotations

import re
from pathlib import Path

from uml_planterator import models
from uml_planterator.adapters.base import Adapter


class JavaAdapter(Adapter):
    CLASS_RE = re.compile(r"\b(class|interface)\s+(\w+)\b")

    @property
    def language(self) -> str:
        return "java"

    def supported_extensions(self) -> list[str]:
        return [".java"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo:
        module_name = path.stem
        rel = str(path.relative_to(path.parent))
        classes = []
        for m in self.CLASS_RE.finditer(source):
            cname = m.group(2)
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

    def compute_complexity(self, module: models.ModuleInfo) -> int:
        return int(getattr(module, "cc", 1))
