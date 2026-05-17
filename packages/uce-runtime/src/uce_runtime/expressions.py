"""Safe expression evaluator for `when` conditions and templating.

Restricted to literal constants, names (resolved from a context dict), attribute/
subscript access, comparisons, boolean logic, arithmetic, and a small set of
built-ins (len, str, int, float, bool, abs, min, max).

No `eval`, no `exec`, no imports, no calls to arbitrary functions.
"""
from __future__ import annotations

import ast
import operator
from typing import Any

__all__ = ["EvalError", "safe_eval"]


class EvalError(ValueError):
    """Raised when an expression is invalid or accesses disallowed nodes."""


_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}

_CMP_OPS: dict[type, Any] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}

_SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "any": any,
    "all": all,
    "round": round,
    "True": True,
    "False": False,
    "None": None,
}


def safe_eval(expr: str, context: dict[str, Any] | None = None) -> Any:
    """Evaluate `expr` against `context`. Returns the result.

    >>> safe_eval("a + 1", {"a": 2})
    3
    >>> safe_eval("user.role in ['admin', 'author']", {"user": {"role": "admin"}})
    True
    """
    if not expr or not expr.strip():
        raise EvalError("empty expression")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise EvalError(f"syntax error: {e}") from e
    ctx = dict(context or {})
    return _eval(tree.body, ctx)


def _eval(node: ast.AST, ctx: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ctx:
            return ctx[node.id]
        if node.id in _SAFE_BUILTINS:
            return _SAFE_BUILTINS[node.id]
        raise EvalError(f"undefined name: {node.id}")
    if isinstance(node, ast.Attribute):
        target = _eval(node.value, ctx)
        return _get_attr(target, node.attr)
    if isinstance(node, ast.Subscript):
        target = _eval(node.value, ctx)
        key = _eval(node.slice, ctx)
        try:
            return target[key]
        except (KeyError, IndexError, TypeError) as e:
            raise EvalError(f"subscript failed: {e}") from e
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise EvalError(f"unsupported binary op: {type(node.op).__name__}")
        return op(_eval(node.left, ctx), _eval(node.right, ctx))
    if isinstance(node, ast.UnaryOp):
        op = _UNARY_OPS.get(type(node.op))
        if op is None:
            raise EvalError(f"unsupported unary op: {type(node.op).__name__}")
        return op(_eval(node.operand, ctx))
    if isinstance(node, ast.BoolOp):
        values = [_eval(v, ctx) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise EvalError("unsupported boolean op")
    if isinstance(node, ast.Compare):
        left = _eval(node.left, ctx)
        for op_node, right_node in zip(node.ops, node.comparators):
            op = _CMP_OPS.get(type(op_node))
            if op is None:
                raise EvalError(f"unsupported comparison: {type(op_node).__name__}")
            right = _eval(right_node, ctx)
            if not op(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.List):
        return [_eval(e, ctx) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e, ctx) for e in node.elts)
    if isinstance(node, ast.Dict):
        return {_eval(k, ctx): _eval(v, ctx) for k, v in zip(node.keys, node.values) if k is not None}
    if isinstance(node, ast.Set):
        return {_eval(e, ctx) for e in node.elts}
    if isinstance(node, ast.Call):
        func = _eval(node.func, ctx)
        if func not in _SAFE_BUILTINS.values():
            raise EvalError("only safe built-in function calls are allowed")
        args = [_eval(a, ctx) for a in node.args]
        kwargs = {k.arg: _eval(k.value, ctx) for k in node.keywords if k.arg}
        return func(*args, **kwargs)
    raise EvalError(f"unsupported node: {type(node).__name__}")


def _get_attr(target: Any, name: str) -> Any:
    # Allow dict-style or object-style access. Block dunders to prevent escape.
    if name.startswith("_"):
        raise EvalError(f"access to private attribute denied: {name}")
    if isinstance(target, dict):
        if name not in target:
            raise EvalError(f"key not found: {name}")
        return target[name]
    if hasattr(target, name):
        return getattr(target, name)
    raise EvalError(f"attribute not found: {name}")
