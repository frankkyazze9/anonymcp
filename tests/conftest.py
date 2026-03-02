"""Shared test fixtures for AnonyMCP."""

from __future__ import annotations

import pytest

from anonymcp.audit.logger import AuditLogger
from anonymcp.engine.anonymizer import TextAnonymizer
from anonymcp.engine.classifier import TextClassifier
from anonymcp.engine.detector import TextDetector
from anonymcp.policy.engine import PolicyEngine
from anonymcp.policy.models import GovernancePolicy


@pytest.fixture
def default_policy() -> GovernancePolicy:
    """A default governance policy for testing."""
    return GovernancePolicy()


@pytest.fixture
def policy_engine(default_policy: GovernancePolicy) -> PolicyEngine:
    return PolicyEngine(policy=default_policy)


@pytest.fixture
def detector() -> TextDetector:
    return TextDetector()


@pytest.fixture
def anonymizer(default_policy: GovernancePolicy) -> TextAnonymizer:
    return TextAnonymizer(policy=default_policy)


@pytest.fixture
def classifier(policy_engine: PolicyEngine) -> TextClassifier:
    return TextClassifier(policy_engine=policy_engine)


@pytest.fixture
def audit_logger() -> AuditLogger:
    return AuditLogger()


# Sample texts with known PII for testing
SAMPLE_TEXT_EMAIL = "Contact us at test@example.com for more info."
SAMPLE_TEXT_SSN = "My SSN is 219-09-9999 and my name is John Smith."
SAMPLE_TEXT_CREDIT_CARD = "Payment card: 4111-1111-1111-1111"
SAMPLE_TEXT_MIXED = (
    "John Smith (test@example.com) called from 555-123-4567. "
    "His SSN is 123-45-6789 and he paid with card 4111-1111-1111-1111."
)
SAMPLE_TEXT_CLEAN = "The weather is sunny with clear skies and warm temperatures."
