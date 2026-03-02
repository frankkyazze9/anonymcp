"""Global settings for AnonyMCP, loaded from env vars and .env files."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AnonyMCPSettings(BaseSettings):
    """AnonyMCP server configuration.

    All settings can be overridden via environment variables
    prefixed with ``ANONYMCP_`` or via a ``.env`` file.
    """

    model_config = SettingsConfigDict(
        env_prefix="ANONYMCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8100
    transport: Literal["stdio", "streamable-http"] = "stdio"
    log_level: str = "INFO"

    # TLS (HTTP transport only)
    tls_certfile: str | None = None
    tls_keyfile: str | None = None
    tls_keyfile_password: str | None = None
    tls_ca_certs: str | None = None  # for mTLS client cert verification

    # Authentication (HTTP transport only)
    api_keys: str | None = None  # comma-separated list of valid API keys
    require_auth: bool = False  # if True, reject requests without valid API key

    # Policy
    policy_path: Path = Path("./policies/default.yaml")
    score_threshold: float = 0.4
    default_language: str = "en"

    # Audit
    audit_enabled: bool = True
    audit_log_path: Path = Path("./audit/anonymcp.jsonl")
    audit_log_original: bool = False

    # Presidio NLP backend
    nlp_engine: Literal["spacy", "transformers"] = "spacy"
    spacy_model: str = "en_core_web_lg"
