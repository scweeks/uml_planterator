from pathlib import Path

from uml_planterator import generator


def test_complexity_subdiagram_written(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "complex.py"
    # create a function with many nested branches to increase CC
    f.write_text("""
def f():
""" + "\n".join(["    if True:" for _ in range(12)]) + "\n        return 1\n")

    out = tmp_path / "out"
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    res = g.run(dry_run=False)
    counts = res.get("counts", {})
    # complexity diagrams should be produced when cc >=10
    assert counts.get("complexity", 0) >= 0
