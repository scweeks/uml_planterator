from pathlib import Path

from uml_planterator import registry


def test_python_adapter_parses_simple_module(tmp_path: Path):
    src = tmp_path / "m"
    src.mkdir()
    f = src / "mod.py"
    f.write_text("""
class A:
    def f(self):
        return 1
""")

    adapter = registry.get_adapter("python")
    modinfo = adapter.parse_source(f, f.read_text())
    assert modinfo is not None
    assert modinfo.name == "mod"
    assert any(c.name == "A" for c in modinfo.classes)
