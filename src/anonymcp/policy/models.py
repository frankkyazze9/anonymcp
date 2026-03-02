"""Pydantic models for governance policy schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SensitivityLevel(str, Enum):
    """Sensitivity level for PII entity types."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClassificationLevel(str, Enum):
    """Data classification levels, ordered by sensitivity."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class OperatorSpec(BaseModel):
    """Configuration for an anonymization operator."""

    operator: str = "replace"
    params: dict[str, Any] = Field(default_factory=dict)


class ClassificationRule(BaseModel):
    """Rule that maps a condition to a classification level."""

    condition: str  # e.g. "any HIGH entity", "only LOW entities"


class AlertRule(BaseModel):
    """Rule that triggers alerts based on governance actions."""

    name: str
    condition: str
    action: str = "log"  # log | webhook
    level: str = "WARNING"
    webhook_url: str | None = None


class AuditSettings(BaseModel):
    """Audit subsystem configuration."""

    enabled: bool = True
    log_original_text: bool = False
    log_anonymized_text: bool = True
    exporters: list[dict[str, Any]] = Field(default_factory=list)


class DetectionSettings(BaseModel):
    """PII detection configuration."""

    score_threshold: float = 0.4
    language: str = "en"


class GovernancePolicy(BaseModel):
    """Complete governance policy definition.

    Loaded from YAML policy files and used by the PolicyEngine
    to drive classification, anonymization, and alerting behavior.
    """

    name: str = "default"
    version: str = "1.0"
    description: str = ""

    # Entity sensitivity mapping: level -> list of entity types
    entity_sensitivity: dict[SensitivityLevel, list[str]] = Field(
        default_factory=lambda: {
            SensitivityLevel.HIGH: [
                "US_SSN",
                "CREDIT_CARD",
                "US_BANK_NUMBER",
                "IBAN_CODE",
                "CRYPTO",
                "US_PASSPORT",
                "UK_NHS",
                "MEDICAL_LICENSE",
            ],
            SensitivityLevel.MEDIUM: [
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "PERSON",
                "US_DRIVER_LICENSE",
                "IP_ADDRESS",
                "LOCATION",
            ],
            SensitivityLevel.LOW: [
                "URL",
                "DATE_TIME",
                "NRP",
                "TITLE",
            ],
        }
    )

    # Classification rules
    classification: dict[ClassificationLevel, ClassificationRule] = Field(
        default_factory=lambda: {
            ClassificationLevel.RESTRICTED: ClassificationRule(condition="any HIGH entity"),
            ClassificationLevel.CONFIDENTIAL: ClassificationRule(
                condition="any MEDIUM entity"
            ),
            ClassificationLevel.INTERNAL: ClassificationRule(condition="only LOW entities"),
            ClassificationLevel.PUBLIC: ClassificationRule(condition="no entities detected"),
        }
    )

    # Anonymization operators per sensitivity level
    anonymization: dict[SensitivityLevel, OperatorSpec] = Field(
        default_factory=lambda: {
            SensitivityLevel.HIGH: OperatorSpec(operator="redact"),
            SensitivityLevel.MEDIUM: OperatorSpec(
                operator="replace", params={"new_value": "[{entity_type}]"}
            ),
            SensitivityLevel.LOW: OperatorSpec(
                operator="mask", params={"masking_char": "*", "chars_to_mask": 4}
            ),
        }
    )

    # Per-entity operator overrides
    operator_overrides: dict[str, OperatorSpec] = Field(default_factory=dict)

    # Detection settings
    detection: DetectionSettings = Field(default_factory=DetectionSettings)

    # Audit settings
    audit: AuditSettings = Field(default_factory=AuditSettings)

    # Alert rules
    alerts: list[AlertRule] = Field(default_factory=list)

    def get_sensitivity(self, entity_type: str) -> SensitivityLevel | None:
        """Look up the sensitivity level for an entity type."""
        for level, entities in self.entity_sensitivity.items():
            if entity_type in entities:
                return level
        return None

    def get_operator_for_entity(self, entity_type: str) -> OperatorSpec:
        """Get the anonymization operator config for an entity type.

        Checks per-entity overrides first, then falls back to
        sensitivity-level defaults.
        """
        # Check per-entity overrides
        if entity_type in self.operator_overrides:
            return self.operator_overrides[entity_type]

        # Fall back to sensitivity-level default
        sensitivity = self.get_sensitivity(entity_type)
        if sensitivity and sensitivity in self.anonymization:
            return self.anonymization[sensitivity]

        # Ultimate fallback: replace with entity type placeholder
        return OperatorSpec(operator="replace", params={"new_value": f"[{entity_type}]"})
