"""Deferral: a known, deliberately deferred finding with a NAMED trigger is a reading, not an alarm.

Added 2026-09-23. Two points stood at `warn` for days although nothing was supposed to be done
(`ops-health.advisory-outputs`: one DEFERRED advisory record; `memory.hybrid-index-fresh`: a stale
index whose rebuild the user ruled to wait). An alarm colour that stays lit for "known, deferred,
nothing to do" teaches the reader to skip orange -- the ISA-18.2 standing-alarm smell.

Canon: ISA-18.2 separates SHELVING (an operator mutes a still-abnormal alarm for a TIME; this
registry's `disposition: shelved` + `until`) from SUPPRESSED BY DESIGN (logic holds the alarm off
while a named CONDITION holds, and it returns by itself when the condition changes). A deferral
with a trigger is the second kind, so it is not modelled as shelving.

Shape (both sources carry the same spec; the registry's wins over a native document's):
    {"kind": "probe" | "manual",
     "trigger": "<the event that starts the work, in words>",          # required, non-empty
     "ruling": "<who ruled the deferral, when>",                      # required for kind manual
     "argv": [...], "cwd": ".", "timeout_s": N,                      # kind probe only
     "fired_exits": [..], "unfired_exits": [..],                      # kind probe only
     "fired": true,                                                   # kind manual: a recorded firing
     "items": [{"item": "...", "trigger": "..."}]}                    # optional, per deferred item

Resolution (`resolve`), every branch below is a regression case in controls.py:
  * applies ONLY to quality `good` + state `warn`: a fail is never deferred, and a probe that did
    not run is never masked (same reason as W-1 for shelving);
  * no trigger (or a manual one with no ruling, or an item without its own trigger) -> the
    deferral is REJECTED: the reading stays `warn`, and says why;
  * trigger fired, or undeterminable (probe exit outside both declared sets, timeout) -> stays
    `warn`: a trigger the machine cannot read never silences anything;
  * trigger not fired -> state `pass` with `deferral.status = "holding"`; the raw state and
    evidence ride in the annotation. `pass` here means "no operator action is due" (the state axis
    answers ISA-18.2's "does this need a response"); the fact itself is never hidden, and every
    reader that draws a reading shows the holding deferral distinctly from a plain pass.
INV-3 is untouched: a deferral cannot turn no_probe/undetermined/probe_error into pass.
"""
from . import adapters

KINDS = ("probe", "manual")


def spec_problems(spec):
    """-> list of reasons this spec cannot hold a warn off. Empty = well-formed."""
    if not isinstance(spec, dict):
        return ["deferral is not an object"]
    probs = []
    if not str(spec.get("trigger") or "").strip():
        probs.append("no trigger recorded")
    kind = spec.get("kind")
    if kind not in KINDS:
        probs.append(f"trigger kind {kind!r} is not probe/manual")
    if kind == "manual" and not str(spec.get("ruling") or "").strip():
        probs.append("a manual trigger needs the ruling that deferred it")
    if kind == "probe":
        argv = spec.get("argv")
        if not (isinstance(argv, list) and argv):
            probs.append("a probe trigger needs argv")
        fired, unfired = spec.get("fired_exits"), spec.get("unfired_exits")
        if not (isinstance(fired, list) and fired and isinstance(unfired, list) and unfired):
            probs.append("a probe trigger needs fired_exits and unfired_exits")
        elif set(fired) & set(unfired):
            probs.append("fired_exits and unfired_exits overlap")
    for it in spec.get("items") or []:
        if not str((it or {}).get("trigger") or "").strip():
            probs.append(f"item {(it or {}).get('item')!r} has no trigger")
    return probs


def trigger_state(spec, home, run=adapters._run):
    """-> (fired: True | False | None, evidence). None = the machine cannot tell."""
    if spec.get("kind") == "manual":
        if spec.get("fired"):
            return True, "manual trigger recorded as fired"
        return False, "manual trigger: fires when a human records it (ruling: " + str(spec.get("ruling")) + ")"
    cwd = adapters._cwd_for(home, spec)
    code, out, err, error = run(spec["argv"], cwd, spec.get("timeout_s", 30))
    tail = (out or err or "").strip().splitlines()
    tail = tail[-1] if tail else ""
    if error:
        return None, f"trigger probe did not run: {error}"
    if code in spec["fired_exits"]:
        return True, f"trigger probe exit {code}: {tail}"
    if code in spec["unfired_exits"]:
        return False, f"trigger probe exit {code}: {tail}"
    return None, f"trigger probe exit {code} is in neither declared set: {tail}"


def resolve(reading, spec, home, run=adapters._run):
    """-> the reading to record. Never mutates `reading`."""
    if not spec or reading.get("quality") != "good" or reading.get("state") != "warn":
        return reading
    out = dict(reading)
    raw_ev = reading.get("evidence") or ""
    base = {"kind": spec.get("kind") if isinstance(spec, dict) else None,
            "trigger": (spec.get("trigger") if isinstance(spec, dict) else None),
            "ruling": (spec.get("ruling") if isinstance(spec, dict) else None),
            "items": (spec.get("items") if isinstance(spec, dict) else None),
            "raw_state": "warn", "raw_evidence": raw_ev}
    probs = spec_problems(spec)
    if probs:
        out["deferral"] = dict(base, status="rejected", reason="; ".join(probs))
        out["evidence"] = "deferral NOT applied (" + "; ".join(probs) + ") -- " + raw_ev
        return out
    fired, tev = trigger_state(spec, home, run)
    if fired is None:
        out["deferral"] = dict(base, status="rejected", reason=tev, trigger_evidence=tev)
        out["evidence"] = "deferral NOT applied (" + tev + ") -- " + raw_ev
        return out
    if fired:
        out["deferral"] = dict(base, status="fired", trigger_evidence=tev)
        out["evidence"] = "deferral trigger FIRED (" + str(spec["trigger"]) + "; " + tev + ") -- " + raw_ev
        return out
    out["state"] = "pass"
    out["deferral"] = dict(base, status="holding", trigger_evidence=tev)
    out["evidence"] = "DEFERRED until: " + str(spec["trigger"]) + " -- raw reading warn: " + raw_ev
    return out


def holding(reading):
    """True when this reading is a deferral holding a warn off (the one non-alarm deferred reading)."""
    return ((reading or {}).get("deferral") or {}).get("status") == "holding"
