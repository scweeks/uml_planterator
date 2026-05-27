from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_anon_class_name_and_declarators_none(monkeypatch, tmp_path: Path):
    class Field:
        def __init__(self):
            self.modifiers = ["public"]
            self.type = None
            self.declarators = None

    class TypeDecl:
        def __init__(self):
            # intentionally omit 'name' attribute to trigger '<anon>' fallback
            self.fields = [Field()]
            self.methods = []

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "AN.java"
    src.write_text("class AN{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    # class should be named '<anon>' because name missing
    assert mod.classes[0].name == "<anon>"


def test_protected_visibility(monkeypatch, tmp_path: Path):
    class Declarator:
        def __init__(self, name):
            self.name = name

    class Field:
        def __init__(self):
            self.modifiers = ["protected"]
            self.type = type("T", (), {"name": "Z"})()
            self.declarators = [Declarator("pf")]

    class Method:
        def __init__(self):
            self.modifiers = ["protected"]
            self.parameters = []
            self.return_type = None
            self.name = "mpf"
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "Prot"
            self.fields = [Field()]
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )
    adapter = JavaJavalangAdapter()
    src = tmp_path / "Prot.java"
    src.write_text("class Prot{}")
    mod = adapter.parse_source(src, src.read_text())
    cls = mod.classes[0]
    assert cls.attributes[0].visibility == "#"
    assert cls.methods[0].visibility == "#"
