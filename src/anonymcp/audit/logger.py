"""Central audit logger that routes records to exporters."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any

import structlog

from anonymcp.audit.exporters.file import FileExporter
from anonymcp.audit.exporters.stdout import StdoutExporter

if TYPE_CHECKING:
    from anonymcp.audit.events import AuditRecord

logger = structlog.get_logger(__name__)


class AuditExporter:
    """Base class for audit record exporters."""

    async def export(self, record: AuditRecord) -> None:
        raise NotImplementedError

    async def query(
        self,
        limit: int = 50,
        since: str | None = None,
        action_type: str | None = None,
        classification: str | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError


class AuditLogger:
    """Routes audit records to configured exporters and keeps an in-memory buffer.

    The AuditLogger is the single point of entry for all governance
    audit events. It fans out records to all registered exporters
    and maintains a bounded in-memory log for queries.
    """

    def __init__(self, max_buffer: int = 10000) -> None:
        self._exporters: list[Any] = []
        self._buffer: deque[AuditRecord] = deque(maxlen=max_buffer)

    def add_exporter(self, exporter: AuditExporter) -> None:
        """Register an audit exporter."""
        self._exporters.append(exporter)

    def configure_from_policy(self, exporter_configs: list[dict[str, Any]]) -> None:
        """Configure exporters from policy audit settings."""
        for config in exporter_configs:
            exporter_type = config.get("type", "stdout")
            if exporter_type == "file":
                path = config.get("path", "./audit/anonymcp.jsonl")
                self._exporters.append(FileExporter(path=path))
            elif exporter_type == "stdout":
                self._exporters.append(StdoutExporter(level=config.get("level", "INFO")))

    async def log(self, record: AuditRecord) -> None:
        """Log an audit record to all exporters and the in-memory buffer."""
        self._buffer.append(record)

        for exporter in self._exporters:
            try:
                await exporter.export(record)
            except Exception:
                logger.exception("audit_export_failed", exporter=type(exporter).__name__)

    def query(
        self,
        limit: int = 50,
        since: str | None = None,
        action_type: str | None = None,
        classification: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query the in-memory audit buffer.

        Args:
            limit: Maximum records to return.
            since: ISO 8601 timestamp — only return records after this time.
            action_type: Filter by action (analyze, anonymize, etc.).
            classification: Filter by classification level.

        Returns:
            List of audit record dicts, most recent first.
        """
        records = list(self._buffer)

        if since:
            records = [r for r in records if r.timestamp >= since]
        if action_type:
            records = [r for r in records if r.action == action_type]
        if classification:
            records = [r for r in records if r.classification == classification]

        # Most recent first
        records.reverse()
        return [r.to_dict() for r in records[:limit]]

    @property
    def total_records(self) -> int:
        return len(self._buffer)
