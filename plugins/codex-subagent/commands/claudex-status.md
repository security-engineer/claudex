---
description: Show actual Claude context usage / remaining tokens and Codex sub-agent status
---

Report **claudex status** as one compact block. Run the two checks below, then present the results. Never print secrets or tokens.

### A) Claude context — actual usage & remaining

Run this (it finds the current session transcript, reads the real API `usage`, and auto-detects the context window):

```bash
python3 - <<'PY'
import json, os, glob
proj = "/root/.claude/projects/" + os.getcwd().replace("/", "-")
files = sorted(glob.glob(proj + "/*.jsonl"), key=os.path.getmtime)
if not files:
    print("transcript not found — use /cost and the UI context meter"); raise SystemExit
tp = files[-1]
size = os.path.getsize(tp)
with open(tp, "rb") as f:
    if size > 262144: f.seek(size - 262144); f.readline()
    tail = f.read().decode("utf-8", "ignore")
used = out = 0
for line in tail.splitlines():
    try: o = json.loads(line)
    except: continue
    m = o.get("message") if isinstance(o.get("message"), dict) else o
    u = m.get("usage") if isinstance(m.get("usage"), dict) else None
    if u:
        used = (u.get("input_tokens",0) or 0)+(u.get("cache_read_input_tokens",0) or 0)+(u.get("cache_creation_input_tokens",0) or 0)
        out = u.get("output_tokens",0) or 0
env = os.environ.get("CODEX_CONTEXT_BUDGET")
window = int(env) if env else (1000000 if used > 200000 else 200000)
remaining = max(0, window - used); pct = (used/window*100) if window else 0
tier = "normal" if pct < 60 else "elevated" if pct < 80 else "aggressive" if pct < 90 else "MAX"
print(f"used (live context): {used:,} tok")
print(f"window:              {window:,} tok  ({'env' if env else 'auto-detected'})")
print(f"remaining:           {remaining:,} tok")
print(f"usage:               {pct:.0f}%   adaptive tier: {tier}")
print(f"last output:         {out:,} tok")
PY
```

### B) Codex sub-agent

- `codex login status` · `codex --version` · `model`/`model_reasoning_effort` from `~/.codex/config.toml` · `claude mcp list` (is `codex` `✔ Connected`?)

### Present

A tidy two-part block — **Claude**: used / window / **remaining** / % / tier; **Codex**: logged in?, version, model, MCP connected?. Notes: this is the **context window** (not plan/billing — for that use `/cost` and the Anthropic console); window is auto-detected (set `CODEX_CONTEXT_BUDGET` to override). If Codex is logged out or MCP disconnected, give the fix (`codex login`, restart).
