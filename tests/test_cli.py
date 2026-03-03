"""Tests for CLI entrypoints and the /health endpoint."""

from __future__ import annotations

import importlib
import subprocess
import sys
from unittest.mock import patch

import pytest

# -- __main__.py ----------------------------------------------------------


def test_main_module_is_importable() -> None:
    """python -m anonymcp should resolve to __main__.py."""
    mod = importlib.import_module("anonymcp.__main__")
    assert hasattr(mod, "__name__")


# -- argparse --------------------------------------------------------------


def test_help_flag_exits_zero() -> None:
    """anonymcp --help should print usage and exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "anonymcp", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "AnonyMCP" in result.stdout
    assert "--transport" in result.stdout
    assert "--port" in result.stdout
    assert "--host" in result.stdout


def test_cli_flags_override_settings() -> None:
    """CLI flags should override env-var defaults in settings."""
    from anonymcp.server import _parse_args, settings

    original_transport = settings.transport
    original_port = settings.port
    original_host = settings.host

    try:
        argv = [
            "anonymcp",
            "--transport",
            "streamable-http",
            "--port",
            "9999",
            "--host",
            "127.0.0.1",
        ]
        with patch("sys.argv", argv):
            _parse_args()

        assert settings.transport == "streamable-http"
        assert settings.port == 9999
        assert settings.host == "127.0.0.1"
    finally:
        # Restore originals so other tests aren't affected
        settings.transport = original_transport  # type: ignore[assignment]
        settings.port = original_port
        settings.host = original_host


def test_cli_flags_default_to_none() -> None:
    """When no flags are passed, settings should not change."""
    from anonymcp.server import _parse_args, settings

    original_transport = settings.transport
    original_port = settings.port

    try:
        with patch("sys.argv", ["anonymcp"]):
            _parse_args()

        assert settings.transport == original_transport
        assert settings.port == original_port
    finally:
        settings.transport = original_transport  # type: ignore[assignment]
        settings.port = original_port


# -- /health endpoint -----------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """GET /health should return status ok without auth."""
    from anonymcp.server import _init_components, mcp

    _init_components()
    starlette_app = mcp.streamable_http_app()

    # Add health route the same way _run_http does
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    from anonymcp.server import policy_engine

    async def _health_check(request):  # type: ignore[no-untyped-def]
        return JSONResponse(
            {
                "status": "ok",
                "policy": policy_engine.policy.name,
                "policy_version": policy_engine.policy.version,
            }
        )

    starlette_app.routes.append(Route("/health", _health_check))

    from starlette.testclient import TestClient

    client = TestClient(starlette_app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "policy" in data
    assert "policy_version" in data
