import sys
from pathlib import Path
import importlib.util
from pathlib import Path


def _load_generate_puml_module():
    p = Path(__file__).resolve()
    for anc in p.parents:
        candidate = anc / "src" / "generate_puml.py"
        if candidate.exists():
            spec = importlib.util.spec_from_file_location(
                "generate_puml", str(candidate)
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RuntimeError("couldn't find src/generate_puml.py")

 
generate_puml = _load_generate_puml_module()


def test_generate_puml_main_default(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "argv", ["generate_puml", "--src", str(tmp_path)])
    # create empty src to avoid errors
    (tmp_path / "a.py").write_text("")
    res = generate_puml.main()
    assert res == 0


def test_generate_puml_dry_run_and_verbose(
    monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_puml",
            "--src",
            str(tmp_path),
            "--dry-run",
            "--verbose",
        ],
    )
    (tmp_path / "b.py").write_text("")
    res = generate_puml.main()
    assert res == 0
