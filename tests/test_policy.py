"""Tests for the policy engine."""

from __future__ import annotations

from anonymcp.policy.engine import PolicyEngine
from anonymcp.policy.models import (
    ClassificationLevel,
    GovernancePolicy,
    OperatorSpec,
    SensitivityLevel,
)


class TestGovernancePolicy:
    def test_default_policy_has_all_levels(self, default_policy: GovernancePolicy) -> None:
        assert SensitivityLevel.HIGH in default_policy.entity_sensitivity
        assert SensitivityLevel.MEDIUM in default_policy.entity_sensitivity
        assert SensitivityLevel.LOW in default_policy.entity_sensitivity

    def test_get_sensitivity_known_entity(self, default_policy: GovernancePolicy) -> None:
        assert default_policy.get_sensitivity("US_SSN") == SensitivityLevel.HIGH
        assert default_policy.get_sensitivity("EMAIL_ADDRESS") == SensitivityLevel.MEDIUM
        assert default_policy.get_sensitivity("URL") == SensitivityLevel.LOW

    def test_get_sensitivity_unknown_entity(self, default_policy: GovernancePolicy) -> None:
        assert default_policy.get_sensitivity("UNKNOWN_TYPE") is None

    def test_get_operator_for_entity(self, default_policy: GovernancePolicy) -> None:
        op = default_policy.get_operator_for_entity("US_SSN")
        assert op.operator == "redact"

        op = default_policy.get_operator_for_entity("EMAIL_ADDRESS")
        assert op.operator == "replace"

    def test_get_operator_fallback(self, default_policy: GovernancePolicy) -> None:
        op = default_policy.get_operator_for_entity("TOTALLY_UNKNOWN")
        assert op.operator == "replace"
        assert "TOTALLY_UNKNOWN" in op.params.get("new_value", "")


class TestPolicyEngine:
    def test_classify_empty(self, policy_engine: PolicyEngine) -> None:
        assert policy_engine.classify([]) == ClassificationLevel.PUBLIC

    def test_classify_high(self, policy_engine: PolicyEngine) -> None:
        assert policy_engine.classify(["CREDIT_CARD"]) == ClassificationLevel.RESTRICTED

    def test_classify_medium(self, policy_engine: PolicyEngine) -> None:
        assert policy_engine.classify(["PHONE_NUMBER"]) == ClassificationLevel.CONFIDENTIAL

    def test_classify_low(self, policy_engine: PolicyEngine) -> None:
        assert policy_engine.classify(["DATE_TIME"]) == ClassificationLevel.INTERNAL

    def test_should_alert_empty(self, policy_engine: PolicyEngine) -> None:
        alerts = policy_engine.should_alert(ClassificationLevel.PUBLIC, 0)
        assert alerts == []
