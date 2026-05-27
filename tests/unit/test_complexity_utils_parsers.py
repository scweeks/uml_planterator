import ast

from uml_planterator import complexity, parsers, utils


def test_cyclomatic_complexity_counts_if_and_for():
    src = """
def f(x):
    if x:
        pass
    for i in range(2):
        pass
"""
    tree = ast.parse(src)
    cc = complexity.cyclomatic_complexity(tree)
    assert cc >= 3


def test_utils_safe_id_and_vis_and_up():
    # safe_id determinism
    a = utils.safe_id("a b")
    b = utils.safe_id("a b")
    assert a == b
    # vis
    assert utils.vis("__priv") == "-"
    assert utils.vis("_prot") == "#"
    assert utils.vis("pub") == "+"
    # up with None
    assert utils.up(None) == ""


def test_parsers_helpers_and_class_parsing():
    src = """
class C:
    x: int
    def __init__(self):
        self.state = 'ready'
    def m(self):
        raise ValueError('x')
"""
    tree = ast.parse(src)
    cls = tree.body[0]
    cinfo = parsers.parse_class(cls)
    assert cinfo.name == "C"
    assert any(a.name == "x" or a.name == "state" for a in cinfo.attributes)
    assert any(m.name == "m" for m in cinfo.methods)
