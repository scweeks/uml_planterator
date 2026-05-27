"""Orchestrator that parses sources and renders PlantUML files.

This class is intentionally small and testable. It delegates parsing to
`parsers`, rendering to `renderers`, and file I/O to `io`.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List

from uml_planterator import io as io_mod
from uml_planterator import models, registry, renderers
from uml_planterator.adapters.base import AdapterError


class PUMLGenerator:
    def __init__(self, src_root: Path, out_root: Path, verbose: bool = False):
        self.src_root = Path(src_root)
        self.out_root = Path(out_root)
        self.verbose = verbose
        # `writer` is any object with a `write_puml(content, path, verbose)`
        # method. It defaults to the module-level `io.write_puml` helper.
        self.writer = None

    def _discover_and_parse(self) -> list[tuple[models.ModuleInfo, object]]:
        """Discover source files and parse them with registered adapters.

        Returns a list of (ModuleInfo, adapter) tuples.
        """
        all_modules: list[tuple[models.ModuleInfo, object]] = []
        seen = set()
        for adapter in registry.get_all_adapters():
            for ext in adapter.supported_extensions():
                for p in sorted(self.src_root.rglob(f"*{ext}")):
                    if p in seen:
                        continue
                    seen.add(p)
                    src = p.read_text(encoding="utf-8", errors="replace")
                    try:
                        mod = adapter.parse_source(p, src)
                    except AdapterError:
                        mod = None
                    if mod:
                        all_modules.append((mod, adapter))
        return all_modules

    def _filter_content_modules(
        self, all_modules: list[tuple[models.ModuleInfo, object]]
    ) -> list[tuple[models.ModuleInfo, object]]:
        return [(m, a) for (m, a) in all_modules if m.classes or m.top_level_functions]

    def _writer(self):
        # Return the writer object to use; module `io` has `write_puml`.
        return self.writer if self.writer is not None else io_mod

    def _maybe_write(self, content: str, path: Path, dry_run: bool) -> None:
        if dry_run:
            return
        self._writer().write_puml(content, path, self.verbose)

    def run(self, dry_run: bool = False) -> Dict:  # noqa: C901
        all_modules = self._discover_and_parse()
        content_mods = self._filter_content_modules(all_modules)

        counts: DefaultDict[str, int] = defaultdict(int)
        written: List[Path] = []

        # Class diagrams
        for module, adapter in content_mods:
            rel_dir = Path(module.rel_path).parent
            mod_base = self.out_root / rel_dir / module.name
            for cls in module.classes:
                content = renderers.gen_class_diagram(cls, module)
                p = mod_base / "Class" / f"{module.name}-{cls.name}.puml"
                counts["class"] += 1
                if dry_run:
                    written.append(p)
                else:
                    self._maybe_write(content, p, dry_run)

                # If complexity is high, produce a complexity sub-diagram.
                try:
                    cc = int(adapter.compute_complexity(module))
                except (ValueError, TypeError, AttributeError):
                    cc = int(getattr(module, "cc", 1))
                if cc >= 10:
                    c_content = (
                        f"@startuml {module.name}-{cls.name}-complexity\n"
                        f"title Complexity for {cls.name} (cc={cc})\n\n@enduml"
                    )
                    cp = (
                        mod_base
                        / "Complexity"
                        / f"{module.name}-{cls.name}-complexity.puml"
                    )
                    counts["complexity"] += 1
                    if dry_run:
                        written.append(cp)
                    else:
                        self._maybe_write(c_content, cp, dry_run)

        # Package diagram per directory
        pkg_groups: Dict[str, List[models.ModuleInfo]] = {}
        for mod, _ in content_mods:
            key = str(Path(mod.rel_path).parent)
            pkg_groups.setdefault(key, []).append(mod)

        for dir_key, pkg_mods in sorted(pkg_groups.items()):
            pkg_name = dir_key.replace("/", ".")
            pkg_name = pkg_name.replace("\\", ".")
            pkg_name = pkg_name.strip(".") or "root"
            content = renderers.gen_package_diagram(
                pkg_mods, pkg_name, self.src_root.name
            )
            p = self.out_root / dir_key / "Package" / (f"{pkg_name}-package.puml")
            counts["package"] += 1
            if dry_run:
                written.append(p)
            else:
                self._maybe_write(content, p, dry_run)

        # System-level package overview
        content = renderers.gen_system_package_diagram(
            [m for (m, _) in all_modules], self.src_root.name
        )
        p = self.out_root / "Package" / "system-package-overview.puml"
        counts["package"] += 1
        if dry_run:
            written.append(p)
        else:
            self._maybe_write(content, p, dry_run)

        return {"counts": dict(counts), "paths": [str(p) for p in written]}
