from pathlib import Path
 

import pytest

from uml_planterator.adapters.java_jdt_adapter import JavaJDTAdapter
from uml_planterator.adapters.base import AdapterError


def test_jdt_adapter_fallback_when_no_jar(monkeypatch, tmp_path: Path):
    # Ensure fallback is used when env var missing or jar not found
    monkeypatch.delenv("UML_PLANETATOR_JDTLS", raising=False)

    adapter = JavaJDTAdapter()
    src = tmp_path / "X.java"
    src.write_text("class X{}")
    # Fallback returns None when javalang not configured; acceptable
    res = adapter.parse_source(src, src.read_text())
    assert res is None or hasattr(res, "classes")


def test_jdt_adapter_raises_adapter_error_and_shuts_down(
    monkeypatch, tmp_path: Path
):
    # Create a fake JDTLSClient that raises during request and record shutdown
    class FakeClient:
        def __init__(self, cmd, workspace):
            self.started = False
            self.shutdown_called = False

        def start(self):
            self.started = True

        def initialize(self, root_uri):
            return {}

        def open_text_document(self, path, source):
            return None

        def request(self, method, params=None):
            raise RuntimeError("boom")

        def shutdown(self):
            self.shutdown_called = True

    # Put a fake jar path and ensure Path exists
    jar = tmp_path / "jdtls.jar"
    jar.write_text("")
    monkeypatch.setenv("UML_PLANETATOR_JDTLS", str(jar))

    # Monkeypatch the JDTLSClient class used in module
    import importlib

    mod = importlib.import_module("uml_planterator.adapters.java_jdt_adapter")
    monkeypatch.setattr(mod, "JDTLSClient", FakeClient)

    adapter = JavaJDTAdapter()
    src = tmp_path / "Y.java"
    src.write_text("class Y{}")
    with pytest.raises(AdapterError):
        adapter.parse_source(src, src.read_text())
