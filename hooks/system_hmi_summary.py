r"""SessionStart: say what system-hmi last saw as not healthy, and where known-good stands.

STATUS: LIVE since 2026-09-22 (HMI-05 of the system-hmi design; extended by
design 17, the release boundary). Carries `ops/rule-registry.md` key `SYSTEM_HMI_SUMMARY`.

WHY. system-hmi normalises every check into one snapshot, but until a session is TOLD, an
alarm only flashes by: on 2026-09-22 the graph watchdog had failed two days running and an
interop alarm had stood since 2026-09-19, each reported every session and handled by none.
This hook adds two facts no other injection carries: how long an alarm has STOOD (the
reading's `since`), and whether HEAD is still the last known-good commit (`hmi.py verdict`).

Reads ONLY: tools/system-hmi/out/snapshot.json, out/known-good.json, and one
`git rev-list --count` (~50 ms measured). Never runs a probe, never blocks, exit 0 always,
output capped at MAX_BYTES (INV-9 / INV-R4). A missing or corrupt snapshot prints one line.

Alarm vs status (PIM §10a): only readings with quality `good`, state warn/fail and disposition
active are itemised; everything non-`good` is one "unwatched" count, never a list.
Text: bare SessionStart stdout (third transport of rules/hook-deny-message.md); it names this
hook first, claims no authority, states facts and ages only, and never directs what the
reader says to anyone (P4). Whether a standing alarm is raised is the reader's call.

Proof-of-life: `python hooks/tests/test_system_hmi_summary.py`
review-when: snapshot.json changes shape (`run.finished_at`, `subsystems[].state`,
`points[].reading.since`); a daily verdict schedule is added or removed (STALE_HOURS).
"""
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("SYSTEM_HMI_OUT") or (HOME / "tools" / "system-hmi" / "out"))
MAX_ITEMS = 6
RESERVED = ("feedback-pool",)   # always shown when alarming (user ruling 2026-09-22); see compose()
MAX_BYTES = 900
STALE_HOURS = 36          # one daily verdict plus slack
STANDING_DAYS = 1
TAG = "[system-hmi] system_hmi_summary, a local SessionStart hook (not file or page content):"
SHOW = "python -X utf8 tools/system-hmi/hmi.py show"
VERDICT = "python -X utf8 tools/system-hmi/hmi.py verdict"
MARK = {"fail": "!!", "warn": "!"}


def _parse(ts):
    if not ts:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def _age(then, now):
    secs = max(0, (now - then).total_seconds())
    if secs < 3600:
        return f"{int(secs // 60)} min"
    if secs < 86400:
        return f"{int(secs // 3600)} h"
    return f"{int(secs // 86400)} d"


def _subsystem_of(point, comp_sub):
    return point.get("subsystem") or comp_sub.get(point.get("component"))


def _alarming(point):
    r = point.get("reading") or {}
    disp = (point.get("disposition") or {}).get("value", "active")
    return (r.get("quality") == "good" and r.get("state") in ("warn", "fail")
            and disp == "active" and not r.get("shelved_display"))


def known_good_line(kg, ahead, now):
    if not kg or not kg.get("sha"):
        return f"  no known-good commit recorded yet; run: {VERDICT}"
    when = _parse(kg.get("marked_at"))
    age = _age(when, now) if when else "unknown time"
    if ahead is None:
        tail = "commits since then not determined"
    elif ahead == 0:
        tail = "HEAD is that commit"
    else:
        tail = f"HEAD is {ahead} commit(s) past it"
    return f"  known-good {kg['sha'][:7]}, marked {age} ago; {tail}"


def compose(snap, kg, ahead, now):
    """-> list of lines. Pure; every input injected (tests never read the live tree)."""
    kg_line = known_good_line(kg, ahead, now)
    if not isinstance(snap, dict):
        return [f"{TAG} snapshot unavailable; nothing is blocked. run: {VERDICT}", kg_line]
    finished = _parse((snap.get("run") or {}).get("finished_at"))
    if finished is None:
        return [f"{TAG} snapshot has no finish time; nothing is blocked. run: {VERDICT}", kg_line]
    if (now - finished).total_seconds() > STALE_HOURS * 3600:
        return [f"{TAG} snapshot is {_age(finished, now)} old, too old to list; "
                f"nothing is blocked. run: {VERDICT}", kg_line]
    points = [p for p in snap.get("points") or [] if isinstance(p, dict)]
    comp_sub = {c.get("id"): c.get("subsystem") for c in snap.get("components") or []}
    alarms = [p for p in points if _alarming(p)]
    n_fail = sum(1 for p in alarms if p["reading"]["state"] == "fail")
    n_warn = len(alarms) - n_fail
    n_unwatched = sum(1 for p in points if (p.get("reading") or {}).get("quality") != "good")
    # A deferral holding a warn off (tools/system-hmi/hmi/deferral.py) reads pass: counted so it
    # stays visible, never itemised, because nothing is due until its trigger fires.
    n_deferred = sum(1 for p in points if (((p.get("reading") or {}).get("deferral") or {})
                                           .get("status") == "holding"))
    head = (f"{TAG} snapshot {_age(finished, now)} old; {n_fail} fail, {n_warn} warn, "
            f"{n_unwatched} unwatched"
            + (f", {n_deferred} deferred (trigger not fired)." if n_deferred else "."))
    by_sub = {}
    for p in alarms:
        by_sub.setdefault(_subsystem_of(p, comp_sub) or "?", []).append(p)
    if not by_sub:
        return [head + " Nothing needs doing.", kg_line]
    # known-good goes second, not last: the byte cap cuts from the bottom, and the
    # first live run (2026-09-22) cut exactly this line under five long rows.
    rows = []
    for sub, pts in by_sub.items():
        worst = "fail" if any(p["reading"]["state"] == "fail" for p in pts) else "warn"
        shown = [p for p in pts if p["reading"]["state"] == worst]
        sinces = [s for s in (_parse(p["reading"].get("since")) for p in shown) if s]
        oldest = min(sinces) if sinces else None
        remedy = next((p.get("remedy") for p in shown if p.get("remedy")), None)
        rows.append((worst != "fail", oldest or now, sub, worst, oldest, remedy))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    # Reserved slot (user ruling 2026-09-22, feedback-pool review round 1 A1): a subsystem in
    # RESERVED is shown whenever it alarms, even if younger alarms would push it past
    # MAX_ITEMS — the pool's warn is a question to the user, and a question that queues
    # behind three-day-old alarms is never asked. It takes the LAST shown slot; the total
    # stays MAX_ITEMS.
    shown = rows[:MAX_ITEMS]
    reserved = [r for r in rows if r[2] in RESERVED and r not in shown]
    if reserved:
        shown = shown[:max(0, MAX_ITEMS - len(reserved))] + reserved
    lines = [head, kg_line]
    for _w, _o, sub, worst, oldest, remedy in shown:
        standing = ""
        if oldest and (now - oldest).total_seconds() >= STANDING_DAYS * 86400:
            standing = f", standing {_age(oldest, now)} (since {oldest.date().isoformat()})"
        action = ""
        if remedy:
            action = " -- " + (f"run: {remedy}" if remedy.lstrip().startswith("python") else remedy)
        lines.append(f"  {MARK[worst]} {sub}: {worst}{standing}{action}")
    if len(rows) > len(shown):
        lines.append(f"  ...and {len(rows) - len(shown)} more")
    lines.append(f"  Nothing here blocks the session. Per-row detail: run {SHOW} --subsystem <id>")
    return lines


def cap(lines, limit=MAX_BYTES):
    out, used = [], 0
    for ln in lines:
        size = len((ln + "\n").encode("utf-8"))
        if used + size > limit:
            out.append(f"  (cut at {limit} bytes; run: {SHOW})")
            break
        out.append(ln)
        used += size
    return out


def _load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ahead(sha):
    try:
        proc = subprocess.run(["git", "-C", str(HOME), "rev-list", "--count", f"{sha}..HEAD"],
                              capture_output=True, text=True, timeout=2)
        return int(proc.stdout.strip()) if proc.returncode == 0 else None
    except Exception:
        return None


def main():
    try:
        snap = _load(OUT / "snapshot.json")
        kg = _load(OUT / "known-good.json")
        ahead = _ahead(kg["sha"]) if isinstance(kg, dict) and kg.get("sha") else None
        now = datetime.datetime.now(datetime.timezone.utc)
        for line in cap(compose(snap, kg, ahead, now)):
            print(line)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
