from uml_planterator import registry


class FakeJDTAdapter:
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
