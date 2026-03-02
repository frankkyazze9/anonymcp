# Contributing to AnonyMCP

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. Fork and clone the repo
2. Install dependencies: `uv sync --dev`
3. Download the spaCy model: `uv run python -m spacy download en_core_web_lg`
4. Run tests: `uv run pytest tests/ -v`

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass and linting is clean
4. Submit a PR with a clear description of the change

## Code Style

- We use `ruff` for linting and formatting
- Type hints are required (enforced by `mypy --strict`)
- Docstrings follow Google style

## Areas for Contribution

- Custom PII recognizers
- New audit exporters (OpenTelemetry, Datadog, etc.)
- Compliance policy presets (HIPAA, GDPR, PCI-DSS)
- Multi-language support
- Documentation improvements
