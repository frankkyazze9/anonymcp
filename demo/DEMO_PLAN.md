# AnonyMCP Demo Plan

## What's Ready

Everything is installed and configured. You have two demo paths:

---

## Option A: Terminal CLI Demo (for README GIF)

This runs a scripted demo showing 3 scenarios with colored output.

### Record with VHS (automated — recommended for GIF)

```bash
cd ~/Desktop/anonymcp
vhs demo/demo.tape
```

This produces `demo/anonymcp-demo.gif` automatically. Drop it into the README.

### Record with asciinema (manual — good for sharing)

```bash
cd ~/Desktop/anonymcp
asciinema rec demo/anonymcp-demo.cast
# Then run:
uv run python demo/demo_cli.py
# Press Ctrl+D when done
```

Convert to GIF with: `agg demo/anonymcp-demo.cast demo/anonymcp-demo.gif`
Or share directly: `asciinema upload demo/anonymcp-demo.cast`

---

## Option B: Claude Desktop Demo (for YouTube video)

This shows AnonyMCP as a live MCP server in Claude Desktop — much more impressive for a video because it demonstrates real AI agent integration.

### Setup (already done)

Claude Desktop config is at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

AnonyMCP is registered as an MCP server. **Restart Claude Desktop** to load it.

### Verify It's Working

After restarting Claude Desktop:
1. Open a new conversation
2. Click the 🔌 (plug) icon or MCP tools area
3. You should see AnonyMCP listed with its 6 tools

### Demo Script — What to Say to Claude

Use these prompts in order. Each one demonstrates a different capability:

**Prompt 1 — Detection + Classification:**
> I need you to check this customer email for sensitive data:
> "Hi, I'm Sarah Johnson (sarah.j@acme.com). My SSN is 123-45-6789 and my credit card is 4111-1111-1111-1111. Can you help reset my account?"

*Expected: Claude calls `analyze_text`, shows detected entities, then calls `classify_sensitivity` → RESTRICTED*

**Prompt 2 — Full Protection Pipeline:**
> Take this medical note and make it safe to share:
> "Patient Michael Chen, DOB 03/15/1985, presented at 123 Oak St, Springfield IL. Contact: mchen@hospital.org, phone 555-234-5678."

*Expected: Claude calls `scan_and_protect`, returns anonymized text with classification*

**Prompt 3 — Clean Text Verification:**
> Is this text safe to publish?
> "Our Q1 revenue grew 15% year-over-year. The product team shipped 3 major features and reduced latency by 40%."

*Expected: Claude calls `classify_sensitivity` → PUBLIC, confirms it's safe*

**Prompt 4 — Audit Trail:**
> Show me the audit log of everything we just did.

*Expected: Claude calls `get_audit_log`, shows all 3 previous actions with timestamps and classifications*

**Prompt 5 — Policy Inspection:**
> What PII entity types can you detect?

*Expected: Claude calls `manage_policy` with action "list", shows all supported entities*

### Screen Recording for YouTube

On macOS, use one of:
- **Built-in:** Cmd+Shift+5 → Record Selected Portion (frame just the Claude Desktop window)
- **OBS Studio** (free): Better for editing, webcam overlay, etc.
- **Screen Studio** (paid, Mac-native): Automatic zoom effects, very polished output

### Suggested YouTube Video Structure (3-5 minutes)

1. **Intro (30s):** "What if you could add a privacy firewall to any AI workflow in one line of config?"
2. **Show the config (15s):** Flash the `claude_desktop_config.json` — just 5 lines to add AnonyMCP
3. **Demo 1 (45s):** Customer email → detection → RESTRICTED classification
4. **Demo 2 (45s):** Medical note → full anonymization pipeline
5. **Demo 3 (30s):** Clean text → PUBLIC, safe to publish
6. **Demo 4 (30s):** Audit log showing everything that happened
7. **Architecture (30s):** Show the architecture diagram from the README
8. **Outro (15s):** Link to GitHub, call to action

---

## Adding the GIF to the README

Once you have the GIF, add this to `README.md` right after the title:

```markdown
<p align="center">
  <img src="demo/anonymcp-demo.gif" alt="AnonyMCP Demo" width="800">
</p>
```

---

## Tips for a Good Recording

- Use a dark terminal theme (the demo uses Rich which looks great on dark backgrounds)
- Increase terminal font size to 16-18pt for readability
- For Claude Desktop, zoom in on the conversation (Cmd+= a few times)
- Keep pauses short — people skip long GIFs
- For YouTube, edit out any loading/waiting time
