import generate_puml


class DummyGen:
    def __init__(self, src_root, out_root, verbose=False):
        self.src_root = src_root
        self.out_root = out_root
        self.verbose = verbose

    def run(self, *_, **__):
        return {"counts": {"class": 1, "package": 1}}


def test_main_with_args(monkeypatch, capsys, tmp_path):
    # Monkeypatch the PUMLGenerator used by the module
    monkeypatch.setattr(generate_puml, "PUMLGenerator", DummyGen)

    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()

    args = ["--src", str(src), "--out", str(out), "--dry-run"]
    rc = generate_puml.main(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Generated" in captured.out
    assert "class" in captured.out
