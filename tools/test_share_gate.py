#!/usr/bin/env python3
"""test_share_gate.py — prove the gate catches the incidents that created it.

    python tools/test_share_gate.py

Each case plants a real regression into the working tree, runs the gate, and
restores the file. A gate nobody has seen FAIL is not evidence of anything —
these four cases are the evidence. Exit 0 = all cases behaved as specified.

Cases mirror the two failure classes the gate was built for:
  1  over-scrub      the historical `<URL>` version of interop-layer/README.md
  2  under-declare   an undeclared source-environment dependency
  3  leak            a planted address and a planted home path
  4  control         the current tree passes
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = [sys.executable, str(ROOT / "tools" / "share_gate.py")]
OVER_SCRUB_COMMIT = "1cb38ef"          # last commit carrying the <URL> damage
OVER_SCRUB_FILE = "interop-layer/README.md"
MANIFEST = ROOT / "tools" / "share-manifest.toml"


def gate(*args):
    p = subprocess.run(GATE + list(args), capture_output=True, text=True,
                       cwd=str(ROOT))
    return p.returncode, p.stdout + p.stderr


def case(name, expect_fail, expect_in_output, mutate, restore):
    mutate()
    try:
        rc, out = gate()
        ok_rc = (rc == 1) if expect_fail else (rc == 0)
        ok_txt = all(s in out for s in expect_in_output)
        status = "PASS" if (ok_rc and ok_txt) else "FAIL"
        print(f"[{status}] {name}  (exit {rc})")
        if status == "FAIL":
            for s in expect_in_output:
                if s not in out:
                    print(f"         expected to see: {s!r}")
            print("         --- gate output ---")
            print("         " + out.strip().replace("\n", "\n         "))
        return status == "PASS"
    finally:
        restore()


def main():
    results = []
    target = ROOT / OVER_SCRUB_FILE
    saved = target.read_text(encoding="utf-8")
    old = subprocess.run(["git", "-C", str(ROOT), "show",
                          f"{OVER_SCRUB_COMMIT}:{OVER_SCRUB_FILE}"],
                         capture_output=True, text=True)
    if old.returncode != 0:
        print(f"FATAL: cannot read {OVER_SCRUB_COMMIT}:{OVER_SCRUB_FILE}")
        return 2

    # 1 — the historical over-scrub must not be publishable.
    results.append(case(
        "over-scrub: the <URL> version of the interop manual",
        expect_fail=True,
        expect_in_output=["<URL>", OVER_SCRUB_FILE],
        mutate=lambda: target.write_text(old.stdout, encoding="utf-8", newline=""),
        restore=lambda: target.write_text(saved, encoding="utf-8", newline=""),
    ))

    # 2 — removing a disposition must resurface the dependency.
    man_saved = MANIFEST.read_text(encoding="utf-8")
    man_cut = man_saved.replace('path = "settings.json"',
                                'path = "__removed_for_test__.json"')
    assert man_cut != man_saved, "manifest fixture no longer matches"
    results.append(case(
        "under-declare: settings.json with its disposition removed",
        expect_fail=True,
        expect_in_output=["settings.json", "does not ship"],
        mutate=lambda: MANIFEST.write_text(man_cut, encoding="utf-8", newline=""),
        restore=lambda: MANIFEST.write_text(man_saved, encoding="utf-8", newline=""),
    ))

    # 3 — planted personal data, one of each shape.
    plant = saved + (
        "\n\n<!-- planted by test_share_gate.py -->\n"
        "contact: someone.real@example.com\n"
        "path: C:\\Users\\somebodyelse\\AppData\\Roaming\\thing\n")
    results.append(case(
        "leak: planted address + another account's home path",
        expect_fail=True,
        expect_in_output=["email address", "absolute home path"],
        mutate=lambda: target.write_text(plant, encoding="utf-8", newline=""),
        restore=lambda: target.write_text(saved, encoding="utf-8", newline=""),
    ))

    # 4 — a collected file whose edits were never written down.
    man_unrecorded = man_saved.replace(
        'edits = [\n  "docstring: replaced a local session id',
        'edits_MISSING = [\n  "docstring: replaced a local session id')
    assert man_unrecorded != man_saved, "collection fixture no longer matches"
    results.append(case(
        "unrecorded edit: a collected file with status 'edited' and no edit list",
        expect_fail=True,
        expect_in_output=["model_cap_guard.py", "no recorded edits"],
        mutate=lambda: MANIFEST.write_text(man_unrecorded, encoding="utf-8", newline=""),
        restore=lambda: MANIFEST.write_text(man_saved, encoding="utf-8", newline=""),
    ))

    # 5 — control: the tree as it stands must pass.
    results.append(case(
        "control: current tree",
        expect_fail=False,
        expect_in_output=["share gate CLEAN"],
        mutate=lambda: None,
        restore=lambda: None,
    ))

    print(f"\n{sum(results)}/{len(results)} cases behaved as specified")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
