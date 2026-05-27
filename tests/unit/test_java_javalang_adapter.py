from pathlib import Path

from uml_planterator.adapters.java_javalang_adapter import JavaJavalangAdapter


def test_javalang_adapter_parses_simple(tmp_path: Path):
    src = tmp_path / "S.java"
    src.write_text(
        """
        package p;
        public class S {
            private int x;
            public void m() {}
        }
        """
    )
    adapter = JavaJavalangAdapter()
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    assert any(c.name == "S" for c in mod.classes)
