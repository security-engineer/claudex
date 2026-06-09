# claudex

*🌐 **English** · [한국어](README.ko.md)*

Use **OpenAI Codex (GPT-5.x)** as a *balanced sub-agent* under **Claude Code**.

Claude is the supervisor and final decision-maker; Codex does the token-heavy grunt work
(exploration, first drafts, second-opinion reviews) inside **its own** context, so that work
runs on your OpenAI/ChatGPT quota instead of Anthropic tokens. Claude reviews Codex's output
before anything is applied — quality is protected by review, and with two independent frontier
models cross-checking, it often *improves*.

This repo is a **Claude Code plugin marketplace** with one plugin: **`codex-subagent`**.

## What the plugin sets up

- **`codex` MCP server** — auto-registered via the bundled `.mcp.json` (runs `codex mcp-server`).
- **`codex-subagent` skill** — the balanced-delegation workflow + safety rules (loaded on demand, costs no context until used).
- **`/codex <task>`** — delegate one focused task to Codex, then review.
- **`/cross-review <target>`** — bounded Claude↔Codex feedback loop with a user-chosen round count.
- **SessionStart hook** — injects a short standing policy each session so Claude defaults to the balanced posture (always-on).

## Prerequisites

1. **Claude Code** installed.
2. **Codex CLI** installed and logged in, in the **same environment** as Claude Code
   (if Claude runs in a container, Codex must be installed and logged in inside that container):
   ```bash
   curl -fsSL https://chatgpt.com/codex/install.sh | sh   # install
   codex login                                            # or: codex login --device-auth
   codex login status                                     # verify
   ```
3. Pick Codex's model/effort in `~/.codex/config.toml` (the MCP server inherits these):
   ```toml
   model = "gpt-5.5"
   model_reasoning_effort = "xhigh"
   ```

## Install

```bash
# 1) Add this repo as a marketplace (GitHub repo, URL, or local path all work)
claude plugin marketplace add security-engineer/claudex

# 2) Install the plugin
claude plugin install codex-subagent@claudex

# 3) Restart Claude Code so the MCP server, hook, skill, and commands load
```

Local development install (no GitHub needed):

```bash
claude plugin marketplace add /absolute/path/to/claudex
claude plugin install codex-subagent@claudex
```

Verify:

```bash
claude plugin list
claude mcp list          # codex should be ✔ Connected
# in a session:  /mcp   then   /codex hello   then   /cross-review <target>
```

---

## Usage

**Division of labor**

- **Claude (Opus 4.8)** = supervisor — final judgment, applying edits, running tests, reconciling.
- **Codex (GPT-5.x, xhigh)** = sub-agent — token-heavy exploration, first drafts, independent review, edge-case hunting. Runs on your OpenAI/ChatGPT quota, **not** Anthropic tokens.

Just work normally — the SessionStart policy nudges Claude to delegate appropriately. Or drive it directly with the commands below.

### `/codex <task>`

Delegate a single focused task to Codex, then review the result before applying.

**Flow:** scope files → delegate (MCP or `codex exec`) → review critically → you (Claude) apply + test.

**Examples**
- `/codex review the diff in src/auth/ and list edge cases`
- `/codex draft a refactor of utils/date.py to remove duplication`
- `/codex find the root cause of the failing test in tests/test_api.py`

Codex runs **read-only** by default; it writes only when a patch is explicitly required. Never include secrets or huge dataset dirs in scope.

### `/cross-review <target> [rounds=N] [style=ab|independent|debate]`

Run a **bounded** Claude↔Codex feedback loop, then Claude delivers a verdict.

**Arguments**
- `target` — a file, a diff (e.g. “the staged diff”), or a question/topic. Everything that isn't a `key=value` flag.
- `rounds=N` — **you choose** how many critique↔rebuttal rounds. Default **2**. Hard ceiling **5** (clamped — it never loops past 5, even if you ask for more).
- `style` — `ab` (default: one drafts, the other critiques), `independent` (both solve separately, Claude diffs them), or `debate` (adversarial back-and-forth).

**The loop (style `ab`)**
1. Claude states its position/draft.
2. Codex critiques — bugs, edge cases, disagreements, each with `file:line`.
3. Claude rebuts or revises each point.
4. Convergence check — resolved/trivial → stop early.
5. Repeat up to `rounds`, then stop **deterministically**.
6. If still not converged at the cap → Claude (the supervisor) decides **and reports the unresolved disagreement to you**, so a human breaks the tie. **No infinite loops.**

**Examples**
- `/cross-review src/auth.py` — 2 rounds, A→B.
- `/cross-review the staged diff rounds=4` — up to 4 rounds.
- `/cross-review "queue vs cron for this job?" style=independent` — independent-then-compare.
- `/cross-review payments/refund.py rounds=3 style=debate` — 3-round adversarial debate.

**Cost note:** cross-review trades extra tokens/latency for quality — use it on important or contentious code, not everything. Codex side = OpenAI tokens; Claude's orchestration/judging = Anthropic tokens.

### The `codex-subagent` skill

Loaded **on demand** (no context cost until used). Claude invokes it automatically when a task is heavy on exploration, drafting, or edge-case hunting, or wants an independent second opinion — or when you mention Codex / delegating to save tokens. It encodes the balanced posture, a delegation prompt template, and the safety rules. Trigger it explicitly with: “use the codex-subagent workflow.”

### MCP tools (advanced / direct control)

The plugin auto-registers the **`codex`** MCP server. After installing, **restart Claude Code** so the tools load in-session.

- **`codex`** — start a Codex session. Key params: `prompt` (required), `cwd` (scope to the code folder), `sandbox` (`read-only` default · `workspace-write` for patches · `danger-full-access`), `model` (default from `~/.codex/config.toml`), `approval-policy` (`never` for non-interactive). Returns a `threadId`.
- **`codex-reply`** — continue a thread: `threadId` + `prompt`. Powers multi-round `/cross-review`.

**CLI fallback (deterministic, works even before a restart):**
```bash
codex exec -C <code-dir> -s read-only --skip-git-repo-check "<focused task>"
```

---

## Configuration

- **Codex model / reasoning effort** — `~/.codex/config.toml` (`model`, `model_reasoning_effort`). The MCP server and `codex exec` both inherit these. Don't downgrade the model to save money — that's the one change that actually lowers quality.
- **Cross-review rounds** — per call via `rounds=N` (default 2, ceiling 5).
- **Sandbox** — read-only by default; `workspace-write` only when Codex must produce a patch.

## Adaptive delegation (token pressure)

As Claude's context fills, a `UserPromptSubmit` hook estimates usage and injects an `[adaptive-delegation]` directive that **widens delegation to Codex**, so the session stretches further on Anthropic tokens.

| Context pressure | Behavior |
|---|---|
| < 60% | Normal balanced posture |
| 60–80% (elevated) | Prefer Codex for all exploration + first drafts; review summaries, not full re-reads |
| ≥ 80% (aggressive) | Hand drafting + multi-file reading to Codex; Claude reviews diffs/summaries only |
| ≥ 90% (max) | Codex does nearly everything; Claude only orchestrates + judges; suggests `/compact` |

The estimate is **approximate** (derived from transcript size; harness compaction makes it imperfect). Tune it:

| Env var | Default | Meaning |
|---|---|---|
| `CODEX_CONTEXT_BUDGET` | `200000` | total context tokens to measure against |
| `CODEX_DELEGATE_THRESHOLD` | `0.80` | fraction that triggers the *aggressive* tier |
| `CODEX_DELEGATE_FORCE` | _(unset)_ | `off` · `elevated` · `aggressive` · `max` — force a tier (manual override) |

## Safety

- Never send secrets, `.env`, private keys, credentials, tokens, SSH/cloud auth to Codex.
- Never ask Codex to scan large dataset folders — scope with `-C <code-dir>` / `cwd`.
- Keep Codex read-only unless a patch is required.
- Claude reviews Codex output before applying — always.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `/codex`, `/cross-review`, or codex MCP tools missing | Restart Claude Code — MCP + commands load at session start |
| codex MCP not connected | `codex login status`; install + log in to codex in the **same** environment as Claude Code |
| Codex returns an auth error | `codex login` (or `codex login --device-auth`) |
| `codex exec` errors “Not inside a trusted directory” | add `--skip-git-repo-check` and `-C <code-dir>` |
| Codex slow / scanning too much | always pass `-C <code-dir>` / `cwd`; never point at a huge repo root |

## Publish updates

This plugin lives at **github.com/security-engineer/claudex**. To ship a change:

```bash
# bump "version" in plugins/codex-subagent/.claude-plugin/plugin.json, then:
git add -A && git commit -m "describe the change" && git push
```

Users pick it up with `claude plugin update codex-subagent@claudex` (restart to apply).

## License

MIT — see [LICENSE](LICENSE).
