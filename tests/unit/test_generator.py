"""Tests for generator.py — 100% line and branch coverage."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from uml_planterator import generator, models
from uml_planterator.adapters.base import Adapter, AdapterError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _simple_module(name="mymod", cc=1):
    cls = models.ClassInfo(name="A", cc=cc)
    return models.ModuleInfo(
        name=name, package=name, rel_path=f"{name}.py", classes=[cls], cc=cc
    )


class _StubAdapter(Adapter):
    """Minimal adapter returning a fixed ModuleInfo."""

    def __init__(self, module=None, ext=".py", raise_error=False, bad_complexity=False):
        self._module = module
        self._ext = ext
        self._raise_error = raise_error
        self._bad_complexity = bad_complexity

    @property
    def language(self):
        return "stub"

    def supported_extensions(self):
        return [self._ext]

    def parse_source(self, path, source):
        if self._raise_error:
            raise AdapterError("parse failed")
        return self._module

    def compute_complexity(self, module):
        if self._bad_complexity:
            raise ValueError("bad cc")
        return int(getattr(module, "cc", 1))


def _make_generator(tmp_path, adapter, suffix=".py"):
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / f"mod{suffix}").write_text("x = 1")
    out = tmp_path / "out"
    return generator.PUMLGenerator(
        src_root=src,
        out_root=out,
        adapters_factory=lambda: [adapter],
    )


# ---------------------------------------------------------------------------
# Existing test
# ---------------------------------------------------------------------------


def test_generator_dry_run_creates_expected_counts(tmp_path: Path):
    src = tmp_path / "srcpkg"
    src.mkdir()
    mod = src / "mymod.py"
    mod.write_text("class A:\n    def f(self):\n        return 1\n")
    out = tmp_path / "out"
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    result = g.run(dry_run=True)
    counts = result.get("counts", {})
    assert counts.get("class", 0) >= 1
    assert counts.get("package", 0) >= 1


# ---------------------------------------------------------------------------
# _discover_and_parse: AdapterError → module skipped
# ---------------------------------------------------------------------------


def test_discover_and_parse_skips_module_on_adapter_error(tmp_path):
    adapter = _StubAdapter(raise_error=True)
    g = _make_generator(tmp_path, adapter)
    result = g.run(dry_run=True)
    assert result["counts"].get("class", 0) == 0


# ---------------------------------------------------------------------------
# _discover_and_parse: relative_to raises ValueError → rel_path left as-is
# ---------------------------------------------------------------------------


def test_discover_and_parse_handles_relative_to_value_error(tmp_path):
    module = _simple_module()
    adapter = _StubAdapter(module=module)
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("x = 1")
    out = tmp_path / "out"
    g = generator.PUMLGenerator(
        src_root=src,
        out_root=out,
        adapters_factory=lambda: [adapter],
    )
    with patch.object(Path, "relative_to", side_effect=ValueError("oops")):
        result = g.run(dry_run=True)
    # Module was still added despite the ValueError
    assert result["counts"].get("class", 0) >= 1


# ---------------------------------------------------------------------------
# run: CC >= 10 produces complexity sub-diagram
# ---------------------------------------------------------------------------


def test_run_writes_complexity_subdiagram_when_cc_ge_10(tmp_path):
    module = _simple_module(cc=10)
    adapter = _StubAdapter(module=module)
    g = _make_generator(tmp_path, adapter)
    result = g.run(dry_run=True)
    assert result["counts"].get("complexity", 0) >= 1
    assert any("complexity" in p for p in result["paths"])


def test_run_no_complexity_subdiagram_when_cc_lt_10(tmp_path):
    module = _simple_module(cc=9)
    adapter = _StubAdapter(module=module)
    g = _make_generator(tmp_path, adapter)
    result = g.run(dry_run=True)
    assert result["counts"].get("complexity", 0) == 0


# ---------------------------------------------------------------------------
# run: compute_complexity raises → falls back to module.cc
# ---------------------------------------------------------------------------


def test_run_complexity_fallback_on_bad_compute_complexity(tmp_path):
    module = _simple_module(cc=10)
    adapter = _StubAdapter(module=module, bad_complexity=True)
    g = _make_generator(tmp_path, adapter)
    result = g.run(dry_run=True)
    # cc falls back to module.cc=10 → complexity diagram still generated
    assert result["counts"].get("complexity", 0) >= 1


# ---------------------------------------------------------------------------
# _maybe_write: dry_run=False actually calls writer
# ---------------------------------------------------------------------------


def test_maybe_write_calls_writer_when_not_dry_run(tmp_path):
    module = _simple_module()
    adapter = _StubAdapter(module=module)
    g = _make_generator(tmp_path, adapter)
    mock_writer = MagicMock()
    g.writer = mock_writer
    g.run(dry_run=False)
    assert mock_writer.write_puml.called


def test_maybe_write_skips_writer_on_dry_run(tmp_path):
    module = _simple_module()
    adapter = _StubAdapter(module=module)
    g = _make_generator(tmp_path, adapter)
    mock_writer = MagicMock()
    g.writer = mock_writer
    g.run(dry_run=True)
    mock_writer.write_puml.assert_not_called()


def test_run_writes_complexity_subdiagram_non_dry_run(tmp_path):
    # dry_run=False with cc>=10 → _maybe_write called for complexity file (line 121)
    module = _simple_module(cc=10)
    adapter = _StubAdapter(module=module)
    g = _make_generator(tmp_path, adapter)
    mock_writer = MagicMock()
    g.writer = mock_writer
    g.run(dry_run=False)
    # At least one call should be for the complexity diagram
    calls = [str(c) for c in mock_writer.write_puml.call_args_list]
    assert any("complexity" in c for c in calls)


def test_discover_and_parse_skips_duplicate_paths(tmp_path):
    # Two adapters with the same extension → second finds file already in `seen`
    module = _simple_module()
    adapter1 = _StubAdapter(module=module, ext=".py")
    adapter2 = _StubAdapter(module=module, ext=".py")
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("x = 1")
    out = tmp_path / "out"
    g = generator.PUMLGenerator(
        src_root=src,
        out_root=out,
        adapters_factory=lambda: [adapter1, adapter2],
    )
    result = g.run(dry_run=True)
    # Only one class diagram — the duplicate was skipped
    assert result["counts"].get("class", 0) == 1


# ---------------------------------------------------------------------------
# PUMLGenerator: default adapters_factory (registry import path)
# ---------------------------------------------------------------------------


def test_generator_uses_registry_by_default(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "mod.py").write_text("x = 1")
    out = tmp_path / "out"
    # No adapters_factory provided → uses registry.get_all_adapters
    g = generator.PUMLGenerator(src_root=src, out_root=out)
    result = g.run(dry_run=True)
    assert "counts" in result
