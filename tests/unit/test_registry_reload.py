import importlib
import sys
from types import ModuleType
from pathlib import Path


def test_registry_registers_jdt_when_env_and_adapter_present(
    monkeypatch, tmp_path: Path
):
    # Create a fake jar file and set env var
    jar = tmp_path / "jdtls.jar"
    jar.write_text("")
    monkeypatch.setenv("UML_PLANETATOR_JDTLS", str(jar))

    # Create a fake module for uml_planterator.adapters.java_jdt_adapter
    fake_mod = ModuleType("uml_planterator.adapters.java_jdt_adapter")

    class FakeJDTAdapter:
        def __init__(self):
            pass

    setattr(fake_mod, "JavaJDTAdapter", FakeJDTAdapter)
    sys.modules["uml_planterator.adapters.java_jdt_adapter"] = fake_mod

    # Reload registry to pick up new module and env var
    reg = importlib.import_module("uml_planterator.registry")
    importlib.reload(reg)

    # get_adapter should return something for java
    adapter = reg.get_adapter("java")
    assert adapter is not None
