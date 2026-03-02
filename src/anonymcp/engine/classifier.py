"""Text sensitivity classification based on PII content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from anonymcp.policy.models import ClassificationLevel

if TYPE_CHECKING:
    from anonymcp.policy.engine import PolicyEngine

logger = structlog.get_logger(__name__)


@dataclass
class ClassificationResult:
    """Result of a sensitivity classification."""

    classification: ClassificationLevel
    confidence: float
    reason: str
    entity_summary: dict[str, list[str]]
    policy_applied: str


class TextClassifier:
    """Classifies text sensitivity based on detected PII entities.

    Uses the PolicyEngine to map detected entity types to sensitivity
    levels, then determines the overall classification.
    """

    def __init__(self, policy_engine: PolicyEngine) -> None:
        self._policy_engine = policy_engine

    @property
    def policy_engine(self) -> PolicyEngine:
        return self._policy_engine

    def classify(
        self,
        entity_types: list[str],
        scores: list[float] | None = None,
    ) -> ClassificationResult:
        """Classify data sensitivity based on detected entity types.

        Args:
            entity_types: List of detected PII entity type strings.
            scores: Optional confidence scores corresponding to each entity.

        Returns:
            ClassificationResult with level, confidence, and reasoning.
        """
        classification = self._policy_engine.classify(entity_types)

        # Build entity summary by sensitivity level
        policy = self._policy_engine.policy
        entity_summary: dict[str, list[str]] = {
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
            "UNKNOWN": [],
        }

        unique_types = list(set(entity_types))
        for entity_type in unique_types:
            level = policy.get_sensitivity(entity_type)
            if level:
                entity_summary[level.value].append(entity_type)
            else:
                entity_summary["UNKNOWN"].append(entity_type)

        # Calculate confidence from detection scores
        if scores and len(scores) > 0:
            confidence = round(sum(scores) / len(scores), 4)
        else:
            confidence = 1.0 if not entity_types else 0.8

        # Build human-readable reason
        reason = self._build_reason(classification, entity_summary)

        logger.info(
            "classification_completed",
            classification=classification.value,
            entity_count=len(entity_types),
        )

        return ClassificationResult(
            classification=classification,
            confidence=confidence,
            reason=reason,
            entity_summary={k: v for k, v in entity_summary.items() if v},
            policy_applied=policy.name,
        )

    @staticmethod
    def _build_reason(
        classification: ClassificationLevel,
        entity_summary: dict[str, list[str]],
    ) -> str:
        """Build a human-readable explanation of the classification."""
        if classification == ClassificationLevel.PUBLIC:
            return "No PII entities detected"

        parts: list[str] = []
        for level in ("HIGH", "MEDIUM", "LOW"):
            entities = entity_summary.get(level, [])
            if entities:
                count = len(entities)
                names = ", ".join(entities)
                suffix = "y" if count == 1 else "ies"
                parts.append(
                    f"{count} {level}-sensitivity entit{suffix} ({names})"
                )

        return f"Contains {'; '.join(parts)}"
