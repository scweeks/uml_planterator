"""Adapter that uses JDT LS (via `JDTLSClient`) to produce rich ModuleInfo.

If `UML_PLANETATOR_JDTLS` env var is not set or JDT LS cannot be started,
this adapter falls back to the `java_javalang_adapter` implementation.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from uml_planterator.adapters.base import Adapter, AdapterError
from uml_planterator import models


try:
    from uml_planterator.lsp.jdtls_client import JDTLSClient
except ImportError:  # pragma: no cover - import-time fallback handling
    JDTLSClient = None  # type: ignore


class JavaJDTAdapter(Adapter):
    @property
    def language(self) -> str:
        return "java-jdtls"

    def supported_extensions(self) -> list[str]:
        return [".java"]

    def _fallback(
        self, path: Path, source: str
    ) -> Optional[models.ModuleInfo]:
        # Defer to javalang-backed adapter if available
        try:
            from uml_planterator.adapters.java_javalang_adapter import (
                JavaJavalangAdapter,
            )

            return JavaJavalangAdapter().parse_source(path, source)
        except Exception:
            return None

    def parse_source(
        self, path: Path, source: str
    ) -> Optional[models.ModuleInfo]:
        jdtls_jar = os.environ.get("UML_PLANETATOR_JDTLS")
        if (
            not jdtls_jar
            or not Path(jdtls_jar).exists()
            or JDTLSClient is None
        ):
            return self._fallback(path, source)

        # Start a temporary workspace rooted at the file's parent
        workspace = path.parent
        cmd = ["java", "-jar", str(jdtls_jar), "-data", str(workspace)]
        client = JDTLSClient(cmd, workspace)
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
                    models.ClassInfo(
                        name=name, attributes=attributes, methods=methods
                    )
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
        except Exception as exc:  # pragma: no cover - runtime errors should surface
            raise AdapterError("JDT LS adapter failed") from exc
        finally:
            try:
                client.shutdown()
            except OSError:
                pass

    def compute_complexity(self, module: models.ModuleInfo) -> int:
        return int(getattr(module, "cc", 1))
