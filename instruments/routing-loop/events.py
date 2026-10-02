"""Derive routing events from the local transcripts.

skill-route: replays the SAME state machine as skill-routing-audit.scan()
(imported, not copied: INV-8 -- one parser, so the loop's HIT/BYPASS/MISS/LATE
can never drift from the audit's) and emits one event per scored candidate,
plus two outcomes the audit only counts in aggregate or not at all:
  UNPREDICTED  a skill fired and no dict vocabulary of THAT skill matched the
               turn that preceded it
  SLASH        the user invoked a skill by `/name` -- routing did not have to
               decide, which makes it a candidate for "routing never catches this"

model-route: every Agent/Task dispatch (EXPLICIT / INHERITED / DENIED) and
every codex or extdispatch call seen in a shell command (EXTERNAL). The shell
match is a heuristic; its version is part of the ruler.

No prompt text is written anywhere (INV-3): events carry pointers (session,
record uuid) and the dict token that matched.
"""
import importlib.util
import io
import json
import os
import re
from collections import defaultdict

import store

# Every wording model_cap_guard has used for a deny. A missing wording reads
# the deny as an INHERITED dispatch that ran: measured 2026-09-26, the 09-07
# denies used the older "Model cost cap:" text and 7 of them were misread.
DENY_MARKS = ("Dispatch denied by model_cap_guard",
              "Model cost cap: `model` is required")


def local_agent_models(home):
    """{subagent_type: model} from agents/*.md frontmatter, matched by `name:`
    and by file stem -- the same resolution model_cap_guard applies, so an
    omitted `model` on a pinned type is PINNED, not INHERITED."""
    out = {}
    d = os.path.join(home, "agents")
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if not fn.endswith(".md"):
            continue
        try:
            with io.open(os.path.join(d, fn), encoding="utf-8",
                         errors="replace") as fh:
                head = fh.read(4000)
        except OSError:
            continue
        if not head.startswith("---") or head.count("---") < 2:
            continue
        fm = head.split("---", 2)[1]
        model = re.search(r"^model:\s*(\S+)", fm, re.MULTILINE)
        if not model:
            continue
        m = model.group(1).strip().strip("'\"").lower()
        name = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
        out[fn[:-3]] = m
        if name:
            out[name.group(1)] = m
    return out
CODEX_RX = re.compile(r"codex(?:\.exe)?\"?\s[^\n]*?(?:-m|--model)\s+\"?([\w.\-]+)")
EXTDISPATCH_RX = re.compile(r"extdispatch\S*\s+(?:\S+\s+)?(query|dispatch)\b")


def load_audit():
    """Import tools/skill-routing-audit.py and re-point its module paths at
    HOME_CLAUDE (the module computes them at import from ~/.claude)."""
    spec = importlib.util.spec_from_file_location("skill_routing_audit",
                                                  store.AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.HOME = store.HOME_CLAUDE
    mod.DICT = os.path.join(store.HOME_CLAUDE, "skill-trigger-dict.md")
    mod.CLASSES = os.path.join(store.HOME_CLAUDE, "ops", "references",
                               "skill-trigger-classes.md")
    mod.SKILLS = os.path.join(store.HOME_CLAUDE, "skills")
    mod.PROJECTS = os.path.join(store.HOME_CLAUDE, "projects")
    return mod


def _slash_name(txt):
    m = re.search(r"<command-name>/?([^<]+)</command-name>", txt)
    return m.group(1).strip() if m else None


def _tool_results(rec):
    """Yield (tool_use_id, text) for tool_result blocks in a user record."""
    msg = rec.get("message")
    if not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
        return
    for b in msg["content"]:
        if not isinstance(b, dict) or b.get("type") != "tool_result":
            continue
        c = b.get("content")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        yield b.get("tool_use_id"), c if isinstance(c, str) else ""


def derive(since=None, audit=None):
    """Return (events, stats) where stats carries corpus counts for the run
    record. Deterministic: same corpus + same dict -> same event list."""
    a = audit or load_audit()
    entries = a.load_entries()
    classes = a.load_classes()
    pats = {s: a.compile_tokens(e["keywords"]) for s, e in entries.items()}
    avoid = {s: a.compile_tokens(e["avoid"]) for s, e in entries.items()}
    local = set()
    if os.path.isdir(a.SKILLS):
        local = {n for n in os.listdir(a.SKILLS)
                 if os.path.isfile(os.path.join(a.SKILLS, n, "SKILL.md"))}
    known = local | set(entries)
    pinned = local_agent_models(store.HOME_CLAUDE)

    events, stats = [], {"files": 0, "turns": 0, "parse_skipped": 0}

    def cls(skill):
        return (classes.get(skill) or {}).get("class")

    for dirpath, _, names in os.walk(a.PROJECTS):
        for name in sorted(names):
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(dirpath, name)
            session = name[:-6]
            stats["files"] += 1
            pending = None      # (cands, date, turn_uuid)
            seen_since = 0
            ev = 0
            session_miss = []   # (event index in `out`, skill, ev at MISS)
            session_fire = defaultdict(list)
            seen_turns = set()
            out = []
            agent_calls = {}    # tool_use_id -> index in out
            denied = set()
            try:
                fh = io.open(path, encoding="utf-8", errors="replace")
            except OSError:
                continue

            def close(pend, fired, fired_all):
                """Mirror audit.record(): one event per keyword candidate.
                Returns the set of skills whose fire this turn explained."""
                cands, date, tuuid = pend
                explained = set()
                kw = {c[0] for c in cands if c[2] != "avoid"}
                for skill, tok, kind, _exc in cands:
                    if kind == "avoid":
                        continue
                    if fired == skill:
                        outcome = "HIT"
                    elif fired:
                        outcome = "BYPASS"
                    else:
                        outcome = "MISS"
                    out.append({
                        "event_id": store.event_id("skill-route", session,
                                                   tuuid, skill),
                        "node": "skill-route", "date": date,
                        "session": session, "record_uuid": tuuid,
                        "subject": skill, "outcome": outcome, "late": False,
                        "token": tok, "fired": fired, "class": cls(skill),
                        "needs_judgment": outcome in store.NEEDS_JUDGMENT})
                    if outcome == "MISS":
                        session_miss.append((len(out) - 1, skill, ev))
                for f in fired_all:
                    if f in kw:
                        explained.add(f)
                return explained

            with fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except ValueError:
                        stats["parse_skipped"] += 1
                        continue
                    date = (rec.get("timestamp") or "")[:10]
                    if since and date and date < since:
                        continue
                    ruuid = rec.get("uuid") or ""

                    if rec.get("type") == "user":
                        for tid, text in _tool_results(rec):
                            if tid and any(m in (text or "") for m in DENY_MARKS):
                                denied.add(tid)
                        txt = a.human_text(rec)
                        if txt is None:
                            continue
                        if "<command-name>" in txt:
                            pending = None
                            sk = _slash_name(txt)
                            if sk and (sk in local or ":" in sk):
                                out.append({
                                    "event_id": store.event_id(
                                        "skill-route", session, ruuid, sk),
                                    "node": "skill-route", "date": date,
                                    "session": session, "record_uuid": ruuid,
                                    "subject": sk, "outcome": "SLASH",
                                    "late": False, "token": None,
                                    "fired": sk, "class": cls(sk),
                                    "needs_judgment": False})
                            continue
                        key = hash(txt)
                        if key in seen_turns:
                            pending = None
                            continue
                        seen_turns.add(key)
                        stats["turns"] += 1
                        cands = a.match_turn(txt, pats, avoid)
                        pending = (cands, date, ruuid) if cands else None
                        seen_since = 0
                        continue

                    if rec.get("isSidechain"):
                        continue
                    ev += 1
                    blocks = []
                    a.walk_tool_uses(rec.get("message"), blocks)
                    fired = [(b.get("input") or {}).get("skill")
                             for b in blocks if b.get("name") == "Skill"]
                    fired = [f for f in fired if f]
                    for f in fired:
                        session_fire[f].append(ev)

                    explained = set()
                    if pending is not None:
                        seen_since += 1
                        if fired:
                            explained = close(pending, fired[0], fired)
                            pending = None
                        elif seen_since >= a.LOOKAHEAD:
                            close(pending, None, [])
                            pending = None
                    for i, f in enumerate(fired):
                        if f in explained:
                            continue
                        ref = f"{ruuid}#skill{i}"
                        out.append({
                            "event_id": store.event_id("skill-route", session,
                                                       ref, f),
                            "node": "skill-route", "date": date,
                            "session": session, "record_uuid": ref,
                            "subject": f, "outcome": "UNPREDICTED",
                            "late": False, "token": None, "fired": f,
                            "class": cls(f), "needs_judgment": True})

                    for b in blocks:
                        _model_event(b, out, agent_calls, session, ruuid, pinned,
                                     date)
            if pending is not None:
                close(pending, None, [])
            for idx, skill, at in session_miss:
                if any(i > at for i in session_fire.get(skill, ())):
                    out[idx]["late"] = True
            for tid, idx in agent_calls.items():
                if tid in denied:
                    out[idx]["outcome"] = "DENIED"
                    out[idx]["needs_judgment"] = False
            # A transcript can carry the same record twice (resume / retry
            # re-emits it; measured 2026-09-25: 64 repeated ids on the live
            # corpus, none of them HIT/BYPASS/MISS). The audit's scored
            # outcomes are left exactly as it counts them (INV-8); the extra
            # outcomes this tool adds keep the first copy only, so INV-2 holds.
            seen_ids = set()
            for e in out:
                if e["event_id"] in seen_ids and e["outcome"] not in (
                        "HIT", "BYPASS", "MISS"):
                    stats["dup_records"] = stats.get("dup_records", 0) + 1
                    continue
                seen_ids.add(e["event_id"])
                events.append(e)
    stats["known_skills"] = len(known)
    return events, stats


def _model_event(b, out, agent_calls, session, ruuid, pinned, date):
    name = b.get("name")
    inp = b.get("input") or {}
    tid = b.get("id") or ""
    if name in ("Agent", "Task"):
        model = inp.get("model")
        carrier, agent_type = "agent", inp.get("subagent_type") or "general-purpose"
        if model:
            outcome, subject = "EXPLICIT", model
        elif agent_type in pinned:
            outcome, subject = "PINNED", pinned[agent_type]
        else:
            outcome, subject = "INHERITED", "inherited"
    elif name in ("Bash", "PowerShell"):
        cmd = inp.get("command") or ""
        m = CODEX_RX.search(cmd)
        if m:
            subject, carrier = m.group(1), "codex"
        elif EXTDISPATCH_RX.search(cmd):
            subject, carrier = "extdispatch", "extdispatch"
        else:
            return
        outcome, agent_type = "EXTERNAL", None
    else:
        return
    ref = f"{ruuid}#{tid}"
    out.append({
        "event_id": store.event_id("model-route", session, ref, subject),
        "node": "model-route", "date": date, "session": session,
        "record_uuid": ref, "subject": subject, "outcome": outcome,
        "carrier": carrier, "agent_type": agent_type,
        "needs_judgment": outcome in store.NEEDS_JUDGMENT})
    if carrier == "agent" and tid and tid not in agent_calls:
        agent_calls[tid] = len(out) - 1     # first copy is the one kept


def counts_by_entry(events):
    """INV-8 view: per dict entry, the audit's four counters."""
    c = defaultdict(lambda: {"hit": 0, "bypass": 0, "miss": 0, "late": 0})
    for e in events:
        if e["node"] != "skill-route":
            continue
        o = e["outcome"]
        if o == "HIT":
            c[e["subject"]]["hit"] += 1
        elif o == "BYPASS":
            c[e["subject"]]["bypass"] += 1
        elif o == "MISS":
            c[e["subject"]]["miss"] += 1
            if e["late"]:
                c[e["subject"]]["late"] += 1
    return c
