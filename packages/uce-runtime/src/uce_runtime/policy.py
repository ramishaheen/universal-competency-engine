"""Policy engine — evaluates allow/deny/require_approval rules before actions."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Any

from uce_core.models import Policy, PolicyEffect as CorePolicyEffect

from uce_runtime.expressions import EvalError, safe_eval

# Re-export so callers don't need to import from uce_core directly.
PolicyEffect = CorePolicyEffect


@dataclass
class PolicyDecision:
    effect: PolicyEffect
    matched: list[str] = field(default_factory=list)  # policy IDs
    reasons: list[str] = field(default_factory=list)
    required_role: str | None = None
    audit_required: bool = True

    @property
    def allowed(self) -> bool:
        return self.effect == PolicyEffect.ALLOW

    @property
    def denied(self) -> bool:
        return self.effect == PolicyEffect.DENY

    @property
    def needs_approval(self) -> bool:
        return self.effect == PolicyEffect.REQUIRE_APPROVAL


class PolicyEngine:
    """Evaluate a set of policies against (action, context).

    Resolution order: explicit DENY beats REQUIRE_APPROVAL beats ALLOW. If no policy
    matches, default is `default_effect` (ALLOW unless overridden).
    """

    def __init__(self, policies: list[Policy], *, default_effect: PolicyEffect = PolicyEffect.ALLOW) -> None:
        self.policies = policies
        self.default_effect = default_effect

    def check(self, action: str, context: dict[str, Any]) -> PolicyDecision:
        applicable: list[Policy] = []
        for p in self.policies:
            if not _matches_any(action, p.applies_to):
                continue
            if p.when:
                try:
                    if not bool(safe_eval(p.when, context)):
                        continue
                except EvalError:
                    # A malformed condition is a fail-closed signal: don't match the policy.
                    continue
            applicable.append(p)

        if not applicable:
            return PolicyDecision(effect=self.default_effect, reasons=["no policy matched"])

        # Resolve: DENY > REQUIRE_APPROVAL > ALLOW
        denies = [p for p in applicable if p.effect == PolicyEffect.DENY]
        approvals = [p for p in applicable if p.effect == PolicyEffect.REQUIRE_APPROVAL]
        allows = [p for p in applicable if p.effect == PolicyEffect.ALLOW]

        if denies:
            return PolicyDecision(
                effect=PolicyEffect.DENY,
                matched=[p.id for p in denies],
                reasons=[p.reason or f"denied by {p.id}" for p in denies],
                audit_required=any(p.audit_required for p in denies),
            )
        if approvals:
            # If actor already has the required role, treat as ALLOW.
            actor_roles = set(context.get("actor", {}).get("roles", []))
            required_role = next((p.required_role for p in approvals if p.required_role), None)
            if required_role and required_role in actor_roles:
                return PolicyDecision(
                    effect=PolicyEffect.ALLOW,
                    matched=[p.id for p in approvals],
                    reasons=[f"actor has required role '{required_role}'"],
                    audit_required=any(p.audit_required for p in approvals),
                )
            return PolicyDecision(
                effect=PolicyEffect.REQUIRE_APPROVAL,
                matched=[p.id for p in approvals],
                reasons=[p.reason or f"approval required by {p.id}" for p in approvals],
                required_role=required_role,
                audit_required=any(p.audit_required for p in approvals),
            )
        return PolicyDecision(
            effect=PolicyEffect.ALLOW,
            matched=[p.id for p in allows],
            reasons=[f"allowed by {p.id}" for p in allows],
            audit_required=any(p.audit_required for p in allows),
        )


def _matches_any(action: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(action, p) for p in patterns)
