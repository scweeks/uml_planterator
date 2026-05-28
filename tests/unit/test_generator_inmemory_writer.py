from pathlib import Path

from uml_planterator import models
from uml_planterator.generator import PUMLGenerator


class FakeAdapter:
    @staticmethod
    def supported_extensions():
        return [".py"]

    @staticmethod
    def parse_source(path: Path, src: str):
        # Return a ModuleInfo with one class to force class diagram generation
        cls = models.ClassInfo(name="Foo", cc=1)
        mod = models.ModuleInfo(
            name=path.stem,
            package="pkg",
            rel_path=str(path.relative_to(path.parent.parent)),
            classes=[cls],
            cc=12,
        )
        return mod

    @staticmethod
    def compute_complexity(module: models.ModuleInfo):
        return 12


class InMemoryWriter:
    def __init__(self):
        self.writes = []

    def write_puml(self, content: str, path: Path, verbose: bool = False):
        self.writes.append((str(path), content))


def test_generator_writes_with_inmemory_writer(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    out.mkdir()

    # create a fake source file
    f = src / "module_a.py"
    f.write_text("class Foo: pass\n")

    gen = PUMLGenerator(
        src, out, verbose=False, adapters_factory=lambda: [FakeAdapter()]
    )
    writer = InMemoryWriter()
    gen.writer = writer

    res = gen.run(dry_run=False)

    # should have produced class, complexity and package diagrams
    assert res["counts"]["class"] >= 1
    assert res["counts"]["complexity"] >= 1
    assert res["counts"]["package"] >= 1

    # writer should have recorded writes
    assert any("-Foo.puml" in p for p, _ in writer.writes)
