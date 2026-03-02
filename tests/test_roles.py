"""Tests for role-based authorization."""

from __future__ import annotations

from anonymcp.middleware.roles import (
    caller_role,
    check_tool_access,
    parse_api_keys,
)


class TestParseApiKeys:
    def test_key_with_role(self) -> None:
        result = parse_api_keys("my-key:read")
        assert result == {"my-key": "read"}

    def test_key_without_role_defaults_admin(self) -> None:
        result = parse_api_keys("my-key")
        assert result == {"my-key": "admin"}

    def test_multiple_keys(self) -> None:
        result = parse_api_keys("pipeline-key:read,admin-key:admin,legacy-key")
        assert result == {
            "pipeline-key": "read",
            "admin-key": "admin",
            "legacy-key": "admin",
        }

    def test_whitespace_handling(self) -> None:
        result = parse_api_keys(" key1 : read , key2 : admin ")
        assert result == {"key1": "read", "key2": "admin"}

    def test_empty_string(self) -> None:
        result = parse_api_keys("")
        assert result == {}

    def test_unknown_role_defaults_admin(self) -> None:
        result = parse_api_keys("key1:superuser")
        assert result == {"key1": "admin"}

    def test_key_with_colons_in_value(self) -> None:
        """Key might contain colons (e.g. base64). Last colon is the delimiter."""
        result = parse_api_keys("abc:def:ghi:read")
        assert result == {"abc:def:ghi": "read"}


class TestCheckToolAccess:
    def test_admin_can_access_read_tools(self) -> None:
        token = caller_role.set("admin")
        try:
            assert check_tool_access("analyze_text") is None
            assert check_tool_access("anonymize_text") is None
            assert check_tool_access("classify_sensitivity") is None
            assert check_tool_access("scan_and_protect") is None
        finally:
            caller_role.reset(token)

    def test_admin_can_access_admin_tools(self) -> None:
        token = caller_role.set("admin")
        try:
            assert check_tool_access("get_audit_log") is None
            assert check_tool_access("manage_policy") is None
        finally:
            caller_role.reset(token)

    def test_read_can_access_read_tools(self) -> None:
        token = caller_role.set("read")
        try:
            assert check_tool_access("analyze_text") is None
            assert check_tool_access("anonymize_text") is None
            assert check_tool_access("classify_sensitivity") is None
            assert check_tool_access("scan_and_protect") is None
        finally:
            caller_role.reset(token)

    def test_read_cannot_access_admin_tools(self) -> None:
        token = caller_role.set("read")
        try:
            err = check_tool_access("get_audit_log")
            assert err is not None
            assert "admin" in err
            assert "read" in err

            err = check_tool_access("manage_policy")
            assert err is not None
            assert "admin" in err
        finally:
            caller_role.reset(token)

    def test_default_role_is_admin(self) -> None:
        """stdio transport never sets the contextvar, so default must be admin."""
        # Don't set the contextvar - use its default
        assert check_tool_access("manage_policy") is None
        assert check_tool_access("get_audit_log") is None

    def test_unknown_tool_allowed(self) -> None:
        token = caller_role.set("read")
        try:
            assert check_tool_access("some_future_tool") is None
        finally:
            caller_role.reset(token)
