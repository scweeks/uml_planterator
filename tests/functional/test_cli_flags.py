import sys
from pathlib import Path
import importlib

import pytest

generate_puml = importlib.import_module("generate_puml")


def test_cli_dry_run_prints_summary(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "mymod.py"
    f.write_text("""
class A:
    def f(self):
        return 1
""")

    out = tmp_path / "out"
    argv = ["generate_puml", "--src", str(src), "--out", str(out), "--dry-run"]
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(sys, "argv", argv)
        rc = generate_puml.main()
    finally:
        monkeypatch.undo()

    assert rc == 0


def test_cli_writes_files(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "mymod.py"
    f.write_text("""
class A:
    def f(self):
        return 1
""")

    out = tmp_path / "out"
    argv = ["generate_puml", "--src", str(src), "--out", str(out)]
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(sys, "argv", argv)
        rc = generate_puml.main()
    finally:
        monkeypatch.undo()

    assert rc == 0
    # ensure some .puml files exist under out
    found = list(out.rglob("*.puml"))
    assert found
