from __future__ import annotations

import pytest

from uce_runtime.expressions import EvalError, safe_eval


def test_literals():
    assert safe_eval("1 + 2") == 3
    assert safe_eval('"hello"') == "hello"
    assert safe_eval("True and not False") is True
    assert safe_eval("[1, 2, 3]") == [1, 2, 3]


def test_names_from_context():
    assert safe_eval("a + b", {"a": 1, "b": 2}) == 3


def test_attribute_and_subscript():
    ctx = {"user": {"role": "admin", "scopes": ["a", "b"]}, "n": 5}
    assert safe_eval("user.role == 'admin'", ctx) is True
    assert safe_eval("user.scopes[0] == 'a'", ctx) is True
    assert safe_eval("user['role'] == 'admin'", ctx) is True


def test_comparisons_and_membership():
    assert safe_eval("x in [1,2,3]", {"x": 2}) is True
    assert safe_eval("x not in [1,2]", {"x": 3}) is True
    assert safe_eval("1 < x < 5", {"x": 3}) is True


def test_safe_builtins_only():
    assert safe_eval("len([1,2,3])") == 3
    with pytest.raises(EvalError):
        safe_eval("__import__('os')")


def test_dunder_blocked():
    with pytest.raises(EvalError):
        safe_eval("user.__class__", {"user": object()})


def test_unknown_name_raises():
    with pytest.raises(EvalError):
        safe_eval("missing", {})


def test_empty_expr_raises():
    with pytest.raises(EvalError):
        safe_eval("")
