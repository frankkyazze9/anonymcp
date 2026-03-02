"""Policy evaluation and enforcement engine."""

from __future__ import annotations

from pathlib import Path

import structlog

from anonymcp.config.loader import load_policy_file
from anonymcp.policy.models import (
    ClassificationLevel,
    GovernancePolicy,
    SensitivityLevel,
)

logger = structlog.get_logger(__name__)


class PolicyEngine:
    """Evaluates governance policies against detected PII entities.

    The PolicyEngine is the central decision-maker: given a set of
    detected entity types, it determines the classification level
    and which anonymization operators to apply.
    """

    def __init__(self, policy: GovernancePolicy | None = None) -> None:
        self._policy = policy or GovernancePolicy()

    @classmethod
    def from_file(cls, path: Path) -> PolicyEngine:
        """Load a PolicyEngine from a YAML/JSON policy file."""
        raw = load_policy_file(path)
        policy = GovernancePolicy(**raw)
        logger.info("policy_loaded", name=policy.name, version=policy.version)
        return cls(policy=policy)

    @property
    def policy(self) -> GovernancePolicy:
        return self._policy

    def reload(self, path: Path) -> None:
        """Hot-reload a policy from disk."""
        raw = load_policy_file(path)
        self._policy = GovernancePolicy(**raw)
        logger.info("policy_reloaded", name=self._policy.name, version=self._policy.version)

    def classify(self, entity_types: list[str]) -> ClassificationLevel:
        """Classify data based on detected entity types.

        Evaluates entity types against the policy's sensitivity mappings
        and returns the highest applicable classification level.

        Args:
            entity_types: List of detected PII entity type strings.

        Returns:
            The classification level for the data.
        """
        if not entity_types:
            return ClassificationLevel.PUBLIC

        sensitivity_levels: set[SensitivityLevel] = set()
        for entity_type in entity_types:
            level = self._policy.get_sensitivity(entity_type)
            if level:
                sensitivity_levels.add(level)

        if SensitivityLevel.HIGH in sensitivity_levels:
            return ClassificationLevel.RESTRICTED
        if SensitivityLevel.MEDIUM in sensitivity_levels:
            return ClassificationLevel.CONFIDENTIAL
        if SensitivityLevel.LOW in sensitivity_levels:
            return ClassificationLevel.INTERNAL

        # Entities found but not in any sensitivity mapping — treat as INTERNAL
        return ClassificationLevel.INTERNAL

    def should_alert(
        self,
        classification: ClassificationLevel,
        entities_found: int,
    ) -> list[dict[str, str]]:
        """Evaluate alert rules and return any triggered alerts.

        Args:
            classification: The classification level of the data.
            entities_found: Number of PII entities detected.

        Returns:
            List of triggered alert dicts with name, action, and details.
        """
        triggered: list[dict[str, str]] = []

        for rule in self._policy.alerts:
            condition = rule.condition
            fire = False

            if "classification ==" in condition:
                target_level = condition.split("==")[-1].strip()
                fire = classification.value == target_level
            elif "entities_found >" in condition:
                threshold = int(condition.split(">")[-1].strip())
                fire = entities_found > threshold

            if fire:
                triggered.append(
                    {
                        "name": rule.name,
                        "action": rule.action,
                        "level": rule.level,
                        "webhook_url": rule.webhook_url or "",
                    }
                )

        return triggered
