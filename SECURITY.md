# Security Model and Hardening Guide

AnonyMCP processes personally identifiable information by definition.
If you're deploying this in an environment where that matters (and if
it doesn't matter, why are you using this tool?), read this document.

## Threat Model

AnonyMCP sits in the data path between your AI systems and the
outside world. It sees raw PII on input and produces anonymized
text on output. That makes it a high-value target and a single
point of failure for data governance.

Threats we design against:

- **Transport interception** - PII in transit between client and server
- **Unauthorized access** - unauthenticated callers hitting the API
- **Policy tampering** - an attacker downgrading anonymization rules
- **Resource exhaustion** - oversized inputs consuming CPU/memory
- **Audit log exposure** - governance records leaking sensitive metadata
- **Container escape** - compromised container escalating to host

Threats that are out of scope (your responsibility):

- Key management for API keys and TLS certificates
- Network segmentation and firewall rules
- Secrets management (Vault, AWS Secrets Manager, etc.)
- Log aggregation pipeline security
- Client-side credential storage
## Security Controls

### 1. Transport Encryption (TLS)

**Default:** Off (plain HTTP).
**Production requirement:** On.

```bash
ANONYMCP_TLS_CERTFILE=/etc/ssl/certs/anonymcp.pem
ANONYMCP_TLS_KEYFILE=/etc/ssl/private/anonymcp-key.pem
```

AnonyMCP will warn on startup if you bind to a network interface
(`0.0.0.0`) without TLS. Localhost-only (`127.0.0.1`) skips the
warning since traffic stays on the box.

For mutual TLS (client cert verification):

```bash
ANONYMCP_TLS_CA_CERTS=/etc/ssl/certs/client-ca.pem
```

Only clients with a cert signed by your CA will be allowed to connect.

### 2. API Key Authentication

**Default:** Off.
**Production requirement:** On for any shared deployment.

```bash
ANONYMCP_REQUIRE_AUTH=true
ANONYMCP_API_KEYS=prod-key-abc123,staging-key-def456
```

Keys are compared using `hmac.compare_digest` (constant-time) to
prevent timing side-channel attacks. Failed auth attempts are logged
with client IP and request path.

If `REQUIRE_AUTH=true` but no keys are configured, the server refuses
to start. This is intentional -- failing closed is better than
running open.
### 3. PII Leakage Prevention in API Responses

The `analyze_text` tool returns entity type, position (start/end
offsets), and confidence score. It does **not** return the matched
PII text itself. This is deliberate. A detection API that echoes
back `"text": "219-09-9999"` in its JSON response is leaking the
exact data you called it to find.

The raw matched text is available internally to the anonymizer
engine (it needs it to do replacements), but it never crosses the
MCP tool boundary.

### 4. Input Size Limits

**Default:** 100,000 characters.

```bash
ANONYMCP_MAX_TEXT_LENGTH=100000  # adjust as needed, 0 = unlimited
```

Presidio's NLP pipeline (spaCy) loads the full input into memory
for NER processing. Without a size limit, a single oversized request
can consume all available RAM and stall the server. The default of
100K characters is generous for typical document processing. Adjust
based on your workload and available memory.

### 5. Policy Change Auditing

Every call to `manage_policy` with `action="set"` generates a
RESTRICTED-level audit record that captures the old and new policy
name/version. Policy changes are logged at WARNING level to stderr.

In a production deployment, consider:

- Mounting the policy YAML as a read-only volume (Docker/K8s)
- Monitoring audit logs for `action: policy_change` events
- Using GitOps for policy updates instead of the runtime API

The `manage_policy` set action is powerful. If your deployment
doesn't need runtime policy changes, don't expose it. You can
remove it from the tool list by commenting out the `@mcp.tool()`
decorator or adding a settings guard.

### 6. Container Security

The Docker image runs as a non-root user (`anonymcp`). The policy
volume is mounted read-only by default. Audit logs write to a named
Docker volume.

Additional hardening for production:

```yaml
# docker-compose.yaml additions
services:
  anonymcp:
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
```
### 7. Audit Log Security

Audit records contain:

- Action type, timestamp, audit ID
- Classification level
- Entity types found (e.g., `["EMAIL_ADDRESS", "US_SSN"]`)
- Entity count, text length, processing duration
- Policy name and version

Audit records do **not** contain:

- The original input text (unless `audit.log_original_text: true`)
- Raw PII values

The `log_anonymized_text` setting (default: true) includes the
post-anonymization output in audit records. This is useful for
QA and compliance review but may not be appropriate in all
environments. Disable it if your audit pipeline doesn't need it:

```yaml
# policies/default.yaml
audit:
  log_anonymized_text: false
```

### 8. Webhook Exporter

The webhook exporter uses `httpx` with default TLS verification
(system CA bundle). Audit records sent to webhooks follow the same
content rules above. If your webhook endpoint is internal and uses
a private CA, you'll need to either add the CA to the system trust
store or extend the exporter to accept a custom CA path.

The webhook exporter does not currently support authentication
headers. If your endpoint requires auth, put it behind a reverse
proxy or submit a PR.

## Known Limitations

These are things we know about and have not yet addressed:

1. **No rate limiting on the HTTP endpoint.** A determined caller
   can submit requests as fast as the server can handle them.
   Use your API gateway or service mesh for rate limiting until
   we add native support.

2. **No per-key authorization scoping.** All valid API keys have
   equal access to all tools. There's no way to give one key
   read-only access (analyze/classify) while restricting another
   from policy changes. This is on the roadmap.

3. **`get_audit_log` has no access control.** Any authenticated
   MCP client can query the full audit history. In multi-tenant
   deployments, this means one client can see metadata about
   what other clients processed. Scope audit queries to caller
   identity if this matters for your deployment.

4. **In-memory audit buffer is not persisted.** If the process
   crashes, buffered records that haven't been flushed to a file
   or webhook exporter are lost. Use the file exporter for
   durable audit storage.

## Reporting Vulnerabilities

If you find a security issue, please email frankkyazze@gmail.com
instead of opening a public GitHub issue. Include:

- Description of the vulnerability
- Steps to reproduce
- Affected version/commit

I'll acknowledge receipt within 48 hours and aim to ship a fix
within 7 days for critical issues.