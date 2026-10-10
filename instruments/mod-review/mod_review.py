#!/usr/bin/env python3
r"""mod-review — every Claude Code mod on this machine carries a review record.

STATUS: LIVE since 2026-10-02 (user ruling 2026-10-02 「走建議」 on a dated
Claude Code upgrade-delta addendum under the source's reports/ tree, not shipped
here; pending item 1).
Carries `ops/rule-registry.md` key `MOD_REVIEW`.

THE ASSET PROPERTY. Every plugin on disk whose `hooks/hooks.json` names a
hooks module (`"modules": [...]`, which is what makes a plugin a mod, Claude
Code >= 2.1.287) has a record `reports/mod-reviews/<name>@<version>.md` written
by `review` from the output of `claude plugin validate`.

WHY. A mod runs inside Claude Code with the user's permissions, unsandboxed,
and a `tool.check` hook can approve a call that one of this machine's
PreToolUse hooks blocked (docs: plugins/mods/events, "The order mods run in").
Every hook-enforced invariant here assumes nothing can approve past a hook; a
reviewed mod is the only way that assumption survives a mod being installed.
The check runs on what is ON DISK, enabled or not, because `/plugin` enables
a plugin without any tool call a hook could see — on disk is the last point
before it can run.

  python mod_review.py scan [--json]       mods on disk, and which lack a record
  python mod_review.py review <plugin-dir> run `claude plugin validate`, write the record

Severity: `scan` exit 1 when a mod lacks a record. ops-health check
`mod-review` reports it as an ALARM — a determinable closure (the record
exists or it does not), so FAIL grade (gate-severity-by-consumer).
Proof-of-life: `python tools/mod-review/controls.py`.

review-when: Claude Code renames `modules` in hooks.json or moves where it
caches installed plugins (`plugins/cache/<marketplace>/<name>/<version>`);
`claude plugin validate` stops printing `hooks:` / `calls:` lines; a plugin
source other than the four ROOTS below starts loading on this machine.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys

# Places a plugin can sit on disk and load from (2.1.287). `marketplaces/` is
# deliberately absent: it is a catalog of what COULD be installed, not code
# that loads. dev-mods holds mods Claude wrote in a session; they load only
# after an in-session approval, but they are on disk and count.
ROOTS = (
    ("installed", ("plugins", "cache")),
    ("synced", ("plugins", "synced")),
    ("skills-dir", ("skills",)),
    ("dev-mods", ("dev-mods",)),
)
RECORD_DIR = ("reports", "mod-reviews")
MAX_DEPTH = 5

# Events and calls that reach past observation into deciding or acting. A
# validate line naming one is flagged in the record; it does not fail the
# review — the record is for a reader to decide from.
RISKY_EVENTS = ("tool.check", "tool.call", "prompt.submit", "classic.",
                "session.receive", "session.send", "config.set", "*")
RISKY_CALLS = ("$.process.", "$.http.", "$.fs.write", "$.session.send",
               "$.prompt.submit", "$.config.set", "$.env.set", "$.model.")


def _home(home=None):
    return home or os.path.join(os.path.expanduser("~"), ".claude")


def _modules(plugin_root):
    """The hooks-module list of a plugin, or [] when it is not a mod."""
    p = os.path.join(plugin_root, "hooks", "hooks.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    mods = data.get("modules") if isinstance(data, dict) else None
    return [m for m in mods if isinstance(m, str)] if isinstance(mods, list) else []


def _manifest(plugin_root):
    p = os.path.join(plugin_root, ".claude-plugin", "plugin.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def record_path(home, name, version):
    safe = re.sub(r"[^A-Za-z0-9._@-]", "_", f"{name}@{version}")
    return os.path.join(home, *RECORD_DIR, safe + ".md")


def find_mods(home=None):
    """Every plugin root under ROOTS whose hooks.json names a hooks module."""
    home = _home(home)
    found = []
    for origin, parts in ROOTS:
        base = os.path.join(home, *parts)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, _files in os.walk(base):
            depth = dirpath[len(base):].count(os.sep)
            if depth >= MAX_DEPTH:
                dirnames[:] = []
            if os.path.basename(dirpath) == ".claude-plugin":
                dirnames[:] = []
                continue
            man = _manifest(dirpath)
            if man is None:
                continue
            dirnames[:] = []          # a plugin root does not nest another
            modules = _modules(dirpath)
            if not modules:
                continue
            name = str(man.get("name") or os.path.basename(dirpath))
            version = str(man.get("version") or "unversioned")
            found.append({"name": name, "version": version, "origin": origin,
                          "root": dirpath, "modules": modules,
                          "record": record_path(home, name, version)})
    return found


def scan(home=None):
    mods = find_mods(home)
    unreviewed = [m for m in mods if not os.path.isfile(m["record"])]
    return {"mods": mods, "unreviewed": unreviewed}


def _flag(line):
    hits = [t for t in RISKY_EVENTS + RISKY_CALLS if t in line]
    return f"  <- reaches past observing: {', '.join(hits)}" if hits else ""


def review(plugin_dir, home=None, claude="claude"):
    """Run `claude plugin validate` and write the record. Returns exit code."""
    home = _home(home)
    plugin_dir = os.path.abspath(plugin_dir)
    man = _manifest(plugin_dir)
    if man is None:
        print(f"mod-review: no .claude-plugin/plugin.json under {plugin_dir}",
              file=sys.stderr)
        return 2
    name = str(man.get("name") or os.path.basename(plugin_dir))
    version = str(man.get("version") or "unversioned")
    try:
        r = subprocess.run([claude, "plugin", "validate", plugin_dir],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"mod-review: validate did not run: {exc}", file=sys.stderr)
        return 2
    out = (r.stdout or "") + (r.stderr or "")
    lines = [ln.strip() for ln in out.splitlines()]
    scope = [ln for ln in lines if not ln.startswith("Validating")
             and (" hooks: " in ln or " calls: " in ln
                  or "env reads:" in ln or "env writes:" in ln)]
    passed = r.returncode == 0
    flagged = [ln + _flag(ln) for ln in scope]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = [
        f"# Mod review: {name}@{version}",
        "",
        f"status: {'VALIDATED' if passed else 'VALIDATE-FAILED'} · {now} · "
        f"written by tools/mod-review/mod_review.py",
        "",
        f"- 路徑 (root)：`{plugin_dir}`",
        f"- hooks modules：{', '.join(_modules(plugin_dir)) or '(none)'}",
        f"- `claude plugin validate` exit {r.returncode}",
        "",
        "## 它處理的事件與呼叫 (hooks / calls)",
        "",
        "```",
        *(flagged or ["(validate printed no hooks:/calls: lines)"]),
        "```",
        "",
        "標了 `<- reaches past observing` 的行代表它能改寫、放行或對外動作，"
        "啟用前要讀它的原始碼確認用途。",
        "",
        "## validate 原始輸出",
        "",
        "```",
        *lines,
        "```",
        "",
    ]
    path = record_path(home, name, version)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(body))
    print(f"mod-review: {'VALIDATED' if passed else 'VALIDATE-FAILED'} "
          f"{name}@{version} -> {path}")
    return 0 if passed else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "scan":
        res = scan()
        if "--json" in argv:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            print(f"mod-review: {len(res['mods'])} mod(s) on disk, "
                  f"{len(res['unreviewed'])} without a record")
            for m in res["unreviewed"]:
                print(f"  {m['name']}@{m['version']} ({m['origin']}) {m['root']}")
        return 1 if res["unreviewed"] else 0
    if argv[0] == "review" and len(argv) == 2:
        return review(argv[1])
    print("usage: mod_review.py scan [--json] | review <plugin-dir>",
          file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
