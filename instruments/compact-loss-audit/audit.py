"""Compaction handoff audit: completeness + misleading-ness of each recorded (auto) compaction.

Severity: WARN, advisory. The consumer is the user (or an LLM session the user
opens); nothing downstream consumes the verdict. Promotion trigger: if a
determinable check below is later wired into a PreCompact deny, that hook
carries FAIL semantics — this tool stays a reviewer's packet.

What it DETERMINES (mechanical, printed with evidence):
  C1 path coverage   — of the file paths Written/Edited before the compaction
                       (paths_pre, recorded by compact_loss_record.py), which are
                       named in the summary or the handoff snapshot. Missing
                       paths are listed; a missing path is a candidate loss, not
                       a verdict (a scratch file may be rightly dropped).
  C2 snapshot present — was a handoff snapshot on disk at compaction time, and
                       was the deny-once branch exercised.
  M1 gate re-arm     — in the first POST_TURNS post-compact assistant turns, did
                       the session touch a prior-art / intake instrument
                       (xi.py query, gsnap.py, PROJECTS.md, phase-log read,
                       KEYPOINTS/index reads) before its first Write to a
                       deliverable? Absence is a MISLEADING-candidate, not proof.
  M2 user correction — in the first POST_TURNS user turns, a correction phrase
                       (漏了/之前說過/上次/不是這樣/你忘了/already decided/we said)
                       appears. Presence is a LOSS-candidate.
What it FORWARDS (not determinable here): whether decisions, rules and the
consulted list survived. For that it emits a review packet per compaction:
summary text + snapshot + the last 12 pre-compact user/assistant text turns +
first 6 post-compact turns, so a reader (human or an LLM session) can judge
with the evidence in front of them. Calibration: run once on a compaction you
KNOW went badly and one you know went well; a tool that rates both the same is
broken (CLAUDE.md gate rule).

Usage:
  python audit.py [--all] [--post-turns 8] [--out reports/]
Marks rows audited=True in telemetry/compact-loss.jsonl after writing the packet.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
LOG_PATH = CLAUDE_DIR / "telemetry" / "compact-loss.jsonl"
GATE_TOUCH = re.compile(r"xi\.py\s+query|gsnap\.py|PROJECTS\.md|phase-log\.md|KEYPOINTS\.md|session-find\.py|prior-art|consulted", re.I)
CORRECTION = re.compile(r"漏了|之前(說|講|提)過|上次|不是這樣|你忘了|忘記|already (decided|said)|we (said|agreed)|you (forgot|missed)", re.I)


def text_of(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in (content or []) if isinstance(b, dict) and b.get("type") == "text")


def load_transcript(path: Path):
    recs = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                o["_line"] = i
                recs.append(o)
    except Exception:
        pass
    return recs


def find_summary(recs, after_ts: int):
    """The compaction summary record nearest after the compaction timestamp."""
    best = None
    for o in recs:
        if not o.get("isCompactSummary"):
            continue
        ts = o.get("timestamp", "")
        try:
            t = time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone
        except Exception:
            t = 0
        if t >= after_ts - 120 and (best is None or t < best[0]):
            best = (t, o)
    return best[1] if best else None


def turns(recs, start_line: int, n: int, role: str, forward=True):
    out = []
    seq = [o for o in recs if o.get("type") == role and not o.get("isSidechain") and not o.get("isCompactSummary")]
    seq = [o for o in seq if (o["_line"] > start_line if forward else o["_line"] < start_line)]
    if not forward:
        seq = seq[::-1]
    for o in seq:
        txt = text_of((o.get("message") or {}).get("content")).strip()
        if txt and not txt.startswith("<"):
            out.append((o["_line"], txt[:1200]))
        if len(out) >= n:
            break
    return out if forward else out[::-1]


def tool_calls(recs, start_line: int, n_turns: int):
    calls = []
    count = 0
    for o in recs:
        if o.get("type") != "assistant" or o.get("isSidechain") or o["_line"] <= start_line:
            continue
        count += 1
        if count > n_turns:
            break
        for b in ((o.get("message") or {}).get("content") or []):
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input") or {}
                calls.append((b.get("name"), json.dumps(inp, ensure_ascii=False)[:300]))
    return calls


def audit_row(row, post_turns: int):
    tp = Path(row["transcript_path"])
    recs = load_transcript(tp)
    summary = find_summary(recs, row["ts"])
    summary_txt = text_of((summary or {}).get("message", {}).get("content")) if summary else ""
    sline = summary["_line"] if summary else (row.get("bookmark") or {}).get("line_count") or 0
    snap_txt = ""
    if (row.get("snapshot") or {}).get("exists"):
        try:
            snap_txt = Path(row["snapshot"]["path"]).read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    carrier = summary_txt + "\n" + snap_txt
    paths = row.get("paths_pre") or []
    named = [p for p in paths if os.path.basename(p) in carrier or p in carrier]
    missing = [p for p in paths if p not in named]

    # T1 — real post-compaction context. The platform's compactMetadata.postTokens
    # (14-24k measured 2026-09-06) understates the floor ~4x: the first API call after
    # the boundary carries the cached system layer plus the re-injected summary,
    # restored files, invoked skills and hook cards (~100k measured). PostCompact
    # fires before that call exists, so the recorder writes a null placeholder and
    # this audit backfills it from the transcript (user ruling 2026-09-06).
    meta = next((o.get("compactMetadata") or {} for o in reversed(recs)
                 if o["_line"] < sline and o.get("type") == "system" and o.get("subtype") == "compact_boundary"), {})
    post_prompt_actual = post_first_cache_write = None
    for o in recs:
        if o["_line"] <= sline or o.get("type") != "assistant":
            continue
        u = (o.get("message") or {}).get("usage") or {}
        if u:
            post_prompt_actual = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
            post_first_cache_write = u.get("cache_creation_input_tokens") or 0
            break

    post_calls = tool_calls(recs, sline, post_turns)
    first_write_idx = next((i for i, (n, a) in enumerate(post_calls) if n in ("Write", "Edit")), None)
    gate_before_write = any(GATE_TOUCH.search(a) for n, a in post_calls[: (first_write_idx if first_write_idx is not None else len(post_calls))])
    post_users = turns(recs, sline, post_turns, "user")
    corrections = [(l, t[:200]) for l, t in post_users if CORRECTION.search(t)]

    verdict = {
        "C1_paths_total": len(paths), "C1_paths_named": len(named), "C1_missing": missing[:20],
        "C2_snapshot": bool(snap_txt), "C2_denied_before": row.get("denied_before"),
        "M1_gate_touched_before_first_write": gate_before_write if post_calls else None,
        "M2_user_corrections": corrections,
        "summary_found": bool(summary),
        "T1_post_prompt_actual": post_prompt_actual,
        "T1_post_first_cache_write": post_first_cache_write,
        "T1_platform_pre": meta.get("preTokens"),
        "T1_platform_post": meta.get("postTokens"),
    }
    packet = {
        "row": row, "verdict": verdict,
        "summary": summary_txt[:12000], "snapshot": snap_txt[:8000],
        "pre_turns": turns(recs, sline, 12, "user", forward=False) + turns(recs, sline, 6, "assistant", forward=False),
        "post_turns": post_users + turns(recs, sline, post_turns, "assistant"),
        "post_calls": post_calls[:40],
    }
    return verdict, packet


def render(packets, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d-%H%M")
    path = out_dir / f"{stamp}-compact-loss-audit.md"
    lines = [f"# Compaction handoff audit — {stamp}", "",
             "**狀態**：advisory｜嚴重度 WARN｜工具 `tools/compact-loss-audit/audit.py`｜判決只涵蓋可判定項（C1/C2/M1/M2），其餘交由讀者依 packet 裁定", "",
             "| session | trigger | C1 paths named/total | C2 snapshot | M1 gate before write | M2 corrections | summary found | T1 real post ctx (platform postTokens) | T1 first cache write |", "|---|---|---|---|---|---|---|---|---|"]
    def _k(n):
        return "?" if n is None else f"{n/1000:.0f}k"
    for v, p in packets:
        r = p["row"]
        lines.append(f"| {r['session'][:8]} | {r['trigger']} | {v['C1_paths_named']}/{v['C1_paths_total']} | {'yes' if v['C2_snapshot'] else 'no'}{' (denied-once)' if v['C2_denied_before'] else ''} | {v['M1_gate_touched_before_first_write']} | {len(v['M2_user_corrections'])} | {v['summary_found']} | {_k(v['T1_post_prompt_actual'])} ({_k(v['T1_platform_post'])}) | {_k(v['T1_post_first_cache_write'])} |")
    for v, p in packets:
        r = p["row"]
        lines += ["", f"## {r['session'][:8]} · {r['trigger']} · {time.strftime('%Y-%m-%d %H:%M', time.localtime(r['ts']))} · {r['cwd']}", ""]
        if v["C1_missing"]:
            lines += ["**C1 缺漏路徑（候選）**："] + [f"- `{m}`" for m in v["C1_missing"]] + [""]
        if v["M2_user_corrections"]:
            lines += ["**M2 使用者更正語句**："] + [f"- L{l}: {t}" for l, t in v["M2_user_corrections"]] + [""]
        lines += ["### 讀者裁定（請填）", "- 決策是否完整帶過：", "- 已查閱清單是否以名稱保留：", "- 摘要是否誤導（把前置 gate 說成已完成）：", "- 續接第一回合是否無需詢問即可續做：", ""]
        lines += ["<details><summary>摘要 (summary)</summary>", "", "```", p["summary"] or "(not found)", "```", "</details>", ""]
        lines += ["<details><summary>交接快照 (handoff snapshot)</summary>", "", "```", p["snapshot"] or "(none)", "```", "</details>", ""]
        lines += ["<details><summary>壓縮前後回合</summary>", ""]
        for l, t in p["pre_turns"]:
            lines.append(f"- PRE L{l}: {t[:400]}")
        for l, t in p["post_turns"]:
            lines.append(f"- POST L{l}: {t[:400]}")
        lines += ["", "post-compact tool calls:"] + [f"- {n}: {a[:160]}" for n, a in p["post_calls"]] + ["", "</details>"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include manual compactions and already-audited rows")
    ap.add_argument("--post-turns", type=int, default=8)
    ap.add_argument("--out", default=str(CLAUDE_DIR / "reports"))
    ap.add_argument("--run", metavar="SESSION", help="process-ledger audit (F1/F3/F4/F6/F7 + canary) via tools/process-ledger/run_audit.py")
    a = ap.parse_args()
    if a.run:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "process-ledger"))
        import run_audit
        print(run_audit.render(run_audit.run(a.run)))
        return
    if not LOG_PATH.is_file():
        print("no telemetry yet:", LOG_PATH); return
    rows = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    todo = [r for r in rows if a.all or (r.get("trigger") == "auto" and not r.get("audited"))]
    if not todo:
        print("nothing to audit (auto compactions unaudited: 0)"); return
    packets = [audit_row(r, a.post_turns) for r in todo]
    out = render(packets, Path(a.out))
    for v, p in packets:   # backfill T1 into the telemetry row (same dict object as in rows)
        p["row"]["post_prompt_actual"] = v["T1_post_prompt_actual"]
        p["row"]["post_first_cache_write"] = v["T1_post_first_cache_write"]
        p["row"]["platform_tokens"] = {"pre": v["T1_platform_pre"], "post": v["T1_platform_post"]}
    for r in rows:
        if r in todo:
            r["audited"] = True
    LOG_PATH.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"audited {len(todo)} compaction(s) -> {out}")
    for v, p in packets:
        print(f"  {p['row']['session'][:8]} {p['row']['trigger']}: paths {v['C1_paths_named']}/{v['C1_paths_total']}, snapshot={v['C2_snapshot']}, gate_before_write={v['M1_gate_touched_before_first_write']}, corrections={len(v['M2_user_corrections'])}, post_ctx_real={v['T1_post_prompt_actual']} (platform post={v['T1_platform_post']}), first_cache_write={v['T1_post_first_cache_write']}")


if __name__ == "__main__":
    main()
