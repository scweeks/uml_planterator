from pathlib import Path

from uml_planterator import models, renderers
from uml_planterator.generator import PUMLGenerator


def test_gen_class_diagram_with_docstring():
    cls = models.ClassInfo(name="Foo", docstring="This is a doc\nmore")
    cls.attributes = [models.AttributeInfo(name="x", type_hint="int")]
    m = models.MethodInfo(name="do", params=[models.Param("a", "int")])
    cls.methods = [m]
    mod = models.ModuleInfo(name="mymod", package="pkg", rel_path="pkg/mymod.py")

    out = renderers.gen_class_diagram(cls, mod)
    assert "note bottom" in out
    assert "@startuml" in out


def test_package_and_system_renderers():
    cls = models.ClassInfo(name="C1", is_abstract=True)
    mod = models.ModuleInfo(
        name="mod1",
        package="pkg.sub",
        rel_path="pkg/sub/mod1.py",
        classes=[cls],
    )
    pkg = renderers.gen_package_diagram([mod], "pkg.sub", "src")
    assert "package pkg.sub" in pkg
    assert "class C1 <<abstract>>" in pkg

    system = renderers.gen_system_package_diagram([mod], src_name="src")
    assert "component [pkg]" in system


def test_sequence_activity_state_usecase():
    m = models.MethodInfo(name="m1", calls=[("B", "call")])
    c = models.ClassInfo(name="A", methods=[m])
    mod = models.ModuleInfo(name="mod", package="pkg", rel_path="mod.py", classes=[c])

    seq = renderers.gen_sequence_diagram(mod)
    assert "participant A" in seq
    assert "A -> B: call" in seq

    fn = models.MethodInfo(name="doit")
    mod2 = models.ModuleInfo(
        name="m2",
        package="pkg",
        rel_path="m2.py",
        top_level_functions=[fn],
    )
    act = renderers.gen_activity_diagram(mod2)
    assert ":doit();" in act

    c2 = models.ClassInfo(name="S", state_attributes=["state1"])
    st = renderers.gen_state_diagram(c2)
    assert "state state1" in st

    uc = renderers.gen_usecase_diagram([mod2], name="uc")
    assert "actor m2User" in uc


# Parser-specific branches are covered in dedicated parser tests.
# The duplicate parser checks were moved to
# tests/unit/test_parsers_additional_branches.py to avoid overlap.


def test_generator_dry_run_and_complexity_fallback(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()

    # create a source file
    f = src / "m.py"
    f.write_text("class Foo: pass\n")

    # Adapter that raises AttributeError on compute_complexity
    class BadAdapter:
        @staticmethod
        def supported_extensions():
            return [".py"]

        @staticmethod
        def parse_source(path: Path, _src: str):
            cls = models.ClassInfo(name="Foo")
            return models.ModuleInfo(
                name="m",
                package="pkg",
                rel_path=str(path.relative_to(path.parent.parent)),
                classes=[cls],
                cc=12,
            )

        @staticmethod
        def compute_complexity(module):
            raise AttributeError()

    gen = PUMLGenerator(src, out, adapters_factory=lambda: [BadAdapter()])

    res = gen.run(dry_run=True)
    # should have paths for class and complexity and package
    assert any("-Foo.puml" in p for p in res["paths"]) or any(
        "complexity" in p for p in res["paths"]
    )
