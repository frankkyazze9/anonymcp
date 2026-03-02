"""End-to-end security smoke tests.

These tests verify the security hardening actually works at the
tool level, not just in unit isolation. They import the real
tool functions and engine components.
"""

from __future__ import annotations

import pytest

from anonymcp.middleware.roles import caller_role

# ---------------------------------------------------------------------------
# Fixtures: initialize the server components once
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def _init_server():
    """Initialize AnonyMCP server components for tool-level tests."""
    from anonymcp.server import _init_components

    _init_components()


# ---------------------------------------------------------------------------
# 1. PII Redaction in analyze_text response
# ---------------------------------------------------------------------------


class TestPIIRedaction:
    @pytest.mark.asyncio
    async def test_analyze_does_not_return_raw_pii(self) -> None:
        """analyze_text must NOT include the matched PII text in results."""
        from anonymcp.server import analyze_text

        result = await analyze_text(
            text="My SSN is 219-09-9999 and email is test@example.com",
        )

        assert result["entities_found"] >= 1
        for entity in result["results"]:
            # Must have these fields
            assert "entity_type" in entity
            assert "start" in entity
            assert "end" in entity
            assert "score" in entity
            # Must NOT have the raw PII text
            assert "text" not in entity

    @pytest.mark.asyncio
    async def test_analyze_results_have_no_pii_values(self) -> None:
        """Double-check: no field in the result contains the actual SSN."""
        from anonymcp.server import analyze_text

        ssn = "219-09-9999"
        result = await analyze_text(text=f"SSN: {ssn}")

        result_str = str(result["results"])
        assert ssn not in result_str


# ---------------------------------------------------------------------------
# 2. Input size limits
# ---------------------------------------------------------------------------


class TestInputLimits:
    @pytest.mark.asyncio
    async def test_analyze_rejects_oversized_input(self) -> None:
        from anonymcp.server import analyze_text, settings

        original = settings.max_text_length
        settings.max_text_length = 100  # temporarily lower
        try:
            result = await analyze_text(text="A" * 200)
            assert "error" in result
            assert "too large" in result["error"]
        finally:
            settings.max_text_length = original

    @pytest.mark.asyncio
    async def test_anonymize_rejects_oversized_input(self) -> None:
        from anonymcp.server import anonymize_text, settings

        original = settings.max_text_length
        settings.max_text_length = 100
        try:
            result = await anonymize_text(text="A" * 200)
            assert "error" in result
        finally:
            settings.max_text_length = original

    @pytest.mark.asyncio
    async def test_classify_rejects_oversized_input(self) -> None:
        from anonymcp.server import classify_sensitivity, settings

        original = settings.max_text_length
        settings.max_text_length = 100
        try:
            result = await classify_sensitivity(text="A" * 200)
            assert "error" in result
        finally:
            settings.max_text_length = original

    @pytest.mark.asyncio
    async def test_scan_and_protect_rejects_oversized_input(self) -> None:
        from anonymcp.server import scan_and_protect, settings

        original = settings.max_text_length
        settings.max_text_length = 100
        try:
            result = await scan_and_protect(text="A" * 200)
            assert "error" in result
        finally:
            settings.max_text_length = original

    @pytest.mark.asyncio
    async def test_normal_input_passes(self) -> None:
        from anonymcp.server import analyze_text, settings

        original = settings.max_text_length
        settings.max_text_length = 1000
        try:
            result = await analyze_text(text="Hello world")
            assert "error" not in result
        finally:
            settings.max_text_length = original


# ---------------------------------------------------------------------------
# 3. RBAC enforcement at tool level
# ---------------------------------------------------------------------------


class TestRBACEnforcement:
    @pytest.mark.asyncio
    async def test_read_role_blocked_from_audit_log(self) -> None:
        from anonymcp.server import get_audit_log

        token = caller_role.set("read")
        try:
            result = await get_audit_log()
            assert "error" in result
            assert "Access denied" in result["error"]
        finally:
            caller_role.reset(token)

    @pytest.mark.asyncio
    async def test_read_role_blocked_from_manage_policy(self) -> None:
        from anonymcp.server import manage_policy

        token = caller_role.set("read")
        try:
            result = await manage_policy(action="get")
            assert "error" in result
            assert "Access denied" in result["error"]
        finally:
            caller_role.reset(token)

    @pytest.mark.asyncio
    async def test_admin_role_can_access_audit_log(self) -> None:
        from anonymcp.server import get_audit_log

        token = caller_role.set("admin")
        try:
            result = await get_audit_log()
            assert "error" not in result
            assert "total_records" in result
        finally:
            caller_role.reset(token)

    @pytest.mark.asyncio
    async def test_admin_role_can_manage_policy(self) -> None:
        from anonymcp.server import manage_policy

        token = caller_role.set("admin")
        try:
            result = await manage_policy(action="get")
            assert "error" not in result
            assert "name" in result
        finally:
            caller_role.reset(token)

    @pytest.mark.asyncio
    async def test_read_role_can_analyze(self) -> None:
        """Read role should have full access to detection tools."""
        from anonymcp.server import analyze_text

        token = caller_role.set("read")
        try:
            result = await analyze_text(text="test@example.com")
            assert "error" not in result
            assert "entities_found" in result
        finally:
            caller_role.reset(token)


# ---------------------------------------------------------------------------
# 4. Policy change audit trail
# ---------------------------------------------------------------------------


class TestPolicyChangeAudit:
    @pytest.mark.asyncio
    async def test_policy_set_creates_audit_record(self) -> None:
        from anonymcp.server import audit_logger, manage_policy

        initial_count = audit_logger.total_records

        await manage_policy(
            action="set",
            policy_config={"name": "test-policy", "version": "99.0"},
        )

        assert audit_logger.total_records > initial_count
        records = audit_logger.query(limit=1)
        latest = records[0]
        assert latest["action"] == "policy_change"
        assert latest["classification"] == "RESTRICTED"
        assert latest["metadata"]["previous_policy"] is not None
