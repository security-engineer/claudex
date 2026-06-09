---
description: Show the current work-split mode and Codex sub-agent status
---

Report **claudex status** as one compact block. Run the checks below, then present the results. Never print secrets or tokens.

### A) Work-split mode

```bash
cat ~/.claude/claudex-mode 2>/dev/null || echo balanced
```
The active mode is one of `solo | balanced | codex | max`. Change it with `/claudex:mode <mode>`.

### B) Codex sub-agent

- `codex login status` · `codex --version` · `model`/`model_reasoning_effort` from `~/.codex/config.toml` · `claude mcp list` (is `codex` `✔ Connected`?)

### Present

A tidy block — **mode**: the active work split; **Codex**: logged in?, version, model, MCP connected?. If Codex is logged out or the MCP is disconnected, give the fix (`codex login`, restart Claude Code).

Note: for Claude's own usage, use the built-in **`/usage`** (plan quota) and **`/context`** (context window) — this plugin does not reinvent those.
