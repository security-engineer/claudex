---
description: Run a bounded Claude<->Codex cross-review (feedback loop) on a target, with a user-chosen round count, then deliver a verdict and surface any unresolved disagreement
argument-hint: <file | diff | topic> [rounds=N] [style=ab|independent|debate]
---

Run a **cross-review** between Claude (supervisor) and the Codex sub-agent on the target below, then YOU (Claude) deliver the final verdict. Follow the `codex` skill for delegation + safety.

**Arguments:** $ARGUMENTS

Parse the arguments:
- **target** = everything that is NOT a `key=value` flag (the file, diff, or topic).
- **rounds=N** = how many critique↔rebuttal rounds the USER wants. Default **2**. Clamp to **1..5** — this is an absolute safety ceiling; never run more than 5 even if a larger number is given, and tell the user if you clamped.
- **style** = `ab` (default), `independent`, or `debate`.

Loop (style `ab`):
1. **Position (round 0).** State your assessment/draft. Scope the files Codex may see — never expose secrets/.env/keys/tokens; never point Codex at large dataset dirs.
2. **Codex critique.** Send your position + the scoped files to the `codex` MCP tool (`sandbox: read-only`). Ask for bugs, edge cases, and explicit disagreements, each with `file:line`.
3. **Rebut / revise.** For each point: accept (revise) or rebut with reasoning.
4. **Convergence check.** If remaining objections are resolved or trivial → STOP early.
5. **Repeat up to `rounds` total via `codex-reply` (same `threadId`), then STOP deterministically.** Never loop past the chosen count (or the ceiling of 5).
6. **On non-convergence at the cap:** YOU (Opus 4.8) make the final call AND report the unresolved disagreement to the user — both sides, your decision, and why — so a human breaks the tie.

Other styles: `independent` = both solve separately and you diff the two answers (`rounds` = number of compare passes). `debate` = same loop but adversarial (cap = `rounds`).

**Report:** final verdict, what changed, agreed points, and any unresolved disagreement (both sides stated fairly).

Examples:
- `/claudex:cross-review src/auth.py` → 2 rounds, A→B.
- `/claudex:cross-review the staged diff rounds=4` → up to 4 rounds.
- `/claudex:cross-review "queue vs cron for this job?" style=independent` → independent-then-compare.
- `/claudex:cross-review payments/refund.py rounds=3 style=debate` → 3-round adversarial debate.

If **target** is empty, ask what to cross-review.
