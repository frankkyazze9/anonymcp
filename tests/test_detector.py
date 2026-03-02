"""Tests for the PII detection engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.conftest import (
    SAMPLE_TEXT_CLEAN,
    SAMPLE_TEXT_EMAIL,
    SAMPLE_TEXT_MIXED,
    SAMPLE_TEXT_SSN,
)

if TYPE_CHECKING:
    from anonymcp.engine.detector import TextDetector


class TestTextDetector:
    def test_detect_email(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_EMAIL)
        assert result.entities_found >= 1
        types = result.entity_types()
        assert "EMAIL_ADDRESS" in types

    def test_detect_ssn(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_SSN)
        assert result.entities_found >= 1
        types = result.entity_types()
        assert "US_SSN" in types

    def test_detect_clean_text(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_CLEAN)
        assert result.entities_found == 0

    def test_detect_mixed_pii(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_MIXED)
        assert result.entities_found >= 3
        types = result.entity_types()
        assert "EMAIL_ADDRESS" in types

    def test_detect_with_entity_filter(self, detector: TextDetector) -> None:
        result = detector.detect(
            SAMPLE_TEXT_MIXED,
            entities=["EMAIL_ADDRESS"],
        )
        types = result.entity_types()
        assert "EMAIL_ADDRESS" in types
        # Should not detect other types when filtered
        assert "US_SSN" not in types

    def test_detect_score_threshold(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_EMAIL, score_threshold=0.99)
        # Very high threshold should filter out lower-confidence results
        for r in result.results:
            assert r["score"] >= 0.99

    def test_get_supported_entities(self, detector: TextDetector) -> None:
        entities = detector.get_supported_entities()
        assert len(entities) > 0
        assert "EMAIL_ADDRESS" in entities
        assert "CREDIT_CARD" in entities

    def test_result_structure(self, detector: TextDetector) -> None:
        result = detector.detect(SAMPLE_TEXT_EMAIL)
        assert result.entities_found >= 1
        entry = result.results[0]
        assert "entity_type" in entry
        assert "text" in entry
        assert "start" in entry
        assert "end" in entry
        assert "score" in entry
        assert isinstance(entry["start"], int)
        assert isinstance(entry["score"], float)
