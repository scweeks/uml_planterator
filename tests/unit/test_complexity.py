"""Tests for complexity.py — 100% line and branch coverage."""

import ast

from uml_planterator import complexity


def test_cyclomatic_simple_if():
    tree = ast.parse("def f(x):\n    if x > 0:\n        return 1\n    return 0\n")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_for_loop():
    tree = ast.parse("def f():\n    for i in range(3):\n        pass\n")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_while_loop():
    tree = ast.parse("def f():\n    while True:\n        break\n")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_with_statement():
    tree = ast.parse("def f():\n    with open('x') as f:\n        pass\n")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_assert():
    tree = ast.parse("def f(x):\n    assert x > 0\n")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_comprehension():
    tree = ast.parse("[x for x in range(3)]")
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_except_handler():
    tree = ast.parse(
        "def f():\n    try:\n        pass\n    except ValueError:\n        pass\n"
    )
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_boolop_two_values():
    tree = ast.parse("def f(a, b):\n    return a and b\n")
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 2


def test_cyclomatic_boolop_three_values():
    tree = ast.parse("def f(a, b, c):\n    return a and b and c\n")
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 3


def test_cyclomatic_match_case():
    src = "match x:\n    case 1:\n        pass\n    case 2:\n        pass\n"
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return  # Python < 3.10 — skip
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 3


def test_cyclomatic_empty_function():
    tree = ast.parse("def f():\n    pass\n")
    assert complexity.cyclomatic_complexity(tree) == 1
