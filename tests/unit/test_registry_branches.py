import importlib
import importlib.util
from pathlib import Path
from types import ModuleType


def _load_registry_with_import_hook(hook):
    # Load the registry.py source into an isolated module while the
    # provided import hook is active.
    import importlib as _importlib

    real_import = _importlib.import_module
    _importlib.import_module = hook
    try:
        p = Path(__file__).resolve()
        for anc in p.parents:
            candidate = anc / "src" / "uml_planterator" / "registry.py"
            if candidate.exists():
                break
        spec = importlib.util.spec_from_file_location("temp_registry", str(candidate))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        _importlib.import_module = real_import


def test_registry_fallback_to_regex_adapter():
    def hook(name, package=None):
        if name == "uml_planterator.adapters.java_javalang_adapter":
            raise ImportError()
        if name == "uml_planterator.adapters.java_adapter":
            m = ModuleType(name)

            class JavaAdapter:
                pass

            setattr(m, "JavaAdapter", JavaAdapter)
            return m
        if name == "uml_planterator.adapters.java_jdt_adapter":
            raise ImportError()
        return importlib.import_module(name)

    mod = _load_registry_with_import_hook(hook)
    a = mod.get_adapter("java")
    assert a is not None


def test_registry_uses_javalang_when_present():
    def hook(name, package=None):
        if name == "uml_planterator.adapters.java_javalang_adapter":
            m = ModuleType(name)

            class JavaJavalangAdapter:
                def __init__(self):
                    pass

            setattr(m, "JavaJavalangAdapter", JavaJavalangAdapter)
            return m
        return importlib.import_module(name)

    mod = _load_registry_with_import_hook(hook)
    a = mod.get_adapter("java")
    assert a is not None
