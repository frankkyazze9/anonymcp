# AnonyMCP

**Data governance as a composable MCP layer.** AnonyMCP is an open-source [Model Context Protocol](https://modelcontextprotocol.io) server that wraps [Microsoft Presidio](https://microsoft.github.io/presidio/) to provide PII detection, anonymization, classification, and audit logging for any AI workflow.

Think of it as a **privacy firewall you can drop into any AI stack**.

---

## Features

- **Detect** — Identify PII entities (emails, SSNs, credit cards, names, etc.) with confidence scores
- **Anonymize** — Replace, redact, mask, hash, or encrypt PII using configurable operators
- **Classify** — Categorize text as PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED
- **Audit** — Structured logging of every governance action with exporters (file, stdout, webhook)
- **Policy-driven** — YAML-based governance policies with per-entity operator rules and alerting
- **MCP-native** — Works with any MCP client: Claude Desktop, custom agents, RAG pipelines

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
# Clone the repo
git clone https://github.com/frankkyazze9/anonymcp.git
cd anonymcp

# Install with uv
uv sync

# Download the spaCy NLP model
uv run python -m spacy download en_core_web_lg
```

### Run with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "anonymcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/anonymcp", "run", "anonymcp"]
    }
  }
}
```

### Run as HTTP Server

```bash
ANONYMCP_TRANSPORT=streamable-http anonymcp
```

### Docker

```bash
cd docker
docker compose up --build
```

## MCP Tools

| Tool | Description |
|---|---|
| `analyze_text` | Detect and locate PII entities in text |
| `anonymize_text` | Anonymize PII using configurable operators |
| `classify_sensitivity` | Classify text by sensitivity level |
| `scan_and_protect` | Full governance pipeline in one call |
| `get_audit_log` | Query audit records |
| `manage_policy` | View or update the active policy |

## Configuration

Copy `.env.example` to `.env` and customize. Key settings:

| Variable | Default | Description |
|---|---|---|
| `ANONYMCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `ANONYMCP_POLICY_PATH` | `./policies/default.yaml` | Path to governance policy |
| `ANONYMCP_SCORE_THRESHOLD` | `0.4` | Minimum PII detection confidence |
| `ANONYMCP_AUDIT_ENABLED` | `true` | Enable audit logging |

## Governance Policies

Policies are YAML files that control classification, anonymization operators, and alerting rules. See `policies/default.yaml` for the full schema.

```yaml
entity_sensitivity:
  HIGH: [US_SSN, CREDIT_CARD, IBAN_CODE]
  MEDIUM: [EMAIL_ADDRESS, PHONE_NUMBER, PERSON]
  LOW: [URL, DATE_TIME]

anonymization:
  HIGH:
    operator: redact
  MEDIUM:
    operator: replace
    params:
      new_value: "[{entity_type}]"
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/anonymcp/
```

## Architecture

```
MCP Clients → AnonyMCP Server → Governance Engine → Audit Logger
                                  ├── Detector (Presidio Analyzer)
                                  ├── Anonymizer (Presidio Anonymizer)
                                  ├── Classifier (Policy-based)
                                  └── Policy Engine (YAML config)
```

## Roadmap

- [ ] Multi-language PII detection
- [ ] Image PII redaction
- [ ] Structured data scanning
- [ ] Prometheus metrics
- [ ] OpenTelemetry exporter
- [ ] Compliance preset policies (HIPAA, PCI-DSS, GDPR)
- [ ] Custom recognizer plugin system

## License

Apache 2.0 — see [LICENSE](LICENSE).
