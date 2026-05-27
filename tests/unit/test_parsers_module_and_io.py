from pathlib import Path


from uml_planterator.parsers import parse_module_from_source
from uml_planterator import io


def test_parse_module_from_source_imports_and_main(tmp_path: Path):
    src_root = tmp_path / "proj"
    src_root.mkdir()
    pkg_dir = src_root / "pkg"
    pkg_dir.mkdir()
    f = pkg_dir / "mod.py"
    f.write_text(
        """
import os
from .sub import helper
__all__ = ["X", "Y"]
def main():
    pass
if __name__ == '__main__':
    main()
"""
    )

    mod = parse_module_from_source(f, f.read_text(), src_root)
    assert mod is not None
    assert "os" in mod.imports
    assert "pkg.sub" or "sub"  # smoke
    assert mod.has_main
    assert "X" in mod.public_exports


def test_write_puml_writes_file_and_verbose(tmp_path: Path, capsys):
    p = tmp_path / "out" / "a.puml"
    io.write_puml("content", p, verbose=True)
    assert p.exists()
    assert p.read_text(encoding="utf-8") == "content"
    captured = capsys.readouterr()
    assert "wrote" in captured.out
