from pathlib import Path
from types import SimpleNamespace

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_private_visibility_and_empty_declarators(monkeypatch, tmp_path: Path):
    class Field:
        def __init__(self):
            self.modifiers = ["private"]
            self.type = SimpleNamespace(name="X")
            self.declarators = []

    class Method:
        def __init__(self):
            self.modifiers = ["private"]
            self.parameters = []
            self.return_type = None
            self.name = "mp"
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "P"
            self.fields = [Field()]
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "P.java"
    src.write_text("class P{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    cls = mod.classes[0]
    # private visibility for attribute and method
    assert cls.attributes == []
    assert cls.methods[0].visibility == "-"


def test_static_and_abstract_flags(monkeypatch, tmp_path: Path):
    class Method:
        def __init__(self, mods):
            self.modifiers = mods
            self.parameters = []
            self.return_type = None
            self.name = "mf"
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "S"
            self.fields = []
            self.methods = [Method(["static"]), Method(["abstract"])]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "S.java"
    src.write_text("class S{}")
    mod = adapter.parse_source(src, src.read_text())
    cls = mod.classes[0]
    assert cls.methods[0].is_static
    assert cls.methods[1].is_abstract


def test_children_list_and_tuple_recursion(monkeypatch, tmp_path: Path):
    class IfStatement:
        pass

    class ForStatement:
        pass

    class Method:
        def __init__(self):
            self.modifiers = ["public"]
            self.parameters = []
            self.return_type = None
            self.name = "c1"
            # nested children lists/tuples
            self.children = [[IfStatement(), (ForStatement(),)]]

    class TypeDecl:
        def __init__(self):
            self.name = "C1"
            self.fields = []
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "C1.java"
    src.write_text("class C1{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    assert mod.classes[0].methods[0].cc >= 2


def test_field_type_none(monkeypatch, tmp_path: Path):
    class Field:
        def __init__(self):
            self.modifiers = ["public"]
            self.type = None
            self.declarators = [type("D", (), {"name": "fn"})()]

    class TypeDecl:
        def __init__(self):
            self.name = "FN"
            self.fields = [Field()]
            self.methods = []

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr("javalang.parse.parse", lambda src: Tree(), raising=False)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "FN.java"
    src.write_text("class FN{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    # type hint should be empty string when type is None
    assert mod.classes[0].attributes[0].type_hint == ""
