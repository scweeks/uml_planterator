from pathlib import Path

from uml_planterator.adapters.java_adapter import JavaAdapter


def test_java_adapter_parses_classes(tmp_path: Path):
    src = tmp_path / "Example.java"
    src.write_text(
        """
        package com.example;

        public class Foo {}

        interface Bar {}
        """
    )

    adapter = JavaAdapter()
    mod = adapter.parse_source(src, src.read_text())
    assert mod is not None
    names = [c.name for c in mod.classes]
    assert "Foo" in names
    assert "Bar" in names
