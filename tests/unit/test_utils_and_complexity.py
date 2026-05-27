import ast

from uml_planterator import complexity, utils


def test_safe_id_edgecases():
    a = utils.safe_id("")
    assert a.startswith("id")
    b = utils.safe_id("1start")
    assert b.startswith("id_")
    # collisions
    x = utils.safe_id("a b")
    y = utils.safe_id("a?b")
    assert x != y


def test_up_handles_unparseable(monkeypatch):
    def _bad(node):
        raise Exception("bad")

    monkeypatch.setattr(utils.ast, "unparse", _bad)
    assert utils.up(ast.parse("x=1").body[0]) == ""


def test_cyclomatic_counts_comprehension_and_match():
    src = """
def f(x):
    a = [i for i in range(3) if i>0]
    match x:
        case 1:
            pass
"""
    tree = ast.parse(src)
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 2
