#!/usr/bin/env bash
# SessionStart hook for the codex-subagent plugin.
# Injects a short standing policy so Claude defaults to the balanced
# Codex-delegation posture in every session. Kept brief on purpose —
# the full workflow lives in the `codex-subagent` skill (loaded on demand).
set -euo pipefail

read -r -d '' POLICY <<'EOF' || true
The `codex` MCP server (OpenAI Codex, GPT-5.x) is available as a BALANCED sub-agent.
Default posture — save Anthropic tokens without losing quality:
- Delegate to Codex: codebase exploration, first-draft code/refactors, independent second-opinion review, edge-case hunting, large-file reading.
- Keep on Claude: final judgment, applying edits, running tests, and anything needing deep conversation continuity.
- ALWAYS inspect Codex output before applying. NEVER send secrets/.env/keys/tokens/credentials. NEVER ask Codex to scan large dataset folders — scope it to the code directory with `-C`.
For the full workflow invoke the `codex-subagent` skill. Quick one-shot delegation: /codex <task>.
EOF

# Gentle warning if the codex CLI is not installed (plugin can't work without it).
if ! command -v codex >/dev/null 2>&1; then
  POLICY="${POLICY}"$'\n'"NOTE: the codex CLI was not found on PATH — install it (https://chatgpt.com/codex) and run 'codex login' for this plugin to function."
fi

# Minimal JSON string escaping (single-pass parameter substitutions).
escape_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/\\n}"
  s="${s//$'\r'/\\r}"
  s="${s//$'\t'/\\t}"
  printf '%s' "$s"
}

ESC="$(escape_json "$POLICY")"

# Claude Code expects hookSpecificOutput.additionalContext; other harnesses
# (Copilot CLI, SDK) accept top-level additionalContext.
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
  printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$ESC"
else
  printf '{\n  "additionalContext": "%s"\n}\n' "$ESC"
fi

exit 0
