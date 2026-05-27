from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_javalang_adapter_handles_attribute_errors(monkeypatch, tmp_path: Path):
    # Build fake AST-like objects that exercise AttributeError branches
    class BadType:
        def __getattr__(self, item):
            raise AttributeError()

    class Field:
        def __init__(self, name):
            self.modifiers = []
            self.type = BadType()
            self.declarators = [type("D", (), {"name": name})()]

    class MethodIf:
        def __init__(self, name_):
            self.modifiers = []
            self.parameters = [
                type("P", (), {"name": "p", "type": BadType()})(),
            ]
            self.return_type = BadType()
            self.name = name_
            self.children = []

    class TypeDecl:
        def __init__(self, name):
            self.name = name
            self.fields = [Field("f1")]
            self.methods = [MethodIf("m1")]

    class Tree:
        def __init__(self):
            self.package = None
            self.types = [TypeDecl("T")]

    monkeypatch.setattr(
        "javalang.parse.parse",
        lambda src: Tree(),
        raising=False,
    )

    adapter = JavaJavalangAdapter()
    mod = adapter.parse_source(tmp_path / "A.java", "public class A{}")
    assert mod is not None
    assert any(c.name == "T" for c in mod.classes)


def test_jdt_adapter_uses_fake_client(monkeypatch, tmp_path: Path):
    # Create a fake launcher file and set env
    launcher = tmp_path / "jdtls.jar"
    launcher.write_text("")
    monkeypatch.setenv("UML_PLANETATOR_JDTLS", str(launcher))

    # Fake client that returns a documentSymbol with children
    class FakeClient:
        def __init__(self, cmd, workspace):
            self.cmd = cmd
            self.workspace = workspace

        def start(self):
            return None

        def initialize(self, _root_uri):
            return {}

        def open_text_document(self, _path, _source):
            return None

        def request(self, _method, _params=None):
            # return one class with two children symbols (field and method)
            return {
                "result": [
                    {
                        "name": "C",
                        "children": [
                            {"name": "f", "kind": 8},
                            {"name": "m", "kind": 6},
                        ],
                    }
                ]
            }

        def shutdown(self):
            return None

    # Monkeypatch the JDTLSClient used in the adapter module
    import uml_planterator.adapters.java_jdt_adapter as jdtmod

    monkeypatch.setattr(jdtmod, "JDTLSClient", FakeClient)

    adapter = jdtmod.JavaJDTAdapter()
    src = tmp_path / "C.java"
    src.write_text("public class C{}")
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    assert any(c.name == "C" or c.name == "C" for c in mod.classes)
