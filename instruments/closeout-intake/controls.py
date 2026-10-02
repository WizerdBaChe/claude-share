"""controls.py — two-sided controls for closeout-intake (PSM §4, cases C-01..C-99).

Every case is a POSITIVE control (must fire / must succeed) or a NEGATIVE control (must
stay silent / must reject). A checker that has never been shown a known-true and a
known-false input has no verdict (global gate rule). C-42a..d add the third outcome
(AP-62): an event line outside the closed EVENT_KINDS vocabulary is named in the error
list, dropped from the events, and absent from the derived hits and state — never
folded into the nearest kind. Runs on a TEMP store — never on
ops/lessons/. Hook cases (C-9x) are SKIPPED with a named reason when the hook file does
not exist yet (M2 builds it); the final line then says so — "ALL PASS" is only printed
when nothing was skipped.
Usage: python tools/closeout-intake/controls.py [--keep]
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import intake_core as core  # noqa: E402

PY = sys.executable
INTAKE = os.path.join(HERE, "intake.py")
GUARD = os.path.join(HOME, "hooks", "intake_guard.py")
MATCH_HOOK = os.path.join(HOME, "hooks", "intake_match_shadow.py")
RESULTS: list[tuple[str, bool, str]] = []
SKIPPED: list[tuple[str, str]] = []


def check(cid: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((cid, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'} {cid} {detail[:110]}")


def skip(cid: str, why: str) -> None:
    SKIPPED.append((cid, why)); print(f"SKIP {cid} {why}")


def run(*args, cwd=HOME) -> subprocess.CompletedProcess:
    return subprocess.run([PY, INTAKE, *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


GOOD_DRAFT = """---
what: 測試用教訓 (a test lesson about shell transport)
tags: [shell, verify]
---
## Record
locator: turn 12 / tool_use_id toolu_test

## Context
A test context line.

## Pitfall
The mechanism under test: a control draft.

## Fix
Use the tool.

## Detection
Run controls.py.

## Narrative
Free text kept verbatim.
"""


def draft(**mod) -> str:
    t = GOOD_DRAFT
    for k, v in mod.items():
        t = t.replace(k, v)
    return t


def wfile(d: str, name: str, text: str) -> str:
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return p


def main() -> int:
    keep = "--keep" in sys.argv
    tmp = tempfile.mkdtemp(prefix="intake-ctl-")
    store = os.path.join(tmp, "store")
    vocab = {"shell", "verify", "env"}
    try:
        # ---- INV-1 / D-rules --------------------------------------------------------
        check("C-01", core.validate_draft(GOOD_DRAFT, vocab) == [], "valid draft accepted")
        r = run("add", "--from", wfile(tmp, "d1.md", GOOD_DRAFT), "--store", store, "--session", "abcdef12-0000")
        check("C-01b", r.returncode == 0 and os.path.isfile(os.path.join(store, "L-001.md")), r.stdout.strip()[:80] or r.stderr[:80])
        cases = {
            "C-02 D1": (draft(**{"---\nwhat:": "---\nxi: 1\nwhat:"}), "D9"),          # tool-owned key → D9 (xi)
            "C-03 D1b": (GOOD_DRAFT.replace("---\nwhat", "what"), "D1"),               # no front matter
            "C-04 D2": (draft(**{"測試用教訓 (a test lesson about shell transport)": "a test lesson only latin"}), "D2"),
            "C-05 D3": (draft(**{"[shell, verify]": "[nothing-known]"}), "D3"),
            "C-06 D4": (draft(**{"## Fix\nUse the tool.\n": "## Fix\n\n"}), "D4"),
            "C-07 D5": (draft(**{"The mechanism under test: a control draft.": "x" * 701}), "D5"),
            "C-08 D6": (draft(**{"locator: turn 12 / tool_use_id toolu_test": "locator:"}), "D6"),
            "C-09 D7": (GOOD_DRAFT + "\n## Events\n- 2026-01-01 born\n", "D7"),
            "C-10 D8": (draft(**{"A test context line.": "A line with hits: 3 inside"}), "D8"),
            "C-10b D9": (draft(**{"locator: turn": "id: L-999\nlocator: turn"}), "D9"),
        }
        for cid, (txt, rule) in cases.items():
            errs = core.validate_draft(txt, vocab)
            check(cid, bool(errs) and errs[0][0] == rule, f"want {rule}, got {errs[0][0] if errs else 'accept'}: {errs[0][1][:60] if errs else ''}")
        # planted invalid file → check exit 4
        wfile(store, "L-002.md", "---\nxi: 1\nwhat: bad\n---\n## Record\nid: L-002\n\n## Context\nx\n")
        r = run("check", "--store", store)
        check("C-11", r.returncode == 4 and "L-002" in r.stdout, r.stdout.strip().split("\n")[0][:90])
        os.remove(os.path.join(store, "L-002.md"))

        # ---- INV-6 ------------------------------------------------------------------
        check("C-60", core.validate_draft(draft(**{"locator: turn 12 / tool_use_id toolu_test": "locator:"}), vocab)[0][0] == "D6")
        check("C-61", core.validate_draft(draft(**{"turn 12 / tool_use_id toolu_test": "unrecorded"}), vocab) == [], "literal unrecorded accepted")
        r = run("add", "--from", wfile(tmp, "d62.md", GOOD_DRAFT), "--store", store, "--session", "auto",
                cwd=tmp)  # cwd outside HOME → no session pointer? pointer path is absolute; simulate by env-less read
        # G-6: we cannot remove the real pointer; assert the fallback code path via core (session string 'unrecorded' allowed)
        check("C-62", r.returncode == 0, "add with --session auto exits 0 (fallback tolerated)")

        # ---- INV-4 / derive table -----------------------------------------------------
        ev = lambda *lines: core.parse_events(list(lines))[0]
        t = _dt.date(2026, 9, 7)
        check("C-41a", core.derive(ev("- 2026-09-01 born session=x"), t)["state"] == "live")
        check("C-41b", core.derive(ev("- 2026-05-01 born session=x"), t)["state"] == "dormant", "90d no event, hits 1")
        d = core.derive(ev("- 2026-05-01 born session=x", "- 2026-05-02 recurrence session=y project=p held=no"), t)
        check("C-41c", d["hits"] == 2 and d["state"] == "live", f"hits {d['hits']} state {d['state']}")
        d = core.derive(ev("- 2026-09-01 born session=x", "- 2026-09-02 fold → ops/40-maintenance.md §2a"), t)
        check("C-41d", d["state"] == "folded" and core.project_status(d["state"], None) == "spent")
        # A fold's reason is optional and lives after " — "; the target must survive it,
        # and a note-less line from before 2026-09-08 must parse exactly as it always did.
        e_why = core.parse_events(["- 2026-09-08 fold → CLAUDE.md — the routing bullet owns it"])[0][0]
        e_bare = core.parse_events(["- 2026-09-02 fold → ops/40-maintenance.md §2a"])[0][0]
        check("C-41d2", e_why["target"] == "CLAUDE.md" and e_why["why"] == "the routing bullet owns it"
              and e_bare["target"] == "ops/40-maintenance.md §2a" and e_bare["why"] is None,
              f"{e_why['target']!r} / {e_bare['target']!r}")
        d = core.derive(ev("- 2026-09-01 born session=x", "- 2026-09-02 supersede → L-777 — r"), t)
        check("C-41e", d["state"] == "superseded" and core.project_status(d["state"], d["successor"]) == "superseded: L-777")
        d = core.derive(ev("- 2026-09-01 born session=x", "- 2026-09-02 imported hits=5 from f"), t)
        check("C-41f", d["hits"] == 5, f"imported hits → {d['hits']}")
        check("C-41g", core.transition("superseded", "recurrence") == "illegal" and core.transition("folded", "fold") == "illegal"
              and core.transition("live", "match") == "ignored" and core.transition("dormant", "match") == "ok")
        # ---- AP-62: an event line matching NO declared kind -------------------------------
        # EVENT_KINDS is the closed vocabulary and `derive` is the verdict count (hits +
        # lifecycle state). A line whose kind is outside it fits no class: parse_events
        # reports it by name and drops it, so it can never be folded into the nearest kind.
        # The fold would be silent — `hits` would simply read one higher, which is exactly
        # the number a reader trusts to decide whether the 2nd-report rule has fired.
        evs, errs = core.parse_events(["- 2026-09-01 born session=x",
                                       "- 2026-09-02 escalation session=y held=no"])
        check("C-42a undetermined event kind: named in errs, dropped from the events",
              errs == ["bad-event-kind:escalation"] and len(evs) == 1,
              f"errs={errs}, kept={[e['kind'] for e in evs]}")
        d = core.derive(evs, t)
        check("C-42b undetermined event changes no derived count",
              d["hits"] == 1 and d["state"] == "live",
              f"hits {d['hits']}, state {d['state']}")
        _, errs2 = core.parse_events(["* 2026-09-02 recurrence session=y"])
        check("C-42c a line that is not an event line at all is undetermined too",
              len(errs2) == 1 and errs2[0].startswith("bad-event-line:"), f"{errs2}")
        # calibration: the SAME line with a DECLARED kind must move the count, or "excluded"
        # above would only prove the parser rejects everything.
        dk = core.derive(core.parse_events(["- 2026-09-01 born session=x",
                                            "- 2026-09-02 recurrence session=y held=no"])[0], t)
        check("C-42d calibration: a DECLARED kind still moves the count",
              dk["hits"] == 2, f"hits {dk['hits']}")

        # ---- held split + re-fold loop (2026-09-23; the five folded-but-recurring lessons) -----
        # after_last_fold is the ONE definition of "folded but recurring". The value a defect
        # would change is WHICH list a recurrence lands in, so the cases assert on the lists.
        F = "- 2026-09-02 fold → CLAUDE.md — r"
        post = core.after_last_fold(ev("- 2026-09-01 born session=x", F,
                                       "- 2026-09-03 recurrence session=y project=p held=yes — caught"))
        check("C-43a held=yes after the fold is CAUGHT, not escaped",
              len(post["caught"]) == 1 and post["escaped"] == [], f"{post}")
        post = core.after_last_fold(ev("- 2026-09-01 born session=x", F,
                                       "- 2026-09-03 recurrence session=y project=p held=no — escaped"))
        check("C-43b held=no after the fold is ESCAPED (the positive side of C-43a)",
              len(post["escaped"]) == 1 and post["caught"] == [], f"{post}")
        post = core.after_last_fold(ev("- 2026-09-01 born session=x", F,
                                       "- 2026-09-03 recurrence session=y project=p — no field"))
        check("C-43c a recurrence with no held field counts as escaped (a caught claim is never inferred)",
              len(post["escaped"]) == 1, f"{post}")
        post = core.after_last_fold(ev("- 2026-09-01 born session=x",
                                       "- 2026-09-02 recurrence session=y project=p held=no — before", F))
        check("C-43d a recurrence BEFORE the last fold is not after it",
              post == {"escaped": [], "caught": []}, f"{post}")
        e_c = core.parse_events(["- 2026-09-23 fold → rules/x.md — cause=wrong-layer; moved"])[0][0]
        check("C-43e a re-fold line keeps its target and exposes its cause",
              e_c["target"] == "rules/x.md" and e_c["cause"] == "wrong-layer", f"{e_c['target']!r} {e_c['cause']!r}")
        # CLI: the gate in cmd_event, on a temp store, both directions.
        rst = os.path.join(tmp, "refold")
        os.makedirs(rst)
        run("add", "--from", wfile(tmp, "dr.md", GOOD_DRAFT), "--store", rst, "--session", "s")
        run("event", "L-001", "--kind", "fold", "--target", "ops/40-maintenance.md §2a", "--note", "n", "--store", rst, "--session", "s")
        r = run("event", "L-001", "--kind", "recurrence", "--note", "x", "--store", rst, "--session", "s")
        check("C-44a recurrence without --held is refused", r.returncode == 2 and "--held" in (r.stdout + r.stderr), (r.stdout + r.stderr).strip()[:90])
        r = run("event", "L-001", "--kind", "recurrence", "--held", "yes", "--note", "x", "--store", rst, "--session", "s")
        check("C-44b held=yes on a folded record says the fold held", r.returncode == 0 and "caught" in r.stdout, r.stdout.strip()[:90])
        r = run("event", "L-001", "--kind", "fold", "--target", "CLAUDE.md", "--cause", "wrong-layer", "--note", "n",
                "--store", rst, "--session", "s")
        check("C-44c re-fold with only CAUGHT recurrences is refused", r.returncode == 2 and "ILLEGAL" in (r.stdout + r.stderr), (r.stdout + r.stderr).strip()[:90])
        rep = run("report", "--store", rst).stdout
        check("C-44d caught-only record is in (b') and NOT in (b)",
              "(b') folded, recurred, caught (held=yes only — the fold held): ['L-001']" in rep
              and "(b) folded but recurring (held=no since the last fold): -" in rep, rep.replace("\n", " | ")[:140])
        run("event", "L-001", "--kind", "recurrence", "--held", "no", "--note", "x", "--store", rst, "--session", "s")
        rep = run("report", "--store", rst).stdout
        check("C-44e an escaped recurrence puts it in (b) (positive side of C-44d)",
              "(b) folded but recurring (held=no since the last fold): ['L-001']" in rep, rep.replace("\n", " | ")[:140])
        r = run("event", "L-001", "--kind", "fold", "--target", "CLAUDE.md", "--note", "n", "--store", rst, "--session", "s")
        check("C-44f re-fold without --cause is refused", r.returncode == 2 and "--cause" in (r.stdout + r.stderr), (r.stdout + r.stderr).strip()[:90])
        r = run("event", "L-001", "--kind", "fold", "--target", "CLAUDE.md", "--cause", "wrong-layer", "--note", "the rule owns it",
                "--store", rst, "--session", "s")
        rep = run("report", "--store", rst).stdout
        body = open(os.path.join(rst, "L-001.md"), encoding="utf-8").read()
        check("C-44g an admitted re-fold clears (b) and records cause + reason",
              r.returncode == 0 and "(b) folded but recurring (held=no since the last fold): -" in rep
              and "fold → CLAUDE.md — cause=wrong-layer; the rule owns it" in body, (r.stdout + r.stderr).strip()[:90])
        r = run("event", "L-001", "--kind", "fold", "--target", "ops/40-maintenance.md §2a", "--cause", "wrong-layer", "--note", "n",
                "--store", rst, "--session", "s")
        check("C-44h a second re-fold with no new escape is refused (the loop needs fresh evidence)",
              r.returncode == 2, (r.stdout + r.stderr).strip()[:90])
        r = run("event", "L-001", "--kind", "recurrence", "--held", "no", "--cause", "inert-text", "--store", rst, "--session", "s")
        check("C-44i --cause outside a fold is refused", r.returncode == 2, (r.stdout + r.stderr).strip()[:90])

        # ---- INV-2 via event + check --against HEAD (git repo in tmp) --------------------
        git = lambda *a: subprocess.run(["git", *a], cwd=tmp, capture_output=True, text=True)
        # build a mini repo whose HEAD holds the store, then mutate
        git("init", "-q"); git("config", "user.email", "c@t"); git("config", "user.name", "ctl")
        git("add", "store"); git("commit", "-qm", "base")
        # monkeypatch HOME for check via env: intake.py uses its own HOME; emulate with a copy of the check logic
        import intake as ik
        ik.HOME = tmp
        r = run("event", "L-001", "--kind", "recurrence", "--held", "yes", "--note", "again", "--store", store, "--session", "abcdef12")
        check("C-20a", r.returncode == 0 and "hits 2" in r.stdout, r.stdout.strip()[:80])
        v = ik.check_store(store, True, None, vocab)
        check("C-20", v == [], f"tool-driven event passes check: {v[:1]}")
        p1 = os.path.join(store, "L-001.md")
        orig = open(p1, encoding="utf-8").read()
        with open(p1, "w", encoding="utf-8", newline="\n") as f:
            f.write(orig.replace("A test context line.", "A CHANGED context line."))
        v = ik.check_store(store, True, None, vocab)
        check("C-21", any("Context changed" in x for x in v), str(v[:1]))
        with open(p1, "w", encoding="utf-8", newline="\n") as f:
            f.write(orig.replace("status: live", "status: spent"))
        v = ik.check_store(store, True, None, vocab)
        check("C-22", any("inconsistent" in x for x in v), str(v[:1]))
        with open(p1, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(orig.split("\n")[:-3]) + "\n")   # drop the last event line
        v = ik.check_store(store, True, None, vocab)
        check("C-23", any("append-only" in x or "first event" in x or "hits" in x for x in v), str(v[:1]))
        with open(p1, "w", encoding="utf-8", newline="\n") as f:
            f.write(orig)
        check("C-40", core.validate_draft(draft(**{"A test context line.": "hits: 2"}), vocab)[0][0] == "D8")

        # ---- INV-3 concurrent allocation ---------------------------------------------------
        st2 = os.path.join(tmp, "race")
        os.makedirs(st2)
        dpath = wfile(tmp, "race.md", GOOD_DRAFT)
        procs = [subprocess.Popen([PY, INTAKE, "add", "--from", dpath, "--store", st2, "--session", "s"],
                                  cwd=HOME, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(20)]
        rcs = [p.wait() for p in procs]
        files = sorted(f for f in os.listdir(st2) if f.endswith(".md"))
        check("C-30", rcs.count(0) == 20 and len(files) == 20 and len(set(files)) == 20, f"rc0={rcs.count(0)} files={len(files)}")

        # ---- INV-5 render idempotence ------------------------------------------------------
        items = ik.store_items(store)
        a1 = core.render_index(items, t, generated_at="X"); a2 = core.render_index(items, t, generated_at="X")
        check("C-50", a1 == a2 and "generated-from:" in a1)
        idx = os.path.join(tmp, "index.md")
        r = run("render", "--store", store, "--out", idx)
        with open(idx, "a", encoding="utf-8") as f:
            f.write("\nhand edit\n")
        v = ik.check_store(store, False, idx, vocab)
        check("C-51", any("INV-5" in x for x in v), str(v[:1]))

        # ---- INV-7 match budgets (property) -------------------------------------------------
        try:
            from hypothesis import given, settings, strategies as stt
            @settings(max_examples=200, deadline=None)
            @given(stt.integers(1, 5), stt.integers(200, 3000), stt.lists(stt.sampled_from(["shell", "verify", "env"]), min_size=1, max_size=3))
            def prop(bc, bb, words):
                res = core.match(items, " ".join(words), None, bc, bb, t)
                assert len(res) <= bc and sum(len(c.encode()) for _, _, c in res) <= bb
                assert all(c.startswith("## " + rid) for rid, _, c in res)
            prop(); check("C-70", True, "hypothesis 200 examples")
        except ImportError:
            skip("C-70", "hypothesis not importable")
        res = core.match(items, "a prompt mentioning shell transport", None, 3, 1500, t)
        check("C-71p", bool(res) and res[0][0] == "L-001", f"positive match → {[r for r,_,_ in res]}")
        res = core.match(items, "nothing relevant here at all", None, 3, 1500, t)
        check("C-71n", res == [], "negative match → empty")
        proj = core.parse_record(items[0][1])["record"].get("project", "")
        res = core.match(items, "nothing relevant here at all", proj, 3, 1500, t)
        check("C-71q", res == [], f"no tag words + matching project {proj!r} → empty (bonus is not a qualifier)")
        if proj and proj != "-":
            res = core.match(items, "", proj, 3, 1500, t)
            check("C-71r", bool(res) and all(core.parse_record(dict(items)[r])["record"].get("project", "") == proj for r, _, _ in res),
                  f"empty text + project → the project's cards {[r for r,_,_ in res]}")
        else:
            skip("C-71r", "fixture records carry no project")

        # ---- INV-8 import against the REAL legacy files into a temp store ------------------------
        st3 = os.path.join(tmp, "import")
        r = run("import", "--legacy-cards", os.path.join(HOME, "ops", "lessons.md"),
                "--legacy-detail", os.path.join(HOME, "ops", "references", "lessons-detail.md"), "--store", st3, "--verify")
        n = len([f for f in os.listdir(st3) if f.endswith(".md")]) if os.path.isdir(st3) else 0
        check("C-80", r.returncode == 0 and n >= 50, f"rc={r.returncode} records={n} {r.stdout.strip().split(chr(10))[-1][:70]}")
        v = ik.check_store(st3, False, None, vocab | set())
        check("C-80b", v == [], f"imported store passes check: {v[:2]}")
        # tampered source → verify fails
        tam = os.path.join(tmp, "tampered-detail.md")
        src = open(os.path.join(HOME, "ops", "references", "lessons-detail.md"), encoding="utf-8").read()
        with open(tam, "w", encoding="utf-8", newline="\n") as f:
            f.write(src.replace("## L-011 ", "## L-011 TAMPERED ", 1))
        r = run("import", "--legacy-cards", os.path.join(HOME, "ops", "lessons.md"), "--legacy-detail", tam, "--store", st3, "--verify", "--force")
        check("C-81", r.returncode == 4, f"tampered source → rc {r.returncode}")

        # ---- lock liveness ---------------------------------------------------------------------
        lk = os.path.join(store, "L-001.lock")
        with open(lk, "w") as f:
            f.write("1 0\n")
        os.utime(lk, (time.time() - 20, time.time() - 20))
        r = run("event", "L-001", "--kind", "recurrence", "--held", "no", "--store", store, "--session", "s")
        check("C-95", r.returncode == 0 and "stale lock broken" in r.stdout, r.stdout.strip()[:80])
        with open(lk, "w") as f:
            f.write("1 0\n")
        t0 = time.monotonic()
        r = run("event", "L-001", "--kind", "recurrence", "--held", "no", "--store", store, "--session", "s")
        check("C-96", r.returncode == 3 and time.monotonic() - t0 >= 1.5, f"fresh lock → rc {r.returncode} after {time.monotonic()-t0:.1f}s")
        os.remove(lk)

        # ---- INV-9 guard hook ------------------------------------------------------------------
        if os.path.isfile(GUARD):
            # The guard resolves its store from CLAUDE_CONFIG_DIR (else ~/.claude),
            # and these cases used to build their paths from HOME, the checkout
            # this file happens to live in. The two coincide in the canonical tree
            # and NOWHERE ELSE: run the suite from a linked worktree and C-90 was
            # asking whether a write to the worktree's ops/lessons is denied by a
            # guard pointed at the canonical one. Passing or failing, it was not
            # measuring path resolution -- it was measuring where it was run
            # from (L-047: a predicate that is a POSITION). Both sides now come
            # from `fake`, so the case states the property: a write under the
            # store THIS CONFIGURATION resolves to is denied.
            fake = os.path.join(tmp, "fakehome")
            elsewhere = os.path.join(tmp, "otherco")
            for d in (os.path.join(fake, "ops", "lessons"),
                      os.path.join(elsewhere, "ops", "lessons")):
                os.makedirs(d, exist_ok=True)
            real_tele = os.path.join(HOME, "telemetry", "intake-guard.jsonl")
            tele_before = os.path.getsize(real_tele) if os.path.isfile(real_tele) else -1
            genv = dict(os.environ, INTAKE_GUARD_LOG=os.path.join(tmp, "intake-guard.jsonl"),
                        CLAUDE_CONFIG_DIR=fake)

            def hook(tool, inp):
                payload = json.dumps({"tool_name": tool, "tool_input": inp, "cwd": fake, "session_id": "ctl"})
                r = subprocess.run([PY, GUARD], input=payload, capture_output=True, text=True, cwd=fake, env=genv)
                return r.stdout
            deny = lambda out: '"deny"' in out
            check("C-90", deny(hook("Write", {"file_path": os.path.join(fake, "ops", "lessons", "L-999.md"), "content": "x"})))
            check("C-90b", deny(hook("Edit", {"file_path": os.path.join(fake, "ops", "lessons.md"), "old_string": "a", "new_string": "b"})))
            # The declared "target is elsewhere" branch, and the discriminator for
            # the two above: an identically-SHAPED path under another root must
            # pass. Without it, a guard matching on the suffix alone would look
            # exactly as green as one that resolves the root.
            check("C-90c", not deny(hook("Write", {"file_path": os.path.join(elsewhere, "ops", "lessons", "L-999.md"), "content": "x"})))
            check("C-91", not deny(hook("Write", {"file_path": os.path.join(tmp, "draft.md"), "content": "x"})))
            check("C-92", deny(hook("Bash", {"command": "echo x >> ops/lessons/L-011.md"})))
            check("C-92b", deny(hook("PowerShell", {"command": "Add-Content ops\\lessons.md 'x'"})))
            check("C-93", not deny(hook("Bash", {"command": "python tools/closeout-intake/intake.py add --from d.md"})))
            check("C-93b", not deny(hook("Bash", {"command": "grep -n L-011 ops/lessons.md"})))
            # 2026-09-22 narrowing (FALSE-POSITIVE LOG, 5 observed): the inline-script rule now needs a
            # write verb in the script text. C-93c/d are the observed misfire shapes (MUST-PASS);
            # C-92c/d keep the rule's teeth (MUST-DENY: an inline script that writes into the store).
            check("C-93c", not deny(hook("Bash", {"command": "python - <<'EOF'\nprint(open('ops/lessons.md','rb').read().count(b'\\r\\n'))\nEOF"})))
            check("C-93d", not deny(hook("Bash", {"command": "printf '%s' 'python - <<EOF see ops/lessons.md EOF' | python hooks/other.py"})))
            check("C-92c", deny(hook("Bash", {"command": "python - <<'EOF'\nfrom pathlib import Path\nPath('ops/lessons/L-011.md').write_text('x')\nEOF"})))
            check("C-92d", deny(hook("Bash", {"command": "python - <<'EOF'\nopen('ops/lessons.md','a').write('x')\nEOF"})))
            # Isolation, measured the same way the model-cap suite measures it.
            # Until CLAUDE_CONFIG_DIR was pinned above, every run of this file
            # appended four synthetic deny receipts to the LIVE telemetry -- 724
            # bytes a run, indistinguishable from real denials in the file that
            # report_fp.py reads as the denominator for the misfire rate.
            tele_after = os.path.getsize(real_tele) if os.path.isfile(real_tele) else -1
            check("C-90t", tele_before == tele_after,
                  f"live telemetry {tele_before} -> {tele_after} bytes")
        else:
            for cid in ("C-90", "C-91", "C-92", "C-93"):
                skip(cid, "hooks/intake_guard.py not built yet (M2)")

        # ---- S-8 shadow match hook (M3): prints nothing, logs one row per prompt --------------
        if os.path.isfile(MATCH_HOOK):
            mlog = os.path.join(tmp, "intake-match.jsonl")
            menv = dict(os.environ, INTAKE_MATCH_LOG=mlog, INTAKE_MATCH_STORE=store)

            def mhook(prompt):
                payload = json.dumps({"prompt": prompt, "cwd": HOME, "session_id": "ctl"})
                r = subprocess.run([PY, MATCH_HOOK], input=payload, capture_output=True, text=True, cwd=HOME, env=menv)
                rows = []
                if os.path.isfile(mlog):
                    with open(mlog, encoding="utf-8") as f:
                        rows = [json.loads(ln) for ln in f if ln.strip()]
                return r.stdout, rows[-1] if rows else None
            out, row = mhook("a prompt mentioning shell transport and nothing else")
            check("C-72p", out == "" and row is not None and row.get("n_cards", 0) >= 1 and "L-001" in row.get("ids", []),
                  f"positive prompt → stdout {out!r}, row {row}")
            out, row = mhook("nothing relevant here at all, truly")
            check("C-72n", out == "" and row is not None and row.get("n_cards") == 0, f"negative prompt → row {row}")
            out, row2 = mhook("hi")
            check("C-72s", out == "" and row2 == row, "short prompt → no row, no output")
        else:
            for cid in ("C-72p", "C-72n", "C-72s"):
                skip(cid, "hooks/intake_match_shadow.py not built yet (M3)")

        # ---- session resolution: this process's env id beats the shared pointer ---------------
        # Ported from ledger.py 2026-09-07. The pointer is one GLOBAL file every session
        # overwrites, so under concurrency it is fresh, correct, and somebody else's — and a
        # record is never rewritten, so a wrong `session:` is permanent. The positive control
        # only means something if the pointer really disagrees, so C-97 sets it to a DIFFERENT id.
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("intake_cli_ctl", INTAKE)
        _cli = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_cli)
        MINE = "11111111-2222-3333-4444-555555555555"
        OTHER = "99999999-8888-7777-6666-555555555555"
        _cli.SESSION_FILE = wfile(tmp, "current-session.json", json.dumps({"session": OTHER}))
        _saved = os.environ.get("CLAUDE_CODE_SESSION_ID")
        try:
            os.environ["CLAUDE_CODE_SESSION_ID"] = MINE
            sid, warn = _cli.session_id("auto")
            check("C-97", sid == MINE and warn is not None and OTHER[:8] in warn,
                  f"env beats a disagreeing pointer → {sid[:8]}, warned={warn is not None}")
            os.environ.pop("CLAUDE_CODE_SESSION_ID")
            check("C-98", _cli.session_id("auto")[0] == OTHER, "env unset → pointer fallback")
            os.environ["CLAUDE_CODE_SESSION_ID"] = "not-a-uuid"
            check("C-98b", _cli.session_id("auto")[0] == OTHER, "junk env → pointer fallback")
            os.environ["CLAUDE_CODE_SESSION_ID"] = MINE
            check("C-99", _cli.session_id(OTHER)[0] == OTHER, "explicit --session wins over env")
        finally:
            if _saved is None:
                os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            else:
                os.environ["CLAUDE_CODE_SESSION_ID"] = _saved
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
    fails = [c for c, ok, _ in RESULTS if not ok]
    n = len(RESULTS)
    if fails:
        print(f"FAILED {len(fails)}/{n}: {', '.join(fails)}")
        return 1
    if SKIPPED:
        print(f"PASS {n}/{n} (skipped {len(SKIPPED)}: {', '.join(c for c, _ in SKIPPED)})")
        return 0
    print(f"ALL PASS {n}/{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
