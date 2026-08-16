#!/usr/bin/env python3
"""test_share_gate.py — prove the gate catches the incidents that created it.

    python tools/test_share_gate.py

Each case plants a real regression into the working tree, runs the gate, and
restores the file. A gate nobody has seen FAIL is not evidence of anything —
these cases are the evidence. Exit 0 = all cases behaved as specified.

Every case is a real incident, not a hypothetical:
  1  over-scrub      the historical `<URL>` version of interop-layer/README.md
  2  under-declare   an undeclared source-environment dependency
  3  leak            a planted address and a planted home path
  4  unrecorded edit a collected file claiming 'edited' with no edit list
  5  leak            an absolute path on a non-system drive (2026-08-16: nine
                     entered in one refresh, three were already published)
  6  CONTROL         system paths on a drive letter must NOT fire — the
                     negative half of case 5. A pattern that fires on
                     `C:\\Windows` gets switched off within a week.
  7  unmounted hook  a hook that ships with no way to turn it on (the template
                     was mounting 7 of 9)
  8  dead permission an [[allow]] whose finding no longer exists
  9  CONTROL         the current tree passes
 10  source-verify   a declared edit reverted by a verbatim refresh — the
                     2026-08-16 failure, and the only case needing --source
 11  CONTROL         an undeclared non-README file under a collected root
                     still fires — the negative half of the ACCEPTANCE.md
                     name-exemption added 2026-08-16 (compact-recovery round).
                     The exemption's fails-without-it half is case 9: the live
                     tree now holds compact-recovery/ACCEPTANCE.md, so the
                     old gate fails the current-tree control.

Two of the eleven assert that the gate stays QUIET. That ratio is deliberate: a
gate calibrated only on things it should catch scores 100% by rejecting
everything, which is the reasoning `global-claude-md/CLAUDE.md` states and this
file has to live up to.
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


def case_v(src):
    """The 2026-08-16 failure, reproduced: a declared edit silently reverted.

    A verbatim refresh overwrote files whose repo copies were deliberately
    different, and every repo-local check passed — none of them was comparing
    anything. Here that is staged by copying the SOURCE version of an edited
    file over the repo's, which is exactly what the refresh did, and check V
    must say so.
    """
    rel = "hooks/model_cap_guard.py"
    target = ROOT / rel
    saved = target.read_bytes()
    src_bytes = (src / rel).read_bytes()

    def run():
        target.write_bytes(src_bytes)
        try:
            p = subprocess.run(GATE + ["--source", str(src)],
                               capture_output=True, text=True, cwd=str(ROOT))
            out = p.stdout + p.stderr
            ok = p.returncode == 1 and "byte-identical to the source" in out \
                and rel in out
            print(f"[{'PASS' if ok else 'FAIL'}] source-verify: a declared edit "
                  f"reverted by a refresh  (exit {p.returncode})")
            if not ok:
                print("         --- gate output ---")
                print("         " + out.strip().replace("\n", "\n         "))
            return ok
        finally:
            target.write_bytes(saved)

    return run()


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

    # 5 — a private path on a non-system drive. The class that let nine
    #     pointers through the 2026-08-16 refresh and had three more sitting in
    #     published files: the home-path patterns never looked at other drives.
    drive_plant = saved + (
        "\n\n<!-- planted by test_share_gate.py -->\n"
        "registry: D:\\SomePrivateTree\\vault\\registry.json\n")
    results.append(case(
        "leak: an absolute path on a non-system drive",
        expect_fail=True,
        expect_in_output=["absolute local path", "SomePrivateTree"],
        mutate=lambda: target.write_text(drive_plant, encoding="utf-8", newline=""),
        restore=lambda: target.write_text(saved, encoding="utf-8", newline=""),
    ))

    # 6 — a system path on the same drive letter must NOT fire. The negative
    #     half of case 5's calibration: a pattern that fires on every drive
    #     letter would bury the real findings under C:\Windows and the gate
    #     would be switched off within a week.
    system_plant = saved + (
        "\n\n<!-- planted by test_share_gate.py -->\n"
        "crash dump: C:\\Windows\\LiveKernelReports\\thing.sys\n"
        "interpreter: C:\\Program Files\\Python312\\python.exe\n")
    results.append(case(
        "control: system paths on a drive letter are not findings",
        expect_fail=False,
        expect_in_output=["share gate CLEAN"],
        mutate=lambda: target.write_text(system_plant, encoding="utf-8", newline=""),
        restore=lambda: target.write_text(saved, encoding="utf-8", newline=""),
    ))

    # 7 — check S5: a hook that ships with no way to turn it on. The template
    #     was mounting 7 of 9 and nothing noticed.
    tmpl_path = ROOT / "hooks" / "settings.example.json"
    tmpl_saved = tmpl_path.read_text(encoding="utf-8")
    tmpl_cut = tmpl_saved.replace("hooks/context_runway_shadow.py",
                                  "hooks/__unmounted_for_test__.py")
    assert tmpl_cut != tmpl_saved, "mount fixture no longer matches"
    results.append(case(
        "unmounted hook: a shipped hook missing from settings.example.json",
        expect_fail=True,
        expect_in_output=["context_runway_shadow.py", "ships but is not mounted"],
        mutate=lambda: tmpl_path.write_text(tmpl_cut, encoding="utf-8", newline=""),
        restore=lambda: tmpl_path.write_text(tmpl_saved, encoding="utf-8", newline=""),
    ))

    # 8 — check D: a standing permission for a finding that no longer exists.
    man_dead = man_saved.replace(
        'file = "tools/test_share_gate.py"\nkind = "email address"',
        'file = "tools/test_share_gate.py"\nkind = "private network host"', 1)
    assert man_dead != man_saved, "dead-allow fixture no longer matches"
    results.append(case(
        "dead declaration: an [[allow]] that excuses nothing any more",
        expect_fail=True,
        expect_in_output=["matches nothing there any more"],
        mutate=lambda: MANIFEST.write_text(man_dead, encoding="utf-8", newline=""),
        restore=lambda: MANIFEST.write_text(man_saved, encoding="utf-8", newline=""),
    ))

    # 9 — control: the tree as it stands must pass.
    results.append(case(
        "control: current tree",
        expect_fail=False,
        expect_in_output=["share gate CLEAN"],
        mutate=lambda: None,
        restore=lambda: None,
    ))

    # 10 — check V, which needs a source tree. Skipped LOUDLY when there is
    #      none: an adopter has no source, and this must never read as a pass.
    src = Path.home() / ".claude"
    if src.is_dir() and (src / "hooks").is_dir():
        results.append(case_v(src))
    else:
        print(f"[SKIP] source-verify: no source tree at {src} — check V not exercised")

    # 11 — the negative control for the ACCEPTANCE.md name-exemption
    #      (2026-08-16): an undeclared, non-exempt file under a collected root
    #      must still fire check C. Mutates the INDEX, not just a file, because
    #      the gate reads tracked files; restore un-stages and deletes.
    stray = ROOT / "compact-recovery" / "__undeclared_for_test__.md"

    def plant_stray():
        stray.write_text("planted by test_share_gate.py\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(ROOT), "add", "--", str(stray)],
                       capture_output=True)

    def remove_stray():
        subprocess.run(["git", "-C", str(ROOT), "rm", "--cached", "-q", "--",
                        str(stray)], capture_output=True)
        stray.unlink(missing_ok=True)

    results.append(case(
        "control: undeclared file under a collected root still fires",
        expect_fail=True,
        expect_in_output=["__undeclared_for_test__.md",
                          "no provenance entry"],
        mutate=plant_stray,
        restore=remove_stray,
    ))

    print(f"\n{sum(results)}/{len(results)} cases behaved as specified")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
