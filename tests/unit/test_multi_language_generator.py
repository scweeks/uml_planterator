from pathlib import Path

import pytest

from uml_planterator import generator, registry

testcases = [
    (
        "python",
        "mod.py",
        "class A:\n    def f(self):\n        if True:\n            if True:\n                if True:\n                    if True:\n                        if True:\n                            if True:\n                                if True:\n                                    if True:\n                                        if True:\n                                            return 1\n",
    ),
    ("c", "mod.c", "typedef struct Foo { int x; } Foo;\n"),
    ("cpp", "mod.cpp", "class A { };\n"),
]


@pytest.mark.parametrize("lang,filename,content", testcases)
def test_multi_language_generation_creates_expected_diagrams(
    tmp_path: Path, lang, filename, content
):
    src = tmp_path / "srcpkg"
    src.mkdir()
    f = src / filename
    f.write_text(content)

    out = tmp_path / "out"

    # Wrap original adapter to force high complexity for complexity sub-diagram
    orig = registry.get_adapter(lang)

    class Wrapper:
        def __init__(self, base):
            self._base = base

        @property
        def language(self):
            return self._base.language

        def supported_extensions(self):
            return self._base.supported_extensions()

        def parse_source(self, path, source):
            return self._base.parse_source(path, source)

        def compute_complexity(self, module):
            return 12

    try:
        registry.register_adapter(lang, Wrapper(orig))

        g = generator.PUMLGenerator(src_root=src, out_root=out)
        res = g.run(dry_run=True)
        counts = res.get("counts", {})

        assert counts.get("class", 0) >= 1
        assert counts.get("package", 0) >= 1
        # Complexity sub-diagram should have been produced via Wrapper.compute_complexity
        assert counts.get("complexity", 0) >= 1
    finally:
        # restore original adapter
        registry.register_adapter(lang, orig)
