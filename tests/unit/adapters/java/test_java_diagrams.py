from pathlib import Path

import pytest

from uml_planterator import registry, renderers


def make_java_file(path: Path):
    content = """
public class A {
    private int state;

    public void doIt() {
        Other.process();
    }
}

public class Other {
    public static void process() {}
}
"""
    path.write_text(content)


def test_java_diagrams_generate(tmp_path: Path):
    src = tmp_path / "java_src"
    src.mkdir()
    f = src / "A.java"
    make_java_file(f)

    try:
        adapter = registry.get_adapter("java")
    except KeyError:
        pytest.xfail("Java adapter not implemented yet")

    mod = adapter.parse_source(f, f.read_text())
    assert mod is not None

    # Class diagram
    if mod.classes:
        cls = mod.classes[0]
        out = renderers.gen_class_diagram(cls, mod)
        assert out.startswith("@startuml") and out.endswith("@enduml")

    # Package & system diagrams
    _ = renderers.gen_package_diagram([mod], "pkg")
    _ = renderers.gen_system_package_diagram([mod])

    # Ensure renderers run without error
    _ = renderers.gen_component_diagram([mod])
    _ = renderers.gen_sequence_diagram(mod)
    _ = renderers.gen_activity_diagram(mod)
    if mod.classes:
        _ = renderers.gen_state_diagram(mod.classes[0])
    _ = renderers.gen_usecase_diagram([mod])
