from pathlib import Path

from uml_planterator import models, parsers, renderers
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


def test_parse_module_branches(tmp_path):
    src_root = tmp_path / "srcroot"
    src_root.mkdir()
    p = src_root / "pkg"
    p.mkdir()
    f = p / "mod.py"

    # Syntax error
    src = "def bad(:\n"
    assert parsers.parse_module_from_source(f, src, src_root) is None

    # relative import -> internal_imports
    src = "from .sub import x\n"
    mi = parsers.parse_module_from_source(f, src, src_root)
    assert "sub" in mi.internal_imports

    # public exports and main detection and cli detection
    src = "__all__ = ['a']\nimport click\ndef main():\n    pass\n"
    mi = parsers.parse_module_from_source(f, src, src_root)
    assert "a" in mi.public_exports
    assert mi.has_main
    assert mi.has_cli


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
        def parse_source(path: Path, src: str):
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
