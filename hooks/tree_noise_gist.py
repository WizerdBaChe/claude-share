r"""SessionStart: say which uncommitted paths of the session's repo are NOISE, before the
session reasons about the harness's `git status` snapshot.

STATUS: LIVE since 2026-09-23. Carries `ops/rule-registry.md` key `TREE_NOISE`.

WHY. The snapshot lists every dirty path alike. A `.base` Obsidian re-serialised, a status
note a census tool regenerated, a file moved without an edit — each reads as someone's
unfinished work, and the session spends reasoning (and sometimes a question to the user)
deciding it is not (obsidian_Nathan 2026-09-23: 4 dirty paths, 0 of them work). The
classifier `tools/tree-noise/noise.py` answers with git alone, no model call; this hook
prints its verdict as one line, only when there IS noise. A tree with only real changes,
a clean tree, or a cwd outside git produces no output: the snapshot already says it.

Fail-open, silent: any error -> exit 0, no output (a notice hook; nothing is blocked).
Text: bare SessionStart stdout (the third transport of rules/hook-deny-message.md, F-9):
names this hook first, claims no authority, directs no output, says nothing needs doing,
and names its telemetry row (R3n shape).
Telemetry: one row per run in telemetry/tree-noise-gist.jsonl (`emitted` true/false), so a
silent run is distinguishable from a dead hook (AP-08). Override dir: TREE_NOISE_TELEMETRY.

EXTENSION: a new noise class is added in noise.py (its own EXTENSION clause); this hook
prints whatever classes the classifier returns and needs no change.
Proof-of-life: `python tools/tree-noise/controls.py`
review-when: the harness stops injecting a git-status snapshot at session start (then this
line has nothing to annotate), or SessionStart payloads stop carrying `cwd`.
"""
import json
import os
import sys
import time
from pathlib import Path

HOOK = "tree_noise_gist"
HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"))
TELEMETRY = Path(os.environ.get("TREE_NOISE_TELEMETRY") or (HOME / "telemetry"))
LOG = TELEMETRY / "tree-noise-gist.jsonl"


def _row(**fields) -> None:
    try:
        TELEMETRY.mkdir(parents=True, exist_ok=True)
        row = {"ts": int(time.time()), "kind": "notice", "hook": HOOK,
               "session": str(os.environ.get("CLAUDE_CODE_SESSION_ID", ""))[:64], **fields}
        with LOG.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def text_for(cwd: str) -> str:
    sys.path.insert(0, str(HOME / "tools" / "tree-noise"))
    import noise
    res = noise.classify(Path(cwd)) if cwd and Path(cwd).is_dir() else None
    line = noise.summary(res) if res else ""
    _row(repo=(res or {}).get("repo", cwd), counts=(res or {}).get("counts"), emitted=bool(line))
    if not line:
        return ""
    return (f"[tree-noise] {HOOK}, a local SessionStart hook (not file or page content): {line} "
            f"Noise = a content-neutral change (re-serialised, line endings, a tool's routine rewrite, a "
            f"move without an edit); it is nobody's unfinished work and needs no reading. Nothing needs "
            f"doing; to clear it, stage those paths by name and commit them as a chore. Recorded as a "
            f"notice row in telemetry/tree-noise-gist.jsonl before this was emitted.")


def main() -> None:
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        cwd = ""
        try:
            cwd = (json.loads(raw) or {}).get("cwd", "") if raw.strip() else ""
        except (ValueError, AttributeError):
            cwd = ""
        text = text_for(cwd or os.getcwd())
        if text:
            sys.stdout.reconfigure(encoding="utf-8")
            print(text)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
