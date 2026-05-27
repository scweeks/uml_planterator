"""Adapter that uses JDT LS (via `JDTLSClient`) to produce rich ModuleInfo.

If `UML_PLANETATOR_JDTLS` env var is not set or JDT LS cannot be started,
this adapter falls back to the `java_javalang_adapter` implementation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from uml_planterator import models
from uml_planterator.adapters.base import Adapter, AdapterError

try:
    from uml_planterator.lsp.jdtls_client import JDTLSClient
except ImportError:  # pragma: no cover - import-time fallback handling
    JDTLSClient = None  # type: ignore


class JavaJDTAdapter(Adapter):
    def __init__(self, jdtls_client_factory: Optional[callable] = None) -> None:
        self._jdtls_client_factory = jdtls_client_factory

    @property
    def language(self) -> str:
        return "java-jdtls"

    def supported_extensions(self) -> list[str]:
        return [".java"]

    def _make_client(self, cmd: list[str], workspace: Path):
        if self._jdtls_client_factory:
            return self._jdtls_client_factory(cmd, workspace)
        # Prefer the module-level JDTLSClient if available
        if JDTLSClient is not None:
            return JDTLSClient(cmd, workspace)
        raise AdapterError("JDTLSClient not available")

    def parse_source(self, path: Path, source: str) -> models.ModuleInfo:
        jdtls_jar = os.environ.get("UML_PLANETATOR_JDTLS")
        if not jdtls_jar or not Path(jdtls_jar).exists() or JDTLSClient is None:
            # Fallback path should either return a ModuleInfo or raise
            try:
                from uml_planterator.adapters.java_javalang_adapter import (
                    JavaJavalangAdapter,
                )

                return JavaJavalangAdapter().parse_source(path, source)
            except Exception as exc:
                raise AdapterError("No suitable Java adapter available") from exc

        # Start a temporary workspace rooted at the file's parent
        workspace = path.parent
        cmd = ["java", "-jar", str(jdtls_jar), "-data", str(workspace)]
        client = self._make_client(cmd, workspace)
        try:
            client.start()
            client.initialize(f"file://{workspace}")
            client.open_text_document(path, source)

            # Request document symbols
            resp = client.request(
                "textDocument/documentSymbol",
                {"textDocument": {"uri": f"file://{path}"}},
            )
            results = resp.get("result") or []

            classes: list[models.ClassInfo] = []
            for item in results:
                # item may be DocumentSymbol or SymbolInformation
                name = item.get("name")
                children = item.get("children") or []
                methods = []
                attributes = []
                for c in children:
                    c_name = c.get("name")
                    # Heuristic: symbol kind 6 = Method (not all servers use
                    # numeric kind codes)
                    kind = c.get("kind")
                    if kind == 6 or c.get("children") is None:
                        methods.append(models.MethodInfo(name=c_name))
                    else:
                        attributes.append(models.AttributeInfo(name=c_name))

                classes.append(
                    models.ClassInfo(name=name, attributes=attributes, methods=methods)
                )

            module = models.ModuleInfo(
                name=path.stem,
                package=path.parent.name,
                rel_path=str(path.relative_to(path.parent)),
                classes=classes,
                top_level_functions=[],
                imports=[],
                internal_imports=[],
                has_main=False,
                has_cli=False,
                is_init=False,
                public_exports=[],
                cc=sum((cls.cc for cls in classes), 0) or 1,
            )
            return module
        except Exception as exc:  # pragma: no cover - runtime errors
            raise AdapterError("JDT LS adapter failed") from exc
        finally:
            try:
                client.shutdown()
            except OSError:
                pass

    def compute_complexity(self, module: models.ModuleInfo) -> int:
        return int(getattr(module, "cc", 1))
