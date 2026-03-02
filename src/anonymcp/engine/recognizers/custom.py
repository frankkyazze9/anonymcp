"""Custom recognizer registry for user-defined PII patterns.

This module provides a registry for adding custom Presidio recognizers
at runtime, allowing users to extend detection beyond built-in entities.
"""

from __future__ import annotations

from typing import Any

import structlog
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer

logger = structlog.get_logger(__name__)


class RecognizerRegistry:
    """Manages custom PII recognizers and registers them with Presidio.

    Example usage::

        registry = RecognizerRegistry(analyzer)
        registry.add_pattern_recognizer(
            name="employee_id",
            entity_type="EMPLOYEE_ID",
            patterns=[r"EMP-\\d{6}"],
            score=0.9,
        )
    """

    def __init__(self, analyzer: AnalyzerEngine) -> None:
        self._analyzer = analyzer
        self._custom_recognizers: dict[str, PatternRecognizer] = {}

    def add_pattern_recognizer(
        self,
        name: str,
        entity_type: str,
        patterns: list[str],
        *,
        score: float = 0.85,
        context_words: list[str] | None = None,
    ) -> None:
        """Add a regex-based pattern recognizer.

        Args:
            name: Unique recognizer name.
            entity_type: The entity type this recognizer detects.
            patterns: List of regex patterns.
            score: Base confidence score for matches.
            context_words: Optional context words that boost confidence.
        """
        presidio_patterns = [
            Pattern(name=f"{name}_pattern_{i}", regex=p, score=score)
            for i, p in enumerate(patterns)
        ]

        recognizer = PatternRecognizer(
            supported_entity=entity_type,
            name=name,
            patterns=presidio_patterns,
            context=context_words,  # type: ignore[arg-type]
        )

        self._analyzer.registry.add_recognizer(recognizer)
        self._custom_recognizers[name] = recognizer

        logger.info(
            "custom_recognizer_added",
            name=name,
            entity_type=entity_type,
            pattern_count=len(patterns),
        )

    def remove_recognizer(self, name: str) -> bool:
        """Remove a custom recognizer by name.

        Returns True if the recognizer was found and removed.
        """
        if name in self._custom_recognizers:
            recognizer = self._custom_recognizers.pop(name)
            self._analyzer.registry.remove_recognizer(recognizer.name)  # type: ignore[has-type]
            logger.info("custom_recognizer_removed", name=name)
            return True
        return False

    def list_custom_recognizers(self) -> list[dict[str, Any]]:
        """Return metadata about all registered custom recognizers."""
        return [
            {
                "name": name,
                "entity_type": r.supported_entities[0],
                "pattern_count": len(r.patterns),  # type: ignore[has-type]
            }
            for name, r in self._custom_recognizers.items()
        ]
