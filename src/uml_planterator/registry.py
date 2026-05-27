"""Adapter registry implementing a singleton registry/factory.

Provides `get_adapter` and `register_adapter` convenience functions that
delegate to the singleton `AdapterRegistry` instance. This follows the
Factory and Singleton patterns to manage adapters.
"""
from __future__ import annotations

from typing import Dict
import os
from pathlib import Path
from uml_planterator.adapters.python_adapter import PythonAdapter
from uml_planterator.adapters.cpp_adapter import CppAdapter
from uml_planterator.adapters.c_adapter import CAdapter
import importlib

# Import the richer Java adapter if available; otherwise fall back to the
# lightweight regex-based adapter. Use importlib to keep line lengths short
# and to catch ImportError specifically.
JavaJavalangAdapter = None
JavaAdapter = None
JavaJDTAdapter = None
try:
    _mod = importlib.import_module(
        "uml_planterator.adapters.java_javalang_adapter"
    )
    JavaJavalangAdapter = getattr(_mod, "JavaJavalangAdapter")
except ImportError:
    _mod = importlib.import_module("uml_planterator.adapters.java_adapter")
    JavaAdapter = getattr(_mod, "JavaAdapter")

# Try to import the JDT LS backed adapter; registration depends on
# the presence of a configured JDT LS (UML_PLANETATOR_JDTLS env var).
try:
    _mod2 = importlib.import_module(
        "uml_planterator.adapters.java_jdt_adapter"
    )
    JavaJDTAdapter = getattr(_mod2, "JavaJDTAdapter")
except ImportError:
    JavaJDTAdapter = None


class AdapterRegistry:
    """Singleton-style registry for adapters.

    Use `register` to add adapters and `get` to retrieve them by language
    identifier.
    """

    def __init__(self) -> None:
        self._map: Dict[str, object] = {}

    def register(self, language: str, adapter: object) -> None:
        self._map[language.lower()] = adapter

    def get(self, language: str):
        key = language.lower()
        if key in self._map:
            return self._map[key]
        raise KeyError(f"No adapter registered for language: {language}")

    def all_adapters(self):
        """Return a list of all registered adapter instances."""
        return list(self._map.values())


# Create the global registry and register default adapters
_INSTANCE = AdapterRegistry()
_INSTANCE.register("python", PythonAdapter())
_INSTANCE.register("cpp", CppAdapter())
_INSTANCE.register("c", CAdapter())

# If the environment points to a JDT LS launcher JAR and the adapter is
# available, register the JDT-based adapter as the `java` backend. This
# allows CI/dev to opt-in by setting `UML_PLANETATOR_JDTLS` to the
# launcher jar path. Otherwise, prefer the javalang adapter or the
# lightweight regex adapter.
jdtls_path = os.environ.get("UML_PLANETATOR_JDTLS")
if jdtls_path and Path(jdtls_path).exists() and JavaJDTAdapter:
    _INSTANCE.register("java", JavaJDTAdapter())
elif JavaJavalangAdapter:
    _INSTANCE.register("java", JavaJavalangAdapter())
else:
    _INSTANCE.register("java", JavaAdapter())


def get_adapter(language: str):
    return _INSTANCE.get(language)


def register_adapter(language: str, adapter: object) -> None:
    _INSTANCE.register(language, adapter)


def get_all_adapters():
    return _INSTANCE.all_adapters()


def create_adapter(language: str, **kwargs):
    """Factory: create an adapter instance for `language`.

    Optional kwargs may include `jdtls_client_factory` used to inject a
    testable `JDTLSClient` into the `JavaJDTAdapter`.
    """
    if not isinstance(language, str) or not language:
        raise ValueError("language must be a non-empty string")
    key = language.lower()
    if key == "java":
        jdtls_factory = kwargs.get("jdtls_client_factory")
        env_jdtls = os.environ.get("UML_PLANETATOR_JDTLS")
        if env_jdtls and Path(env_jdtls).exists() and JavaJDTAdapter:
            return JavaJDTAdapter(jdtls_client_factory=jdtls_factory)
        if JavaJavalangAdapter:
            return JavaJavalangAdapter()
        return JavaAdapter()
    # Defer to existing registry for other languages
    return _INSTANCE.get(language)
