---
description: Delegate a focused task to the Codex (GPT-5.x) sub-agent, then review its output before applying
argument-hint: <task to delegate to Codex>
---

Delegate the task below to the **Codex** sub-agent, then supervise the result. Follow the `codex` skill.

**Task:** $ARGUMENTS

1. **Scope it.** Identify the specific files/diff Codex needs. Never include secrets, `.env`, keys, or tokens. Never point Codex at large dataset folders.
2. **Delegate.** Prefer the `codex` MCP tool. Deterministic CLI fallback (read-only, scoped):
   `codex exec -C <code-dir> -s read-only --skip-git-repo-check "<focused task>"`
   Use a writable sandbox only when Codex must produce a patch, with no secrets in scope.
3. **Review.** Inspect Codex's output critically — verify claims and edge cases. Do not apply blindly.
4. **Decide & apply.** You (Claude) make the final call, apply edits, and run the tests.

If **Task** is empty, ask the user what to delegate.
