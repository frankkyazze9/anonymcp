"""PII detection engine wrapping Presidio Analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog
from presidio_analyzer import AnalyzerEngine, RecognizerResult

logger = structlog.get_logger(__name__)


@dataclass
class DetectionResult:
    """Result of a PII detection scan."""

    entities_found: int
    results: list[dict[str, Any]]
    raw_results: list[RecognizerResult] = field(repr=False, default_factory=list)

    def entity_types(self) -> list[str]:
        """Return unique entity types found."""
        return list({r["entity_type"] for r in self.results})


class TextDetector:
    """Detects PII entities in text using Presidio AnalyzerEngine.

    This is the primary detection interface. It wraps Presidio's
    AnalyzerEngine and normalizes outputs for downstream use by
    the classifier, anonymizer, and audit logger.
    """

    def __init__(self, analyzer: AnalyzerEngine | None = None) -> None:
        self._analyzer = analyzer or AnalyzerEngine()

    @property
    def analyzer(self) -> AnalyzerEngine:
        return self._analyzer

    def detect(
        self,
        text: str,
        *,
        entities: list[str] | None = None,
        language: str = "en",
        score_threshold: float = 0.4,
    ) -> DetectionResult:
        """Detect PII entities in text.

        Args:
            text: The text to analyze.
            entities: Optional list of entity types to detect.
                If None, all supported entities are scanned.
            language: Language code for NLP processing.
            score_threshold: Minimum confidence score to include.

        Returns:
            DetectionResult with normalized entity data.
        """
        logger.debug(
            "detection_started",
            text_length=len(text),
            entities_filter=entities,
            language=language,
        )

        raw_results: list[RecognizerResult] = self._analyzer.analyze(
            text=text,
            entities=entities,
            language=language,
            score_threshold=score_threshold,
        )

        normalized = [
            {
                "entity_type": r.entity_type,
                "text": text[r.start : r.end],
                "start": r.start,
                "end": r.end,
                "score": round(r.score, 4),
            }
            for r in raw_results
        ]

        logger.info("detection_completed", entities_found=len(normalized))

        return DetectionResult(
            entities_found=len(normalized),
            results=normalized,
            raw_results=raw_results,
        )

    def get_supported_entities(self, language: str = "en") -> list[str]:
        """Return all entity types the analyzer can detect."""
        return self._analyzer.get_supported_entities(language=language)
