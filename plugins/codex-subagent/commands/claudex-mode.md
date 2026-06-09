---
description: Choose how work is split between Claude and the Codex sub-agent (solo | balanced | codex | max)
argument-hint: "[solo|balanced|codex|max]  (no arg = show current)"
---

Set or show the **work-split mode** between Claude and Codex. The mode is stored in `~/.claude/claudex-mode` and read by the delegation hook each turn, so it takes effect from the next turn.

**Arguments:** $ARGUMENTS

- **No arg** → read the current mode and show the table below:
  `cat ~/.claude/claudex-mode 2>/dev/null || echo balanced`
- **`solo` | `balanced` | `codex` | `max`** → save it, then confirm:
  `printf '%s' "<mode>" > ~/.claude/claudex-mode`
- Anything else → reject and show the valid options.

| Mode | Work split |
|---|---|
| `solo` | Claude does everything; Codex only if the user explicitly asks. |
| `balanced` (default) | Exploration, first drafts, and second-opinion reviews → Codex; Claude scopes, reviews, applies, tests, and judges. |
| `codex` | Drafting, multi-file reading, and most generation → Codex; Claude orchestrates and renders final judgment. |
| `max` | Almost everything → Codex; Claude only orchestrates and judges. |

After setting, confirm the new mode back to the user and note it applies from the next turn.
