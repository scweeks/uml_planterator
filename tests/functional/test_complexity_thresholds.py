from pathlib import Path

from uml_planterator import registry, generator


class CCWrapper:
    def __init__(self, base, cc_value):
        self._base = base
        self._cc = cc_value

    @property
    def language(self):
        return self._base.language

    def supported_extensions(self):
        return self._base.supported_extensions()

    def parse_source(self, path, source):
        return self._base.parse_source(path, source)

    def compute_complexity(self, module):
        _ = module
        return self._cc


def test_complexity_thresholds(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "mymod.py"
    f.write_text("""
class A:
    def f(self):
        if True:
            if True:
                return 1
""")

    out = tmp_path / "out"
    orig = registry.get_adapter("python")
    try:
        registry.register_adapter("python", CCWrapper(orig, 9))
        g = generator.PUMLGenerator(src_root=src, out_root=out)
        res = g.run(dry_run=True)
        assert res["counts"].get("complexity", 0) == 0

        registry.register_adapter("python", CCWrapper(orig, 12))
        g2 = generator.PUMLGenerator(src_root=src, out_root=out)
        res2 = g2.run(dry_run=True)
        assert res2["counts"].get("complexity", 0) >= 1
    finally:
        registry.register_adapter("python", orig)
