"""Tests for the PII anonymization engine."""

from __future__ import annotations

from anonymcp.engine.anonymizer import TextAnonymizer
from anonymcp.engine.detector import TextDetector
from anonymcp.policy.models import GovernancePolicy
from tests.conftest import SAMPLE_TEXT_EMAIL, SAMPLE_TEXT_MIXED


class TestTextAnonymizer:
    def test_anonymize_replaces_email(
        self, detector: TextDetector, anonymizer: TextAnonymizer
    ) -> None:
        detection = detector.detect(SAMPLE_TEXT_EMAIL)
        result = anonymizer.anonymize(SAMPLE_TEXT_EMAIL, detection.raw_results)
        assert "test@example.com" not in result.anonymized_text
        assert result.entities_anonymized >= 1

    def test_anonymize_mixed_pii(
        self, detector: TextDetector, anonymizer: TextAnonymizer
    ) -> None:
        detection = detector.detect(SAMPLE_TEXT_MIXED)
        result = anonymizer.anonymize(SAMPLE_TEXT_MIXED, detection.raw_results)
        assert "test@example.com" not in result.anonymized_text
        assert result.entities_anonymized >= 3

    def test_anonymize_with_operator_override(
        self, detector: TextDetector, anonymizer: TextAnonymizer
    ) -> None:
        detection = detector.detect(SAMPLE_TEXT_EMAIL)
        result = anonymizer.anonymize(
            SAMPLE_TEXT_EMAIL,
            detection.raw_results,
            operator_overrides={
                "EMAIL_ADDRESS": {"type": "replace", "new_value": "HIDDEN"},
            },
        )
        assert "HIDDEN" in result.anonymized_text
        assert result.operators_applied.get("EMAIL_ADDRESS") == "replace"

    def test_anonymize_empty_results(self, anonymizer: TextAnonymizer) -> None:
        result = anonymizer.anonymize("Hello world", [])
        assert result.anonymized_text == "Hello world"
        assert result.entities_anonymized == 0

    def test_operators_applied_tracking(
        self, detector: TextDetector, anonymizer: TextAnonymizer
    ) -> None:
        detection = detector.detect(SAMPLE_TEXT_EMAIL)
        result = anonymizer.anonymize(SAMPLE_TEXT_EMAIL, detection.raw_results)
        assert len(result.operators_applied) > 0
        for entity_type, operator_name in result.operators_applied.items():
            assert isinstance(entity_type, str)
            assert isinstance(operator_name, str)
