"""Data models for UML generation.

These mirror the original structures but are kept in a dedicated module
to improve testability and separation of concerns.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class Param:
    name: str
    type_hint: str = ""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.name}: {self.type_hint}" if self.type_hint else self.name


@dataclass
class MethodInfo:
    name: str
    params: List[Param] = field(default_factory=list)
    return_type: str = ""
    visibility: str = "+"
    is_static: bool = False
    is_class_method: bool = False
    is_property: bool = False
    is_abstract: bool = False
    cc: int = 1
    calls: List[Tuple[str, str]] = field(default_factory=list)
    raises: List[str] = field(default_factory=list)
    state_transitions: List[Tuple[str, str, str]] = field(default_factory=list)
    docstring: str = ""
    lineno: int = 0
    line_count: int = 0


@dataclass
class AttributeInfo:
    name: str
    type_hint: str = ""
    visibility: str = "-"
    is_class_var: bool = False


@dataclass
class ClassInfo:
    name: str
    bases: List[str] = field(default_factory=list)
    attributes: List[AttributeInfo] = field(default_factory=list)
    methods: List[MethodInfo] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: str = ""
    is_abstract: bool = False
    is_dataclass: bool = False
    has_state: bool = False
    state_attributes: List[str] = field(default_factory=list)
    cc: int = 1


@dataclass
class ModuleInfo:
    name: str
    package: str
    rel_path: str
    classes: List[ClassInfo] = field(default_factory=list)
    top_level_functions: List[MethodInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    internal_imports: List[str] = field(default_factory=list)
    has_main: bool = False
    has_cli: bool = False
    is_init: bool = False
    public_exports: List[str] = field(default_factory=list)
    cc: int = 1
