import builtins
from types import SimpleNamespace
from pathlib import Path
from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_fallback_to_regex_adapter_when_javalang_missing(
    monkeypatch, tmp_path: Path
):
    # Force ImportError when importing 'javalang'
    real_import = builtins.__import__

    def _fake_import(name, _globals=None, _locals=None, fromlist=(), level=0):
        if name == "javalang":
            raise ImportError()
        return real_import(name, _globals, _locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    adapter = JavaJavalangAdapter()
    src = tmp_path / "Z.java"
    src.write_text("class Z{}")
    # Should not raise and should return a ModuleInfo (fallback)
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None


def test_default_visibility_and_empty_package(monkeypatch, tmp_path: Path):
    # Tree with package present but empty name, plus no-modifier members
    class DummyPackage:
        def __init__(self):
            self.name = ""

    class Declarator:
        def __init__(self, name):
            self.name = name

    class Field:
        def __init__(self, name):
            self.modifiers = []
            self.type = SimpleNamespace(name="T")
            self.declarators = [Declarator(name)]

    class Method:
        def __init__(self):
            self.modifiers = []
            self.parameters = []
            self.return_type = None
            self.name = "m"
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "D"
            self.fields = [Field("f")]
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = DummyPackage()
            self.types = [TypeDecl()]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "D.java"
    src.write_text("class D{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    # package should fall back to parent folder name
    assert mod.package == src.parent.name
    cls = mod.classes[0]
    assert cls.attributes[0].visibility == "~"
    assert cls.methods[0].visibility == "~"


def test_count_various_branch_nodes(monkeypatch, tmp_path: Path):
    # Create method children whose type names match the branch list
    class NodeBase:
        pass

    class IfStatement(NodeBase):
        pass

    class ForStatement(NodeBase):
        pass

    class WhileStatement(NodeBase):
        pass

    class DoStatement(NodeBase):
        pass

    class SwitchStatement(NodeBase):
        pass

    class CatchClause(NodeBase):
        pass

    class TernaryExpression(NodeBase):
        pass

    class Method:
        def __init__(self):
            self.modifiers = ["public"]
            self.parameters = []
            self.return_type = None
            self.name = "b"
            self.children = [
                IfStatement(),
                ForStatement(),
                WhileStatement(),
                DoStatement(),
                SwitchStatement(),
                CatchClause(),
                TernaryExpression(),
            ]

    class TypeDecl:
        def __init__(self):
            self.name = "B"
            self.fields = []
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "B.java"
    src.write_text("class B{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    cls = mod.classes[0]
    assert cls.methods[0].cc >= 8


def test_return_type_attrerror_branch(monkeypatch, tmp_path: Path):
    class BadRet:
        def __getattr__(self, _):
            raise AttributeError()

    class Method:
        def __init__(self):
            self.modifiers = []
            self.parameters = []
            self.return_type = BadRet()
            self.name = "r"
            self.children = []

    class TypeDecl:
        def __init__(self):
            self.name = "R"
            self.fields = []
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "R.java"
    src.write_text("class R{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    cls = mod.classes[0]
    # return_type should be empty string handled via except branch
    assert cls.methods[0].return_type == ""


def test_inner_javalang_import_failure_simulated(monkeypatch, tmp_path: Path):
    # When inner import fails, CC should remain the default 1
    class IfStatement:
        pass

    class Method:
        def __init__(self):
            self.modifiers = ["public"]
            self.parameters = []
            self.return_type = None
            self.name = "ix"
            self.children = [IfStatement()]

    class TypeDecl:
        def __init__(self):
            self.name = "IX"
            self.fields = []
            self.methods = [Method()]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl()]

    monkeypatch.setenv("UML_PLANETATOR_TEST_JAVALANG_INNER_FAIL", "1")
    monkeypatch.setattr(
        "javalang.parse.parse", lambda src: Tree(), raising=False
    )

    adapter = JavaJavalangAdapter()
    src = tmp_path / "IX.java"
    src.write_text("class IX{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    assert mod.classes[0].methods[0].cc == 1
