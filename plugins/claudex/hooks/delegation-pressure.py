#!/usr/bin/env python3
"""UserPromptSubmit hook for the claudex plugin: inject the chosen work-split mode each turn.

The mode lives in ~/.claude/claudex-mode (solo | balanced | codex | max; default balanced),
set via /claudex-mode. 'balanced' injects nothing (the SessionStart policy + skill govern).
Re-read every turn, so a mode change takes effect on the next turn without a restart.

Never fails the turn: any error → no injection, exit 0.
"""
import json
import os
import sys

MODE_FILE = os.path.expanduser("~/.claude/claudex-mode")

MODE_MSG = {
    "solo":  "mode SOLO — handle this yourself; do NOT delegate to Codex unless the user explicitly asks.",
    "codex": "mode CODEX-FIRST — delegate drafting, multi-file reading, and most generation to Codex; you orchestrate and render final judgment.",
    "max":   "mode MAX — delegate almost everything to Codex; you only orchestrate and judge.",
}


def read_mode():
    try:
        with open(MODE_FILE, encoding="utf-8") as f:
            m = f.read().strip().lower()
        return m if m in ("solo", "balanced", "codex", "max") else "balanced"
    except Exception:
        return "balanced"


def main():
    msg = MODE_MSG.get(read_mode())
    if msg:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "[claudex] " + msg,
        }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
