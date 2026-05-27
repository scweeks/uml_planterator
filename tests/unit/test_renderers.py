from uml_planterator import models, renderers


def make_simple_class():
    m = models.MethodInfo(name="do", params=[models.Param("x")], return_type="int")
    a = models.AttributeInfo(name="value", type_hint="int")
    cls = models.ClassInfo(
        name="MyClass", attributes=[a], methods=[m], docstring="Example class"
    )
    mod = models.ModuleInfo(
        name="mod", package="pkg.mod", rel_path="pkg/mod.py", classes=[cls]
    )
    return cls, mod


def test_gen_class_diagram_contains_class_name():
    cls, mod = make_simple_class()
    out = renderers.gen_class_diagram(cls, mod)
    assert out.startswith("@startuml")
    assert "MyClass" in out
    assert "Example class" in out


def test_gen_package_diagram_lists_class():
    _cls, mod = make_simple_class()
    out = renderers.gen_package_diagram([mod], "pkg.mod", src_name="src")
    assert out.startswith("@startuml")
    assert "pkg.mod" in out or "pkg" in out
    assert "MyClass" in out
