r"""Run report skeleton for an unattended run: reports/<date>-run-<slug>.md.

Everything the tool can DETERMINE is pre-filled with evidence; everything else
is a blank the model fills before the Stop hook lets the session end. The
report is a human-read document (Traditional Chinese headings, English data).

Sections
  1 ledger        register writes (ledger.py registers) + appendix rows
  2 acceptance    manifest items; `file exists` auto-evidence when the item
                  names a path that is on disk; otherwise `evidence: (fill)`
  3 not-done      blank list the model fills (F6 negative control: a listed
                  not-done item is NOT a distortion)
  4 compactions   rows from telemetry/compact-loss.jsonl for this session,
                  each with snapshot age at compaction (mtime delta)
  5 canary        keep: grep over deliverables (hit/miss per file);
                  drop: grep over deliverables + this report + summaries → must be 0
  6 close         blockers by name (fill) — never a question

Usage: python report.py [--session ID] [--force]   (default: current run)
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger  # noqa: E402

CLAUDE_DIR = ledger.CLAUDE_DIR
HANDOFF_DIR = ledger.HANDOFF_DIR
LOSS_LOG = CLAUDE_DIR / "telemetry" / "compact-loss.jsonl"


def manifest(session: str) -> dict:
    p = HANDOFF_DIR / f"{session[:64]}.run.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        sys.exit(f"no manifest for {session}: {p}")


def grep_files(paths, needle: str):
    hits = {}
    for p in paths:
        try:
            hits[str(p)] = needle in Path(p).read_text(encoding="utf-8", errors="replace")
        except Exception:
            hits[str(p)] = None
    return hits


def compactions(session: str):
    if not LOSS_LOG.is_file():
        return []
    rows = []
    for l in LOSS_LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("session") != session:
            continue
        snap = r.get("snapshot") or {}
        age = (r["ts"] - snap["mtime"]) if snap.get("exists") and snap.get("mtime") else None
        rows.append({"ts": r["ts"], "trigger": r.get("trigger"), "snapshot": bool(snap.get("exists")),
                     "snapshot_age_min": (round(age / 60) if age is not None else None)})
    return rows


def resolve(path: str, cwd: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(cwd) / p


def build(session: str, m: dict, force: bool) -> Path:
    slug = m["slug"]
    out = CLAUDE_DIR / "reports" / f"{time.strftime('%Y-%m-%d')}-run-{slug}.md"
    existing = sorted((CLAUDE_DIR / "reports").glob(f"*-run-{slug}.md"))
    if existing and not force:
        sys.exit(f"report exists: {existing[-1]} (edit it in place, or --force to write a new skeleton)")
    cwd = m.get("cwd", "")
    t = ledger.find_transcript(session)
    regs = ledger.register_writes(t) if t else []
    app = ledger.read_appendix(session)
    deliv = [resolve(d, cwd) for d in m.get("deliverables", [])]
    keep, drop = (m.get("canary") or {}).get("keep"), (m.get("canary") or {}).get("drop")

    fb = m.get("filled_by") or {}
    prov = ", ".join(f"{k}={fb.get(k, 'hook-default')}" for k in ("scope", "deliverables", "acceptance", "rulings", "canary"))
    L = [f"# Run report — {slug}（session {session[:8]}，{time.strftime('%Y-%m-%d %H:%M')}）", "",
         f"**狀態**：run report｜manifest `cache/handoff/{session[:64]}.run.json`｜工具 `tools/unattended-run/report.py`｜"
         "機器可判定項已附證據，`(fill)` 為模型必填", "",
         f"**欄位來源 (filled_by)**：{prov} — `model` 表示交付物／驗收是模型從任務推導的，讀者第一件事是核對它們是否等於你交辦的意圖", "",
         "## 1. 決策帳 (ledger)", "",
         f"### 1a. 登記表寫入（transcript 抽出，{len(regs)} 筆）", "",
         "| # | line | tool | path | excerpt |", "|---|---|---|---|---|"]
    L += [f"| {n} | {r['line']} | {r['tool']} | `{r['path']}` | {r['excerpt'].replace('|', '/')} |" for n, r in enumerate(regs, 1)] or ["| – | – | – | (none) | – |"]
    L += ["", f"### 1b. 過程決策附錄（{len(app)} 筆）", "", "| ts | subject | choice | reason | reversible | origin | ref |", "|---|---|---|---|---|---|---|"]
    L += [f"| {time.strftime('%H:%M', time.localtime(r['ts']))} | {r['subject']} | {r['choice']} | {r['reason']} | {r['reversible']} | {r['origin']} | {r.get('register_ref', '')} |" for r in app] or ["| – | (none) | | | | | |"]
    L += ["", "## 2. 驗收 (acceptance)", "", "| item | evidence | status |", "|---|---|---|"]
    for item in m.get("acceptance", []) or ["(manifest carried no acceptance items)"]:
        ev, st = "(fill)", "(fill)"
        for tok in re.findall(r"[\w./\\-]+\.[A-Za-z0-9]{1,6}", item):
            p = resolve(tok, cwd)
            if p.is_file():
                ev, st = f"file exists: `{tok}` ({p.stat().st_size} B)", "exists (content: fill)"
                break
        L.append(f"| {item.replace('|', '/')} | {ev} | {st} |")
    L += ["", "## 3. 未做＋原因 (not-done)", "", "- (fill — 每項一行：項目 → 原因；列在這裡的不算失真)", ""]
    L += ["## 4. 壓縮 (compactions)", "", "| ts | trigger | snapshot on disk | snapshot age at compaction (min) |", "|---|---|---|---|"]
    L += [f"| {time.strftime('%m-%d %H:%M', time.localtime(c['ts']))} | {c['trigger']} | {c['snapshot']} | {c['snapshot_age_min']} |" for c in compactions(session)] or ["| – | (no compaction recorded) | | |"]
    L += ["", "## 5. Canary", ""]
    snap = HANDOFF_DIR / f"{session[:64]}.md"
    if keep:
        # Q2 (user ruling 2026-09-08): keep is graded on PROCESS CARRIERS — the handoff
        # snapshot, this report (stamped on line 2 by this tool) and the compaction
        # summaries (run_audit) — never on deliverables. Grading deliverables put run
        # ids into project files and a public README, and forced two claude-share runs
        # to fail keep on purpose rather than leak a private pointer into a public repo.
        L.insert(1, keep)
        snap_hit = grep_files([snap], keep).get(str(snap)) if snap.is_file() else None
        L += [f"keep=`{keep}` — graded on carriers (snapshot, this report, compaction summaries), not deliverables:", "",
              f"- {'HIT' if snap_hit else ('MISS' if snap_hit is False else 'no snapshot on disk')} `{snap}`",
              f"- HIT `{out}` (stamped by report.py)",
              "- compaction summaries: see run_audit.py (deliverables are not graded — ruling Q2 2026-09-08)"]
    else:
        L.append("keep: (none planted)")
    L.append("")
    if drop:
        hits = grep_files(deliv + ([snap] if snap.is_file() else []), drop)
        # The token itself is withheld: printing it here made this report the leak
        # run_audit then found (2026-09-06 — a self-inflicted false positive).
        L += ["drop token — withheld from this report; must appear nowhere (deliverables and snapshot checked here; summaries and this report checked by run_audit):", ""] + [f"- {'LEAK' if v else 'clean'} `{k}`" for k, v in hits.items()]
    else:
        L.append("drop: (none planted)")
    L += ["", "## 6. 收尾 (close)", "", "- 具名阻塞 (blockers): (fill — 每項「需要誰做什麼」，不得是問句)",
          "- 交付路徑 (deliverables):"] + [f"  - `{d}` — {'exists' if d.is_file() else 'MISSING'}" for d in deliv] + [""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    session = ledger.current_session(a.session)
    print(build(session, manifest(session), a.force))


if __name__ == "__main__":
    main()
