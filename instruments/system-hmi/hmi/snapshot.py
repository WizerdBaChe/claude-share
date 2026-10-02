"""Snapshot schema, atomic write, previous rotation (SG-3)."""
import hashlib
import json
import os
from pathlib import Path


def registry_sha256(registry_dir):
    h = hashlib.sha256()
    for f in sorted(Path(registry_dir).glob("*.json")):
        h.update(f.read_bytes())
    return h.hexdigest()


def write(out_dir, snap):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    current = out_dir / "snapshot.json"
    previous = out_dir / "snapshot.previous.json"
    tmp = out_dir / "snapshot.json.tmp"
    if current.exists():
        previous.write_bytes(current.read_bytes())
    tmp.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, current)
    try:
        append_history(out_dir, snap)
    except OSError:
        pass  # history is a by-product: a failed append never fails the collect


_STATES = ("fail", "warn", "pass")


def point_state(p):
    s = (p.get("reading") or {}).get("state")
    return s if s in _STATES else "und"


def history_row(snap):
    """One compact line per collect: enough to draw trends later, nothing that restates a threshold."""
    run = snap.get("run") or {}
    pts = snap.get("points") or []
    counts = {k: 0 for k in _STATES + ("und",)}
    for p in pts:
        counts[point_state(p)] += 1
    return {
        "at": run.get("finished_at"),
        "scope": run.get("scope"),
        "tiers": run.get("tiers_run"),
        "status": run.get("status"),
        "counts": counts,
        "subsystems": {s["id"]: [s.get("r_state"), s.get("i_state")] for s in snap.get("subsystems") or []},
        "points": {p["id"]: point_state(p)[0] for p in pts},   # f / w / p / u
    }


def append_history(out_dir, snap):
    line = json.dumps(history_row(snap), ensure_ascii=False, separators=(",", ":"))
    with open(Path(out_dir) / "history.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def load(out_dir, name="snapshot.json"):
    p = Path(out_dir) / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def previous_points_by_id(out_dir):
    prev = load(out_dir, "snapshot.json")  # the "current" one becomes "previous" for the NEXT run;
    # for the run in progress, the previous state is whatever is currently on disk before we write.
    if not prev:
        return {}
    return {p["id"]: p for p in prev.get("points", [])}
