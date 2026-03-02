"""PII anonymization engine wrapping Presidio Anonymizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from anonymcp.policy.models import GovernancePolicy, OperatorSpec

logger = structlog.get_logger(__name__)


@dataclass
class AnonymizationResult:
    """Result of a PII anonymization operation."""

    anonymized_text: str
    entities_anonymized: int
    operators_applied: dict[str, str]


class TextAnonymizer:
    """Anonymizes PII in text using Presidio AnonymizerEngine.

    Reads operator configuration from the GovernancePolicy to
    determine how each entity type should be anonymized.
    """

    def __init__(
        self,
        anonymizer: AnonymizerEngine | None = None,
        policy: GovernancePolicy | None = None,
    ) -> None:
        self._anonymizer = anonymizer or AnonymizerEngine()
        self._policy = policy or GovernancePolicy()

    @property
    def policy(self) -> GovernancePolicy:
        return self._policy

    @policy.setter
    def policy(self, value: GovernancePolicy) -> None:
        self._policy = value

    def anonymize(
        self,
        text: str,
        analyzer_results: list[RecognizerResult],
        *,
        operator_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> AnonymizationResult:
        """Anonymize PII in text based on detection results and policy.

        Args:
            text: Original text containing PII.
            analyzer_results: Presidio RecognizerResult list from detection.
            operator_overrides: Optional per-call operator overrides.
                Format: {"ENTITY_TYPE": {"type": "mask", "masking_char": "*"}}

        Returns:
            AnonymizationResult with transformed text and metadata.
        """
        operators = self._build_operators(analyzer_results, operator_overrides)
        operators_applied: dict[str, str] = {}

        # Track which operators are used per entity type
        for result in analyzer_results:
            entity_type = result.entity_type
            if entity_type in operators:
                operators_applied[entity_type] = operators[entity_type].operator_name
            elif "DEFAULT" in operators:
                operators_applied[entity_type] = operators["DEFAULT"].operator_name

        logger.debug("anonymization_started", entity_count=len(analyzer_results))

        engine_result = self._anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators,
        )

        logger.info(
            "anonymization_completed",
            entities_anonymized=len(analyzer_results),
        )

        return AnonymizationResult(
            anonymized_text=engine_result.text,
            entities_anonymized=len(analyzer_results),
            operators_applied=operators_applied,
        )

    def _build_operators(
        self,
        analyzer_results: list[RecognizerResult],
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, OperatorConfig]:
        """Build Presidio OperatorConfig map from policy + overrides."""
        operators: dict[str, OperatorConfig] = {}

        # Get unique entity types from results
        entity_types = {r.entity_type for r in analyzer_results}

        for entity_type in entity_types:
            # Check call-level overrides first
            if overrides and entity_type in overrides:
                spec = overrides[entity_type]
                operators[entity_type] = OperatorConfig(
                    spec.get("type", "replace"),
                    self._resolve_params(spec, entity_type),
                )
            else:
                # Fall back to policy
                policy_spec = self._policy.get_operator_for_entity(entity_type)
                operators[entity_type] = OperatorConfig(
                    policy_spec.operator,
                    self._resolve_params(
                        {"type": policy_spec.operator, **policy_spec.params},
                        entity_type,
                    ),
                )

        return operators

    @staticmethod
    def _resolve_params(spec: dict[str, Any], entity_type: str) -> dict[str, Any]:
        """Resolve template variables in operator params."""
        params = {k: v for k, v in spec.items() if k != "type"}
        # Resolve {entity_type} placeholder in string values
        for key, value in params.items():
            if isinstance(value, str) and "{entity_type}" in value:
                params[key] = value.replace("{entity_type}", entity_type)
        return params
