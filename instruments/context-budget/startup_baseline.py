#!/usr/bin/env python3
r"""Startup-context baseline -- measure what every session pays before it works.

WHY
---
The E1 (context-budget) change is only worth applying if the saving is real
and only safe if the loss of adherence is visible. Both need MEASUREMENTS,
not the "16 KB is about 4-5k tokens" estimate the plan started from.

WHAT IT MEASURES
----------------
Per session transcript, at the FIRST assistant message:

    startup_tokens = input_tokens
                   + cache_creation_input_tokens
                   + cache_read_input_tokens

That sum is the whole prompt the model was handed before it did anything:
system prompt + tool schemas + CLAUDE.md + MEMORY.md + first user turn.
It is the only number that moves when CLAUDE.md is trimmed, and it is
recorded by the platform, not estimated here.

MEASURED, NOT ASSUMED: the `# claudeMd` / auto-memory blocks are injected at
request time and are NOT persisted in the transcript (verified 2026-08-11 --
the first user record holds only the typed prompt). So the per-file cost
cannot be read back from history; the script instead reports the on-disk size
of every always-loaded instruction file, and the trim is judged by the DELTA
in startup_tokens before vs after. Chars are reported as chars -- deliberately
never converted to tokens, because a made-up ratio is how the original
estimate went wrong.

`startup_tokens` is noisy across sessions (the MCP/tool roster differs), so
the floor matters more than the mean: MIN over a window is the cleanest
estimator of the fixed cost, and MEDIAN is reported beside it.

HOW TO USE IT
-------------
    python startup_baseline.py                        # every project
    python startup_baseline.py --project <project-dir-name>
    python startup_baseline.py --since 2026-08-01 --json

Compare like with like: startup_tokens also moves when the MCP tool set or
skill roster changes, so a before/after judgement is only valid WITHIN one
project over a short window. The script groups by project for that reason and
refuses to print a single global "the number".

Read-only. Touches nothing but stdout.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from statistics import median

PROJECTS_DIR = Path.home() / ".claude" / "projects"
MAX_LINES_SCANNED = 400  # the first assistant turn is always near the top

# Files the platform loads in full at every session start. `~/.claude/rules/`
# entries count ONLY when they carry no `paths:` frontmatter -- a path-scoped
# rule is loaded on demand and costs nothing until a matching file is read.
PATHS_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def always_loaded_inventory():
    """On-disk size of everything paid for before the first token of work."""
    home = Path.home() / ".claude"
    rows = []
    for label, path in (
        ("CLAUDE.md", home / "CLAUDE.md"),
        # SHARE EDITION: the project-dir slug of the config home, computed rather
        # than spelled out (every non-alphanumeric character becomes "-").
        ("MEMORY.md", home / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(home))
         / "memory" / "MEMORY.md"),
    ):
        if path.exists():
            rows.append((label, path.stat().st_size, "always"))

    rules_dir = home / "rules"
    if rules_dir.exists():
        for rule in sorted(rules_dir.rglob("*.md")):
            try:
                head = rule.read_text(encoding="utf-8", errors="replace")[:2000]
            except OSError:
                continue
            fm = PATHS_FRONTMATTER.search(head)
            scoped = bool(fm and "paths:" in fm.group(1))
            rows.append(
                (f"rules/{rule.relative_to(rules_dir)}", rule.stat().st_size,
                 "on-demand" if scoped else "always")
            )
    return rows


def local_date(raw):
    """Transcript timestamps are UTC ('...Z'); bucket them by LOCAL date.

    MEASURED 2026-08-11: a session started 05:07 local (UTC+08) is stamped
    2026-08-10T21:07:43.491Z. Slicing [:10] off the raw string therefore filed
    every session run before 08:00 local under the previous day, and
    `--since <today>` silently returned "no sessions matched" while today's
    transcripts sat on disk. The window this feeds is a before/after
    comparison, so an off-by-one day is not cosmetic.
    """
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return str(raw)[:10]
    if dt.tzinfo is None:
        return dt.date().isoformat()
    return dt.astimezone().date().isoformat()


def scan_session(path):
    """Return one row per transcript, or None when the file has no usable turn."""
    row = {
        "session": path.stem,
        "date": None,
        "startup_tokens": None,
    }
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return None

    with fh:
        for lineno, line in enumerate(fh):
            if lineno > MAX_LINES_SCANNED:
                break
            try:
                rec = json.loads(line)
            except Exception:
                continue

            if row["date"] is None and rec.get("timestamp"):
                row["date"] = local_date(rec["timestamp"])

            msg = rec.get("message") or {}

            if row["startup_tokens"] is None and rec.get("type") == "assistant":
                usage = msg.get("usage") or {}
                if usage:
                    row["startup_tokens"] = (
                        int(usage.get("input_tokens") or 0)
                        + int(usage.get("cache_creation_input_tokens") or 0)
                        + int(usage.get("cache_read_input_tokens") or 0)
                    )

            if row["startup_tokens"] is not None:
                break

    return row if row["startup_tokens"] else None


def collect(project_filter, since):
    projects = {}
    if not PROJECTS_DIR.exists():
        sys.stderr.write(f"no transcript dir: {PROJECTS_DIR}\n")
        return projects

    for proj_dir in sorted(PROJECTS_DIR.iterdir()):
        if not proj_dir.is_dir():
            continue
        if project_filter and project_filter not in proj_dir.name:
            continue
        rows = []
        for transcript in sorted(proj_dir.glob("*.jsonl")):
            row = scan_session(transcript)
            if not row:
                continue
            if since and (row["date"] or "") < since:
                continue
            rows.append(row)
        if rows:
            projects[proj_dir.name] = rows
    return projects


def report(projects):
    if not projects:
        print("no sessions matched -- reporting the on-disk inventory only")
    for name, rows in projects.items():
        rows.sort(key=lambda r: r["date"] or "")
        tokens = [r["startup_tokens"] for r in rows]
        print(f"\n## {name}   ({len(rows)} sessions)")
        print(f"{'date':<12}{'startup_tokens':>16}")
        for r in rows[-12:]:
            print(f"{(r['date'] or '?'):<12}{r['startup_tokens']:>16,}")
        print(f"{'MIN (floor)':<12}{min(tokens):>16,}")
        print(f"{'MEDIAN':<12}{int(median(tokens)):>16,}")

    print("\n## always-loaded instruction files (on disk, now)")
    inventory = always_loaded_inventory()
    total = 0
    for label, size, mode in inventory:
        flag = "" if mode == "always" else "   (on-demand, free at startup)"
        if mode == "always":
            total += size
        print(f"{label:<44}{size:>9,} B{flag}")
    print(f"{'TOTAL charged every session':<44}{total:>9,} B")

    print(
        "\nnote: startup_tokens also moves with the MCP tool set and skill roster."
        "\n      Compare only within one project, and prefer the MIN floor:"
        "\n      a trim shows up as the floor dropping, not the mean."
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", help="substring of the project dir name")
    ap.add_argument("--since", help="ISO date lower bound, e.g. 2026-08-01")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    projects = collect(args.project, args.since)
    if args.json:
        json.dump(projects, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        report(projects)
    return 0


if __name__ == "__main__":
    sys.exit(main())
