#!/usr/bin/env python3
"""Awareness emitter: is the auto-memory index closed over its own files? (hmi-report/1, class=reconcile)

STATUS: LIVE since 2026-09-19. NARROWED 2026-09-19: the work-folder census that was born here
(declared roots + an ignore list) moved to tools/place-ledger, which is footprint-driven and has no
ignore list (user ruling: anything an agent touched must be recorded; "ignored" became a kind).
The HMI reads that tool through its own native source `place-ledger`.

Point:
  awareness.memory-closure  MEMORY.md pointers vs memory/*.md, both directions -> fail on any gap
                            (a determinable closure is FAIL, never WARN)

Read-only. Proof-of-life: `python tools/system-hmi/controls.py`
"""
import json
import re
import sys
import time
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
HOME = TOOL_DIR.parents[1]


def memory_closure(memory_dir):
    """-> (broken_pointers, unindexed_files) or None if the index is unreadable."""
    idx = Path(memory_dir) / "MEMORY.md"
    try:
        text = idx.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    pointed = set(re.findall(r"\]\(([^)#]+\.md)\)", text))
    files = {p.name for p in Path(memory_dir).glob("*.md") if p.name != "MEMORY.md"}
    return sorted(pointed - files), sorted(files - pointed)


def _point(pid, alias, state, findings, ran=True, skip=None, remedy=None):
    return {"id": pid, "alias": alias, "class": "reconcile", "ran": ran, "skip_reason": skip,
            "state": state, "quality": "good", "findings": findings, "remedy": remedy}


def build(home, config=None):
    home = Path(home)
    points = []
    # the runtime names a project folder after the working directory: every non-alphanumeric
    # character becomes "-" (derived from `home`, so no machine's own slug is written here)
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(home))
    mc = memory_closure(home / "projects" / slug / "memory")
    if mc is None:
        points.append(_point("awareness.memory-closure", "記憶索引封閉性", None, [], ran=False,
                             skip="memory-index-unreadable"))
    else:
        broken, unindexed = mc
        f = []
        if broken:
            f.append({"severity": "fail", "label": "MEMORY.md points at a missing file", "text": ", ".join(broken[:8])})
        if unindexed:
            f.append({"severity": "fail", "label": "memory file not in MEMORY.md", "text": ", ".join(unindexed[:8])})
        points.append(_point("awareness.memory-closure", "記憶索引封閉性", "fail" if f else "pass", f,
                             remedy="add the missing pointer line to MEMORY.md, or remove the dead one"))
    return {"protocol": "hmi-report/1", "source": "awareness",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": points}


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(json.dumps(build(HOME), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
