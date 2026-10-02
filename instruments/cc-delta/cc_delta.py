#!/usr/bin/env python3
"""Claude Code version-delta reporter.

Answers one question: since the build the ops layer was last reconciled
against, what changed that could invalidate something ops/ has written down?

Why it exists: ops/rule-registry.md carries 33 `review-when` entries, 6 of them
keyed to "any Claude Code upgrade", and until 2026-08-26 nothing on this machine
ever fired them. The CLI went 2.1.200 -> 2.1.246 with 8 recorded ops facts going
stale unnoticed, including one that pointed at a tool this environment cannot
call.

Design constraints, each earned:
  * `claude --version` is the ONLY trusted version source. Measured 2026-08-26:
    `claude update` refreshes NEITHER cache/changelog.md NOR
    .last-update-result.json, so both keep serving a stale number that reads as
    live. Anything built on those two silently under-reports.
  * The changelog cache may not reach the running build. When it doesn't, this
    tool says so and reports what it CAN see. It never prints a clean bill of
    health for a range it could not read -- a gate may only rule on what it can
    determine; for the rest the output is downgrade-and-forward, never a veto
    and never a false all-clear.
  * stdlib only, so the hook can import nothing and still call it.

Usage:
  python cc_delta.py                 full delta, grouped by what it threatens
  python cc_delta.py --check         one line, for hooks (silent when in sync)
  python cc_delta.py --selectivity   calibration: how much the filter rejects
  python cc_delta.py --assume-version 2.1.200   pretend, for testing
  python cc_delta.py --features      candidate list for the feature-delta record
  python cc_delta.py --stamp --record reports/cc-upgrade-delta/<file>.md
                                     rewrite the stamp to the running build

Feature-delta record (user ruling 2026-09-27): every stamp names a record in
reports/cc-upgrade-delta/ that lists only what matters on THIS machine: new
mechanisms, new features, conflicts with local settings/rules, related items.
It is not a copy of the changelog. `--stamp` refuses without one, because a
stamp is a hard reference that other tools trust (FAIL, not WARN). The record
spec and its required headings are in reports/cc-upgrade-delta/README.md.
`--features` only prepares candidates. Classifying them is the reader's job.
"""

import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~/.claude")
STAMP = os.path.join(HOME, "ops", "cc-reconciled.json")
CACHE = os.path.join(HOME, "cache", "changelog.md")
CLI = os.path.expanduser("~/.local/bin/claude.exe")

# What ops/ has actually written down, and therefore what a changelog bullet has
# to touch before it is worth a human's attention. Deliberately NOT a catch-all:
# a filter that passes everything is the same as no filter, so --selectivity
# prints the rejection rate and the calibration lives in the docstring of
# ops/references/harness-measurements.md.
CATEGORIES = {
    "dispatch": r"subagent|agent spawn|\bfork|background session|ListAgents|"
                r"SendMessage|teammate|cross-session|Workflow|workflow|Task tool",
    "hooks": r"\bhook|SessionStart|PreToolUse|PostToolUse|Notification hook|"
             r"DirectoryAdded|SessionEnd|PreCompact",
    "permissions": r"permission|allow rule|deny rule|sandbox|auto mode|"
                   r"bypassPermissions|acceptEdits|classifier",
    "skills": r"\bskill|SKILL\.md|frontmatter|\bplugin|marketplace",
    "model": r"\bmodel\b|Opus|Sonnet|Haiku|effort|pricing|per Mtok|"
             r"context window|prompt cache|1M context",
    "tools": r"Bash tool|Write tool|Edit tool|Read tool|WebFetch|WebSearch|"
             r"Glob|NotebookEdit|tool call|tool result|MCP",
    "settings": r"settings\.json|CLAUDE_CODE_|ANTHROPIC_|env(?:ironment)? "
                r"variable|managed setting",
    "records": r"transcript|worktree|CLAUDE\.md|memory file|session file|"
               r"\.claude/sessions|claudeMdExcludes",
}
COMPILED = {k: re.compile(v) for k, v in CATEGORIES.items()}

# Surfaces this machine does not run (declared 2026-09-27: Desktop Code tab +
# CLI on Windows). --features counts their bullets and prints none of them.
# VS Code/JetBrains confirmed unused by the user 2026-09-27. review-when: an
# IDE extension, cloud session, Slack install, gateway or self-hosted runner
# comes into use on this machine.
OUT_OF_SCOPE = re.compile(
    r"^\[(VSCode|Claude Code on the web|Claude Tag|Code Review)\]|"
    r"^Self-hosted runner:|Claude apps gateway|\bgateway upstreams?\b")

RECORD_DIR = os.path.join(HOME, "reports", "cc-upgrade-delta")
# Section headings every record must carry, in any order. Consumers are the
# stamp gate (below) and human readers; see reports/cc-upgrade-delta/README.md.
RECORD_HEADINGS = ("## 新機制", "## 新功能", "## 衝突", "## 相關", "## 不適用")
# A stable prefix is all a changelog heading has, so the kinds are closed.
FEATURE_VERBS = ("Added", "Changed", "Removed", "Reverted", "Deprecated")
# Platform words that make a Fixed/Improved bullet worth a look even though
# it is not a new feature. Settings-derived terms are added at run time.
LOCAL_BASE_TERMS = ("Windows", "PowerShell", "AGENTS.md", "CLAUDE.md",
                    "subagent", "compact", "worktree", "Claude Desktop")


def local_terms(settings_path=os.path.join(HOME, "settings.json")):
    """Terms this machine's settings.json actually uses: hook events, top-level
    keys, env names. Derived, so it follows the asset instead of a hand list."""
    terms = set(LOCAL_BASE_TERMS)
    try:
        with open(settings_path, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        return sorted(terms)
    terms.update((s.get("hooks") or {}).keys())
    # Only distinctive keys: plain words like `model` or `theme` match half the
    # changelog and turn the list back into the changelog (measured 2026-09-27).
    terms.update(k for k in s.keys()
                 if k not in ("hooks", "permissions", "env") and re.search(r"[A-Z_]", k))
    terms.update((s.get("env") or {}).keys())
    return sorted(t for t in terms if len(t) >= 5)


def features(sections, lo, hi, terms):
    """-> (candidates [(vs, kind, bullet)], out_of_scope_count, fixed_skipped).
    kind is 'feature' (an Added/Changed/... verb) or 'local' (another verb,
    kept because it names a term this machine uses)."""
    rx = re.compile("|".join(re.escape(t) for t in terms)) if terms else None
    cands, oos, skipped = [], 0, 0
    for vt, vs, bullets in sections:
        if not (lo < vt <= hi):
            continue
        for b in bullets:
            if OUT_OF_SCOPE.search(b):
                oos += 1
                continue
            head = re.sub(r"^Windows:\s*", "", b)
            if head.startswith(FEATURE_VERBS):
                cands.append((vs, "feature", b))
            elif rx and rx.search(b):
                cands.append((vs, "local", b))
            else:
                skipped += 1
    return cands, oos, skipped


def check_record(path, lo, hi):
    """-> list of problems; empty means the record may back a stamp."""
    vstr = lambda t: ".".join(map(str, t))
    if not path:
        return ["no --record given"]
    full = path if os.path.isabs(path) else os.path.join(HOME, path)
    if not os.path.isfile(full):
        return ["record not found: %s" % path]
    if os.path.dirname(os.path.abspath(full)) != os.path.abspath(RECORD_DIR):
        return ["record must live in reports/cc-upgrade-delta/"]
    with open(full, encoding="utf-8", errors="replace") as f:
        text = f.read()
    probs = ["missing heading %r" % h for h in RECORD_HEADINGS
             if not re.search(r"^" + re.escape(h), text, re.M)]
    if vstr(lo) not in text or vstr(hi) not in text:
        probs.append("record does not name the range %s -> %s" % (vstr(lo), vstr(hi)))
    return probs


def vtuple(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s or "")
    return tuple(int(g) for g in m.groups()) if m else None


def running_version():
    """The one trusted source. Returns None if the CLI cannot be reached."""
    exe = CLI if os.path.exists(CLI) else "claude"
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return vtuple(out.stdout)


def load_stamp():
    try:
        with open(STAMP, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def parse_cache():
    """-> (ordered [(vtuple, vstr, [bullets])], newest vtuple or None)."""
    if not os.path.exists(CACHE):
        return [], None
    sections, cur = [], None
    with open(CACHE, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("## "):
                vs = line[3:].strip()
                vt = vtuple(vs)
                cur = (vt, vs, []) if vt else None
                if cur:
                    sections.append(cur)
            elif cur is not None and line.startswith("- "):
                cur[2].append(line[2:].rstrip())
    newest = max((s[0] for s in sections), default=None)
    return sections, newest


def collect(sections, lo, hi):
    """Bullets for versions in (lo, hi]. lo/hi are vtuples."""
    hits, total = {k: [] for k in CATEGORIES}, 0
    for vt, vs, bullets in sections:
        if not (lo < vt <= hi):
            continue
        for b in bullets:
            total += 1
            for name, rx in COMPILED.items():
                if rx.search(b):
                    hits[name].append((vs, b))
                    break
    return hits, total


def main():
    argv = sys.argv[1:]
    stamp = load_stamp()
    if "--assume-stamp" in argv:
        # Calibration input. A detector that has only ever been run against the
        # state it was written in has not been tested -- it needs a known-behind
        # case as well as the known-in-sync one.
        lo = vtuple(argv[argv.index("--assume-stamp") + 1])
    else:
        lo = vtuple(stamp.get("reconciled_version"))

    if "--assume-version" in argv:
        hi = vtuple(argv[argv.index("--assume-version") + 1])
        src = "assumed"
    else:
        hi = running_version()
        src = "claude --version"

    if lo is None or hi is None:
        print("[cc-delta] cannot compare: "
              + ("no stamp at ops/cc-reconciled.json" if lo is None
                 else "`claude --version` did not answer")
              + " -- this is an instrument failure, not an all-clear")
        return 2

    vstr = lambda t: ".".join(map(str, t))

    if "--features" in argv:
        sections, newest = parse_cache()
        if newest is None or newest < hi:
            print("[cc-delta] changelog cache does not reach %s -- splice it first "
                  "(run without flags for the remedy)" % vstr(hi))
            return 2
        cands, oos, skipped = features(sections, lo, hi, local_terms())
        print("# feature-delta candidates %s -> %s" % (vstr(lo), vstr(hi)))
        print("# %d candidates (feature verbs + fixes naming a local term); "
              "%d out-of-scope surface bullets and %d other fixes not listed"
              % (len(cands), oos, skipped))
        for vs, kind, b in cands:
            print("%-9s %-7s %s" % (vs, kind, b))
        return 0

    if "--stamp" in argv:
        rec = argv[argv.index("--record") + 1] if "--record" in argv[:-1] else None
        probs = check_record(rec, lo, hi)
        if probs:
            print("[cc-delta] stamp REFUSED -- a stamp must name a feature-delta "
                  "record (reports/cc-upgrade-delta/README.md):")
            for p in probs:
                print("  - " + p)
            return 2
        stamp["feature_delta"] = os.path.relpath(
            rec if os.path.isabs(rec) else os.path.join(HOME, rec), HOME).replace("\\", "/")
        stamp["reconciled_version"] = vstr(hi)
        try:
            st = os.stat(CLI)
            stamp["binary_size"], stamp["binary_mtime"] = st.st_size, int(st.st_mtime)
        except OSError:
            pass
        # newline="\n": the stamp is pinned eol=lf; text mode on Windows wrote CRLF
        with open(STAMP, "w", encoding="utf-8", newline="\n") as f:
            json.dump(stamp, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("[cc-delta] stamp -> %s (only valid if a pass was actually done)"
              % vstr(hi))
        return 0

    if hi <= lo:
        if "--check" not in argv:
            print("[cc-delta] in sync: ops reconciled at %s, running %s"
                  % (vstr(lo), vstr(hi)))
        return 0

    sections, newest = parse_cache()
    # Coverage is reported BEFORE any count, so a short cache can never be read
    # as "nothing changed".
    covered_hi = min(hi, newest) if newest else None
    gap = None
    if newest is None:
        gap = "changelog cache missing -- 0 of the range is readable"
    elif newest < hi:
        gap = ("cache reaches %s, running %s -- the newest builds are UNREAD"
               % (vstr(newest), vstr(hi)))

    if "--check" in argv:
        msg = ("Claude Code %s but ops reconciled at %s"
               % (vstr(hi), vstr(lo)))
        if gap:
            msg += " (%s)" % gap
        print("[cc-delta] " + msg +
              " -- run `python ~/.claude/tools/cc-delta/cc_delta.py`")
        return 1

    hits, total = collect(sections, lo, covered_hi) if covered_hi else ({}, 0)
    kept = sum(len(v) for v in hits.values())

    print("=" * 68)
    print("Claude Code delta: ops reconciled at %s, running %s (%s)"
          % (vstr(lo), vstr(hi), src))
    if gap:
        print("COVERAGE GAP: %s" % gap)
        # The remedy has to be doable WHERE THIS IS READ. Until 2026-09-06 it
        # said only "/release-notes in an interactive session" -- and this line
        # is printed at session start in the desktop app, which has no
        # interactive slash commands. A remedy that only works in another mode
        # is not a remedy: the cache rotted 19 builds behind (2.1.238 vs
        # 2.1.257) with the message displayed the whole time.
        print("  -> fetch the upstream changelog and splice the missing")
        print("     sections into cache/changelog.md (works in any session):")
        print("     https://raw.githubusercontent.com/anthropics/claude-code"
              "/main/CHANGELOG.md")
        print("     Format is what this file already holds: `## <version>`")
        print("     headings, `- ` bullets, newest first. Splice ABOVE the")
        print("     cache's current newest section; do not overwrite the file.")
        print("     NOTE: upstream SKIPS build numbers that were never")
        print("     published (2.1.213, 2.1.230, 2.1.242, 2.1.244, 2.1.249 are")
        print("     absent upstream) -- a gap is not a bad fetch. What must")
        print("     hold is that both ENDS of the range arrived.")
        print("  -> `/release-notes` also works, but only in an interactive")
        print("     terminal session.")
    print("%d bullets in range, %d touch something ops/ has written down"
          % (total, kept))
    if "--selectivity" in argv:
        pct = (100.0 * kept / total) if total else 0.0
        print("SELECTIVITY: filter keeps %.1f%% (%d/%d). A filter near 0%% or "
              "near 100%% is broken, not clean." % (pct, kept, total))
    print("=" * 68)

    for name in CATEGORIES:
        rows = hits.get(name) or []
        if not rows:
            continue
        print("\n## %s (%d)" % (name, len(rows)))
        for vs, b in rows:
            print("  %-9s %s" % (vs, b[:150]))

    if kept == 0 and not gap:
        print("\nNothing in range touches a recorded ops fact. This is a real "
              "all-clear only because coverage was complete.")
    print("\nAfter reconciling: `cc_delta.py --features` for the candidates, write "
          "reports/cc-upgrade-delta/<date>_%s-%s.md (spec: README.md there), then "
          "`cc_delta.py --stamp --record <it>`" % (vstr(lo), vstr(hi)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
