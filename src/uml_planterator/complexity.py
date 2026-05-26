"""Cyclomatic complexity utilities."""
from __future__ import annotations

import ast

# Thresholds (configurable by client code)
CC_ANNOTATE_THRESHOLD = 10
CC_SUBGROUP_THRESHOLD = 10


def cyclomatic_complexity(node: ast.AST) -> int:
    """Compute a simple McCabe cyclomatic complexity metric.

    CC = 1 + number of decision points. Counts `if`, `for`, `while`, `with`,
    `assert`, comprehensions, `except` handlers, boolean operations, and
    `match/case` nodes where available.
    """
    cc = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.With,
                          ast.Assert, ast.comprehension)):
            cc += 1
        elif isinstance(n, ast.ExceptHandler):
            cc += 1
        elif isinstance(n, ast.BoolOp):
            cc += len(n.values) - 1
        elif hasattr(ast, "match_case") and isinstance(n, ast.match_case):
            cc += 1
    return cc
