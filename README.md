<![CDATA[<h1 align="center">
  🛡️ AnonyMCP
</h1>

<p align="center">
  <strong>Data governance as a composable MCP layer.</strong><br>
  PII detection · anonymization · classification · audit logging — for any AI workflow.
</p>

<p align="center">
  <a href="https://github.com/frankkyazze9/anonymcp/actions"><img src="https://img.shields.io/github/actions/workflow/status/frankkyazze9/anonymcp/ci.yml?style=flat-square" alt="CI"></a>
  <a href="https://github.com/frankkyazze9/anonymcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-purple?style=flat-square" alt="MCP"></a>
</p>]]><![CDATA[

<p align="center">
  <img src="demo/anonymcp-demo.gif" alt="AnonyMCP CLI Demo" width="800">
</p>

---

## Why This Exists

AI doesn't have a compliance layer — yet.

Every time an LLM reads a document, processes customer data, or generates a summary, PII can leak through unnoticed. Today, governance is an afterthought: bolted on at the end, enforced by policy documents nobody reads, and dependent on humans catching what machines miss.

**AnonyMCP changes that.** It embeds governance directly into the AI workflow as a composable MCP server. Instead of asking *"did we redact that?"* after the fact, AnonyMCP makes every piece of text classifiable, auditable, and protectable *before* it ever reaches a model.

This isn't just a PII scrubber. It's a policy-driven governance engine with configurable sensitivity levels, operator rules, real-time alerting, and a full audit trail — designed so that compliance teams, legal, and engineering can speak the same language.

> **The goal:** Make responsible data handling the path of least resistance, not an obstacle to innovation.

---

## Features

- **Detect** — Identify 50+ PII entity types (emails, SSNs, credit cards, names, medical records, etc.) with confidence scores
- **Anonymize** — Replace, redact, mask, hash, or encrypt PII using configurable per-entity operators
- **Classify** — Categorize text as `PUBLIC` / `INTERNAL` / `CONFIDENTIAL` / `RESTRICTED`
- **Audit** — Structured logging of every governance action with exporters (JSONL file, stdout, webhook)
- **Policy-driven** — YAML-based governance policies with per-entity operator rules and alerting thresholds
- **MCP-native** — Works with any MCP client: Claude Desktop, custom agents, RAG pipelines, or your own tooling]]><![CDATA[

---

## Architecture

```mermaid
flowchart TD
    subgraph Clients["MCP Clients"]
        CD["Claude Desktop"]
        CA["Custom Agents"]
        RAG["RAG Pipelines"]
    end

    subgraph AnonyMCP["AnonyMCP Server"]
        MCP["FastMCP Interface<br/><i>stdio · streamable-http</i>"]

        subgraph Tools["MCP Tools"]
            T1["analyze_text"]
            T2["anonymize_text"]
            T3["classify_sensitivity"]
            T4["scan_and_protect"]
            T5["get_audit_log"]
            T6["manage_policy"]
        end

        subgraph Engine["Governance Engine"]
            DET["Detector<br/><i>Presidio Analyzer</i>"]
            ANON["Anonymizer<br/><i>Presidio Anonymizer</i>"]
            CLS["Classifier"]
            PE["Policy Engine"]
        end

        subgraph Audit["Audit System"]
            AL["Audit Logger"]
            FE["File Exporter<br/><i>JSONL</i>"]
            SE["Stdout Exporter"]
            WE["Webhook Exporter"]
        end

        subgraph Policy["Policy Layer"]
            YAML["YAML Config"]
            MODELS["Sensitivity Models"]
            ALERTS["Alert Rules"]
        end
    end

    Clients --> MCP
    MCP --> Tools
    Tools --> Engine
    Engine --> Audit
    PE --> Policy
    AL --> FE
    AL --> SE
    AL --> WE

    style AnonyMCP fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#eee
    style Engine fill:#16213e,stroke:#0f3460,stroke-width:1px,color:#eee
    style Audit fill:#16213e,stroke:#0f3460,stroke-width:1px,color:#eee
    style Policy fill:#16213e,stroke:#0f3460,stroke-width:1px,color:#eee
    style Tools fill:#16213e,stroke:#0f3460,stroke-width:1px,color:#eee
    style Clients fill:#0f3460,stroke:#533483,stroke-width:1px,color:#eee
```]]><![CDATA[

---

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
git clone https://github.com/frankkyazze9/anonymcp.git
cd anonymcp
uv sync
uv run python -m spacy download en_core_web_lg
```

### Use with Claude Desktop

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

Restart Claude Desktop. You'll see 6 new tools available.]]><![CDATA[

### Run as HTTP Server

```bash
ANONYMCP_TRANSPORT=streamable-http uv run anonymcp
```

### Docker

```bash
cd docker && docker compose up --build
```

---

## MCP Tools

| Tool | Description |
|---|---|
| `analyze_text` | Detect and locate PII entities with confidence scores |
| `anonymize_text` | Anonymize PII using configurable operators (replace, redact, mask, hash, encrypt) |
| `classify_sensitivity` | Classify text as PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED |
| `scan_and_protect` | Full detect → classify → anonymize pipeline in one call |
| `get_audit_log` | Query audit records with filters (action, classification, time range) |
| `manage_policy` | View, list entity types, or hot-swap the active governance policy |]]><![CDATA[

---

## Governance Policies

Policies are YAML files that control how AnonyMCP classifies, anonymizes, and alerts. See [`policies/default.yaml`](policies/default.yaml) for the full schema.

```yaml
entity_sensitivity:
  HIGH: [US_SSN, CREDIT_CARD, IBAN_CODE, US_BANK_NUMBER]
  MEDIUM: [EMAIL_ADDRESS, PHONE_NUMBER, PERSON, US_PASSPORT]
  LOW: [URL, DATE_TIME, IP_ADDRESS]

anonymization:
  HIGH:
    operator: redact
  MEDIUM:
    operator: replace
    params:
      new_value: "[{entity_type}]"
  LOW:
    operator: mask
    params:
      masking_char: "*"
      chars_to_mask: 4
      from_end: false
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANONYMCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `ANONYMCP_POLICY_PATH` | `./policies/default.yaml` | Path to governance policy |
| `ANONYMCP_SCORE_THRESHOLD` | `0.4` | Minimum PII detection confidence |
| `ANONYMCP_AUDIT_ENABLED` | `true` | Enable audit logging |
| `ANONYMCP_HOST` | `0.0.0.0` | HTTP server bind address |
| `ANONYMCP_PORT` | `8000` | HTTP server port |]]><![CDATA[

---

## Who Is This For?

### 🏛️ For Legal & Compliance Teams

AnonyMCP provides **auditable, policy-driven PII handling** that maps directly to regulatory requirements. Every detection, classification, and anonymization action is logged with timestamps, entity types, classification levels, and policy versions — giving you the evidence trail regulators expect. Governance policies are defined in human-readable YAML, so legal teams can review and approve the rules without reading code. Classification levels (PUBLIC through RESTRICTED) align with standard data classification frameworks used in GDPR, HIPAA, and PCI-DSS compliance programs.

### 🔐 For CISOs & Security Leaders

AnonyMCP is a **security control for AI workflows**. It sits in the data path and enforces sensitivity policies *before* data reaches LLMs or downstream systems. Configurable alerting rules trigger on high-severity classifications or entity count thresholds, integrating with your existing incident response via webhook exporters. The tool is fully self-hosted — no data leaves your infrastructure. The policy engine supports hot-swapping, so you can update governance rules without restarting services.

### 👩‍💻 For Privacy Engineers & Developers

AnonyMCP is a **drop-in MCP server** you can wire into any AI workflow in minutes. It wraps Microsoft Presidio (the industry-standard NLP-based PII engine) behind a clean tool interface with six composable operations. Use `scan_and_protect` for a one-call pipeline, or chain `analyze_text` → `classify_sensitivity` → `anonymize_text` for granular control. Custom recognizers, per-entity operator overrides, and YAML policy files give you full flexibility without touching core code.]]><![CDATA[

---

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests (36 tests)
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/anonymcp/
```

---

## Roadmap

- [ ] Multi-language PII detection
- [ ] Image & document PII redaction (OCR pipeline)
- [ ] Structured data scanning (JSON, CSV, databases)
- [ ] Compliance preset policies (HIPAA, PCI-DSS, GDPR)
- [ ] Prometheus metrics & OpenTelemetry exporter
- [ ] Custom recognizer plugin system
- [ ] Web dashboard for audit log visualization
- [ ] Batch processing mode for large document sets

---

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/frankkyazze9">Frank Kyazze</a><br>
  <sub>Because privacy shouldn't be an afterthought in AI.</sub>
</p>]]>