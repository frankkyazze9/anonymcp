"""Webhook HTTP audit exporter for external alerting systems."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import structlog

if TYPE_CHECKING:
    from anonymcp.audit.events import AuditRecord

logger = structlog.get_logger(__name__)


class WebhookExporter:
    """POSTs audit records to a configurable HTTP endpoint."""

    def __init__(self, url: str, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout

    async def export(self, record: AuditRecord) -> None:
        """POST the audit record as JSON to the webhook URL."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=record.to_dict())
                response.raise_for_status()
                logger.debug("webhook_sent", url=self._url, status=response.status_code)
        except httpx.HTTPError:
            logger.exception("webhook_failed", url=self._url)
