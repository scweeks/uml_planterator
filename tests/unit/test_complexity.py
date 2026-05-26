import ast

from uml_planterator import complexity


def test_cyclomatic_simple():
    src = """
def f(x):
    if x > 0:
        return 1
    return 0
"""
    tree = ast.parse(src)
    assert complexity.cyclomatic_complexity(tree) >= 2


def test_cyclomatic_boolops_and_loops():
    src = """
def g(x):
    for i in range(3):
        if x and i:
            return True
    return False
"""
    tree = ast.parse(src)
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 3
