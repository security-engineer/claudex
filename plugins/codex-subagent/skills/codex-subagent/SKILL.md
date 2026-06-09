---
name: codex-subagent
description: Use when a task involves heavy codebase exploration, drafting code or refactors, hunting edge cases, or getting an independent second-opinion review — and you want to conserve Claude/Anthropic tokens by delegating to the OpenAI Codex sub-agent. Also use when the user mentions Codex, delegating to save tokens, or cross-checking work with a second model.
---

# Codex Sub-Agent (balanced delegation)

## Overview

The `codex` MCP server runs **OpenAI Codex (GPT-5.x at xhigh reasoning)** as a sub-agent. Codex reads files and reasons inside **its own** context and returns only the result, so the heavy reading/drafting runs on OpenAI's quota instead of Anthropic tokens. **Claude stays the supervisor and makes the final call.**

**Core principle:** delegate the token-heavy work, keep the judgment. Quality is protected by review, not by doing everything yourself.

## When to delegate to Codex

- Exploring an unfamiliar codebase / reading large files to answer a question
- Producing a first-draft implementation, refactor, or patch
- An **independent** second-opinion review of a diff or design (ensemble — two frontier models catch more)
- Hunting edge cases / failure modes in a function or change

## When to keep it on Claude

- Final judgment, applying edits, running tests
- Tasks needing deep continuity with this conversation's context
- Anything where re-reading everything to trust Codex would cost more than just doing it

## Quick reference

| Need | Action |
|------|--------|
| In-session delegation | Call the `codex` MCP tool (`mcp__plugin_codex-subagent_codex__codex`) with a focused prompt |
| Deterministic CLI fallback | `codex exec -C <code-dir> -s read-only --skip-git-repo-check "<task>"` |
| Codex must write a patch | Use a writable sandbox, scoped to the code dir, **no secrets in scope** |
| Discover the exact MCP tool | `/mcp`, or ToolSearch for "codex" |

## Delegation prompt template

Scope first, then phrase a focused request — vague tasks make Codex guess:

```
Task: <one concrete goal>
Files in scope: <explicit paths or the diff>   # never secrets/.env/keys; never a whole dataset dir
Constraints: read-only unless a patch is required; do not read beyond the listed paths
Deliver: <review findings | a patch | edge cases>, concise, with file:line references
```

Map it to a call:
- **MCP:** the `codex` tool with `cwd=<code-dir>`, `sandbox=read-only` (use `workspace-write` only for patches), and the prompt above.
- **CLI:** `codex exec -C <code-dir> -s read-only --skip-git-repo-check "<prompt>"`

## Safety rules (hard requirements)

- **Never** send secrets, `.env`, private keys, credentials, tokens, SSH/cloud auth to Codex.
- **Never** ask Codex to scan large dataset folders — scope it to the actual code directory with `-C`.
- Default Codex to a **read-only** sandbox; grant write access only when it must produce a patch.
- Give Codex **focused** tasks with the specific files/diff. Vague tasks → it guesses → worse output.

## Review discipline

1. **Scope** the task and the files Codex may see.
2. **Delegate** to Codex (MCP tool or `codex exec`).
3. **Inspect** the output critically — verify claims, check edge cases. Do **not** apply blindly.
4. **Decide & apply.** Claude owns the final edit, tests, and explanation.

## Work-split mode

The user picks the Claude↔Codex split with `/claudex-mode` (`solo | balanced | codex | max`, default balanced). A `UserPromptSubmit` hook injects the active mode each turn — honor it: `solo` = do it yourself; `codex`/`max` = delegate drafting/reading/generation to Codex, you orchestrate and judge.

## Common mistakes

- Downgrading Codex's model to save money — that, not delegation, is what actually drops quality. Keep GPT-5.x at high/xhigh (`~/.codex/config.toml`).
- Applying Codex output without review (defeats the supervisor role).
- Letting Codex loose on a huge repo root instead of `-C <code-dir>` (slow, leaks context, may touch secrets).
- Delegating a task whose output you must fully re-derive to trust — no token savings, double cost.
