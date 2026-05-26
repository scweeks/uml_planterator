from uml_planterator import utils


def test_safe_id_sanitizes_and_uniquifies():
    a = utils.safe_id("My-Class@v1")
    b = utils.safe_id("My Class v1")
    assert a != ""
    assert b != ""
    assert " " not in a
    assert "@" not in a
    # calling again returns same alias
    assert utils.safe_id("My-Class@v1") == a


def test_vis_and_is_dunder():
    assert utils.vis("__private") == "-"
    assert utils.vis("_protected") == "#"
    assert utils.vis("public") == "+"
    assert utils.is_dunder("__init__") is True
    assert utils.is_dunder("_not_dunder_") is False
