from uml_planterator import registry


def test_adapters_expose_language_and_extensions():
    for lang in ("python", "cpp", "c"):
        adapter = registry.get_adapter(lang)
        # Adapter must expose a language identifier
        assert hasattr(adapter, "language")
        assert isinstance(adapter.language, str)
        # Adapter must declare supported extensions
        assert hasattr(adapter, "supported_extensions")
        exts = adapter.supported_extensions()
        assert isinstance(exts, list)
        assert all(isinstance(e, str) for e in exts)


def test_compute_complexity_available():
    adapter = registry.get_adapter("python")

    # compute_complexity should return an int (fallback to module.cc)
    # Create a minimal fake ModuleInfo-like object
    class M:
        cc = 3

    assert hasattr(adapter, "compute_complexity")
    val = adapter.compute_complexity(M())
    assert isinstance(val, int)
