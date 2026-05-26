"""Render PlantUML diagrams from models."""
from __future__ import annotations

from typing import Iterable

from uml_planterator import models, utils


def gen_class_diagram(cls: models.ClassInfo, module: models.ModuleInfo) -> str:
    name = f"{module.name}-{cls.name}"
    title = f"{cls.name} — src/{module.rel_path}"
    lines = [f"@startuml {name}", f"title {title}", "", ]

    alias = utils.safe_id(f"{module.name}_{cls.name}")
    lines.append(f'class "{cls.name}" as {alias} {{')

    for a in cls.attributes:
        t = f" : {a.type_hint}" if a.type_hint else ""
        lines.append(f"  {a.visibility} {a.name}{t}")

    for m in cls.methods:
        params = ", ".join(str(p) for p in m.params)
        ret = f" : {m.return_type}" if m.return_type else ""
        lines.append(f"  {m.visibility} {m.name}({params}){ret}")

    lines.append("}")
    if cls.docstring:
        first = cls.docstring.split("\n")[0][:100]
        lines.append(f"note bottom of {alias}")
        lines.append(f"  {first}")
        lines.append("end note")

    lines.append("@enduml")
    return "\n".join(lines)


def gen_package_diagram(modules: Iterable[models.ModuleInfo], pkg_name: str,
                        src_name: str = "src") -> str:
    name = f"{pkg_name}-package"
    title = f"{pkg_name} — {src_name}/{pkg_name}/"
    lines = [f"@startuml {name}", f"title {title}", "", ]

    lines.append(f"package {pkg_name} {{")
    for mod in modules:
        if mod.is_init:
            continue
        if mod.classes:
            lines.append(f"  package {mod.name} {{")
            for cls in mod.classes:
                stereo = " <<abstract>>" if cls.is_abstract else ""
                lines.append(f"    class {cls.name}{stereo}")
            lines.append("  }")
    lines.append("}")
    lines.append("@enduml")
    return "\n".join(lines)


def gen_system_package_diagram(
    all_modules: Iterable[models.ModuleInfo], src_name: str = "src"
) -> str:
    name = "system-package-overview"
    title = f"System Package Overview — {src_name}/"
    lines = [f"@startuml {name}", f"title {title}", "", ]

    top_pkgs = {}
    for m in all_modules:
        top = m.package.split(".")[0]
        top_pkgs.setdefault(top, []).append(m)

    for pkg in sorted(top_pkgs):
        lines.append(f"component [{pkg}] as {pkg}")

    lines.append("@enduml")
    return "\n".join(lines)
