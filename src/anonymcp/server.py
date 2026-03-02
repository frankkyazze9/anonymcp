"""AnonyMCP — MCP server for data governance.

This is the main entrypoint. It exposes PII detection, anonymization,
classification, and audit tools over the Model Context Protocol.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Any

# CRITICAL: In stdio transport mode, stdout is the MCP JSON-RPC channel.
# ALL logging must go to stderr to avoid corrupting the protocol.
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

import structlog  # noqa: E402

# Configure structlog to write to stderr, not stdout
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

from mcp.server.fastmcp import FastMCP  # noqa: E402

from anonymcp.audit.events import AuditRecord  # noqa: E402
from anonymcp.audit.logger import AuditLogger  # noqa: E402
from anonymcp.config.settings import AnonyMCPSettings  # noqa: E402
from anonymcp.engine.anonymizer import TextAnonymizer  # noqa: E402
from anonymcp.engine.classifier import TextClassifier  # noqa: E402
from anonymcp.engine.detector import TextDetector  # noqa: E402
from anonymcp.policy.engine import PolicyEngine  # noqa: E402
from anonymcp.policy.models import GovernancePolicy  # noqa: E402

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Globals initialised at startup
# ---------------------------------------------------------------------------
settings = AnonyMCPSettings()
mcp = FastMCP("AnonyMCP")

policy_engine: PolicyEngine
detector: TextDetector
anonymizer: TextAnonymizer
classifier: TextClassifier
audit_logger: AuditLogger


def _init_components() -> None:
    """Initialise all engine components from settings and policy."""
    global policy_engine, detector, anonymizer, classifier, audit_logger

    # Load policy
    if settings.policy_path.exists():
        policy_engine = PolicyEngine.from_file(settings.policy_path)
    else:
        logger.warning("policy_file_not_found", path=str(settings.policy_path))
        policy_engine = PolicyEngine()

    policy = policy_engine.policy

    # Detection
    detector = TextDetector()

    # Anonymization
    anonymizer = TextAnonymizer(policy=policy)

    # Classification
    classifier = TextClassifier(policy_engine=policy_engine)

    # Audit
    audit_logger = AuditLogger()
    if policy.audit.enabled:
        audit_logger.configure_from_policy(
            [e.copy() if isinstance(e, dict) else e for e in policy.audit.exporters]
        )

    logger.info(
        "anonymcp_initialized",
        policy=policy.name,
        version=policy.version,
        audit_enabled=policy.audit.enabled,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_text_length(text: str) -> str | None:
    """Return an error message if text exceeds the configured limit."""
    if settings.max_text_length > 0 and len(text) > settings.max_text_length:
        return (
            f"Input text too large ({len(text)} chars). "
            f"Maximum is {settings.max_text_length} chars. "
            f"Set ANONYMCP_MAX_TEXT_LENGTH to adjust."
        )
    return None


def _redact_results(results: list[dict]) -> list[dict]:
    """Strip raw PII values from detection results before returning to callers.

    The 'text' field contains the actual PII (SSNs, emails, etc).
    Returning that in API responses defeats the purpose of a governance tool.
    Callers get entity type, position, and score -- enough to act on.
    """
    return [
        {
            "entity_type": r["entity_type"],
            "start": r["start"],
            "end": r["end"],
            "score": r["score"],
        }
        for r in results
    ]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def analyze_text(
    text: str,
    entities: list[str] | None = None,
    language: str = "en",
    score_threshold: float = 0.4,
) -> dict[str, Any]:
    """Detect and locate PII entities in text.

    Scans text for personally identifiable information and returns
    each detected entity with its type, location, and confidence score.

    Args:
        text: The text to analyze for PII.
        entities: Optional list of entity types to detect (e.g. ["EMAIL_ADDRESS", "CREDIT_CARD"]).
            If not provided, all supported entity types are scanned.
        language: Language code for NLP processing (default: "en").
        score_threshold: Minimum confidence score to include a result (default: 0.4).

    Returns:
        Dictionary with entities_found count, results list, and analysis_id.
    """
    if err := _check_text_length(text):
        return {"error": err}

    start = time.monotonic()

    result = detector.detect(
        text,
        entities=entities,
        language=language,
        score_threshold=score_threshold,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    entity_types = result.entity_types()
    classification = policy_engine.classify(entity_types)

    record = AuditRecord(
        action="analyze",
        classification=classification.value,
        entities_found=result.entities_found,
        entity_types=entity_types,
        policy_name=policy_engine.policy.name,
        policy_version=policy_engine.policy.version,
        duration_ms=duration_ms,
        text_length=len(text),
    )
    await audit_logger.log(record)

    return {
        "entities_found": result.entities_found,
        "results": _redact_results(result.results),
        "analysis_id": record.audit_id,
    }


@mcp.tool()
async def anonymize_text(
    text: str,
    operators: dict[str, dict[str, Any]] | None = None,
    entities: list[str] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    """Anonymize PII in text using configurable operators.

    Detects PII entities, then applies anonymization operators
    (replace, redact, mask, hash, encrypt) based on the active
    governance policy or per-call operator overrides.

    Args:
        text: The text to anonymize.
        operators: Optional per-entity operator overrides.
            Format: {"EMAIL_ADDRESS": {"type": "mask", "masking_char": "*", "chars_to_mask": 8}}
        entities: Optional entity types to target. If not provided, all types are processed.
        language: Language code (default: "en").

    Returns:
        Dictionary with anonymized_text, entity count, and operators applied.
    """
    if err := _check_text_length(text):
        return {"error": err}

    start = time.monotonic()

    detection = detector.detect(
        text,
        entities=entities,
        language=language,
        score_threshold=policy_engine.policy.detection.score_threshold,
    )

    anon_result = anonymizer.anonymize(
        text,
        detection.raw_results,
        operator_overrides=operators,
    )

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    entity_types = detection.entity_types()
    classification = policy_engine.classify(entity_types)

    record = AuditRecord(
        action="anonymize",
        classification=classification.value,
        entities_found=detection.entities_found,
        entity_types=entity_types,
        entities_anonymized=anon_result.entities_anonymized,
        operators_used=anon_result.operators_applied,
        policy_name=policy_engine.policy.name,
        policy_version=policy_engine.policy.version,
        duration_ms=duration_ms,
        text_length=len(text),
        anonymized_text=(
            anon_result.anonymized_text
            if policy_engine.policy.audit.log_anonymized_text
            else None
        ),
    )
    await audit_logger.log(record)

    return {
        "anonymized_text": anon_result.anonymized_text,
        "entities_found": detection.entities_found,
        "entities_anonymized": anon_result.entities_anonymized,
        "operators_applied": anon_result.operators_applied,
        "analysis_id": record.audit_id,
    }


@mcp.tool()
async def classify_sensitivity(
    text: str,
    policy: str = "default",
) -> dict[str, Any]:
    """Classify text by sensitivity level based on PII content.

    Scans text for PII, then categorises it as PUBLIC, INTERNAL,
    CONFIDENTIAL, or RESTRICTED based on the governance policy.

    Args:
        text: The text to classify.
        policy: Policy name to apply (default: "default").

    Returns:
        Dictionary with classification level, confidence, reason, and entity summary.
    """
    if err := _check_text_length(text):
        return {"error": err}

    start = time.monotonic()

    detection = detector.detect(
        text,
        language=policy_engine.policy.detection.language,
        score_threshold=policy_engine.policy.detection.score_threshold,
    )

    scores = [r["score"] for r in detection.results]
    cls_result = classifier.classify(detection.entity_types(), scores=scores)

    duration_ms = round((time.monotonic() - start) * 1000, 2)

    record = AuditRecord(
        action="classify",
        classification=cls_result.classification.value,
        entities_found=detection.entities_found,
        entity_types=detection.entity_types(),
        policy_name=cls_result.policy_applied,
        duration_ms=duration_ms,
        text_length=len(text),
    )
    await audit_logger.log(record)

    return {
        "classification": cls_result.classification.value,
        "confidence": cls_result.confidence,
        "reason": cls_result.reason,
        "entity_summary": cls_result.entity_summary,
        "policy_applied": cls_result.policy_applied,
        "analysis_id": record.audit_id,
    }


@mcp.tool()
async def scan_and_protect(
    text: str,
    policy: str = "default",
    return_original: bool = False,
) -> dict[str, Any]:
    """Detect, classify, and anonymize PII in a single call.

    This is the convenience "just make it safe" tool — it runs the
    full governance pipeline and returns protected text.

    Args:
        text: The text to process.
        policy: Policy name to apply (default: "default").
        return_original: If True, include the original text in the response.

    Returns:
        Dictionary with protected_text, classification, and entity counts.
    """
    if err := _check_text_length(text):
        return {"error": err}

    start = time.monotonic()

    # Detect
    detection = detector.detect(
        text,
        language=policy_engine.policy.detection.language,
        score_threshold=policy_engine.policy.detection.score_threshold,
    )

    # Classify
    entity_types = detection.entity_types()
    classification = policy_engine.classify(entity_types)

    # Anonymize
    anon_result = anonymizer.anonymize(text, detection.raw_results)

    duration_ms = round((time.monotonic() - start) * 1000, 2)

    record = AuditRecord(
        action="scan_and_protect",
        classification=classification.value,
        entities_found=detection.entities_found,
        entity_types=entity_types,
        entities_anonymized=anon_result.entities_anonymized,
        operators_used=anon_result.operators_applied,
        policy_name=policy_engine.policy.name,
        policy_version=policy_engine.policy.version,
        duration_ms=duration_ms,
        text_length=len(text),
        anonymized_text=(
            anon_result.anonymized_text
            if policy_engine.policy.audit.log_anonymized_text
            else None
        ),
    )
    await audit_logger.log(record)

    # Check alerts
    alerts = policy_engine.should_alert(classification, detection.entities_found)

    response: dict[str, Any] = {
        "protected_text": anon_result.anonymized_text,
        "classification": classification.value,
        "entities_found": detection.entities_found,
        "entities_anonymized": anon_result.entities_anonymized,
        "policy_applied": policy_engine.policy.name,
        "audit_id": record.audit_id,
    }

    if return_original:
        response["original_text"] = text
    if alerts:
        response["alerts_triggered"] = alerts

    return response


@mcp.tool()
async def get_audit_log(
    limit: int = 50,
    since: str | None = None,
    action_type: str | None = None,
    classification: str | None = None,
) -> dict[str, Any]:
    """Retrieve audit records for governance actions.

    Query the audit log to review past detection, anonymization,
    and classification actions for compliance reporting.

    Args:
        limit: Maximum number of records to return (default: 50).
        since: ISO 8601 timestamp — only return records after this time.
        action_type: Filter by action (analyze, anonymize, classify, scan_and_protect).
        classification: Filter by classification level (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED).

    Returns:
        Dictionary with total_records count and records list.
    """
    records = audit_logger.query(
        limit=limit,
        since=since,
        action_type=action_type,
        classification=classification,
    )

    return {
        "total_records": audit_logger.total_records,
        "returned": len(records),
        "records": records,
    }


@mcp.tool()
async def manage_policy(
    action: str,
    policy_name: str = "default",
    policy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """View or update the active governance policy.

    Args:
        action: One of "get" (view current policy), "list" (list entity types),
            or "set" (update policy configuration).
        policy_name: Policy name to act on (default: "default").
        policy_config: New policy configuration dict (required for "set" action).

    Returns:
        Dictionary with the requested policy information.
    """
    if action == "get":
        p = policy_engine.policy
        return {
            "name": p.name,
            "version": p.version,
            "description": p.description,
            "entity_sensitivity": {
                k.value: v for k, v in p.entity_sensitivity.items()
            },
            "detection": {
                "score_threshold": p.detection.score_threshold,
                "language": p.detection.language,
            },
        }

    elif action == "list":
        supported = detector.get_supported_entities(
            language=policy_engine.policy.detection.language
        )
        return {
            "supported_entities": supported,
            "total": len(supported),
        }

    elif action == "set":
        if not policy_config:
            return {"error": "policy_config is required for 'set' action"}

        old_name = policy_engine.policy.name
        old_version = policy_engine.policy.version
        new_policy = GovernancePolicy(**policy_config)
        policy_engine._policy = new_policy
        anonymizer.policy = new_policy

        # Audit the policy change - this is a security-relevant event
        record = AuditRecord(
            action="policy_change",
            classification="RESTRICTED",
            entities_found=0,
            entity_types=[],
            policy_name=new_policy.name,
            policy_version=new_policy.version,
            metadata={
                "previous_policy": old_name,
                "previous_version": old_version,
            },
        )
        await audit_logger.log(record)

        logger.warning(
            "policy_updated",
            old=f"{old_name}@{old_version}",
            new=f"{new_policy.name}@{new_policy.version}",
        )
        return {
            "status": "updated",
            "name": new_policy.name,
            "version": new_policy.version,
            "audit_id": record.audit_id,
        }

    return {"error": f"Unknown action: {action}. Use 'get', 'list', or 'set'."}


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------


@mcp.resource("anonymcp://entities/supported")
def resource_supported_entities() -> str:
    """List all PII entity types that AnonyMCP can detect."""
    entities = detector.get_supported_entities()
    return "\n".join(sorted(entities))


@mcp.resource("anonymcp://policy/current")
def resource_current_policy() -> str:
    """The currently active governance policy configuration."""
    p = policy_engine.policy
    return f"Policy: {p.name} v{p.version}\n{p.description}"


# ---------------------------------------------------------------------------
# MCP Prompts
# ---------------------------------------------------------------------------


@mcp.prompt()
def governance_review() -> str:
    """System prompt for an LLM acting as a data governance reviewer."""
    return (
        "You are a data governance reviewer. Your role is to analyze text "
        "for personally identifiable information (PII) and recommend "
        "appropriate classification and handling. Use the AnonyMCP tools "
        "available to you:\n\n"
        "1. Use `analyze_text` to detect PII entities\n"
        "2. Use `classify_sensitivity` to determine the data classification\n"
        "3. Use `anonymize_text` to redact or mask sensitive data\n"
        "4. Use `scan_and_protect` for a complete governance pass\n\n"
        "Always explain what PII was found, the classification level, "
        "and why specific anonymization operators were applied."
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def _run_http() -> None:
    """Run the HTTP transport with optional TLS and API key auth."""
    import asyncio

    import uvicorn

    starlette_app = mcp.streamable_http_app()

    # Wire up API key auth if configured
    if settings.require_auth:
        if not settings.api_keys:
            logger.error(
                "auth_enabled_but_no_keys",
                hint="Set ANONYMCP_API_KEYS to a comma-separated list of keys",
            )
            sys.exit(1)

        from anonymcp.middleware.auth import APIKeyAuthMiddleware  # noqa: E402

        valid_keys = {k.strip() for k in settings.api_keys.split(",") if k.strip()}
        starlette_app.add_middleware(APIKeyAuthMiddleware, valid_keys=valid_keys)
        logger.info("auth_enabled", num_keys=len(valid_keys))

    # Build uvicorn config with TLS if certs are provided
    uvicorn_kwargs: dict[str, Any] = {
        "host": settings.host,
        "port": settings.port,
        "log_level": settings.log_level.lower(),
    }

    if settings.tls_certfile and settings.tls_keyfile:
        uvicorn_kwargs["ssl_certfile"] = settings.tls_certfile
        uvicorn_kwargs["ssl_keyfile"] = settings.tls_keyfile
        if settings.tls_keyfile_password:
            uvicorn_kwargs["ssl_keyfile_password"] = settings.tls_keyfile_password
        if settings.tls_ca_certs:
            # Enables mutual TLS (client cert verification)
            import ssl

            uvicorn_kwargs["ssl_ca_certs"] = settings.tls_ca_certs
            uvicorn_kwargs["ssl_cert_reqs"] = ssl.CERT_REQUIRED
        protocol = "https"
        logger.info(
            "tls_enabled",
            certfile=settings.tls_certfile,
            mtls=bool(settings.tls_ca_certs),
        )
    else:
        protocol = "http"
        if settings.host != "127.0.0.1" and settings.host != "localhost":
            logger.warning(
                "no_tls_on_network_interface",
                host=settings.host,
                hint="Set ANONYMCP_TLS_CERTFILE and ANONYMCP_TLS_KEYFILE for production",
            )

    logger.info(
        "http_listening",
        url=f"{protocol}://{settings.host}:{settings.port}/mcp",
    )

    config = uvicorn.Config(starlette_app, **uvicorn_kwargs)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


def main() -> None:
    """Run the AnonyMCP server."""
    _init_components()

    logger.info(
        "anonymcp_starting",
        transport=settings.transport,
        host=settings.host,
        port=settings.port,
    )

    if settings.transport == "streamable-http":
        _run_http()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
