"""Java adapter using `javalang` when available, with a regex fallback.

This adapter attempts to use the `javalang` parser for accurate AST
information. If `javalang` is not installed, it falls back to the
lightweight regex-based `JavaAdapter` to preserve testability and
developer experience in minimal environments.
"""

from __future__ import annotations

from pathlib import Path

from uml_planterator import models
from uml_planterator.adapters.base import Adapter

_BRANCH_NODES = frozenset(
    (
        "IfStatement",
        "ForStatement",
        "WhileStatement",
        "DoStatement",
        "SwitchStatement",
        "CatchClause",
        "TernaryExpression",
    )
)


def _count_branches(node) -> int:
    """Recursively count branching constructs in a javalang AST node."""
    if node is None:
        return 0
    total = 1 if type(node).__name__ in _BRANCH_NODES else 0
    for child in getattr(node, "children", []) or []:
        if isinstance(child, (list, tuple)):
            for c in child:
                total += _count_branches(c)
        else:
            total += _count_branches(child)
    return total


class JavaJavalangAdapter(Adapter):
    @property
    def language(self) -> str:
        return "java"

    def supported_extensions(self) -> list[str]:
        return [".java"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo:
        try:
            import javalang
        except ImportError:
            # Defer to the simple regex adapter if javalang isn't present.
            from uml_planterator.adapters.java_adapter import JavaAdapter

            return JavaAdapter().parse_source(path, source)

        tree = javalang.parse.parse(source)
        module_name = path.stem
        package = ""
        if getattr(tree, "package", None):
            pkg = getattr(tree.package, "name", "")
            package = pkg.split(".")[-1] if pkg else path.parent.name

        classes: list[models.ClassInfo] = []
        for type_decl in getattr(tree, "types", []) or []:
            name = getattr(type_decl, "name", "<anon>")
            attributes: list[models.AttributeInfo] = []
            methods: list[models.MethodInfo] = []

            # fields
            for field in getattr(type_decl, "fields", []) or []:
                mods = set(getattr(field, "modifiers", []) or [])
                if "public" in mods:
                    visibility = "+"
                elif "private" in mods:
                    visibility = "-"
                elif "protected" in mods:
                    visibility = "#"
                else:
                    visibility = "~"

                ftype = ""
                if getattr(field, "type", None):
                    try:
                        ftype = getattr(field.type, "name", "")
                    except AttributeError:
                        ftype = ""

                for decl in getattr(field, "declarators", []) or []:
                    fname = getattr(decl, "name", "")
                    attr = models.AttributeInfo(
                        name=fname, type_hint=ftype, visibility=visibility
                    )
                    attributes.append(attr)

            # methods
            for m in getattr(type_decl, "methods", []) or []:
                mmods = set(getattr(m, "modifiers", []) or [])
                if "public" in mmods:
                    visibility = "+"
                elif "private" in mmods:
                    visibility = "-"
                elif "protected" in mmods:
                    visibility = "#"
                else:
                    visibility = "~"

                params: list[models.Param] = []
                for p in getattr(m, "parameters", []) or []:
                    pname = getattr(p, "name", "")
                    ptype = ""
                    if getattr(p, "type", None):
                        try:
                            ptype = getattr(p.type, "name", "")
                        except AttributeError:
                            ptype = ""
                    params.append(models.Param(name=pname, type_hint=ptype))

                # Determine return type and modifiers
                return_type = ""
                if getattr(m, "return_type", None):
                    try:
                        return_type = getattr(m.return_type, "name", "")
                    except AttributeError:
                        return_type = ""

                is_static = "static" in mmods
                is_abstract = "abstract" in mmods

                # Compute a simple cyclomatic complexity by counting branches.
                cc = 1 + _count_branches(m)

                meth = models.MethodInfo(
                    name=getattr(m, "name", "<anon>"),
                    params=params,
                    return_type=return_type,
                    visibility=visibility,
                    is_static=is_static,
                    is_class_method=False,
                    is_property=False,
                    is_abstract=is_abstract,
                    cc=cc,
                )
                methods.append(meth)

            cls = models.ClassInfo(name=name, attributes=attributes, methods=methods)
            classes.append(cls)

        return models.ModuleInfo(
            name=module_name,
            package=package or path.parent.name,
            rel_path=str(path.relative_to(path.parent)),
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
        # Conservative heuristic: sum method CCs (each at least 1)
        total = 0
        for cls in module.classes:
            for m in cls.methods:
                total += max(1, getattr(m, "cc", 1))
        return max(1, total)
