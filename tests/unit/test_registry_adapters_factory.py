from uml_planterator import registry


class FakeJDTAdapter:
    def __init__(self, jdtls_client_factory=None):
        pass


class FakeJavalangAdapter:
    pass


class FakeJavaRegexAdapter:
    pass


def setup_registry_clean():
    # Recreate the singleton registry for test isolation
    registry._INSTANCE = registry.AdapterRegistry()


def test_register_default_adapters_prefers_jdtls(tmp_path, monkeypatch):
    setup_registry_clean()

    # Prepare a fake JDTLS path and create the file to make Path.exists() true
    jdtls_path = tmp_path / "jdtls.bin"
    jdtls_path.write_text("ok")

    # Monkeypatch adapter availability
    monkeypatch.setattr(registry, "JavaJDTAdapter", FakeJDTAdapter)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", None)
    monkeypatch.setattr(registry, "JavaAdapter", None)

    env = {"UML_PLANETATOR_JDTLS": str(jdtls_path)}
    registry.register_default_adapters(env=env)

    java_adapter = registry.get_adapter("java")
    assert isinstance(java_adapter, FakeJDTAdapter)


def test_register_default_adapters_falls_back_to_javalang(monkeypatch):
    setup_registry_clean()
    monkeypatch.setattr(registry, "JavaJDTAdapter", None)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", FakeJavalangAdapter)
    monkeypatch.setattr(registry, "JavaAdapter", None)

    registry.register_default_adapters(env={})
    java_adapter = registry.get_adapter("java")
    assert isinstance(java_adapter, FakeJavalangAdapter)


def test_register_default_adapters_falls_back_to_regex(monkeypatch):
    setup_registry_clean()
    monkeypatch.setattr(registry, "JavaJDTAdapter", None)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", None)
    monkeypatch.setattr(registry, "JavaAdapter", FakeJavaRegexAdapter)

    registry.register_default_adapters(env={})
    java_adapter = registry.get_adapter("java")
    assert isinstance(java_adapter, FakeJavaRegexAdapter)


def test_register_default_adapters_jdtls_path_not_exists_falls_back(
    tmp_path, monkeypatch
):
    # env var set but the path does not exist → falls through to javalang
    monkeypatch.setattr(registry, "JavaJDTAdapter", FakeJDTAdapter)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", FakeJavalangAdapter)
    setup_registry_clean()
    env = {"UML_PLANETATOR_JDTLS": str(tmp_path / "nonexistent.jar")}
    registry.register_default_adapters(env=env)
    assert isinstance(registry.get_adapter("java"), FakeJavalangAdapter)


def test_adapter_registry_get_raises_key_error_for_unknown_language():
    with __import__("pytest").raises(KeyError, match="unknown_xyz"):
        registry.get_adapter("unknown_xyz")


def test_register_adapter_and_get_adapter_roundtrip():
    sentinel = object()
    registry.register_adapter("test_lang_roundtrip", sentinel)
    assert registry.get_adapter("test_lang_roundtrip") is sentinel


def test_get_all_adapters_returns_list():
    adapters = registry.get_all_adapters()
    assert isinstance(adapters, list)
    assert len(adapters) > 0


# ---------------------------------------------------------------------------
# create_adapter
# ---------------------------------------------------------------------------


def test_create_adapter_raises_for_non_string():
    with __import__("pytest").raises(ValueError, match="non-empty string"):
        registry.create_adapter(123)  # type: ignore[arg-type]


def test_create_adapter_raises_for_empty_string():
    with __import__("pytest").raises(ValueError, match="non-empty string"):
        registry.create_adapter("")


def test_create_adapter_java_uses_jdtls_when_configured(tmp_path, monkeypatch):
    jar = tmp_path / "jdtls.jar"
    jar.write_text("")
    monkeypatch.setenv("UML_PLANETATOR_JDTLS", str(jar))
    monkeypatch.setattr(registry, "JavaJDTAdapter", FakeJDTAdapter)
    result = registry.create_adapter("java")
    assert isinstance(result, FakeJDTAdapter)


def test_create_adapter_java_uses_javalang_when_no_jdtls(monkeypatch):
    monkeypatch.delenv("UML_PLANETATOR_JDTLS", raising=False)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", FakeJavalangAdapter)
    result = registry.create_adapter("java")
    assert isinstance(result, FakeJavalangAdapter)


def test_create_adapter_java_uses_regex_when_neither(monkeypatch):
    monkeypatch.delenv("UML_PLANETATOR_JDTLS", raising=False)
    monkeypatch.setattr(registry, "JavaJavalangAdapter", None)
    monkeypatch.setattr(registry, "JavaAdapter", FakeJavaRegexAdapter)
    result = registry.create_adapter("java")
    assert isinstance(result, FakeJavaRegexAdapter)


def test_create_adapter_non_java_delegates_to_registry():
    adapter = registry.create_adapter("python")
    assert adapter is not None
    assert hasattr(adapter, "parse_source")
