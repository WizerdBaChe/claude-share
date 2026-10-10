r"""Backtest a hook predicate against every recorded tool call.

    python hook_backtest.py <module>:<function> [options]

    python hook_backtest.py adapters:secret_print
    python hook_backtest.py adapters:ps_errorpref --root path/to/snapshot/projects
    python hook_backtest.py my_new_guard:would_fire --tools Bash --dedupe content
    python hook_backtest.py path/to/draft_guard.py:check --excerpt 100 --json fires.json

<module> is a .py path, or a name found in the live ~/.claude/hooks/ first and
then beside this file (adapters.py). <function>(tool_name, tool_input) returns
a falsy value (no fire) or a verdict: a string kind, a dict with "kind", or any
truthy value (kind "fire"). Function attributes `tools`, `dedupe` and
`assistant_only` (see adapters.py) set the defaults; flags override them.

OUTPUT NEVER CARRIES WHAT A CALL TYPED unless --excerpt is given, and then only
after redaction with cred-sweep's credential patterns (fail-closed: no
redactor, no text). Each fire prints date, session, tool, kind and a locator
(project-dir/file:line) that reopens the call. The JSON dump follows the same
rule.

Exit: 0 ran (fires or not), 2 no calls matched the tool filter (an empty corpus
reads as "0 fires" otherwise -- a ruler that never met the data is no ruler).
"""
import argparse
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as hb  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("predicate", help="<module>:<function>")
    ap.add_argument("--root", action="append", dest="roots",
                    help="corpus root (repeatable); default: %s" % ", ".join(hb.DEFAULT_ROOTS))
    ap.add_argument("--tools", help="comma list, e.g. Bash,PowerShell (default: predicate.tools or all)")
    ap.add_argument("--dedupe", choices=sorted(hb.DEDUPE) + ["none"])
    ap.add_argument("--all-records", action="store_true",
                    help="do not require type=assistant on the record")
    ap.add_argument("--list", type=int, default=50, help="max fires listed (default 50, 0 = none)")
    ap.add_argument("--excerpt", type=int, default=0, metavar="N",
                    help="append N chars of REDACTED call text to each listed fire")
    ap.add_argument("--json", dest="dump", help="write every fire (locators, kinds) to this file")
    a = ap.parse_args(argv)

    pred = hb.load_predicate(a.predicate)
    tools = (a.tools.split(",") if a.tools else getattr(pred, "tools", None))
    dname = a.dedupe or getattr(pred, "dedupe", "ts-head")
    dedupe = None if dname == "none" else hb.DEDUPE[dname]
    assistant_only = False if a.all_records else getattr(pred, "assistant_only", True)
    roots = a.roots or hb.DEFAULT_ROOTS

    print("hook   : %s" % a.predicate)
    print("roots  : %s" % ", ".join(roots))
    corpus, fires = hb.run(pred, roots, tools, dedupe, assistant_only)
    lo, hi = corpus.window()
    print("corpus : %d transcript files, %d distinct days (%s .. %s)"
          % (corpus.files, len(corpus.days), lo, hi))
    print("calls  : %s   [tools=%s, dedupe=%s, assistant-only=%s]"
          % (", ".join("%s=%d" % kv for kv in sorted(corpus.calls.items())) or "none",
             ",".join(tools) if tools else "all", dname, "yes" if assistant_only else "no"))
    n = sum(corpus.calls.values())
    if not n:
        print("NO CALLS matched -- check --root / --tools; this is not '0 fires'.")
        return 2
    kinds = Counter(hb.verdict_kind(v) for _, v in fires)
    per_tool = Counter(c.tool for c, _ in fires)
    nday = len(corpus.days) or 1
    print("FIRES  : %d / %d inspected calls = %.3f%%  (%.3f / day)"
          % (len(fires), n, 100.0 * len(fires) / n, len(fires) / nday))
    print("  by kind : %s" % (", ".join("%s=%d" % kv for kv in sorted(kinds.items())) or "-"))
    print("  by tool : %s" % (", ".join("%s=%d" % kv for kv in sorted(per_tool.items())) or "-"))

    if a.list and fires:
        shown = sorted(fires, key=lambda cv: cv[0].ts)[:a.list]
        print()
        print("== fires (%d of %d): date  session  tool  kind  locator ==" % (len(shown), len(fires)))
        for c, v in shown:
            line = "%s  %s  %-10s %-10s %s" % (c.date, c.session[:8], c.tool,
                                               hb.verdict_kind(v), c.locator)
            if a.excerpt:
                line += "\n      " + hb.excerpt(c, a.excerpt)
            print(line)

    if a.dump:
        rows = []
        for c, v in fires:
            r = {"date": c.date, "ts": c.ts, "session": c.session, "tool": c.tool,
                 "kind": hb.verdict_kind(v), "locator": c.locator,
                 "tool_use_id": c.tool_use_id}
            if a.excerpt:
                r["excerpt"] = hb.excerpt(c, a.excerpt)
            rows.append(r)
        io.open(a.dump, "w", encoding="utf-8").write(json.dumps(rows, ensure_ascii=False, indent=1))
        print()
        print("wrote %d fires -> %s" % (len(rows), a.dump))
    return 0


if __name__ == "__main__":
    sys.exit(main())
