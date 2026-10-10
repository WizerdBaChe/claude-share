#!/usr/bin/env python3
"""Proof-of-life for mod_review.scan and ops-health check `mod-review`.

Rung 1 (finite domain): every way a plugin root can sit relative to the
property — a mod with no record, a mod with a record, a plugin that is not a
mod, a hooks.json without `modules`, an empty `modules`, a catalog copy under
marketplaces/, a dev-mod. Each case asserts the COUNTS (mods, unreviewed), so
a defect that drops or adds a plugin moves a number, not only a label; every
line prints the expected and the actual pair.

The last two cases run the real ops-health hook against the fixture home:
the positive must print the finding, the repaired home (record written) must
not. Run: python -X utf8 tools/mod-review/controls.py
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOME_REAL = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(HOME_REAL, "hooks", "ops_health_nudge.py")

spec = importlib.util.spec_from_file_location(
    "mod_review", os.path.join(HERE, "mod_review.py"))
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def plugin(root, name, version="1.0.0", hooks=None):
    os.makedirs(os.path.join(root, ".claude-plugin"), exist_ok=True)
    with open(os.path.join(root, ".claude-plugin", "plugin.json"), "w",
              encoding="utf-8") as f:
        json.dump({"name": name, "version": version}, f)
    if hooks is not None:
        os.makedirs(os.path.join(root, "hooks"), exist_ok=True)
        with open(os.path.join(root, "hooks", "hooks.json"), "w",
                  encoding="utf-8") as f:
            json.dump(hooks, f)


def build(home):
    cache = os.path.join(home, "plugins", "cache", "mkt")
    plugin(os.path.join(cache, "a-mod", "1.0.0"), "a-mod",
           hooks={"modules": ["./register.js"]})                  # mod, no record
    plugin(os.path.join(cache, "b-mod", "2.0.0"), "b-mod", "2.0.0",
           hooks={"modules": ["./register.ts"]})                  # mod, record below
    plugin(os.path.join(cache, "c-skill", "1.0.0"), "c-skill")    # not a mod
    plugin(os.path.join(cache, "d-classic", "1.0.0"), "d-classic",
           hooks={"hooks": {"Stop": []}})                         # settings hooks only
    plugin(os.path.join(cache, "e-empty", "1.0.0"), "e-empty",
           hooks={"modules": []})                                 # empty modules
    plugin(os.path.join(home, "plugins", "marketplaces", "mkt", "f-cat"),
           "f-cat", hooks={"modules": ["./r.js"]})                # catalog: excluded
    plugin(os.path.join(home, "dev-mods", "sess-1", "g-dev"), "g-dev",
           "0.0.1", hooks={"modules": ["./r.js"]})                # dev-mod, no record
    # undetermined inputs: hooks.json that does not parse, and one that parses
    # to a list instead of an object. Neither can be classified as a mod, so
    # both are EXCLUDED (counted nowhere), never folded into a verdict.
    bad = os.path.join(cache, "h-bad", "1.0.0")
    plugin(bad, "h-bad")
    os.makedirs(os.path.join(bad, "hooks"), exist_ok=True)
    with open(os.path.join(bad, "hooks", "hooks.json"), "w", encoding="utf-8") as f:
        f.write("{ not json")
    plugin(os.path.join(cache, "i-list", "1.0.0"), "i-list",
           hooks=["./register.js"])
    rec = mr.record_path(home, "b-mod", "2.0.0")
    os.makedirs(os.path.dirname(rec), exist_ok=True)
    with open(rec, "w", encoding="utf-8") as f:
        f.write("# Mod review: b-mod@2.0.0\n")


def run_hook(home):
    env = dict(os.environ, USERPROFILE=os.path.dirname(home),
               HOME=os.path.dirname(home), HOMEPATH=os.path.dirname(home))
    env.pop("PYTHONPATH", None)
    env["OPS_NUDGE_BUNDLE_STATUS"] = os.path.join(home, "no-disk", "s.json")
    env["OPS_NUDGE_VAULT_ROOT"] = os.path.join(home, "no-vault")
    p = subprocess.run([sys.executable, HOOK, "--all"], input="",
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=home)
    return p.stdout


def main():
    fails = 0

    def check(label, expected, actual):
        nonlocal fails
        ok = expected == actual
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label}: expected={expected!r} "
              f"actual={actual!r}")

    with tempfile.TemporaryDirectory() as tmp:
        home = os.path.join(tmp, ".claude")
        os.makedirs(home)
        res = mr.scan(home)
        check("empty home: mods", 0, len(res["mods"]))
        build(home)
        res = mr.scan(home)
        check("fixture: mods found",
              ["a-mod", "b-mod", "g-dev"], sorted(m["name"] for m in res["mods"]))
        check("fixture: unreviewed",
              ["a-mod", "g-dev"], sorted(m["name"] for m in res["unreviewed"]))
        check("undetermined hooks.json (unparsable / list) excluded", [],
              [m["name"] for m in res["mods"] if m["name"] in ("h-bad", "i-list")])
        check("fixture: origins",
              {"a-mod": "installed", "g-dev": "dev-mods"},
              {m["name"]: m["origin"] for m in res["unreviewed"]})

        out = run_hook(home)
        check("hook positive: finding printed", True,
              "mod(s) on disk without a review record" in out)
        check("hook positive: names both", True,
              "a-mod@1.0.0" in out and "g-dev@0.0.1" in out)
        # repaired input: write the two missing records, the finding must go
        for n, v in (("a-mod", "1.0.0"), ("g-dev", "0.0.1")):
            with open(mr.record_path(home, n, v), "w", encoding="utf-8") as f:
                f.write("x\n")
        check("repaired: unreviewed", 0, len(mr.scan(home)["unreviewed"]))
        out = run_hook(home)
        check("hook repaired: finding absent", False,
              "mod(s) on disk without a review record" in out)

    real = mr.scan(HOME_REAL)
    print(f"INFO  this machine: {len(real['mods'])} mod(s), "
          f"{len(real['unreviewed'])} without a record")
    print(f"mod-review controls: {'OK' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
