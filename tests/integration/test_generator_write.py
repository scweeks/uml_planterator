from pathlib import Path

from uml_planterator import generator


def test_generator_writes_files(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "mymod.py"
    f.write_text("""
class A:
    def f(self):
        return 1
""")

    out = tmp_path / "out"
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    res = g.run(dry_run=False)
    counts = res.get("counts", {})
    # Ensure files were written
    assert counts.get("class", 0) >= 1
    # Check directory exists
    assert (out.exists())
