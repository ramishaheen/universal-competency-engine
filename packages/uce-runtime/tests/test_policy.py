from __future__ import annotations

from uce_core.models import Policy, PolicyEffect
from uce_runtime.policy import PolicyEngine


def _p(id_, effect, applies_to, when=None, role=None):
    return Policy(id=id_, name=id_, effect=effect, applies_to=applies_to, when=when, required_role=role)


def test_no_policy_uses_default_allow():
    e = PolicyEngine([])
    d = e.check("skill:x", {})
    assert d.allowed


def test_explicit_deny_beats_allow():
    e = PolicyEngine(
        [
            _p("allow_all", PolicyEffect.ALLOW, ["*"]),
            _p("deny_contracts", PolicyEffect.DENY, ["skill:contract_*"]),
        ]
    )
    assert e.check("skill:contract_review", {}).denied
    assert e.check("skill:vendor_search", {}).allowed


def test_require_approval_unless_actor_has_role():
    e = PolicyEngine(
        [_p("ra", PolicyEffect.REQUIRE_APPROVAL, ["skill:high_risk_*"], role="admin")]
    )
    assert e.check("skill:high_risk_payment", {"actor": {"roles": ["operator"]}}).needs_approval
    assert e.check("skill:high_risk_payment", {"actor": {"roles": ["admin"]}}).allowed


def test_when_condition_filters_policy():
    e = PolicyEngine(
        [_p("expensive", PolicyEffect.REQUIRE_APPROVAL, ["skill:*"], when="inputs['amount'] > 1000", role="admin")]
    )
    assert e.check("skill:purchase", {"actor": {"roles": ["operator"]}, "inputs": {"amount": 500}}).allowed
    assert e.check("skill:purchase", {"actor": {"roles": ["operator"]}, "inputs": {"amount": 5000}}).needs_approval


def test_glob_matching():
    e = PolicyEngine([_p("deny_admin", PolicyEffect.DENY, ["competency:*:execute"])])
    assert e.check("competency:procurement:execute", {}).denied
    assert e.check("workflow:procurement:step:s1", {}).allowed  # default allow
