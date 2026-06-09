#!/usr/bin/env python3
"""UserPromptSubmit hook for codex-subagent: adaptive delegation under context pressure.

Each turn, reads the ACTUAL token usage recorded in the transcript (the last API
`usage` entry: input + cache_read + cache_creation = live prompt/context size) and,
past configurable thresholds, injects an `[adaptive-delegation]` directive telling
Claude to WIDEN delegation to the Codex sub-agent — stretching the session further on
Anthropic tokens.

Tune via env vars:
  CODEX_CONTEXT_BUDGET      your model's context window in tokens (default 200000;
                            set to 1000000 if on the 1M-context beta)
  CODEX_DELEGATE_THRESHOLD  fraction that triggers the AGGRESSIVE tier (default 0.80)
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


def live_context_tokens(transcript_path):
    """Return the most recent live context size from the transcript's usage records,
    or None. Reads only the tail of the file for speed."""
    try:
        size = os.path.getsize(transcript_path)
        with open(transcript_path, "rb") as f:
            if size > 262144:
                f.seek(size - 262144)
                f.readline()  # drop a possibly-partial line
            tail = f.read().decode("utf-8", errors="ignore")
    except Exception:
        return None
    found = None
    for line in tail.splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        u = None
        m = o.get("message")
        if isinstance(m, dict) and isinstance(m.get("usage"), dict):
            u = m["usage"]
        elif isinstance(o.get("usage"), dict):
            u = o["usage"]
        if u:
            total = (u.get("input_tokens", 0) or 0) \
                + (u.get("cache_read_input_tokens", 0) or 0) \
                + (u.get("cache_creation_input_tokens", 0) or 0)
            if total > 0:
                found = total
    return found


def main():
    force = os.environ.get("CODEX_DELEGATE_FORCE", "").strip().lower()
    if force == "off":
        return
    if force in TIERS:
        label, body = TIERS[force]
        emit("forced %s mode: %s" % (label, body))
        return

    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        return
    tp = data.get("transcript_path")
    if not tp or not os.path.exists(tp):
        return

    tokens = live_context_tokens(tp)
    if not tokens:
        return  # no accurate signal → stay silent (don't guess from bytes)

    try:
        env_b = os.environ.get("CODEX_CONTEXT_BUDGET")
        # Auto-detect the window when unset: >200k used implies the 1M-context tier.
        budget = int(env_b) if env_b else (1000000 if tokens > 200000 else 200000)
        thr = float(os.environ.get("CODEX_DELEGATE_THRESHOLD", "0.80"))
    except Exception:
        budget, thr = 200000, 0.80
    if budget <= 0:
        return

    pct = tokens / budget
    p = int(pct * 100)
    if pct >= 0.90:
        label, body = TIERS["max"]
    elif pct >= thr:
        label, body = TIERS["aggressive"]
    elif pct >= 0.60:
        label, body = TIERS["elevated"]
    else:
        return
    emit("context ~%d%% (%d tok / %d) (%s): %s" % (p, tokens, budget, label, body))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
