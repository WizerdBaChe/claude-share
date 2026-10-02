#!/usr/bin/env python3
"""Fixture-home tests for routing-loop (PSM section 5, A-2..A-6, A-10).

Every test points ROUTING_LOOP_HOME at a temp tree holding a synthetic dict,
three skills, a copy of the real skill-routing-audit.py and hand-written
transcripts, so nothing here reads or writes the live ~/.claude. Status rules
are tested two-sided: each point has an input that must trip it (positive
control) and one that must not (negative control).

    python -X utf8 tools/routing-loop/tests/test_loop.py
"""
import datetime as dt
import importlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.dirname(HERE)
REAL_HOME = os.path.abspath(os.path.join(TOOL, "..", ".."))
# The audit is read from the canonical home when the tool runs from a linked
# worktree whose copy is identical; prefer the sibling in this checkout.
AUDIT_SRC = os.path.join(REAL_HOME, "tools", "skill-routing-audit.py")
if not os.path.isfile(AUDIT_SRC):  # share edition: the audit sits beside the tool dirs
    AUDIT_SRC = os.path.join(TOOL, "..", "skill-routing-audit.py")

DICT = """# dict
### workflow-checkpoint
- 關鍵詞：先到這邊
### skill-a
- 關鍵詞：畫架構圖
"""
SECRET = "這是一段不應該被寫進任何持久檔的使用者原話內容用來測試"
DENY = "Dispatch denied by model_cap_guard, a local PreToolUse hook"
DENY_OLD = "Model cost cap: `model` is required on Agent dispatch — subagent_type"


def rec_user(uuid, text, ts="2026-09-20T01:00:00Z"):
    return {"type": "user", "uuid": uuid, "timestamp": ts,
            "message": {"role": "user", "content": text}}


def rec_tool_result(uuid, tid, text, ts="2026-09-20T01:00:00Z"):
    return {"type": "user", "uuid": uuid, "timestamp": ts,
            "toolUseResult": {}, "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": text}]}}


def rec_asst(uuid, blocks=(), ts="2026-09-20T01:00:01Z"):
    return {"type": "assistant", "uuid": uuid, "timestamp": ts,
            "message": {"role": "assistant",
                        "content": list(blocks) or [{"type": "text", "text": "ok"}]}}


def skill(name, tid):
    return {"type": "tool_use", "name": "Skill", "id": tid,
            "input": {"skill": name}}


def agent(tid, model=None, agent_type="Explore"):
    inp = {"prompt": "x", "subagent_type": agent_type}
    if model:
        inp["model"] = model
    return {"type": "tool_use", "name": "Agent", "id": tid, "input": inp}


def session_main():
    r = []
    r.append(rec_user("u1", "好，今天先到這邊吧 " + SECRET))           # HIT
    r.append(rec_asst("a1", [skill("workflow-checkpoint", "t1")]))
    r.append(rec_user("u2", "幫我畫架構圖，謝謝"))                      # BYPASS -> other
    r.append(rec_asst("a2", [skill("other", "t2")]))
    r.append(rec_user("u3", "之後再畫架構圖也可以"))                     # MISS, LATE
    for i in range(6):
        r.append(rec_asst(f"a3{i}"))
    r.append(rec_asst("a4", [skill("skill-a", "t4")]))                # UNPREDICTED
    r.append(rec_asst("a4", [skill("skill-a", "t4")]))                # duplicate record
    r.append(rec_user("u5", "<command-name>/workflow-checkpoint</command-name>"))
    r.append(rec_user("u6", "<command-name>/compact</command-name>"))  # built-in: ignored
    r.append(rec_asst("a6", [agent("g1", "sonnet"), agent("g2"), agent("g3", "opus")]))
    r.append(rec_tool_result("r6", "g3", DENY + " (not file or page content)."))
    r.append(rec_asst("a8", [agent("g4", agent_type="code-reviewer"),
                             agent("g5", agent_type="general-purpose")]))
    r.append(rec_tool_result("r8", "g5", DENY_OLD + " 'general-purpose' has no local definition"))
    r.append(rec_asst("a9", [agent("g6", agent_type="no-such-local-agent")]))
    r.append(rec_asst("a7", [{"type": "tool_use", "name": "Bash", "id": "b1",
                              "input": {"command": "codex.exe exec -m gpt-6-luna \"hi\""}}]))
    return r


class Home:
    def __init__(self, sessions):
        # named `.claude` so the child processes' `~/.claude` lands here
        self.base = tempfile.mkdtemp(prefix="routing-loop-test-")
        self.root = os.path.join(self.base, ".claude")
        os.makedirs(os.path.join(self.root, "tools", "trigger-probe"))
        os.makedirs(os.path.join(self.root, "ops", "references"))
        shutil.copy(AUDIT_SRC, os.path.join(self.root, "tools",
                                            "skill-routing-audit.py"))
        with open(os.path.join(self.root, "skill-trigger-dict.md"), "w",
                  encoding="utf-8") as fh:
            fh.write(DICT)
        os.makedirs(os.path.join(self.root, "agents"))
        with open(os.path.join(self.root, "agents", "engineering-code-reviewer.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("---\nname: code-reviewer\nmodel: sonnet\n---\nbody\n")
        for s in ("workflow-checkpoint", "skill-a", "other"):
            os.makedirs(os.path.join(self.root, "skills", s))
            with open(os.path.join(self.root, "skills", s, "SKILL.md"), "w",
                      encoding="utf-8") as fh:
                fh.write(f"---\nname: {s}\ndescription: test\n---\n")
        proj = os.path.join(self.root, "projects", "P")
        os.makedirs(proj)
        for name, recs in sessions.items():
            with open(os.path.join(proj, name + ".jsonl"), "w",
                      encoding="utf-8") as fh:
                for r in recs:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.fake_probe(fails=5)

    def fake_probe(self, fails=5, broken=False):
        body = ("import sys\nsys.exit(3)\n" if broken else
                "import json\nprint('# report line')\n"
                "print(json.dumps({'suites': 1, 'probes': 9, 'verdicts': {},"
                f" 'fails': {fails}, 'scorer_version': 'lex-1',"
                " 'calibration_id': 'cal-x'}))\n")
        with open(os.path.join(self.root, "tools", "trigger-probe",
                               "trigger_probe.py"), "w", encoding="utf-8") as fh:
            fh.write(body)

    def load(self):
        os.environ["ROUTING_LOOP_HOME"] = self.root
        sys.path.insert(0, TOOL)
        import store, events, loop  # noqa: E401
        for m in (store, events, loop):
            importlib.reload(m)
        return store, events, loop


RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(f"{'PASS' if cond else 'FAIL'}  {name}{'  -- ' + str(detail) if detail and not cond else ''}")


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


def main():
    h = Home({"s-main": session_main()})
    store, events, loop = h.load()

    # ---- derivation outcomes
    evs, stats = events.derive()
    by = {}
    for e in evs:
        by.setdefault((e["node"], e["outcome"], e["subject"]), []).append(e)
    check("HIT: words + own skill fires", ("skill-route", "HIT", "workflow-checkpoint") in by)
    check("BYPASS: words for skill-a, other fires", ("skill-route", "BYPASS", "skill-a") in by)
    miss = by.get(("skill-route", "MISS", "skill-a"), [])
    check("MISS + LATE: skill-a fires past the window", len(miss) == 1 and miss[0]["late"])
    check("UNPREDICTED: thief fire and the late fire",
          len(by.get(("skill-route", "UNPREDICTED", "other"), [])) == 1
          and len(by.get(("skill-route", "UNPREDICTED", "skill-a"), [])) == 1)
    check("negative: an explained fire is NOT unpredicted",
          ("skill-route", "UNPREDICTED", "workflow-checkpoint") not in by)
    check("SLASH: /workflow-checkpoint recorded", ("skill-route", "SLASH", "workflow-checkpoint") in by)
    check("negative: built-in /compact not recorded",
          not any(e["subject"] == "compact" for e in evs))
    check("model EXPLICIT", ("model-route", "EXPLICIT", "sonnet") in by)
    check("model INHERITED", ("model-route", "INHERITED", "inherited") in by)
    check("model DENIED overrides EXPLICIT", ("model-route", "DENIED", "opus") in by
          and ("model-route", "EXPLICIT", "opus") not in by)
    check("model EXTERNAL codex", ("model-route", "EXTERNAL", "gpt-6-luna") in by)
    check("PINNED: omitted model on a frontmatter-pinned type",
          ("model-route", "PINNED", "sonnet") in by)
    check("DENIED via the older deny wording",
          any(e["outcome"] == "DENIED" and e["agent_type"] == "general-purpose" for e in evs))
    inh = by.get(("model-route", "INHERITED", "inherited"), [])
    check("negative: an unpinned type without model stays INHERITED",
          sorted(e["agent_type"] for e in inh) == ["Explore", "no-such-local-agent"],
          [e["agent_type"] for e in inh])
    check("duplicate record kept once", stats.get("dup_records") == 1, stats)

    # ---- INV-8 parity with the audit on the fixture
    a = events.load_audit()
    S, _, _, _ = a.scan(a.load_entries(), None)
    mine = events.counts_by_entry(evs)
    same = all(mine[k] == {"hit": S[k]["hit"], "bypass": sum(S[k]["bypass"].values()),
                           "miss": S[k]["miss"], "late": S[k]["late"]} for k in S)
    check("INV-8 parity with audit.scan()", same and set(S) <= set(mine) | set())

    # ---- A-2 stable ids, derive never touches labels
    rc, _ = quiet(loop.cmd_derive)
    ids1 = sorted(e["event_id"] for e in store.read_events())
    check("A-2 ids unique", len(ids1) == len(set(ids1)))
    q = next(e for e in store.read_events() if e["outcome"] == "MISS")
    store.add_label(q["event_id"], "should-fire", "test why")
    before = open(store.LABELS, encoding="utf-8").read()
    quiet(loop.cmd_derive)
    ids2 = sorted(e["event_id"] for e in store.read_events())
    check("A-2 ids stable across derive", ids1 == ids2)
    check("A-2 derive leaves labels untouched",
          open(store.LABELS, encoding="utf-8").read() == before)

    # ---- A-3 label states and validation
    latest = store.latest_labels()
    check("A-3 labelled event is judged", store.label_state(q, latest) == "judged")
    b = next(e for e in store.read_events() if e["outcome"] == "BYPASS")
    check("A-3 unlabelled BYPASS is queued", store.label_state(b, latest) == "queued")
    store.add_label(b["event_id"], "abstain", "unsure")
    check("A-3 abstain -> parked", store.label_state(b, store.latest_labels()) == "parked")
    store.add_label(q["event_id"], "abstain", "second thoughts")
    check("A-3 judged -> parked", store.label_state(q, store.latest_labels()) == "parked")
    rc, out = quiet(loop.main, ["queue", "--events", "--history", "--window", "0"])
    check("A-3 queue hides parked", b["event_id"] not in out)
    rc, out = quiet(loop.main, ["queue", "--events", "--all", "--history", "--window", "0"])
    check("A-3 queue --all shows parked", b["event_id"] in out)

    # ---- group judgments: one verdict covers the pattern, now and later
    un = [e for e in store.read_events() if e["outcome"] == "UNPREDICTED"]
    gid = store.group_id(store.group_key(un[0]))
    rc, out = quiet(loop.main, ["queue", "--history", "--window", "0"])
    check("group queue --history lists the UNPREDICTED group", gid in out)
    rc, out = quiet(loop.main, ["queue"])
    check("default queue hides pre-baseline groups (fixture 2026-09-20 < baseline)",
          gid not in out and out.startswith("0 pattern group"), out[:120])
    rc, out = quiet(loop.main, ["queue"])
    check("default queue hides pre-baseline groups (fixture 2026-09-20 < baseline)",
          gid not in out and out.startswith("0 pattern group"), out[:120])
    store.add_label(gid, "dict-gap", "vocabulary missing")
    L = store.latest_labels()
    same = [e for e in store.read_events()
            if store.group_id(store.group_key(e)) == gid]
    check("group label judges every member", same and all(
        store.label_state(e, L) == "judged" for e in same))
    future = dict(same[0], event_id="f" * 16, date="2027-01-01")
    check("group label covers a FUTURE event of the pattern",
          store.label_state(future, L) == "judged")
    other_group = [e for e in store.read_events() if e["needs_judgment"]
                   and store.group_id(store.group_key(e)) != gid
                   and store.label_state(e, L) == "queued"]
    check("negative: a group label does not leak to another group",
          len(other_group) >= 1)
    store.add_label(same[0]["event_id"], "abstain", "exception to the pattern")
    check("event label overrides its group label",
          store.label_state(same[0], store.latest_labels()) == "parked")
    rc, _ = quiet(loop.main, ["label", "g00000000000", "correct", "--why", "x"])
    check("unknown group id refused (exit 2)", rc == 2)
    rc, _ = quiet(loop.main, ["label", b["event_id"], "fit", "--why", "x"])
    check("A-3 verdict from the wrong node refused (exit 2)", rc == 2)
    rc, _ = quiet(loop.main, ["label", "deadbeefdeadbeef", "correct", "--why", "x"])
    check("A-3 unknown event_id refused (exit 2)", rc == 2)
    rc, _ = quiet(loop.main, ["label", "deadbeefdeadbeef", "correct", "--why", "x",
                              "--orphan-ok"])
    check("A-3 --orphan-ok accepted", rc == 0)
    s = store.label_state
    check("orphan counted", "deadbeefdeadbeef" in store.orphans(store.read_events(),
                                                                 store.latest_labels()))
    rc, _ = quiet(loop.main, ["label", b["event_id"], "correct", "--why", "  "])
    check("A-3 empty why refused", rc == 2)

    # ---- A-5 status before any run
    doc = loop.build_status()
    ids = [p["id"] for p in doc["points"]]
    check("A-5 all six points declared (never run)",
          ids == [f"routing-loop.{x}" for x in loop.POINTS], ids)
    fr = doc["points"][0]
    check("freshness never-run -> ran:true fail", fr["ran"] and fr["state"] == "fail")
    check("A-5 ran:false => state:null",
          all(p["state"] is None for p in doc["points"] if not p["ran"]))

    # ---- A-4 run: probe broken -> step failed, run still recorded
    h.fake_probe(broken=True)
    rc, out = quiet(loop.cmd_run)
    run = store.read_last_run()
    st = {x["step"]: x["state"] for x in run["steps"]}
    check("A-4 failing probe step recorded, run not aborted",
          st == {"derive": "ok", "audit-snapshot": "ok", "probe": "failed"}, st)
    check("A-4 telemetry line appended", len(store.previous_runs()) == 1)
    doc = loop.build_status()
    P = {p["id"].split(".", 1)[1]: p for p in doc["points"]}
    check("probe failed -> fail (positive)", P["probe"]["state"] == "fail")

    # ---- A-6 two-sided controls
    h.fake_probe(fails=5)
    quiet(loop.cmd_run)
    h.fake_probe(fails=7)
    quiet(loop.cmd_run)
    P = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    check("probe fails rose 5->7 -> warn (positive)", P["probe"]["state"] == "warn",
          P["probe"])
    h.fake_probe(fails=7)
    quiet(loop.cmd_run)
    P = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    check("probe fails flat 7->7 -> pass (negative)", P["probe"]["state"] == "pass")

    check("freshness fresh -> pass (negative)", P["freshness"]["state"] == "pass")
    later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=20)
    check("freshness 20 d -> warn", {p["id"]: p for p in loop.build_status(later)[
        "points"]}["routing-loop.freshness"]["state"] == "warn")
    later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=40)
    check("freshness 40 d -> fail (positive)", {p["id"]: p for p in loop.build_status(
        later)["points"]}["routing-loop.freshness"]["state"] == "fail")

    check("derive ok -> pass (negative)", P["derive"]["state"] == "pass")
    # baseline: the fixture's events are dated 2026-09-20. Asserted value is
    # the counted group number q (in the finding text), recorded both sides.
    def backlog_q(point):
        return int(re.match(r"(\d+) unjudged", point["findings"][0]["text"]).group(1))
    Pn = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    check("backlog small -> pass (negative)", Pn["skill-backlog"]["state"] == "pass")
    old_w, old_b = loop.BACKLOG_WARN, loop.BACKLOG_BASELINE
    loop.BACKLOG_WARN = 0
    loop.BACKLOG_BASELINE = "2026-09-01"          # fixture groups are post-baseline
    P2 = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    loop.BACKLOG_BASELINE = "2026-09-26"          # fixture groups are pre-baseline
    Pold = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    loop.BACKLOG_WARN, loop.BACKLOG_BASELINE = old_w, old_b
    q_new, q_old = backlog_q(P2["skill-backlog"]), backlog_q(Pold["skill-backlog"])
    check(f"backlog post-baseline groups counted -> warn (positive; q={q_new})",
          P2["skill-backlog"]["state"] == "warn" and q_new >= 1, P2["skill-backlog"])
    check(f"backlog pre-baseline groups not counted -> pass (negative; q={q_old}, "
          f"same data)", Pold["skill-backlog"]["state"] == "pass" and q_old == 0,
          Pold["skill-backlog"])
    check("backlog finding names the uncounted history",
          "pre-baseline history" in Pold["skill-backlog"]["findings"][0]["text"]
          and f"history {q_new} group" in Pold["skill-backlog"]["findings"][0]["text"],
          Pold["skill-backlog"]["findings"][0]["text"])
    # fixture: auto fires = HIT 1, BYPASS 1, UNPREDICTED 2 -> 50%
    check("unpredicted 50% -> warn (positive)", P["skill-unpredicted"]["state"] == "warn")
    old = loop.UNPREDICTED_WARN
    loop.UNPREDICTED_WARN = 0.9
    P3 = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    loop.UNPREDICTED_WARN = old
    check("unpredicted under threshold -> pass (negative)",
          P3["skill-unpredicted"]["state"] == "pass")
    # the fixture's INHERITED is dated 2026-09-20: inside a 30-day window from
    # 2026-10-01, outside from 2026-12-01
    t_in = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
    t_out = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc)
    pin = {p["id"]: p for p in loop.build_status(t_in)["points"]}
    pout = {p["id"]: p for p in loop.build_status(t_out)["points"]}
    check("inherited in window -> warn (positive)",
          pin["routing-loop.model-inherited"]["state"] == "warn")
    check("inherited out of window -> pass (negative)",
          pout["routing-loop.model-inherited"]["state"] == "pass")

    # derive failure: remove the audit -> derive step failed -> fail
    os.rename(store.AUDIT, store.AUDIT + ".gone")
    quiet(loop.cmd_run, probe=False, snapshot=False)
    os.rename(store.AUDIT + ".gone", store.AUDIT)
    P = {p["id"].split(".", 1)[1]: p for p in loop.build_status()["points"]}
    check("derive failed -> fail (positive)", P["derive"]["state"] == "fail")
    check("probe skipped -> ran:false", not P["probe"]["ran"]
          and P["probe"]["skip_reason"] == "skipped")

    # ---- A-5 JSON shape
    rc, out = quiet(loop.main, ["status", "--json"])
    doc = json.loads(out)
    check("A-5 protocol + source + tree", doc["protocol"] == "hmi-report/1"
          and doc["source"] == "routing-loop" and doc["tree"]["id"] == "routing-loop")

    # ---- A-10 no prompt text persisted
    leaked = []
    for path in (store.EVENTS, store.LAST_RUN, store.RUNS, store.LABELS):
        if os.path.exists(path) and SECRET[:20] in open(path, encoding="utf-8").read():
            leaked.append(path)
    check("A-10 no human-turn text in persisted files", not leaked, leaked)
    # positive control for the A-10 check itself: the secret IS in the corpus
    corpus = open(os.path.join(h.root, "projects", "P", "s-main.jsonl"),
                  encoding="utf-8").read()
    check("A-10 control: the secret exists in the corpus", SECRET[:20] in corpus)

    shutil.rmtree(h.base, ignore_errors=True)
    failed = [n for n, ok in RESULTS if not ok]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
