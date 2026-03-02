"""Stdout/console audit exporter for container environments."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from anonymcp.audit.events import AuditRecord

logger = structlog.get_logger("anonymcp.audit")


class StdoutExporter:
    """Logs audit records to stdout via structlog."""

    def __init__(self, level: str = "INFO") -> None:
        self._level = level.upper()

    async def export(self, record: AuditRecord) -> None:
        """Log the audit record to stdout."""
        log_fn = getattr(logger, self._level.lower(), logger.info)
        log_fn(
            "audit_record",
            audit_id=record.audit_id,
            action=record.action,
            classification=record.classification,
            entities_found=record.entities_found,
            entities_anonymized=record.entities_anonymized,
            duration_ms=record.duration_ms,
        )
