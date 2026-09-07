#!/usr/bin/env python3
r"""reflux — the ONE sanctioned write path back into the literature-search-extract loop.

Design of record: ~/.claude/references/lse-feedback-loop-design.md §3.7 (INV-6, INV-11, D-L8),
decision table §3.7.2 (rows 1, 2, 3, 3b, 4, 5, 6, 7, 7b, 8, 8b, 9 — `decide()` below IS that
table; `test_reflux.py` has one test per row).

  python reflux.py <kind> --actor ID [--run-id R] [--claim-id C] [--key K] [--artifact A]
                          [--evidence E] [--note N] [--json]
      kind = consumed | correction | retraction | handoff | rerun
  python reflux.py --selftest        two-sided: an accepted event and a rejected one, on a temp home

Validation is fail-closed: the event is checked against event.schema.json AND the semantic
rules (§3.7.1) BEFORE anything is written; a rejected event prints its reason and appends
nothing. Events are append-only — never edited, never deleted; a wrong event is answered by a
later event. The file is not OS-protected: the single-user trust assumption is stated in the
design (SG-1); a second concurrent writer is the trigger for SQLite (D-L8).
Exit: 0 appended, 2 rejected, 1 usage/environment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import secrets
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import idkey  # noqa: E402
import runs   # noqa: E402

KINDS = ("consumed", "correction", "retraction", "handoff", "rerun")
INDEXED = ("delivered", "invalidated", "superseded")


def decide(kind: str, resolves: bool, in_ledger: bool, state: str | None) -> tuple[str, str]:
    """The §3.7.2 decision table as a pure function -> (row id, action)."""
    if not resolves:
        return ("1", "REJECT")
    if kind == "consumed":
        return ("2", "append")
    if kind == "correction":
        if in_ledger:
            return ("3", "invalidate") if state == "delivered" else ("3b", "annotate")
        return ("4", "annotate")
    if kind == "retraction":
        if in_ledger:                       # ≥1 run cites the key; per-run handling in apply()
            return ("5", "invalidate-per-run")
        return ("6", "append-empty")
    if kind == "handoff":
        return ("7", "append") if state == "delivered" else ("7b", "annotate")
    if kind == "rerun":
        if state in ("delivered", "invalidated"):
            return ("8", "supersede")
        return ("8b", "annotate")
    return ("9", "REJECT")


def new_event(kind, actor, run_id=None, claim_id=None, key=None, artifact=None, evidence=None, note=None) -> dict:
    return {"event_id": dt.datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(3),
            "at": runs.now_iso(), "kind": kind, "actor": actor, "run_id": run_id or None,
            "claim_id": claim_id or None, "key": key or None, "artifact": artifact or None,
            "evidence": evidence or None, "note": note or None}


def _index_entry(idx: dict, run_id: str) -> dict | None:
    for e in idx["entries"]:
        if e["run_id"] == run_id:
            return e
    return None


def _key_in_run(run_dir: Path, key: str, claim_id: str | None) -> bool:
    for row in runs.ledger_rows(run_dir):
        if claim_id and row.get("claim_id") == claim_id:
            return True
        if runs.row_key(row) == key:
            return True
    return False


def append_event(home: Path, ev: dict) -> dict:
    """Validate, decide, apply, append. Returns the stored event (with decision + affected).
    Raises ValueError with the reason on rejection (nothing written)."""
    errs = runs.validate(ev, "event")
    if errs:
        raise ValueError("schema: " + "; ".join(errs))
    kind = ev["kind"]
    if ev.get("key") and not idkey.is_key(ev["key"]):
        r = idkey.key_from_identifier(ev["key"])
        if not r:
            raise ValueError(f"key does not parse: {ev['key']!r}")
        ev["key"] = r[1]
    if kind in ("correction", "retraction") and not ev.get("evidence"):
        raise ValueError(f"{kind} requires evidence (a locator / notice URL / Crossref update-to)")
    if kind == "handoff" and not (ev.get("key") and ev.get("note")):
        raise ValueError("handoff requires key and note")
    if kind == "rerun" and not (ev.get("run_id") and ev.get("artifact")):
        raise ValueError("rerun requires run_id (old) and artifact (new run_id)")
    idx = runs.load_index(home)
    targets: list[dict] = []
    if ev.get("run_id"):
        e = _index_entry(idx, ev["run_id"])
        if not e or e.get("state") not in INDEXED:
            raise ValueError(f"run_id {ev['run_id']} does not resolve (not indexed — runs are indexed at deliver "
                             "when filed, or by adopt; INV-6)")
        targets = [e]
    elif ev.get("key"):
        targets = [e for e in idx["entries"] if ev["key"] in (e.get("keys") or [])
                   or _key_in_run(Path(e["path"]), ev["key"], None)]
    if kind == "rerun":
        new = _index_entry(idx, ev["artifact"])
        if not new or new.get("state") not in INDEXED:
            raise ValueError(f"rerun: new run {ev['artifact']} is not indexed")
        new_run = runs.load_run(Path(new["path"]))
        if new_run["run"].get("wasRevisionOf") != ev["run_id"]:
            raise ValueError(f"rerun: new run {ev['artifact']} does not declare wasRevisionOf={ev['run_id']}")
    # decide per target
    affected = []
    if kind == "retraction":
        row, action = decide(kind, True, bool(targets), None)
    elif kind == "consumed" and not targets:
        row, action = decide(kind, False, False, None)
    else:
        if not targets:
            row, action = decide(kind, False, False, None)
        else:
            row, action = decide(kind, True, _key_in_run(Path(targets[0]["path"]), ev.get("key") or "", ev.get("claim_id")),
                                 targets[0].get("state"))
    if action == "REJECT":
        raise ValueError(f"decision row {row}: target does not resolve (no indexed run cites this target)")
    # PLAN pass — pure: decide per target, touch nothing (build-verification B-1: write-ahead order)
    plan, affected = [], []
    for e in targets:
        run_dir = Path(e["path"])
        run = runs.load_run(run_dir)
        st = run["run"]["state"]
        in_ledger = _key_in_run(run_dir, ev.get("key") or "", ev.get("claim_id"))
        prow, paction = decide(kind, True, in_ledger, st)
        claims = [r.get("claim_id") for r in runs.ledger_rows(run_dir)
                  if (ev.get("claim_id") and r.get("claim_id") == ev["claim_id"]) or runs.row_key(r) == ev.get("key")]
        claims = [c for c in claims if c]
        if paction in ("invalidate", "invalidate-per-run") and st == "delivered" and in_ledger:
            step = ("invalidate", claims)
            affected.append({"run_id": e["run_id"], "row": prow, "state": "invalidated", "claims": claims})
        elif paction == "supersede":
            step = ("supersede", [])
            affected.append({"run_id": e["run_id"], "row": prow, "state": "superseded", "successor": ev["artifact"]})
        else:
            # annotate: a correction/retraction landing on an already invalidated/superseded run, or on a
            # background source, records the event id in invalidation.claims[] (B-7: retraction included)
            annotate = kind in ("correction", "retraction") and paction in ("annotate", "invalidate", "invalidate-per-run")
            step = ("annotate", [ev["event_id"]] if annotate else [])
            affected.append({"run_id": e["run_id"], "row": prow, "state": st, "note": paction})
        plan.append((e, run_dir, run, st, step))
    # APPEND first — the log is the only truth (INV-6); derived views follow it, never precede it
    stored = dict(ev, decision=row, affected=affected)
    with (home / "reflux.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stored, ensure_ascii=False) + "\n")
    # APPLY pass — derived views (run.json, record.md, index, README). A crash here leaves the log AHEAD of
    # the views, which the log-driven `runs.py affected` tolerates; the old order left dangling pointers.
    for e, run_dir, run, st, (action, payload) in plan:
        if action == "invalidate":
            run["run"]["state"] = "invalidated"
            run["invalidation"]["wasInvalidatedBy"] = ev["event_id"]
            run["invalidation"]["invalidatedAtTime"] = ev["at"]
            run["invalidation"]["claims"] = sorted(set(run["invalidation"]["claims"] + payload))
        elif action == "supersede":
            run["run"]["state"] = "superseded"
        else:
            run["invalidation"]["claims"] = sorted(set(run["invalidation"]["claims"] + payload))
        runs.save_run(run_dir, run)
        if Path(run_dir, "record.md").exists() or st != "open":
            Path(run_dir, "record.md").write_text(runs.record_md(run, run_dir), encoding="utf-8")
        e["state"] = run["run"]["state"]
    if targets:
        runs.save_index(home, idx)
        runs.write_readme(home, idx)
    return stored


def selftest() -> int:
    """Two-sided calibration on a temp home: must-REJECT/HOLD cases and must-ACCEPT cases are two lists;
    an empty side (a missing fixture) prints ONE-SIDED and refuses to report (build-verification B-6)."""
    import os
    import shutil
    import tempfile
    good = HERE / "tests" / "fixtures" / "good-run"
    if not (good / "run.json").exists() or not (good / "ledger.jsonl").exists():
        print("ONE-SIDED — fixtures/good-run is missing; refusing to report")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="lse-reflux-"))
    try:
        (tmp / "literature").mkdir()
        os.environ["LSE_RUN_HOME"] = str(tmp / "literature" / "EvidenceRuns")
        h = runs.home()
        runs.cmd_init(argparse.Namespace())
        run_dir = h / "20260101_selftest"
        run_dir.mkdir()
        for name in ("run.json", "ledger.jsonl", "citecheck.json"):
            shutil.copy(good / name, run_dir / name)
        (run_dir / "sources").mkdir()
        run = runs.load_run(run_dir)
        run["run"]["id"], run["run"]["home"], run["run"]["state"] = "20260101_selftest", str(h), "checked"
        runs.save_run(run_dir, run)
        if runs.cmd_register(argparse.Namespace(run_dir=str(run_dir))) != 0:
            print("ONE-SIDED — the good fixture did not register; refusing to report")
            return 2
        key = runs.load_run(run_dir)["keys"][0]
        size = lambda: (h / "reflux.jsonl").stat().st_size  # noqa: E731

        def reject_forged():
            before = size()
            try:
                append_event(h, new_event("consumed", "selftest", run_id="20260101_nonexistent", artifact="x"))
                return False
            except ValueError:
                return size() == before

        def reject_no_evidence():
            before = size()
            try:
                append_event(h, new_event("correction", "selftest", run_id="20260101_selftest", key=key))
                return False
            except ValueError:
                return size() == before

        def accept_consumed():
            return append_event(h, new_event("consumed", "selftest", run_id="20260101_selftest", artifact="row#1"))["decision"] == "2"

        def accept_correction_invalidates():
            ev = append_event(h, new_event("correction", "selftest", run_id="20260101_selftest", key=key,
                                           evidence="selftest: locator", note="span was wrong"))
            return ev["decision"] == "3" and runs.load_run(run_dir)["run"]["state"] == "invalidated"

        def accept_retraction_uncited():
            ev = append_event(h, new_event("retraction", "selftest", key="doi:10.9999/nobody-cites-this", evidence="n"))
            return ev["decision"] == "6" and ev["affected"] == []

        must_reject = [("forged run_id rejected, log unchanged", reject_forged),
                       ("correction without evidence rejected, log unchanged", reject_no_evidence)]
        must_accept = [("consumed -> row 2", accept_consumed),
                       ("correction on ledger key -> row 3, run invalidated", accept_correction_invalidates),
                       ("retraction of an uncited key -> row 6, affected []", accept_retraction_uncited)]
        if not must_reject or not must_accept:
            print("ONE-SIDED — refusing to report")
            return 2
        broken = 0
        for label, fn in must_reject:
            ok = fn()
            print(f"{'ok' if ok else 'BROKEN':7} must-REJECT {label}")
            broken += (not ok)
        for label, fn in must_accept:
            ok = fn()
            print(f"{'ok' if ok else 'BROKEN':7} must-ACCEPT {label}")
            broken += (not ok)
        print(f"{len(must_reject) + len(must_accept)} cases ({len(must_reject)} must-reject / {len(must_accept)} must-accept), "
              f"{broken} broken — {'calibrated' if not broken else 'BROKEN instrument'}")
        return 0 if not broken else 2
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("LSE_RUN_HOME", None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("kind", nargs="?", choices=KINDS)
    ap.add_argument("--actor")
    ap.add_argument("--run-id", dest="run_id", default=None)
    ap.add_argument("--claim-id", dest="claim_id", default=None)
    ap.add_argument("--key", default=None)
    ap.add_argument("--artifact", default=None)
    ap.add_argument("--evidence", default=None)
    ap.add_argument("--note", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.kind or not a.actor:
        ap.print_help()
        return 1
    h = runs.home()
    if not (h / "index.json").exists():
        print(f"REJECTED: no index at {h} — nothing to point at (run `runs.py init`)")
        return 2
    ev = new_event(a.kind, a.actor, a.run_id, a.claim_id, a.key, a.artifact, a.evidence, a.note)
    try:
        stored = append_event(h, ev)
    except ValueError as e:
        print(f"REJECTED ({a.kind}): {e} — nothing appended")
        return 2
    if a.json:
        print(json.dumps(stored, ensure_ascii=False, indent=1))
    else:
        print(f"appended {stored['event_id']} kind={stored['kind']} row={stored['decision']} affected={len(stored['affected'])}")
        for x in stored["affected"]:
            print(f"  - {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
