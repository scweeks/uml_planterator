"""uml_planterator package — modular PlantUML generator.

This package provides a modular API for parsing Python code and
rendering PlantUML diagrams. It is intentionally minimal at this
stage; functions are split across submodules for testability.

Public API is provided by `generator.PUMLGenerator` in later iterations.
"""
__all__ = ["models", "parsers", "renderers", "utils", "complexity", "generator"]

__version__ = "0.0.0"
