import os
from pathlib import Path

import pytest

from uml_planterator.adapters.java_jdt_adapter import JavaJDTAdapter


@pytest.mark.system
def test_jdtls_adapter_parse_simple(tmp_path: Path):
    jdtls = os.environ.get("UML_PLANETATOR_JDTLS")
    if not jdtls:
        pytest.skip("JDT LS not configured (UML_PLANETATOR_JDTLS unset)")

    src_dir = tmp_path / "src" / "com" / "example"
    src_dir.mkdir(parents=True)
    main = src_dir / "Main.java"
    main.write_text(
        """
        package com.example;

        public class Main {
            public static void main(String[] args) {
                Service s = new Service();
                s.doWork();
            }
        }
        """
    )

    service = src_dir / "Service.java"
    service.write_text(
        """
        package com.example;

        public class Service {
            public void doWork() {
                if (System.currentTimeMillis() % 2 == 0) {
                    System.out.println("even");
                } else {
                    System.out.println("odd");
                }
            }
        }
        """
    )

    adapter = JavaJDTAdapter()
    mod = adapter.parse_source(main, main.read_text())
    assert mod is not None
    # Expect at least one class (Main)
    assert any(c.name == "Main" for c in mod.classes)
