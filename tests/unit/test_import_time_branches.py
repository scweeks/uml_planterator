import builtins
import importlib
from pathlib import Path
from types import ModuleType


def test_java_jdt_adapter_import_fallback(monkeypatch, tmp_path: Path):
    # Simulate ImportError when importing the lsp client at module import-time
    real_import = builtins.__import__

    def _fake_import(name, _globals=None, _locals=None, fromlist=(), level=0):
        if name == "uml_planterator.lsp.jdtls_client":
            raise ImportError()
        return real_import(name, _globals, _locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    # Reload the module under test
    mod = importlib.import_module("uml_planterator.adapters.java_jdt_adapter")
    importlib.reload(mod)
    # After reload, JDTLSClient should be set (to None) due to ImportError
    assert getattr(mod, "JDTLSClient") is None


def test_registry_import_order_branches(monkeypatch, tmp_path: Path):
    # Simulate importlib.import_module to test javalang/java_adapter branches
    import importlib as _importlib

    real_import_module = _importlib.import_module

    def fake_import_module(name, _package=None):
        if name == "uml_planterator.adapters.java_javalang_adapter":
            m = ModuleType(name)

            class A:
                pass

            setattr(m, "JavaJavalangAdapter", A)
            return m
        if name == "uml_planterator.adapters.java_adapter":
            m = ModuleType(name)

            class B:
                pass

            setattr(m, "JavaAdapter", B)
            return m
        return real_import_module(name, package=_package)

    monkeypatch.setattr(_importlib, "import_module", fake_import_module)
    # Load the registry source into an isolated module to avoid polluting
    # the global import state used by other tests.
    from importlib import util

    p = Path(__file__).resolve()
    registry_path = None
    for anc in p.parents:
        candidate = anc / "src" / "uml_planterator" / "registry.py"
        if candidate.exists():
            registry_path = candidate
            break
    assert registry_path is not None
    spec = util.spec_from_file_location("temp_registry", str(registry_path))
    temp_reg = util.module_from_spec(spec)
    spec.loader.exec_module(temp_reg)
    a = temp_reg.get_adapter("java")
    assert a is not None
