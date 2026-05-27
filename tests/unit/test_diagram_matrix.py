from pathlib import Path

import pytest

from uml_planterator import registry, renderers


PY_SRC = """
class A:
    def __init__(self):
        self.state = 'init'

    def do(self):
        Other.process()

def top_func():
    return 1

class Other:
    @staticmethod
    def process():
        pass

"""


CPP_SRC = "class A { };\n"


C_SRC = "typedef struct Foo { int x; } Foo;\n"


JAVA_SRC = """
public class A {
    private int state;

    public void doIt() { Other.process(); }
}

public class Other { public static void process() {} }
"""


DIAGRAMS = [
    "class",
    "package",
    "system_package",
    "component",
    "sequence",
    "activity",
    "state",
    "usecase",
]


@pytest.mark.parametrize("lang,filename,src", [
    ("python", "m.py", PY_SRC),
    ("c", "m.c", C_SRC),
    ("cpp", "m.cpp", CPP_SRC),
    ("java", "A.java", JAVA_SRC),
])
@pytest.mark.parametrize("diagram", DIAGRAMS)
def test_diagram_matrix(
    tmp_path: Path, lang: str, filename: str, src: str, diagram: str
):
    src_root = tmp_path / "src"
    src_root.mkdir()
    f = src_root / filename
    f.write_text(src)

    try:
        adapter = registry.get_adapter(lang)
    except KeyError:
        pytest.xfail(f"Adapter for {lang} not implemented")

    mod = adapter.parse_source(f, f.read_text())
    assert mod is not None

    out = ""

    # Choose renderer based on diagram type
    if diagram == "class":
        if not mod.classes:
            pytest.skip("no classes to render")
        out = renderers.gen_class_diagram(mod.classes[0], mod)
    elif diagram == "package":
        out = renderers.gen_package_diagram([mod], "pkg")
    elif diagram == "system_package":
        out = renderers.gen_system_package_diagram([mod])
    elif diagram == "component":
        out = renderers.gen_component_diagram([mod])
    elif diagram == "sequence":
        out = renderers.gen_sequence_diagram(mod)
    elif diagram == "activity":
        out = renderers.gen_activity_diagram(mod)
    elif diagram == "state":
        if not mod.classes:
            pytest.skip("no classes for state diagram")
        out = renderers.gen_state_diagram(mod.classes[0])
    elif diagram == "usecase":
        out = renderers.gen_usecase_diagram([mod])
    else:
        pytest.skip("unknown diagram")

    assert out.startswith("@startuml") and out.strip().endswith("@enduml")
