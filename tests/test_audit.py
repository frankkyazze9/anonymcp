"""Tests for the audit logging system."""

from __future__ import annotations

import pytest

from anonymcp.audit.events import AuditRecord
from anonymcp.audit.logger import AuditLogger


class TestAuditRecord:
    def test_record_auto_generates_id(self) -> None:
        record = AuditRecord(
            action="analyze",
            classification="PUBLIC",
            entities_found=0,
            entity_types=[],
        )
        assert len(record.audit_id) == 12
        assert record.timestamp is not None

    def test_record_to_dict(self) -> None:
        record = AuditRecord(
            action="anonymize",
            classification="CONFIDENTIAL",
            entities_found=2,
            entity_types=["EMAIL_ADDRESS", "PHONE_NUMBER"],
            entities_anonymized=2,
        )
        d = record.to_dict()
        assert d["action"] == "anonymize"
        assert d["classification"] == "CONFIDENTIAL"
        assert d["entities_found"] == 2
        assert "audit_id" in d
        assert "timestamp" in d


class TestAuditLogger:
    @pytest.mark.asyncio
    async def test_log_and_query(self, audit_logger: AuditLogger) -> None:
        record = AuditRecord(
            action="analyze",
            classification="CONFIDENTIAL",
            entities_found=1,
            entity_types=["EMAIL_ADDRESS"],
        )
        await audit_logger.log(record)
        assert audit_logger.total_records == 1

        results = audit_logger.query(limit=10)
        assert len(results) == 1
        assert results[0]["action"] == "analyze"

    @pytest.mark.asyncio
    async def test_query_filter_by_action(self, audit_logger: AuditLogger) -> None:
        await audit_logger.log(
            AuditRecord(action="analyze", classification="PUBLIC", entities_found=0, entity_types=[])
        )
        await audit_logger.log(
            AuditRecord(action="anonymize", classification="CONFIDENTIAL", entities_found=1, entity_types=["EMAIL_ADDRESS"])
        )

        results = audit_logger.query(action_type="anonymize")
        assert len(results) == 1
        assert results[0]["action"] == "anonymize"

    @pytest.mark.asyncio
    async def test_query_filter_by_classification(self, audit_logger: AuditLogger) -> None:
        await audit_logger.log(
            AuditRecord(action="analyze", classification="PUBLIC", entities_found=0, entity_types=[])
        )
        await audit_logger.log(
            AuditRecord(action="analyze", classification="RESTRICTED", entities_found=1, entity_types=["US_SSN"])
        )

        results = audit_logger.query(classification="RESTRICTED")
        assert len(results) == 1
        assert results[0]["classification"] == "RESTRICTED"
