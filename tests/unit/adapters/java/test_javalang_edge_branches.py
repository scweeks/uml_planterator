from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_multi_declarator_and_param_type_attrerror(monkeypatch, tmp_path: Path):
    class BadType:
        def __getattr__(self, _):
            raise AttributeError()

    class Declarator:
        def __init__(self, name):
            self.name = name

    class Field:
        def __init__(self, names):
            self.modifiers = []
            self.type = BadType()
            self.declarators = [Declarator(n) for n in names]

    class Param:
        def __init__(self, name):
            self.name = name
            self.type = BadType()

    class Method:
        def __init__(self, name):
            self.modifiers = []
            self.parameters = [Param("p1")]
            self.return_type = BadType()
            self.name = name
            self.children = [[None], (None,)]

    class TypeDecl:
        def __init__(self):
            self.name = "X"
            self.fields = [Field(["a", "b"])]
            self.methods = [Method("mm")]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "X.java"
    src.write_text("public class X{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    cls = mod.classes[0]
    # both declarators should result in attributes
    assert any(a.name == "a" for a in cls.attributes)
    assert any(a.name == "b" for a in cls.attributes)
