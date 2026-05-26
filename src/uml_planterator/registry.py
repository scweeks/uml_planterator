"""Adapter registry implementing a singleton registry/factory.

Provides `get_adapter` and `register_adapter` convenience functions that
delegate to the singleton `AdapterRegistry` instance. This follows the
Factory and Singleton patterns to manage adapters.
"""
from __future__ import annotations

from typing import Dict
from uml_planterator.adapters.python_adapter import PythonAdapter
from uml_planterator.adapters.cpp_adapter import CppAdapter
from uml_planterator.adapters.c_adapter import CAdapter


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


def get_adapter(language: str):
    return _INSTANCE.get(language)


def register_adapter(language: str, adapter: object) -> None:
    _INSTANCE.register(language, adapter)


def get_all_adapters():
    return _INSTANCE.all_adapters()
