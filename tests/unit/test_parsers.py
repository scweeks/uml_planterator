"""Tests for parsers.py — 100% line and branch coverage."""

import ast
from pathlib import Path

from uml_planterator import parsers
from uml_planterator.parsers import parse_module_from_source

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _func(src: str) -> ast.FunctionDef:
    tree = ast.parse(src)
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))


def _class(src: str) -> ast.ClassDef:
    tree = ast.parse(src)
    return next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))


# ---------------------------------------------------------------------------
# extract_calls
# ---------------------------------------------------------------------------


def test_extract_calls_returns_obj_method_pairs():
    fn = _func("def f():\n" "    service.process()\n" "    repo.save()\n")
    calls = parsers.extract_calls(fn)
    assert ("service", "process") in calls
    assert ("repo", "save") in calls


def test_extract_calls_ignores_self_calls():
    fn = _func("def f(self):\n" "    self.update()\n")
    calls = parsers.extract_calls(fn)
    assert calls == []


def test_extract_calls_ignores_cls_calls():
    fn = _func("def f(cls):\n" "    cls.create()\n")
    calls = parsers.extract_calls(fn)
    assert calls == []


def test_extract_calls_ignores_non_attribute_calls():
    fn = _func("def f():\n" "    print('hi')\n")
    calls = parsers.extract_calls(fn)
    assert calls == []


# ---------------------------------------------------------------------------
# extract_raises
# ---------------------------------------------------------------------------


def test_extract_raises_captures_exception_names():
    fn = _func(
        "def f():\n" "    raise ValueError('bad')\n" "    raise TypeError('worse')\n"
    )
    raises = parsers.extract_raises(fn)
    assert "ValueError" in raises
    assert "TypeError" in raises


def test_extract_raises_deduplicates():
    fn = _func(
        "def f(x):\n"
        "    if x:\n"
        "        raise ValueError('a')\n"
        "    raise ValueError('b')\n"
    )
    raises = parsers.extract_raises(fn)
    assert raises.count("ValueError") == 1


def test_extract_raises_empty_when_no_raises():
    fn = _func("def f():\n    return 1\n")
    assert parsers.extract_raises(fn) == []


# ---------------------------------------------------------------------------
# extract_state_transitions
# ---------------------------------------------------------------------------


def test_extract_state_transitions_captures_self_state_assign():
    fn = _func("def process(self):\n" "    self.state = 'active'\n")
    transitions = parsers.extract_state_transitions(fn)
    assert len(transitions) == 1
    attr, val, method = transitions[0]
    assert attr == "state"
    assert val == "active"
    assert method == "process"


def test_extract_state_transitions_captures_status_keyword():
    fn = _func("def run(self):\n" "    self.status = 'running'\n")
    transitions = parsers.extract_state_transitions(fn)
    assert any(t[0] == "status" for t in transitions)


def test_extract_state_transitions_ignores_non_state_attrs():
    fn = _func("def init(self):\n" "    self.name = 'Bob'\n")
    transitions = parsers.extract_state_transitions(fn)
    assert transitions == []


def test_extract_state_transitions_ignores_non_self_assigns():
    fn = _func("def init(self):\n" "    other.state = 'x'\n")
    transitions = parsers.extract_state_transitions(fn)
    assert transitions == []


# ---------------------------------------------------------------------------
# extract_self_attrs
# ---------------------------------------------------------------------------


def test_extract_self_attrs_finds_init_assignments():
    fn = _func("def __init__(self, x, y):\n" "    self.x = x\n" "    self.y = y\n")
    attrs = parsers.extract_self_attrs(fn)
    assert "x" in attrs
    assert "y" in attrs


def test_extract_self_attrs_ignores_non_self_assigns():
    fn = _func("def __init__(self):\n" "    other.x = 1\n")
    attrs = parsers.extract_self_attrs(fn)
    assert attrs == []


def test_extract_self_attrs_empty_init():
    fn = _func("def __init__(self):\n    pass\n")
    assert parsers.extract_self_attrs(fn) == []


# ---------------------------------------------------------------------------
# parse_method
# ---------------------------------------------------------------------------


def test_parse_method_basic():
    fn = _func("def compute(self, x: int) -> str:\n    return str(x)\n")
    m = parsers.parse_method(fn)
    assert m.name == "compute"
    assert m.return_type == "str"
    assert any(p.name == "x" for p in m.params)


def test_parse_method_static():
    fn = _func("@staticmethod\ndef helper():\n    pass\n")
    m = parsers.parse_method(fn)
    assert m.is_static is True


def test_parse_method_classmethod():
    fn = _func("@classmethod\ndef create(cls):\n    pass\n")
    m = parsers.parse_method(fn)
    assert m.is_class_method is True


def test_parse_method_property():
    fn = _func("@property\ndef value(self):\n    return self._v\n")
    m = parsers.parse_method(fn)
    assert m.is_property is True


def test_parse_method_abstract():
    fn = _func(
        "from abc import abstractmethod\n"
        "@abstractmethod\n"
        "def run(self):\n"
        "    pass\n"
    )
    m = parsers.parse_method(fn)
    assert m.is_abstract is True


def test_parse_method_private_visibility():
    fn = _func("def __secret(self):\n    pass\n")
    m = parsers.parse_method(fn)
    assert m.visibility == "-"


def test_parse_method_no_self_params_counted():
    fn = _func("def top(a: int, b: str) -> None:\n    pass\n")
    m = parsers.parse_method(fn)
    assert len(m.params) == 2


# ---------------------------------------------------------------------------
# parse_class
# ---------------------------------------------------------------------------


def test_parse_class_annotated_attribute():
    cls = _class("class Foo:\n    count: int\n")
    ci = parsers.parse_class(cls)
    assert any(a.name == "count" and a.type_hint == "int" for a in ci.attributes)


def test_parse_class_instance_attr_from_init():
    cls = _class("class Foo:\n" "    def __init__(self):\n" "        self.name = 'x'\n")
    ci = parsers.parse_class(cls)
    assert any(a.name == "name" for a in ci.attributes)


def test_parse_class_state_attr_in_init_detected():
    cls = _class(
        "class Foo:\n" "    def __init__(self):\n" "        self.state = 'idle'\n"
    )
    ci = parsers.parse_class(cls)
    assert "state" in ci.state_attributes


def test_parse_class_state_attr_not_duplicated():
    cls = _class(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.state = 'idle'\n"
        "    def go(self):\n"
        "        self.state = 'running'\n"
    )
    ci = parsers.parse_class(cls)
    assert ci.state_attributes.count("state") == 1


def test_parse_class_is_abstract_from_abc_base():
    cls = _class("class Foo(ABC):\n    pass\n")
    ci = parsers.parse_class(cls)
    assert ci.is_abstract is True


def test_parse_class_is_dataclass():
    cls = _class("@dataclass\nclass Foo:\n    x: int\n")
    ci = parsers.parse_class(cls)
    assert ci.is_dataclass is True


def test_parse_class_has_state_false_when_no_state_attrs():
    # class with no state keyword attributes and no transitions → has_state=False
    cls = _class(
        "class Foo:\n" "    def __init__(self):\n" "        self.name = 'bob'\n"
    )
    ci = parsers.parse_class(cls)
    assert ci.has_state is False


def test_parse_class_has_state_true_with_transitions():
    cls = _class(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.state = 'idle'\n"
        "    def run(self):\n"
        "        self.state = 'active'\n"
    )
    ci = parsers.parse_class(cls)
    assert ci.has_state is True


def test_parse_class_init_attr_not_duplicated_when_annotated():
    cls = _class(
        "class Foo:\n" "    x: int\n" "    def __init__(self):\n" "        self.x = 0\n"
    )
    ci = parsers.parse_class(cls)
    x_attrs = [a for a in ci.attributes if a.name == "x"]
    assert len(x_attrs) == 1


def test_parse_class_cc_is_sum_of_method_cc():
    cls = _class(
        "class Foo:\n"
        "    def a(self):\n"
        "        if True:\n"
        "            pass\n"
        "    def b(self):\n"
        "        pass\n"
    )
    ci = parsers.parse_class(cls)
    assert ci.cc >= 2


# ---------------------------------------------------------------------------
# parse_module_from_source
# ---------------------------------------------------------------------------


def test_parse_method_and_class():
    src = """
class Foo:
    x: int

    def __init__(self, v):
        self.x = v

    def incr(self):
        self.x += 1
"""
    tree = ast.parse(src)
    cls_node = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    ci = parsers.parse_class(cls_node)
    assert ci.name == "Foo"
    assert any(m.name == "incr" for m in ci.methods)
    assert any(a.name == "x" for a in ci.attributes)


def test_parse_module_from_source_basic():
    src = "def main():\n    return 0\n"
    p = Path("pkg/mod.py")
    mi = parse_module_from_source(p, src, Path("pkg"))
    assert mi is not None
    assert mi.name == "mod"


def test_parse_module_syntax_error_returns_none(tmp_path):
    f = tmp_path / "bad.py"
    mi = parse_module_from_source(f, "def (:\n    pass\n", tmp_path)
    assert mi is None


def test_parse_module_external_import_classified(tmp_path):
    src = "import os\nimport sys\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert "os" in mi.imports
    assert "sys" in mi.imports


def test_parse_module_bare_relative_import_no_module_name(tmp_path):
    # from . import helper has node.module=None — parser skips it safely
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    f = pkg / "mod.py"
    src = "from . import helper\n"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi is not None
    assert mi.internal_imports == []


def test_parse_module_from_import_with_module_name(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    f = pkg / "mod.py"
    src = "from .sub import helper\n"
    mi = parse_module_from_source(f, src, tmp_path)
    assert any("sub" in i for i in mi.internal_imports)


def test_parse_module_all_export_detected(tmp_path):
    src = '__all__ = ["Foo", "Bar"]\n'
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert "Foo" in mi.public_exports
    assert "Bar" in mi.public_exports


def test_parse_module_has_main_from_function(tmp_path):
    src = "def main():\n    pass\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_main is True


def test_parse_module_has_main_from_dunder_main_guard(tmp_path):
    src = "if __name__ == '__main__':\n    pass\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_main is True


def test_parse_module_has_cli_detected(tmp_path):
    src = "import argparse\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_cli is True


def test_parse_module_has_cli_false_when_no_cli_import(tmp_path):
    src = "import os\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_cli is False


def test_parse_module_is_init_from_init_file(tmp_path):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    f = pkg / "__init__.py"
    src = ""
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.is_init is True
    assert mi.name == "pkg"


def test_parse_class_state_attr_added_by_method_not_init(tmp_path):
    # method adds a state attr that was NOT in __init__ → state_attrs grows via transitions loop
    cls = _class(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.name = 'x'\n"
        "    def run(self):\n"
        "        self.phase = 'active'\n"
    )
    ci = parsers.parse_class(cls)
    assert "phase" in ci.state_attributes
    assert ci.has_state is True


def test_parse_module_from_external_from_import(tmp_path):
    # from os import path → classified as external, not internal
    src = "from os import path\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert "os" in mi.imports
    assert mi.internal_imports == []


def test_parse_module_non_all_assignment_ignored(tmp_path):
    # top-level assignment that is not __all__ — should not crash
    src = "X = 42\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi is not None
    assert mi.public_exports == []


def test_parse_module_if_not_main_guard(tmp_path):
    # if statement that is NOT __main__ guard — has_main stays False
    src = "if True:\n    pass\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_main is False


def test_parse_module_top_level_function_not_named_main(tmp_path):
    # top-level function that is not named "main" — has_main stays False
    src = "def helper():\n    pass\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.has_main is False
    assert len(mi.top_level_functions) == 1


def test_parse_module_contains_class(tmp_path):
    # exercises the isinstance(node, ast.ClassDef) branch in parse_module_from_source
    src = "class Foo:\n    pass\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert any(c.name == "Foo" for c in mi.classes)


def test_parse_module_all_empty_list(tmp_path):
    # __all__ = [] — the for-elt loop body never executes (189->188 arc)
    src = "__all__ = []\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.public_exports == []


def test_parse_module_non_name_assignment_target(tmp_path):
    # tuple-unpacking assignment — target is not ast.Name, so __all__ check skips (187->185)
    src = "a, b = 1, 2\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.public_exports == []


def test_parse_class_init_with_mixed_state_and_non_state_attrs():
    # __init__ has both a state attr and a non-state attr — exercises the
    # False branch of `if any(kw in attr_name.lower()...)` continuing the loop (127->117)
    cls = _class(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.name = 'bob'\n"
        "        self.state = 'idle'\n"
    )
    ci = parsers.parse_class(cls)
    assert any(a.name == "name" for a in ci.attributes)
    assert "state" in ci.state_attributes


def test_parse_class_state_attr_already_in_state_attrs_not_duplicated():
    # same attr assigned twice in __init__ → second iteration hits
    # `if attr_name not in state_attrs:` False branch (127->117 arc)
    cls = _class(
        "class Foo:\n"
        "    def __init__(self):\n"
        "        self.state = 'idle'\n"
        "        self.state = 'ready'\n"
    )
    ci = parsers.parse_class(cls)
    assert ci.state_attributes.count("state") == 1


def test_parse_module_all_as_tuple_not_list(tmp_path):
    # __all__ = ("Foo",) — value is Tuple not List → 187->185 arc
    src = '__all__ = ("Foo",)\n'
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.public_exports == []


def test_parse_module_all_with_non_constant_element(tmp_path):
    # __all__ = [some_var] — element is Name not Constant → 189->188 arc
    src = "__all__ = [some_var]\n"
    f = tmp_path / "mod.py"
    mi = parse_module_from_source(f, src, tmp_path)
    assert mi.public_exports == []


def test_parse_module_from_source_imports_and_main(tmp_path: Path):
    src_root = tmp_path / "proj"
    src_root.mkdir()
    pkg_dir = src_root / "pkg"
    pkg_dir.mkdir()
    f = pkg_dir / "mod.py"
    f.write_text("""
import os
from .sub import helper
__all__ = ["X", "Y"]
def main():
    pass
if __name__ == '__main__':
    main()
""")
    mod = parse_module_from_source(f, f.read_text(), src_root)
    assert mod is not None
    assert "os" in mod.imports
    assert mod.has_main
    assert "X" in mod.public_exports
