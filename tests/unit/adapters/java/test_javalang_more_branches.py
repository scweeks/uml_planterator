from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_javalang_adapter_modifiers_and_package(monkeypatch, tmp_path: Path):
    # Build fake AST to test protected/private modifiers, static/abstract
    class TName:
        def __init__(self, name):
            self.name = name

    class Param:
        def __init__(self, name):
            self.name = name
            self.type = TName("String")

    class Declarator:
        def __init__(self, name):
            self.name = name

    class Field:
        def __init__(self, name, mods):
            self.modifiers = mods
            self.type = TName("Custom")
            self.declarators = [Declarator(name)]

    class Method:
        def __init__(self, name, mods):
            self.modifiers = mods
            self.parameters = [Param("p")]
            self.return_type = TName("int")
            self.name = name
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "M"
            self.fields = [
                Field("fpub", ["public"]),
                Field("fprot", ["protected"]),
            ]
            self.methods = [
                Method("ms", ["static"]),
                Method("ma", ["abstract"]),
            ]

    class Tree:
        def __init__(self):
            self.package = type("P", (), {"name": "org.example.sub"})()
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "M.java"
    src.write_text("public class M{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    # Package should use last segment
    assert mod.package == "sub"
    cls = mod.classes[0]
    # fields and methods present
    assert any(a.name == "fpub" for a in cls.attributes)
    assert any(m.name == "ms" for m in cls.methods)
