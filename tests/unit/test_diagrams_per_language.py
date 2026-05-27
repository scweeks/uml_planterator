from pathlib import Path

from uml_planterator import registry, renderers


def create_python_source_with_features(path: Path):
    content = """
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
    path.write_text(content)


def test_all_diagrams_for_python(tmp_path: Path):
    src = tmp_path / "p"
    src.mkdir()
    f = src / "m.py"
    create_python_source_with_features(f)

    adapter = registry.get_adapter("python")
    mod = adapter.parse_source(f, f.read_text())
    assert mod is not None

    # Class diagram
    cls = mod.classes[0]
    out = renderers.gen_class_diagram(cls, mod)
    assert out.startswith("@startuml") and out.endswith("@enduml")
    assert cls.name in out

    # Package diagram
    out = renderers.gen_package_diagram([mod], "pkg")
    assert out.startswith("@startuml")

    # System package
    out = renderers.gen_system_package_diagram([mod])
    assert "@startuml" in out

    # Component
    out = renderers.gen_component_diagram([mod])
    assert "component" in out

    # Sequence (should include a call arrow)
    out = renderers.gen_sequence_diagram(mod)
    assert "->" in out or "participant" in out

    # Activity (top-level function)
    out = renderers.gen_activity_diagram(mod)
    assert "start" in out and "stop" in out

    # State diagram
    out = renderers.gen_state_diagram(cls)
    assert "state" in out

    # Usecase
    out = renderers.gen_usecase_diagram([mod])
    assert "actor" in out or "usecase" in out


def test_all_diagrams_for_c_and_cpp(tmp_path: Path):
    examples = {
        "c": ("mod.c", "typedef struct Foo { int x; } Foo;\n"),
        "cpp": ("mod.cpp", "class A { };\n"),
    }
    for lang, (fname, content) in examples.items():
        src = tmp_path / lang
        src.mkdir()
        f = src / fname
        f.write_text(content)

        adapter = registry.get_adapter(lang)
        mod = adapter.parse_source(f, f.read_text())
        assert mod is not None

        # Class diagram
        if mod.classes:
            cls = mod.classes[0]
            out = renderers.gen_class_diagram(cls, mod)
            assert out.startswith("@startuml") and out.endswith("@enduml")

        # Package diagram
        out = renderers.gen_package_diagram([mod], "pkg")
        assert out.startswith("@startuml")

        # System package
        out = renderers.gen_system_package_diagram([mod])
        assert "@startuml" in out

        # Component
        out = renderers.gen_component_diagram([mod])
        assert "component" in out

        # Sequence/activity/state/usecase may be empty for C/C++;
        # ensure no exceptions are raised when generating them
        _ = renderers.gen_sequence_diagram(mod)
        _ = renderers.gen_activity_diagram(mod)
        if mod.classes:
            _ = renderers.gen_state_diagram(mod.classes[0])
        _ = renderers.gen_usecase_diagram([mod])
