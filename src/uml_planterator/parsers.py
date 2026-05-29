"""AST parsing helpers that return `models` objects.

These functions avoid file I/O: callers provide source text or AST nodes.
"""

from __future__ import annotations

import ast
from pathlib import Path

from uml_planterator import complexity, models, utils


def extract_calls(func: ast.FunctionDef) -> list[tuple]:
    calls = []
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                obj = f.value.id
                if obj not in ("self", "cls"):
                    calls.append((obj, f.attr))
    return calls


def extract_raises(func: ast.FunctionDef) -> list[str]:
    raises = []
    for node in ast.walk(func):
        if isinstance(node, ast.Raise) and node.exc:
            raises.append(utils.up(node.exc).split("(")[0])
    return list(dict.fromkeys(raises))


def extract_state_transitions(func: ast.FunctionDef) -> list[tuple]:
    state_kws = ("state", "status", "phase", "mode", "stage")
    transitions = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                    and any(kw in target.attr.lower() for kw in state_kws)
                ):
                    val = utils.up(node.value).strip("\"'")
                    transitions.append((target.attr, val, func.name))
    return transitions


def extract_self_attrs(init: ast.FunctionDef) -> list[str]:
    attrs = []
    for node in ast.walk(init):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attrs.append(target.attr)
    return attrs


def parse_method(func: ast.FunctionDef) -> models.MethodInfo:
    decorators = [utils.up(d) for d in func.decorator_list]
    args = func.args.args
    start = 1 if args and args[0].arg in ("self", "cls") else 0
    params = [models.Param(a.arg, utils.up(a.annotation)) for a in args[start:]]
    return models.MethodInfo(
        name=func.name,
        params=params,
        return_type=utils.up(func.returns),
        visibility=utils.vis(func.name),
        is_static="staticmethod" in decorators,
        is_class_method="classmethod" in decorators,
        is_property=any("property" in d for d in decorators),
        is_abstract=any("abstractmethod" in d for d in decorators),
        cc=complexity.cyclomatic_complexity(func),
        calls=extract_calls(func),
        raises=extract_raises(func),
        state_transitions=extract_state_transitions(func),
        docstring=ast.get_docstring(func) or "",
        lineno=func.lineno,
        line_count=(getattr(func, "end_lineno", func.lineno) - func.lineno),
    )


def parse_class(cls: ast.ClassDef) -> models.ClassInfo:  # noqa: C901
    bases = [utils.up(b) for b in cls.bases]
    decorators = [utils.up(d) for d in cls.decorator_list]
    is_abstract = any("ABC" in b or "Abstract" in b for b in bases) or (
        any("abstractmethod" in d for d in decorators)
    )
    is_dc = any("dataclass" in d for d in decorators)

    attributes = []
    methods = []
    state_attrs = []
    state_kws = ("state", "status", "phase", "mode", "stage")

    for item in cls.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            n = item.target.id
            attributes.append(
                models.AttributeInfo(
                    name=n,
                    type_hint=utils.up(item.annotation),
                    visibility=utils.vis(n),
                    is_class_var=True,
                )
            )
        elif isinstance(item, ast.FunctionDef):
            m = parse_method(item)
            methods.append(m)
            if item.name == "__init__":
                for attr_name in extract_self_attrs(item):
                    if not any(a.name == attr_name for a in attributes):
                        attributes.append(
                            models.AttributeInfo(
                                name=attr_name,
                                type_hint="",
                                visibility=utils.vis(attr_name),
                            )
                        )
                    if any(kw in attr_name.lower() for kw in state_kws):
                        if attr_name not in state_attrs:
                            state_attrs.append(attr_name)

    for m in methods:
        for attr, _, _ in m.state_transitions:
            if attr not in state_attrs:
                state_attrs.append(attr)

    has_state = bool(state_attrs) and any(m.state_transitions for m in methods)
    cc = max(1, sum(m.cc for m in methods))

    return models.ClassInfo(
        name=cls.name,
        bases=bases,
        attributes=attributes,
        methods=methods,
        decorators=decorators,
        docstring=ast.get_docstring(cls) or "",
        is_abstract=is_abstract,
        is_dataclass=is_dc,
        has_state=has_state,
        state_attributes=state_attrs,
        cc=cc,
    )


def parse_module_from_source(  # noqa: C901
    py_file: Path, source: str, src_root: Path
) -> models.ModuleInfo | None:
    try:
        tree = ast.parse(source, filename=str(py_file))
    except SyntaxError:
        return None

    rel = py_file.relative_to(src_root)
    parts = list(rel.with_suffix("").parts)
    is_init = parts[-1] == "__init__"
    if is_init:
        parts = parts[:-1]
    package = ".".join(parts) if parts else py_file.stem
    module_name = parts[-1] if parts else py_file.stem

    ext_imports, int_imports = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                ext_imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if node.level > 0 or top in ("src", "core", "bean_vulnerable"):
                    int_imports.append(node.module)
                else:
                    ext_imports.append(top)

    public_exports = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                public_exports.append(str(elt.value))

    classes, top_fns = [], []
    has_main = False
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(parse_class(node))
        elif isinstance(node, ast.FunctionDef):
            top_fns.append(parse_method(node))
            if node.name == "main":
                has_main = True
        elif isinstance(node, ast.If):
            if "__main__" in utils.up(node.test):
                has_main = True

    cli_kws = ("argparse", "click", "typer", "fire", "docopt")
    has_cli = any(kw in ext_imports for kw in cli_kws)

    return models.ModuleInfo(
        name=module_name,
        package=package,
        rel_path=str(rel),
        classes=classes,
        top_level_functions=top_fns,
        imports=sorted(set(ext_imports)),
        internal_imports=sorted(set(int_imports)),
        has_main=has_main,
        has_cli=has_cli,
        is_init=is_init,
        public_exports=public_exports,
        cc=complexity.cyclomatic_complexity(tree),
    )
