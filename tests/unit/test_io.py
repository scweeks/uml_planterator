"""Tests for io.py — 100% line and branch coverage."""

from uml_planterator import io


def test_write_puml_creates_file_with_content(tmp_path):
    p = tmp_path / "out.puml"
    io.write_puml("@startuml\n@enduml", p)
    assert p.exists()
    assert p.read_text(encoding="utf-8") == "@startuml\n@enduml"


def test_write_puml_creates_parent_directories(tmp_path):
    p = tmp_path / "deep" / "nested" / "diagram.puml"
    io.write_puml("content", p)
    assert p.exists()


def test_write_puml_verbose_prints_path(tmp_path, capsys):
    p = tmp_path / "out.puml"
    io.write_puml("content", p, verbose=True)
    captured = capsys.readouterr()
    assert "wrote" in captured.out
    assert str(p) in captured.out


def test_write_puml_silent_by_default(tmp_path, capsys):
    p = tmp_path / "out.puml"
    io.write_puml("content", p, verbose=False)
    captured = capsys.readouterr()
    assert captured.out == ""
