"""Default policy configuration constants."""

from anonymcp.policy.models import GovernancePolicy

DEFAULT_POLICY = GovernancePolicy(
    name="default",
    version="1.0",
    description="Default data governance policy for AnonyMCP",
)
