from pathlib import Path

from uml_planterator import registry


def test_cpp_adapter_parses_simple_class(tmp_path: Path):
    src = tmp_path / "cpp"
    src.mkdir()
    f = src / "mod.cpp"
    f.write_text("""
class Foo {
public:
    int x;
    void doSomething();
};
""")

    adapter = registry.get_adapter("cpp")
    modinfo = adapter.parse_source(f, f.read_text())
    assert modinfo is not None
    assert modinfo.name == "mod"
    # best-effort: expect a class named Foo
    assert any(c.name == "Foo" for c in modinfo.classes)
