import ast
from pathlib import Path

from uml_planterator import parsers


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


def test_parse_module_from_source():
    src = "def main():\n    return 0\n"
    p = Path("pkg/mod.py")
    mi = parsers.parse_module_from_source(p, src, Path("pkg"))
    assert mi is not None
    assert mi.name == "mod"
