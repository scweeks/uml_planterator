from pathlib import Path

from uml_planterator import generator


def test_generator_dry_run_creates_expected_counts(tmp_path: Path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    mod = src / "mymod.py"
    mod.write_text("""
class A:
    def f(self):
        return 1
""")

    out = tmp_path / "out"
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    result = g.run(dry_run=True)
    counts = result.get("counts", {})
    assert counts.get("class", 0) >= 1
    assert counts.get("package", 0) >= 1
