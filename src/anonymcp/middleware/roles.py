"""Role-based authorization for AnonyMCP tools.

Two built-in roles:

- **read**: Can call detection, classification, and anonymization tools.
  This is what your pipeline agents and application integrations get.
- **admin**: Full access including policy management and audit queries.
  This is for your security team and CI/CD tooling.

Roles are assigned via the ANONYMCP_API_KEYS env var:

    ANONYMCP_API_KEYS=pipeline-key:read,admin-key:admin

Keys without a role tag default to "admin" for backward compatibility.
"""

from __future__ import annotations

from contextvars import ContextVar
from enum import StrEnum

# Stores the caller's role for the current request.
# Set by APIKeyAuthMiddleware, read by tool authorization checks.
# For stdio transport this is never set, so the default is "admin"
# (local user gets full access).
caller_role: ContextVar[str] = ContextVar("caller_role", default="admin")


class Role(StrEnum):
    READ = "read"
    ADMIN = "admin"


# Maps each tool name to the minimum role required.
TOOL_PERMISSIONS: dict[str, Role] = {
    # Read-tier: detection, classification, anonymization
    "analyze_text": Role.READ,
    "anonymize_text": Role.READ,
    "classify_sensitivity": Role.READ,
    "scan_and_protect": Role.READ,
    # Admin-tier: audit and policy management
    "get_audit_log": Role.ADMIN,
    "manage_policy": Role.ADMIN,
}

# Role hierarchy: admin includes all read permissions
ROLE_HIERARCHY: dict[str, set[str]] = {
    Role.READ: {Role.READ},
    Role.ADMIN: {Role.READ, Role.ADMIN},
}


def parse_api_keys(raw: str) -> dict[str, str]:
    """Parse 'key:role,key:role' format into {key: role} mapping.

    Keys without a role suffix default to 'admin' for backward
    compatibility with the original comma-separated key format.
    """
    result: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            key, role = entry.rsplit(":", 1)
            key = key.strip()
            role = role.strip().lower()
            if role not in {r.value for r in Role}:
                role = Role.ADMIN  # unknown role defaults to admin
        else:
            key = entry
            role = Role.ADMIN
        if key:
            result[key] = role
    return result


def check_tool_access(tool_name: str) -> str | None:
    """Check if the current caller's role can access the given tool.

    Returns None if access is allowed, or an error message if denied.
    """
    required = TOOL_PERMISSIONS.get(tool_name)
    if required is None:
        # Unknown tool, allow by default (shouldn't happen)
        return None

    role = caller_role.get()
    allowed_roles = ROLE_HIERARCHY.get(role, set())

    if required not in allowed_roles:
        return (
            f"Access denied: tool '{tool_name}' requires '{required}' role, "
            f"but caller has '{role}' role."
        )
    return None
