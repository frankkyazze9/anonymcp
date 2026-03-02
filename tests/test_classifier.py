"""Tests for the sensitivity classifier."""

from __future__ import annotations

from anonymcp.engine.classifier import TextClassifier
from anonymcp.policy.models import ClassificationLevel


class TestTextClassifier:
    def test_classify_no_entities(self, classifier: TextClassifier) -> None:
        result = classifier.classify([])
        assert result.classification == ClassificationLevel.PUBLIC

    def test_classify_high_sensitivity(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["US_SSN", "CREDIT_CARD"])
        assert result.classification == ClassificationLevel.RESTRICTED

    def test_classify_medium_sensitivity(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["EMAIL_ADDRESS", "PHONE_NUMBER"])
        assert result.classification == ClassificationLevel.CONFIDENTIAL

    def test_classify_low_sensitivity(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["URL", "DATE_TIME"])
        assert result.classification == ClassificationLevel.INTERNAL

    def test_classify_mixed_takes_highest(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["URL", "EMAIL_ADDRESS", "US_SSN"])
        assert result.classification == ClassificationLevel.RESTRICTED

    def test_classification_reason_populated(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["EMAIL_ADDRESS"])
        assert "MEDIUM" in result.reason
        assert "EMAIL_ADDRESS" in result.reason

    def test_entity_summary_structure(self, classifier: TextClassifier) -> None:
        result = classifier.classify(["US_SSN", "EMAIL_ADDRESS", "URL"])
        assert "HIGH" in result.entity_summary
        assert "US_SSN" in result.entity_summary["HIGH"]
        assert "MEDIUM" in result.entity_summary
        assert "EMAIL_ADDRESS" in result.entity_summary["MEDIUM"]

    def test_confidence_with_scores(self, classifier: TextClassifier) -> None:
        result = classifier.classify(
            ["EMAIL_ADDRESS", "PHONE_NUMBER"],
            scores=[0.95, 0.85],
        )
        assert result.confidence == 0.9
