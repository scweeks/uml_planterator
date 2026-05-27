from pathlib import Path

from uml_planterator import generator, registry
from uml_planterator.adapters.base import AdapterError


class BadAdapter:
    @property
    def language(self):
        return "bad"

    def supported_extensions(self):
        return [".bad"]

    def parse_source(self, path, source):
        raise AdapterError("parse failed")


def test_adapter_parse_failure_is_handled(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "x.bad"
    f.write_text("something")

    orig = None
    try:
        try:
            orig = registry.get_adapter("bad")
        except KeyError:
            orig = None
        registry.register_adapter("bad", BadAdapter())

        out = tmp_path / "out"
        g = generator.PUMLGenerator(src_root=src, out_root=out)
        res = g.run(dry_run=True)
        counts = res.get("counts", {})
        # No class diagrams should be produced for the bad file
        assert counts.get("class", 0) == 0
    finally:
        if orig is not None:
            registry.register_adapter("bad", orig)
