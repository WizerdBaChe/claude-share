"""Paths, event ids, ruler and the append-only judgment store for routing-loop.

Design: references/routing-loop-design.md (INV-1..INV-8). Build spec:
references/routing-loop-psm.md.

Every path resolves from HOME_CLAUDE, never from this file's location: the
tool may be run from a linked worktree, and a derived file written there would
be stranded (ops/references/shared-tree-git.md section 1a).
"""
import hashlib
import json
import os
import time

HOME_CLAUDE = os.path.abspath(os.environ.get("ROUTING_LOOP_HOME")
                              or os.path.expanduser("~/.claude"))
CACHE = os.path.join(HOME_CLAUDE, "cache", "routing-loop")
EVENTS = os.path.join(CACHE, "events.jsonl")
LAST_RUN = os.path.join(CACHE, "last-run.json")
RUNS = os.path.join(HOME_CLAUDE, "telemetry", "routing-loop-runs.jsonl")
LABELS = os.path.join(HOME_CLAUDE, "tools", "routing-loop", "labels.jsonl")
AUDIT = os.path.join(HOME_CLAUDE, "tools", "skill-routing-audit.py")
PROBE = os.path.join(HOME_CLAUDE, "tools", "trigger-probe", "trigger_probe.py")
DICT = os.path.join(HOME_CLAUDE, "skill-trigger-dict.md")

NODES = ("skill-route", "model-route")
NEEDS_JUDGMENT = {"BYPASS", "MISS", "UNPREDICTED", "INHERITED"}
VERDICTS = {
    "skill-route": {"correct", "should-fire", "correct-silence", "dict-gap",
                    "description-gap", "wrong-skill", "abstain"},
    "model-route": {"fit", "over-provisioned", "under-provisioned", "abstain"},
}
MODEL_ROUTE_PARSER = "heuristic-v2"


class ValidationError(Exception):
    """A label or argument the store refuses; the CLI maps it to exit 2."""


def event_id(node, session, record_ref, subject):
    """INV-2: stable across re-derivation. `record_ref` already carries any
    disambiguating suffix (tool_use id, occurrence index)."""
    raw = "|".join([node, session, record_ref, subject or ""])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def dict_sha():
    try:
        with open(DICT, "rb") as fh:
            return hashlib.sha1(fh.read()).hexdigest()[:12]
    except OSError:
        return None


def ruler(lookahead, since, probe=None):
    return {"dict_sha": dict_sha(), "lookahead": lookahead, "since": since,
            "probe": probe, "model_route_parser": MODEL_ROUTE_PARSER}


def comparable(a, b):
    """INV-4: return None when two rulers may be trended, else the first field
    that differs (printed as NOT COMPARABLE (<field>))."""
    for key in ("dict_sha", "lookahead", "since", "model_route_parser"):
        if (a or {}).get(key) != (b or {}).get(key):
            return key
    pa, pb = (a or {}).get("probe") or {}, (b or {}).get("probe") or {}
    for key in ("scorer_version", "calibration_id"):
        if pa.get(key) != pb.get(key):
            return "probe." + key
    return None


def _read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        continue
    except OSError:
        pass
    return out


def read_events():
    return _read_jsonl(EVENTS)


def write_events(events):
    """INV-1: whole-file rewrite; this is the only writer of EVENTS and it
    never touches LABELS."""
    os.makedirs(CACHE, exist_ok=True)
    tmp = EVENTS + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for ev in events:
            fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
    os.replace(tmp, EVENTS)


def read_labels():
    return _read_jsonl(LABELS)


def latest_labels():
    """{id: latest row}; event ids and group ids share one namespace (group
    ids start with `g` and are 12 chars, event ids are 16 hex)."""
    latest = {}
    for row in read_labels():
        latest[row.get("event_id") or row.get("group_id")] = row
    return latest


def group_key(ev):
    """The pattern a judgment is really about. One verdict on a group carries
    forward to every future event of the same pattern, which is what lets the
    queue converge (first live run 2026-09-25: 1,009 MISS events in 30 days,
    134 MISS groups; one noisy token alone produced 164 events)."""
    node, o = ev["node"], ev["outcome"]
    if node == "model-route":
        parts = [node, o, ev.get("agent_type") or ev.get("carrier") or ""]
    elif o == "MISS":
        parts = [node, o, ev["subject"], ev.get("token") or ""]
    elif o == "BYPASS":
        parts = [node, o, ev["subject"], ev.get("fired") or ""]
    else:
        parts = [node, o, ev["subject"]]
    return "|".join(parts)


def group_id(key):
    return "g" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:11]


def add_label(target, verdict, why, origin="model", orphan_ok=False,
              events=None):
    """`target` is an event id (16 hex) or a group id (`g` + 11 hex)."""
    events = read_events() if events is None else events
    is_group = target.startswith("g") and len(target) == 12
    node, key = None, None
    if is_group:
        for e in events:
            k = group_key(e)
            if group_id(k) == target:
                node, key = e["node"], k
                break
    else:
        for e in events:
            if e["event_id"] == target:
                node = e["node"]
                break
    if node is None and not orphan_ok:
        raise ValidationError(f"unknown id {target} (run derive, or pass "
                              f"--orphan-ok)")
    allowed = VERDICTS.get(node) if node else set().union(*VERDICTS.values())
    if verdict not in allowed:
        raise ValidationError(f"verdict {verdict!r} not in "
                              f"{sorted(allowed)} for node {node}")
    if origin not in ("user", "model"):
        raise ValidationError("origin must be user or model")
    if not (why or "").strip():
        raise ValidationError("--why is required: a judgment without its "
                              "reason cannot be reused")
    row = {("group_id" if is_group else "event_id"): target, "node": node,
           "verdict": verdict, "why": why.strip(), "origin": origin,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if key:
        row["group"] = key
    os.makedirs(os.path.dirname(LABELS), exist_ok=True)
    with open(LABELS, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def label_state(ev, latest):
    """Design section 3.4 statechart for one event. An event-level label wins
    over its group's label (a specific exception to a pattern verdict)."""
    if not ev.get("needs_judgment"):
        return "settled"
    row = latest.get(ev["event_id"]) or latest.get(group_id(group_key(ev)))
    if row is None:
        return "queued"
    return "parked" if row.get("verdict") == "abstain" else "judged"


def orphans(events, latest):
    ids = {e["event_id"] for e in events}
    ids |= {group_id(group_key(e)) for e in events}
    return [i for i in latest if i not in ids]


def read_last_run():
    try:
        with open(LAST_RUN, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_run(record):
    os.makedirs(CACHE, exist_ok=True)
    with open(LAST_RUN, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=1)
    os.makedirs(os.path.dirname(RUNS), exist_ok=True)
    with open(RUNS, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def previous_runs():
    return _read_jsonl(RUNS)
