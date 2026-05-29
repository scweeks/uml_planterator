"""Tests for utils.py — 100% line and branch coverage."""

import ast
from unittest.mock import patch

from uml_planterator import utils


def test_safe_id_sanitizes_special_characters():
    a = utils.safe_id("My-Class@v1")
    assert "@" not in a
    assert "-" not in a


def test_safe_id_is_deterministic():
    a = utils.safe_id("SomeClass")
    assert utils.safe_id("SomeClass") == a


def test_safe_id_empty_name_becomes_id():
    # empty string → base is empty after sanitisation → falls back to "id"
    result = utils.safe_id("")
    assert result == "id"


def test_safe_id_leading_digit_gets_prefixed():
    result = utils.safe_id("3foo")
    assert result.startswith("id_")
    assert "3foo" in result


def test_safe_id_collision_resolved_with_suffix():
    utils.reset_id_map()
    # "A-B" and "A B" both sanitise to "A_B" — second gets a numeric suffix
    first = utils.safe_id("A-B")
    second = utils.safe_id("A B")
    assert first != second
    assert first == "A_B"
    assert second == "A_B_2"


def test_safe_id_returns_cached_value_on_repeat():
    utils.reset_id_map()
    first = utils.safe_id("repeat_me")
    second = utils.safe_id("repeat_me")
    assert first is second


def test_reset_id_map_clears_all_entries():
    utils.safe_id("before_reset")
    utils.reset_id_map()
    # After reset the same name gets a fresh (non-suffixed) id again
    result = utils.safe_id("before_reset")
    assert "_2" not in result


def test_up_returns_empty_string_for_none():
    assert utils.up(None) == ""


def test_up_returns_empty_string_on_unparse_exception():
    with patch("ast.unparse", side_effect=Exception("fail")):
        node = ast.parse("x = 1").body[0]
        assert utils.up(node) == ""


def test_up_returns_source_for_valid_node():
    node = ast.parse("x + 1", mode="eval").body
    result = utils.up(node)
    assert "x" in result


def test_vis_public():
    assert utils.vis("public_method") == "+"


def test_vis_protected():
    assert utils.vis("_protected") == "#"


def test_vis_private():
    assert utils.vis("__private") == "-"


def test_vis_dunder_is_protected():
    # __init__ starts with _ (but also ends with __) → not private → protected "#"
    assert utils.vis("__init__") == "#"


def test_is_dunder_true():
    assert utils.is_dunder("__init__") is True


def test_is_dunder_false_single_underscore():
    assert utils.is_dunder("_not_dunder") is False


def test_is_dunder_false_only_leading():
    assert utils.is_dunder("__leading_only") is False
