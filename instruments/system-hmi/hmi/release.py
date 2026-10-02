"""release — the known-good verdict of ~/.claude (design 17, R-1/R-2).

Status: live 2026-09-22 | severity: WARN-class signal (the consumer is an LLM
reading the SessionStart summary and a person reading the page); nothing here
blocks | controls: `tools/system-hmi/controls.py` (release R1a..R3) | wired:
`hmi.py verdict`, point `release.verdict-fresh`, `hooks/system_hmi_summary.py`.

Why this exists. `~/.claude` main is the machine's production environment: a
hook is live the moment it is saved, and until 2026-09-22 nothing answered "is
main good right now". Measured that day: a hook's live check had been failing
for about a day (a registry data file changed, the hook did not), found only
because someone ran pol.py by hand.

The verdict is judged over GATE POINTS only -- every generated `hook-suite.*`
point plus any registry point declaring `"gate": "known-good"`. Those are
self-tests (suites, controls, selftests, lints over code in ~/.claude). Freshness,
schedule and environment points never gate: a stale Codex compile is a thing to
act on, not a reason the code cannot be rolled back to.

Only a FULL collect may mark known-good. A slow point is carried when its
declared inputs' fingerprint is unchanged, and the 2026-09-22 failure changed
no declared input -- a carried reading would have said pass.

Writes only under the HMI out/ directory (INV-1); git is read, never written.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

GOOD, BAD, PARTIAL = "GOOD", "BAD", "PARTIAL"
GATE_VALUE = "known-good"
CODE_SUFFIXES = (".py", ".ps1", ".bat", ".sh", ".js", ".mjs", ".toml")
CODE_FILES = ("settings.json", "CLAUDE.md")
CODE_DIRS = ("hooks/", "rules/", "skills/")


def gate_ids(registry_points: list) -> set:
    """Declared gates, read from the REGISTRY. The snapshot is not the source: the
    collector does not copy `gate` into snapshot points, and the first live verdict
    (2026-09-22) therefore judged 38 hook-suite points and silently none of the 13
    declared ones -- a GOOD over an incomplete set."""
    return {p["id"] for p in registry_points if p.get("gate") == GATE_VALUE}


def is_gate(point: dict, declared: set = frozenset()) -> bool:
    pid = point.get("id", "")
    return pid.startswith("hook-suite.") or pid in declared or point.get("gate") == GATE_VALUE


def judge(points: list, declared: set = frozenset()) -> dict:
    """INV-R1. Pure: the verdict over one snapshot's points. A declared gate that is
    absent from the snapshot is non-good, never silently dropped (INV-3)."""
    gates = [p for p in points if is_gate(p, declared)]
    present = {p.get("id") for p in gates}
    failing, non_good = [], sorted(set(declared) - present)
    for p in gates:
        r = p.get("reading") or {}
        if r.get("quality") != "good":
            non_good.append(p["id"])
        elif r.get("state") == "fail":
            failing.append(p["id"])
        elif r.get("state") != "pass":
            non_good.append(p["id"])
    if failing:
        verdict = BAD
    elif non_good or not gates:
        verdict = PARTIAL
    else:
        verdict = GOOD
    total = len(gates) + len(set(declared) - present)
    return {"verdict": verdict, "gate_total": total,
            "gate_pass": total - len(failing) - len(non_good),
            "failing": sorted(failing), "non_good": sorted(non_good)}


def is_code_path(rel: str) -> bool:
    rel = rel.replace("\\", "/").strip('"')
    return (rel.endswith(CODE_SUFFIXES) or rel in CODE_FILES
            or rel.startswith(CODE_DIRS))


def dirty_code(porcelain: str) -> list:
    """Tracked, modified code paths from `git status --porcelain --untracked-files=no`."""
    out = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].split(" -> ")[-1]
        if is_code_path(path):
            out.append(path.strip('"'))
    return out


def markable(result: dict, scope: str, dirty: list, mode: str = "full") -> bool:
    """INV-R2. `mode` is what THIS run collected: a reused snapshot (`none`) may have
    been taken at an older commit, and a `due` run carries readings -- neither marks."""
    return (result["verdict"] == GOOD and mode == "full" and scope.startswith("full")
            and not dirty)


def _git(home: str, *args) -> str:
    proc = subprocess.run(["git", "-C", home, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=30)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} exit {proc.returncode}")
    return proc.stdout


def _write_json(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def run(home: str, out_dir: str, collect, mode: str = "full", declared: set = frozenset()) -> tuple:
    """-> (exit_code, verdict_doc). `collect(mode)` returns an exit code; it is
    injected so the controls can run this without a real collector. `declared` is
    gate_ids(registry points)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    head = _git(home, "rev-parse", "HEAD").strip()
    dirty = dirty_code(_git(home, "status", "--porcelain", "--untracked-files=no"))
    collect_exit = collect(mode) if mode != "none" else 0
    try:
        snap = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))
    except Exception as exc:
        snap, collect_exit = {"points": [], "run": {}}, collect_exit or 3
        load_error = f"{type(exc).__name__}: {exc}"
    else:
        load_error = None
    result = judge(snap.get("points") or [], declared)
    run_meta = snap.get("run") or {}
    scope = str(run_meta.get("scope") or "")
    if collect_exit:
        result["verdict"] = BAD if result["verdict"] == BAD else PARTIAL
    doc = {"verdict": result["verdict"], "sha": head, "mode": mode, "scope": scope,
           "dirty": dirty, "collect_exit": collect_exit, "load_error": load_error,
           "snapshot_finished_at": run_meta.get("finished_at"),
           "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **{k: result[k] for k in
           ("gate_total", "gate_pass", "failing", "non_good")}}
    doc["marked"] = markable(result, scope, dirty, mode) and not collect_exit
    _write_json(out / "verdict.json", doc)
    with open(out / "verdict-history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    if doc["marked"]:
        _write_json(out / "known-good.json", {"sha": head, "marked_at": doc["at"],
                                              "gate_total": doc["gate_total"], "scope": scope})
    if collect_exit:
        return 3, doc
    if doc["verdict"] == BAD:
        return 1, doc
    return (0 if doc["marked"] else 2), doc
