#!/usr/bin/env python3
"""UserPromptSubmit hook for codex-subagent: adaptive delegation under context pressure.

Each turn, estimates how full Claude's context is and — past configurable thresholds —
injects an `[adaptive-delegation]` directive telling Claude to WIDEN delegation to the
Codex sub-agent, so the session stretches further on Anthropic tokens.

The estimate is APPROXIMATE by design: it derives tokens from the transcript file size
(~4 bytes/token) and cannot see harness compaction. Tune via env vars:

  CODEX_CONTEXT_BUDGET      total context tokens to measure against   (default 200000)
  CODEX_DELEGATE_THRESHOLD  fraction that triggers AGGRESSIVE tier    (default 0.80)
  CODEX_DELEGATE_FORCE      off|elevated|aggressive|max  — force a tier (manual override)

Never fails the turn: any error → no injection, exit 0.
"""
import sys, json, os

TIERS = {
    "elevated":   ("elevated",   "prefer the codex sub-agent for ALL exploration and first drafts; review summaries, not full re-reads."),
    "aggressive": ("AGGRESSIVE", "hand first-draft generation and multi-file reading to the codex sub-agent; Claude reviews diffs/summaries only, not full re-reads."),
    "max":        ("MAX",        "delegate almost everything to the codex sub-agent — Codex does drafting, multi-file reading, and generation; Claude only orchestrates and renders final judgment. Suggest /compact or a fresh session."),
}


def emit(text):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "[adaptive-delegation] " + text,
        }
    }))


def main():
    force = os.environ.get("CODEX_DELEGATE_FORCE", "").strip().lower()
    if force == "off":
        return
    if force in TIERS:
        label, body = TIERS[force]
        emit("forced %s mode: %s" % (label, body))
        return

    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except Exception:
        return
    tp = data.get("transcript_path")
    if not tp or not os.path.exists(tp):
        return

    try:
        nbytes = os.path.getsize(tp)
    except Exception:
        return

    try:
        budget = int(os.environ.get("CODEX_CONTEXT_BUDGET", "200000"))
        thr = float(os.environ.get("CODEX_DELEGATE_THRESHOLD", "0.80"))
    except Exception:
        budget, thr = 200000, 0.80
    if budget <= 0:
        return

    pct = (nbytes / 4.0) / budget
    p = int(pct * 100)
    if pct >= 0.90:
        label, body = TIERS["max"]
    elif pct >= thr:
        label, body = TIERS["aggressive"]
    elif pct >= 0.60:
        label, body = TIERS["elevated"]
    else:
        return
    emit("context pressure ~%d%% (%s): %s" % (p, label, body))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
