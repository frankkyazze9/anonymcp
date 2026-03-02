"""Audit event types and record schema."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AuditRecord:
    """Structured record of a governance action.

    Every tool invocation (analyze, anonymize, classify, scan_and_protect)
    produces an AuditRecord that flows through the configured exporters.
    """

    action: str  # analyze | anonymize | classify | scan_and_protect
    classification: str  # PUBLIC | INTERNAL | CONFIDENTIAL | RESTRICTED
    entities_found: int
    entity_types: list[str]
    entities_anonymized: int = 0
    operators_used: dict[str, str] = field(default_factory=dict)
    policy_name: str = "default"
    policy_version: str = "1.0"
    duration_ms: float = 0.0
    text_length: int = 0
    anonymized_text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Auto-generated fields
    audit_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary for JSON export."""
        return {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "classification": self.classification,
            "entities_found": self.entities_found,
            "entity_types": self.entity_types,
            "entities_anonymized": self.entities_anonymized,
            "operators_used": self.operators_used,
            "policy_name": self.policy_name,
            "policy_version": self.policy_version,
            "duration_ms": self.duration_ms,
            "text_length": self.text_length,
            "metadata": self.metadata,
        }
