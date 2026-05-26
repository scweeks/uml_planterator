from pathlib import Path

from uml_planterator import registry


def test_c_adapter_parses_simple_struct(tmp_path: Path):
    src = tmp_path / "c"
    src.mkdir()
    f = src / "mod.c"
    f.write_text("""
typedef struct Foo {
    int x;
} Foo;

void do_something();
""")

    adapter = registry.get_adapter("c")
    modinfo = adapter.parse_source(f, f.read_text())
    assert modinfo is not None
    assert modinfo.name == "mod"
    assert any(c.name == "Foo" for c in modinfo.classes)
