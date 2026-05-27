from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_javalang_adapter_various_shapes(monkeypatch, tmp_path: Path):
    # Build fake javalang-like AST objects
    class TypeName:
        def __init__(self, name):
            self.name = name

    class ParamObj:
        def __init__(self, name, tname=None):
            self.name = name
            self.type = TypeName(tname or "int")

    class Declarator:
        def __init__(self, name):
            self.name = name

    class Field:
        def __init__(self, name, modifiers=None, tname=None):
            self.modifiers = modifiers or ["private"]
            self.type = TypeName(tname or "String")
            self.declarators = [Declarator(name)]

    class Method:
        def __init__(
            self, name, modifiers=None, params=None, return_type=None
        ):
            self.modifiers = modifiers or ["public"]
            self.parameters = params or []
            self.return_type = TypeName(return_type) if return_type else None
            self.name = name

            # children include an IfStatement and ForStatement to increase CC
            class IfStatement:
                pass

            class ForStatement:
                pass

            self.children = [IfStatement(), ForStatement()]

    class TypeDecl:
        def __init__(self, name):
            self.name = name
            self.fields = [Field("f1", modifiers=["public"], tname="int")]
            self.methods = [
                Method(
                    "m1",
                    modifiers=["public"],
                    params=[ParamObj("p")],
                    return_type="void",
                )
            ]

    class Tree:
        def __init__(self):
            self.package = type("P", (), {"name": "com.example"})()
            self.types = [TypeDecl("C")]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "C.java"
    src.write_text("public class C{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    assert mod.classes[0].name == "C"
    # Compute complexity should count method children
    cc = adapter.compute_complexity(mod)
    assert cc >= 2
