#!/usr/bin/env python3
"""Agents-census emitter: reads version-census's `agents` partition snapshot (hmi-report/1, class=reconcile).

STATUS: LIVE since 2026-09-19 (user ruling M4). It READS the snapshot the scheduled carrier wrote
(cache/version-census/agents/scheduled.json) and never runs the probes itself: a session shell sits
in the desktop app's MSIX silo and sees a different HKCU, so a census taken from here would be a
different machine's answer. No scheduled snapshot yet, an unreadable one, or one older than
MAX_AGE_H -> the points did not run (never pass).

Points:
  agents.channels   every install/home channel (registry, appx, dir, home_root) was readable -> pass;
                    any channel UNDET -> the point is undetermined, with the channel's reason
  agents.events     open events since the previous scheduled run (INSTALLED / REMOVED / UPDATED /
                    UNDECLARED-AGENT / FOREIGN-WRITE / UNOWNED-HOME-ENTRY) -> warn; none -> pass.
                    Severity and its promotion trigger belong to version-census (partitions/agents.toml).

Read-only. Proof-of-life: `python tools/system-hmi/controls.py`
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

HOME = Path(__file__).resolve().parents[3]
SNAPSHOT = HOME / "cache" / "version-census" / "agents" / "scheduled.json"
MAX_AGE_H = 48   # the carrier is daily + at logon; two missed days means it is not running


def _pt(pid, alias, state, findings, ran=True, skip=None, remedy=None):
    return {"id": pid, "alias": alias, "class": "reconcile", "ran": ran, "skip_reason": skip, "state": state,
            "quality": "good", "findings": findings, "remedy": remedy}


def build(snapshot_path=SNAPSHOT, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    ids = (("agents.channels", "agent 安裝盤點：管道健康"), ("agents.events", "agent 安裝／外部寫入事件"))
    remedy = "run the daily copy-census scheduled task (its carrier runs census.py --partition agents --context scheduled)"
    why = None
    snap = None
    try:
        snap = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        taken = dt.datetime.fromisoformat(snap["collected_at"])
        age_h = (now - taken).total_seconds() / 3600
        if snap.get("context") != "scheduled":
            why = f"snapshot context is {snap.get('context')!r}, not 'scheduled'"
        elif age_h > MAX_AGE_H:
            why = f"scheduled snapshot is {age_h:.0f} h old (> {MAX_AGE_H} h): the carrier is not running"
    except FileNotFoundError:
        why = "no scheduled snapshot yet: the carrier has not run since the partition was built"
    except (OSError, ValueError, KeyError) as exc:
        why = f"scheduled snapshot unreadable: {type(exc).__name__}"
    if why:
        points = [_pt(pid, alias, None, [], ran=False, skip=why, remedy=remedy) for pid, alias in ids]
    else:
        bad = {c: v for c, v in snap.get("channels", {}).items() if v.get("status") != "ok"}
        if bad:
            points = [_pt(ids[0][0], ids[0][1], None, [], ran=False, remedy=remedy,
                          skip="; ".join(f"{c}: {v.get('status')} ({v.get('reason')})" for c, v in bad.items())[:300])]
        else:
            points = [_pt(ids[0][0], ids[0][1], "pass", [], remedy=None)]
        events = [e for e in snap.get("events", []) if e.get("kind") != "UNDET"]
        if bad and not events:   # a blind channel makes "no events" a lower bound, not a verdict
            points.append(_pt(ids[1][0], ids[1][1], None, [], ran=False, skip="a channel was unreadable", remedy=remedy))
        else:
            f = [{"severity": "warn", "label": e.get("kind", "?"),
                  "text": f"{e.get('name') or '?'} [{e.get('channel')}] {e.get('reason') or ''}"[:200]} for e in events[:12]]
            points.append(_pt(ids[1][0], ids[1][1], "warn" if events else "pass", f,
                              remedy="python tools/version-census/census.py --partition agents --json  (then add the agents.toml row or owner it asks for)"))
    return {"protocol": "hmi-report/1", "source": "agents-census",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": points}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(json.dumps(build(), ensure_ascii=False, indent=1))
