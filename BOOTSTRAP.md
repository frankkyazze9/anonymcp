# AnonyMCP — Bootstrap Context for New Conversations

> **Purpose:** Paste this into a new Claude conversation to resume work on AnonyMCP with full context. Update this file as the project evolves.

---

## What Is AnonyMCP?

AnonyMCP is an open-source MCP (Model Context Protocol) server that wraps Microsoft Presidio to provide **data governance as a composable layer** in any AI workflow. Any MCP-compatible client can call its tools to classify, detect, anonymize, and audit PII.

**Repo:** https://github.com/frankkyazze9/anonymcp
**Local path:** `~/Desktop/anonymcp`
**Language:** Python 3.11+
**License:** Apache 2.0

---

## Current State (v0.1.0 scaffold — March 2, 2026)

### What's Built

The full project scaffold is committed and pushed to GitHub. Here's what exists:

**MCP Server (`src/anonymcp/server.py`):**
- FastMCP server with 6 tools:
  - `analyze_text` — detect PII entities with confidence scores
  - `anonymize_text` — transform PII using configurable operators (replace, redact, mask, hash, encrypt)
  - `classify_sensitivity` — classify text as PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED
  - `scan_and_protect` — combined detect+classify+anonymize in one call
  - `get_audit_log` — query audit records
  - `manage_policy` — view/update governance policy at runtime
- 2 resources: `anonymcp://entities/supported`, `anonymcp://policy/current`
- 1 prompt: `governance_review`
- Supports stdio and streamable-http transports

**Engine (`src/anonymcp/engine/`):**
- `TextDetector` — wraps Presidio `AnalyzerEngine`, returns normalized `DetectionResult`
- `TextAnonymizer` — wraps Presidio `AnonymizerEngine`, reads operator config from policy
- `TextClassifier` — classifies sensitivity based on entity types and policy rules
- `RecognizerRegistry` — custom pattern recognizer management

**Policy (`src/anonymcp/policy/`):**
- `GovernancePolicy` — Pydantic model for the full policy schema (entity sensitivity, classification rules, operator mappings, alerts)
- `PolicyEngine` — evaluates classification, checks alert rules, supports hot-reload
- Default policy YAML at `policies/default.yaml`

**Audit (`src/anonymcp/audit/`):**
- `AuditRecord` dataclass with auto-generated ID and timestamp
- `AuditLogger` — routes records to exporters, maintains in-memory buffer for queries
- Exporters: `FileExporter` (JSONL), `StdoutExporter` (structlog), `WebhookExporter` (httpx)

**Config (`src/anonymcp/config/`):**
- `AnonyMCPSettings` — Pydantic BaseSettings with `ANONYMCP_` env prefix
- `load_policy_file()` — YAML/JSON policy file loader

**Infrastructure:**
- `pyproject.toml` with hatchling build, all deps declared
- Dockerfile + docker-compose.yaml
- GitHub Actions CI (lint, typecheck, test)
- Full test suite in `tests/` (detector, anonymizer, classifier, policy, audit)
- README, CONTRIBUTING, LICENSE, .env.example, .gitignore

### What's NOT Built Yet (Roadmap)

From the architecture doc (`AnonyMCP-Architecture.md`):

**v0.2.0 — Production Hardening:**
- [ ] Policy hot-reloading (watcher)
- [ ] Webhook alerting integration (alert rules → webhook exporter)
- [ ] Custom recognizer plugin system (load from config)
- [ ] Prometheus metrics endpoint
- [ ] Rate limiting
- [ ] Example compliance policy presets (HIPAA, PCI-DSS, GDPR YAML files)

**v0.3.0 — Advanced:**
- [ ] Multi-language PII detection
- [ ] Image PII redaction (presidio-image-redactor)
- [ ] Structured data scanning (presidio-structured)
- [ ] Deanonymization support (reversible encrypt operator)
- [ ] OpenTelemetry exporter
- [ ] Backend-agnostic detector interface (abstract base class so Presidio can be swapped)

---

## Key Files to Read First

When continuing work, start by reading these:

1. `src/anonymcp/server.py` — all tool definitions, the main entrypoint
2. `src/anonymcp/policy/models.py` — the GovernancePolicy schema drives everything
3. `src/anonymcp/engine/detector.py` — how detection works
4. `policies/default.yaml` — the default policy users ship with
5. `tests/conftest.py` — shared fixtures and sample PII texts

---

## Architecture Doc

A comprehensive architecture and design document exists at:
`~/Desktop/anonymcp/../AnonyMCP-Architecture.md`
(It was the first deliverable from the initial conversation — covers vision, all tool schemas with request/response examples, policy engine design, audit system, data flow diagrams, tech stack, and roadmap.)

---

## Tech Stack

| Component | Technology |
|---|---|
| MCP Framework | `mcp` Python SDK (FastMCP) |
| PII Detection | `presidio-analyzer` |
| PII Anonymization | `presidio-anonymizer` |
| NLP Backend | spaCy (`en_core_web_lg`) |
| Configuration | Pydantic v2 + PyYAML |
| Logging | structlog |
| HTTP Client | httpx (webhooks) |
| Async File IO | aiofiles |
| Testing | pytest + pytest-asyncio |
| Linting | ruff |
| Types | mypy (strict) |
| Packaging | hatchling + uv |
| CI | GitHub Actions |

---

## Design Decisions Made

1. **Presidio as default engine** — chosen for completeness (detect + anonymize + operators). Architecture designed to be backend-agnostic so alternative engines (DataFog, custom NER) can be plugged in later.
2. **YAML policies** — governance teams need to configure behavior without writing code. YAML was chosen over JSON for readability.
3. **In-memory audit buffer** — the audit logger keeps a bounded deque for fast queries. File/webhook exporters handle persistence.
4. **FastMCP over low-level Server** — simpler tool definitions, automatic schema generation from type hints.
5. **Apache 2.0 license** — balance of openness and patent protection for enterprise adoption.

---

## Open Questions (from architecture doc)

1. Deanonymization scope — reversible encryption with key management? (punted to v0.3)
2. Batch processing tool — `batch_analyze` vs client-side batching?
3. Streaming PII detection — incremental detection on LLM token streams?
4. Multi-tenancy — per-client policies on shared HTTP deployments?

---

## How to Continue

When starting a new conversation, paste this file and say something like:

> "I'm continuing work on AnonyMCP. The repo is at ~/Desktop/anonymcp. Here's the bootstrap context: [paste this file]. I want to work on [specific task]."

**Update this file** after each major session by appending what was done and what changed.

---

## Session Log

### Session 1 — March 2, 2026
- Created architecture and design doc
- Researched Presidio SDK and MCP Python SDK
- Compared Presidio to alternatives (DataFog, John Snow Labs, Phileas)
- Scaffolded full project (34 files, 2231 lines)
- Created GitHub repo: https://github.com/frankkyazze9/anonymcp
- Pushed initial commit to main
