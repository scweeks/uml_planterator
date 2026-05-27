from uml_planterator import registry
from uml_planterator.adapters import base
from uml_planterator import generator
from pathlib import Path


def test_registry_singleton_and_get_all():
    adapters = registry.get_all_adapters()
    assert isinstance(adapters, list)


def test_adapter_abc_cannot_instantiate():
    try:
        base.Adapter()
        assert False, "Adapter should be abstract and not instantiable"
    except TypeError:
        assert True


def test_generator_facade_dry_run(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "m.py"
    f.write_text("class A: pass\n")
    out = tmp_path / "out"
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    res = g.run(dry_run=True)
    assert "counts" in res and "paths" in res
