from pathlib import Path

import pytest

from uml_planterator import models, registry
from uml_planterator.adapters.base import Adapter, AdapterError


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
    assert any(c.name == "Foo" for c in modinfo.classes)


class DummyAdapter(Adapter):
    @property
    def language(self) -> str:
        return "dummy"

    def supported_extensions(self) -> list[str]:
        return [".dummy"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo | None:
        _ = source
        return models.ModuleInfo(
            name=path.stem,
            package=path.parent.name,
            rel_path=str(path),
            classes=[],
        )


def test_compute_complexity_fallback():
    m = models.ModuleInfo(name="m", package="p", rel_path="m.py", classes=[], cc=5)
    a = DummyAdapter()
    assert a.compute_complexity(m) == 5


def test_parse_ast_not_implemented():
    a = DummyAdapter()
    with pytest.raises(AdapterError):
        a.parse_ast(Path("x"), None)


def test_adapters_expose_language_and_extensions():
    for lang in ("python", "cpp", "c"):
        adapter = registry.get_adapter(lang)
        assert hasattr(adapter, "language")
        assert isinstance(adapter.language, str)
        assert hasattr(adapter, "supported_extensions")
        exts = adapter.supported_extensions()
        assert isinstance(exts, list)
        assert all(isinstance(e, str) for e in exts)


def test_compute_complexity_available():
    adapter = registry.get_adapter("python")

    class M:
        cc = 3

    assert hasattr(adapter, "compute_complexity")
    val = adapter.compute_complexity(M())
    assert isinstance(val, int)


def test_c_adapter_compute_complexity(tmp_path):
    adapter = registry.get_adapter("c")
    mod = models.ModuleInfo(name="m", package="p", rel_path="m.c", classes=[], cc=4)
    assert adapter.compute_complexity(mod) == 4


def test_cpp_adapter_compute_complexity(tmp_path):
    adapter = registry.get_adapter("cpp")
    mod = models.ModuleInfo(name="m", package="p", rel_path="m.cpp", classes=[], cc=7)
    assert adapter.compute_complexity(mod) == 7


def test_c_adapter_compute_complexity_missing_cc():
    adapter = registry.get_adapter("c")

    class NoCC:
        pass

    assert adapter.compute_complexity(NoCC()) == 1


def test_cpp_adapter_compute_complexity_missing_cc():
    adapter = registry.get_adapter("cpp")

    class NoCC:
        pass

    assert adapter.compute_complexity(NoCC()) == 1
