from pathlib import Path

import pytest

from uml_planterator import models
from uml_planterator.adapters.base import Adapter, AdapterError


class DummyAdapter(Adapter):
    @property
    def language(self) -> str:
        return "dummy"

    def supported_extensions(self) -> list[str]:
        return [".dummy"]

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo | None:
        _ = source
        return models.ModuleInfo(
            name=path.stem,
            package=path.parent.name,
            rel_path=str(path),
            classes=[],
        )


def test_compute_complexity_fallback():
    m = models.ModuleInfo(name="m", package="p", rel_path="m.py", classes=[], cc=5)
    a = DummyAdapter()
    assert a.compute_complexity(m) == 5


def test_parse_ast_not_implemented():
    a = DummyAdapter()
    with pytest.raises(AdapterError):
        a.parse_ast(Path("x"), None)
