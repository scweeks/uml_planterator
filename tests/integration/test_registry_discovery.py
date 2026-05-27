from pathlib import Path

from uml_planterator import generator, models, registry


class FooAdapter:
    @property
    def language(self):
        return "foo"

    def supported_extensions(self):
        return [".foo"]

    def parse_source(self, path, source):
        # return a minimal ModuleInfo with one class
        cls = models.ClassInfo(name="X")
        return models.ModuleInfo(
            name=path.stem,
            package=path.stem,
            rel_path=str(path.name),
            classes=[cls],
        )


def test_registry_discovery_with_custom_adapter(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "a.foo"
    f.write_text("class X")

    orig = None
    try:
        try:
            orig = registry.get_adapter("foo")
        except KeyError:
            orig = None
        registry.register_adapter("foo", FooAdapter())

        out = tmp_path / "out"
        g = generator.PUMLGenerator(src_root=src, out_root=out)
        res = g.run(dry_run=True)
        counts = res.get("counts", {})
        assert counts.get("class", 0) >= 1
    finally:
        if orig is not None:
            registry.register_adapter("foo", orig)
