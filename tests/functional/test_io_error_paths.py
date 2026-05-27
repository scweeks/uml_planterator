from pathlib import Path

import pytest

from uml_planterator import generator
from uml_planterator import io as io_mod


def test_io_write_error_bubbles(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "mymod.py"
    f.write_text("""
class A:
    def f(self):
        return 1
""")

    out = tmp_path / "out"

    def bad_write(content, path, verbose=False):
        raise OSError("disk full")

    monkeypatch.setattr(io_mod, "write_puml", bad_write)

    g = generator.PUMLGenerator(src_root=src, out_root=out)
    with pytest.raises(OSError):
        g.run(dry_run=False)
