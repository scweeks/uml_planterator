"""Tests for renderers.py — 100% line and branch coverage."""

from uml_planterator import models, renderers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _method(name="do", params=None, return_type="", calls=None):
    return models.MethodInfo(
        name=name,
        params=params or [],
        return_type=return_type,
        calls=calls or [],
    )


def _attr(name="value", type_hint="", visibility="+"):
    return models.AttributeInfo(name=name, type_hint=type_hint, visibility=visibility)


def _mod(
    name="mod",
    package="pkg.mod",
    rel_path="pkg/mod.py",
    classes=None,
    top_level_functions=None,
    is_init=False,
):
    return models.ModuleInfo(
        name=name,
        package=package,
        rel_path=rel_path,
        classes=classes or [],
        top_level_functions=top_level_functions or [],
        is_init=is_init,
    )


def _cls(
    name="MyClass",
    attributes=None,
    methods=None,
    docstring="",
    is_abstract=False,
    state_attributes=None,
):
    return models.ClassInfo(
        name=name,
        attributes=attributes or [],
        methods=methods or [],
        docstring=docstring,
        is_abstract=is_abstract,
        state_attributes=state_attributes or [],
    )


# ---------------------------------------------------------------------------
# gen_class_diagram
# ---------------------------------------------------------------------------


def test_gen_class_diagram_structure():
    cls = _cls()
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert out.startswith("@startuml mod-MyClass")
    assert out.endswith("@enduml")
    assert "title MyClass" in out


def test_gen_class_diagram_attribute_with_type_hint():
    cls = _cls(attributes=[_attr("count", type_hint="int")])
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "+ count : int" in out


def test_gen_class_diagram_attribute_no_type_hint():
    cls = _cls(attributes=[_attr("count", type_hint="")])
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "+ count" in out
    assert "+ count :" not in out


def test_gen_class_diagram_method_with_return_type():
    cls = _cls(methods=[_method("run", return_type="bool")])
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "run() : bool" in out


def test_gen_class_diagram_method_no_return_type():
    cls = _cls(methods=[_method("run", return_type="")])
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "run()" in out
    assert "run() :" not in out


def test_gen_class_diagram_method_with_params():
    p = models.Param("x", "int")
    cls = _cls(methods=[_method("run", params=[p])])
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "run(x: int)" in out


def test_gen_class_diagram_with_docstring_renders_note():
    cls = _cls(docstring="First line\nSecond line")
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "note bottom of" in out
    assert "First line" in out
    assert "end note" in out


def test_gen_class_diagram_no_docstring_omits_note():
    cls = _cls(docstring="")
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "note bottom of" not in out


def test_gen_class_diagram_docstring_truncated_at_100_chars():
    long_doc = "A" * 150
    cls = _cls(docstring=long_doc)
    mod = _mod(classes=[cls])
    out = renderers.gen_class_diagram(cls, mod)
    assert "A" * 100 in out
    assert "A" * 101 not in out


# ---------------------------------------------------------------------------
# gen_package_diagram
# ---------------------------------------------------------------------------


def test_gen_package_diagram_lists_class():
    cls = _cls()
    mod = _mod(classes=[cls])
    out = renderers.gen_package_diagram([mod], "pkg.mod")
    assert "@startuml pkg.mod-package" in out
    assert "MyClass" in out


def test_gen_package_diagram_skips_init_module():
    cls = _cls()
    init_mod = _mod(name="__init__", classes=[cls], is_init=True)
    out = renderers.gen_package_diagram([init_mod], "pkg")
    assert "MyClass" not in out


def test_gen_package_diagram_skips_module_with_no_classes():
    mod = _mod(classes=[])
    out = renderers.gen_package_diagram([mod], "pkg")
    assert "package mod" not in out


def test_gen_package_diagram_abstract_class_gets_stereotype():
    cls = _cls(is_abstract=True)
    mod = _mod(classes=[cls])
    out = renderers.gen_package_diagram([mod], "pkg")
    assert "<<abstract>>" in out


def test_gen_package_diagram_non_abstract_no_stereotype():
    cls = _cls(is_abstract=False)
    mod = _mod(classes=[cls])
    out = renderers.gen_package_diagram([mod], "pkg")
    assert "<<abstract>>" not in out


# ---------------------------------------------------------------------------
# gen_system_package_diagram
# ---------------------------------------------------------------------------


def test_gen_system_package_diagram_groups_by_top_package():
    m1 = _mod(name="a", package="pkg.a")
    m2 = _mod(name="b", package="pkg.b")
    m3 = _mod(name="c", package="other.c")
    out = renderers.gen_system_package_diagram([m1, m2, m3], src_name="src")
    assert "component [pkg] as pkg" in out
    assert "component [other] as other" in out


def test_gen_system_package_diagram_empty_modules():
    out = renderers.gen_system_package_diagram([])
    assert "@startuml system-package-overview" in out
    assert "@enduml" in out
    assert "component" not in out


def test_gen_system_package_diagram_deduplicates_packages():
    m1 = _mod(name="a", package="pkg.a")
    m2 = _mod(name="b", package="pkg.b")
    out = renderers.gen_system_package_diagram([m1, m2])
    assert out.count("component [pkg]") == 1


# ---------------------------------------------------------------------------
# gen_component_diagram
# ---------------------------------------------------------------------------


def test_gen_component_diagram_lists_components():
    m1 = _mod(name="alpha")
    m2 = _mod(name="beta")
    out = renderers.gen_component_diagram([m1, m2], name="mycomps")
    assert "@startuml mycomps" in out
    assert "title Component View — mycomps" in out
    assert "component [alpha]" in out
    assert "component [beta]" in out
    assert out.endswith("@enduml")


def test_gen_component_diagram_empty_modules():
    out = renderers.gen_component_diagram([])
    assert "@startuml components" in out
    assert "component [" not in out


def test_gen_component_diagram_uses_default_name():
    out = renderers.gen_component_diagram([])
    assert "@startuml components" in out


# ---------------------------------------------------------------------------
# gen_sequence_diagram
# ---------------------------------------------------------------------------


def test_gen_sequence_diagram_structure():
    cls = _cls()
    mod = _mod(name="svc", classes=[cls])
    out = renderers.gen_sequence_diagram(mod)
    assert "@startuml svc-sequence" in out
    assert "title Sequence — svc" in out
    assert "participant MyClass" in out
    assert "@enduml" in out


def test_gen_sequence_diagram_renders_method_calls():
    m = _method("act", calls=[("OtherClass", "doSomething")])
    cls = _cls(methods=[m])
    mod = _mod(classes=[cls])
    out = renderers.gen_sequence_diagram(mod)
    assert "MyClass -> OtherClass: doSomething" in out


def test_gen_sequence_diagram_no_classes():
    mod = _mod(classes=[])
    out = renderers.gen_sequence_diagram(mod)
    assert "participant" not in out
    assert "@enduml" in out


def test_gen_sequence_diagram_class_with_no_methods():
    cls = _cls(methods=[])
    mod = _mod(classes=[cls])
    out = renderers.gen_sequence_diagram(mod)
    assert "participant MyClass" in out
    assert "->" not in out


def test_gen_sequence_diagram_participants_sorted():
    c1 = _cls(name="Zebra")
    c2 = _cls(name="Alpha")
    mod = _mod(classes=[c1, c2])
    out = renderers.gen_sequence_diagram(mod)
    alpha_pos = out.index("participant Alpha")
    zebra_pos = out.index("participant Zebra")
    assert alpha_pos < zebra_pos


# ---------------------------------------------------------------------------
# gen_activity_diagram
# ---------------------------------------------------------------------------


def test_gen_activity_diagram_structure():
    fn = _method("load")
    mod = _mod(name="svc", top_level_functions=[fn])
    out = renderers.gen_activity_diagram(mod)
    assert "@startuml svc-activity" in out
    assert "title Activity — svc" in out
    assert "start" in out
    assert ":load();" in out
    assert "stop" in out
    assert "@enduml" in out


def test_gen_activity_diagram_no_functions():
    mod = _mod(top_level_functions=[])
    out = renderers.gen_activity_diagram(mod)
    assert "start" in out
    assert "stop" in out
    assert "();" not in out


def test_gen_activity_diagram_multiple_functions():
    fns = [_method("step_one"), _method("step_two")]
    mod = _mod(top_level_functions=fns)
    out = renderers.gen_activity_diagram(mod)
    assert ":step_one();" in out
    assert ":step_two();" in out


# ---------------------------------------------------------------------------
# gen_state_diagram
# ---------------------------------------------------------------------------


def test_gen_state_diagram_structure():
    cls = _cls(name="Order", state_attributes=["pending", "shipped"])
    out = renderers.gen_state_diagram(cls)
    assert "@startuml Order-state" in out
    assert "title State — Order" in out
    assert "[*]" in out
    assert "state pending" in out
    assert "state shipped" in out
    assert "@enduml" in out


def test_gen_state_diagram_no_states():
    cls = _cls(state_attributes=[])
    out = renderers.gen_state_diagram(cls)
    assert "[*]" in out
    assert "state " not in out


# ---------------------------------------------------------------------------
# gen_usecase_diagram
# ---------------------------------------------------------------------------


def test_gen_usecase_diagram_renders_actor_and_usecases():
    fn = _method("place_order")
    mod = _mod(name="checkout", top_level_functions=[fn])
    out = renderers.gen_usecase_diagram([mod], name="shop")
    assert "@startuml shop" in out
    assert "title Usecase — shop" in out
    assert "actor checkoutUser" in out
    assert "checkoutUser -> (place_order)" in out
    assert "@enduml" in out


def test_gen_usecase_diagram_skips_module_with_no_functions():
    mod = _mod(name="empty", top_level_functions=[])
    out = renderers.gen_usecase_diagram([mod])
    assert "emptyUser" not in out


def test_gen_usecase_diagram_multiple_modules():
    fn1 = _method("action_a")
    fn2 = _method("action_b")
    mod1 = _mod(name="svc1", top_level_functions=[fn1])
    mod2 = _mod(name="svc2", top_level_functions=[fn2])
    out = renderers.gen_usecase_diagram([mod1, mod2])
    assert "svc1User" in out
    assert "svc2User" in out
    assert "(action_a)" in out
    assert "(action_b)" in out


def test_gen_usecase_diagram_default_name():
    out = renderers.gen_usecase_diagram([])
    assert "@startuml usecases" in out
