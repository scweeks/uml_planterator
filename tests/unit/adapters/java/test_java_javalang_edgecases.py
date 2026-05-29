import builtins
from pathlib import Path
from types import SimpleNamespace

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def _make_decl(name):
    return SimpleNamespace(name=name)


def _make_field_with_bad_type():
    class BadType:
        @property
        def name(self):
            raise AttributeError("no name")

    decl = SimpleNamespace(name="f")
    field = SimpleNamespace(modifiers=None, type=BadType(), declarators=[decl])
    return field


def _make_param_with_bad_type():
    class BadType:
        @property
        def name(self):
            raise AttributeError("no pname")

    return SimpleNamespace(name="p", type=BadType())


def _make_method_with_bad_return():
    class BadType:
        @property
        def name(self):
            raise AttributeError("no r")

    m = SimpleNamespace(
        name="m",
        modifiers=["public"],
        parameters=[_make_param_with_bad_type()],
        return_type=BadType(),
    )
    return m


def test_javalang_fallback_when_missing(monkeypatch, tmp_path: Path):
    # Force top-level import of javalang to fail and ensure fallback
    # to the regex adapter
    real_import = builtins.__import__

    def _fake_import(name, _globals=None, _locals=None, fromlist=(), level=0):
        if name == "javalang":
            raise ImportError()
        return real_import(name, _globals, _locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    adapter = JavaJavalangAdapter()
    # Should return non-None ModuleInfo via fallback
    mod = adapter.parse_source(tmp_path / "A.java", "class A {}")
    assert mod is not None


def test_attribute_errors_and_inner_import(monkeypatch, tmp_path: Path):
    # Build a fake AST that triggers AttributeError branches
    # for field/param/return
    fake_tree = SimpleNamespace()
    type_decl = SimpleNamespace()
    type_decl.name = "A"
    type_decl.fields = [_make_field_with_bad_type()]
    type_decl.methods = [_make_method_with_bad_return()]
    fake_tree.types = [type_decl]
    fake_tree.package = None

    def fake_parse(_src):
        return fake_tree

    monkeypatch.setattr("javalang.parse.parse", fake_parse)

    # Simulate inner complexity counter import failure
    monkeypatch.setenv("UML_PLANETATOR_TEST_JAVALANG_INNER_FAIL", "1")

    adapter = JavaJavalangAdapter()
    mod = adapter.parse_source(tmp_path / "A.java", "class A {}")
    assert mod is not None
    assert len(mod.classes) == 1
    cls = mod.classes[0]
    # attribute type should be empty string due to AttributeError
    assert cls.attributes[0].type_hint == ""
    # method param type and return_type should be empty
    assert cls.methods[0].params[0].type_hint == ""
    assert cls.methods[0].return_type == ""
    # cc should be minimum 1 because inner counter failed
    assert cls.methods[0].cc == 1
