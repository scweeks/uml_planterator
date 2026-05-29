from pathlib import Path

from uml_planterator.adapters.java_jdt_adapter import JavaJDTAdapter


def test_jdt_adapter_falls_back_when_unconfigured(tmp_path: Path, monkeypatch):
    # Ensure env var not set
    monkeypatch.delenv("UML_PLANETATOR_JDTLS", raising=False)
    src = tmp_path / "A.java"
    src.write_text("public class A {}")
    adapter = JavaJDTAdapter()
    mod = adapter.parse_source(src, src.read_text())
    # Fallback should return a ModuleInfo
    assert mod is not None
    assert any(c.name == "A" for c in mod.classes)
