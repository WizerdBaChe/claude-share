#!/usr/bin/env python3
r"""runs — the evidence-run store of the literature-search-extract feedback loop.

Design of record: ~/.claude/references/lse-feedback-loop-design.md (§3.5 run record, §3.9
lifecycle, §3.11 forcing functions, §6.3 LSEL-04). Invariants are cited as INV-n from there.

  python runs.py init                                   create the home (README + empty index); refuses a missing vault
  python runs.py open --question "..." [--caller ID --preset NAME --depth quick|standard|exhaustive --mode 1|2
                                        --purpose .. --source-types .. --scope .. --output-format .. --language ..
                                        --domain .. --slug ..]
                                                        create <home>/<run_id>/run.json (state open) AND run the reuse
                                                        check, writing `reuse_check` into run.json (F-1, INV-4, D-L18)
  python runs.py register <run_dir>                     validate; REFUSE without reuse_check; write record.md; index +
                                                        README when filed; state -> delivered
  python runs.py find <terms...>                        NFKC+casefold search over question / keys / claims / domain
  python runs.py check <run_dir> [--json]               V1-V7 (severity by consumer); exit 2 on any FAIL
  python runs.py check --registry                       consumers/registry.json rows, status transitions, bridge freshness
  python runs.py adopt <unfiled_run_dir>                move an unfiled run into the home and index it (filed -> true)
  python runs.py affected <key-or-identifier> [--scan-srg] [--scan-papersurvey] [--json]
                                                        every run / claim / consumer / SRG row / PaperSurvey run that
                                                        cites the key; COLLISION when two bases share one unresolved hash
  python runs.py bridge                                 render references/bridge.md from the registry rows (derived)
  python runs.py list | readme                          list runs / regenerate README.md
  python runs.py --selftest                             two-sided: tests/fixtures/good-run must pass, bad-run must FAIL

Severity by consumer: FAIL where a downstream tool parses the artifact (schema, ledger presence,
card keys, key syntax, reuse_check — V1/V2/V3/V4/V7); WARN where a human/LLM reads it (unresolved
share, footer, wikilinks — V4b/V5/V6). Exit: 0 ok or WARN, 2 any FAIL, 1 usage/environment.
Never deletes: rollback of anything here is `git`/the folder, never this tool.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
SCHEMAS = HERE / "schemas"
sys.path.insert(0, str(HERE))
import idkey  # noqa: E402

DEFAULT_HOME = Path(os.environ.get("LSE_RUN_HOME", r"<vault>\literature\EvidenceRuns"))


class _EnvPath:
    """A path read from the environment at USE time (tests point these at temp copies)."""

    def __init__(self, var: str, default: Path):
        self.var, self.default = var, default

    def __call__(self) -> Path:
        return Path(os.environ.get(self.var, str(self.default)))


_UNFILED = _EnvPath("LSE_RUN_UNFILED", SKILL_DIR / "runs-unfiled")
_REGISTRY = _EnvPath("LSE_REGISTRY_PATH", SKILL_DIR / "consumers" / "registry.json")
_BRIDGE = _EnvPath("LSE_BRIDGE_PATH", SKILL_DIR / "references" / "bridge.md")
SRG_DOMAINS = SKILL_DIR.parent / "scientific-research-guide" / "domains"
PAPERSURVEY_HOME = Path(os.environ.get("PAPER_DISTILL_HOME", r"<vault>\literature\PaperSurvey"))
FIND_LIMIT = 20
# V2's numeric-claim detector. Coverage is deliberately a LIST, not a grammar: a number in a unit this list
# lacks is still a numeric claim the executor must ledger (P4.5) — the regex only catches the executor who
# forgot. Extend the list when a real run shows a miss (build-verification B-3 added the process units).
NUM_UNIT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s?(?:nm|µm|μm|um|mm|cm|m|km|Å|dB|dBm|%|ppm|ppb|K|°C|°|mA|µA|nA|A|mV|V|kV|Ω|kΩ|MΩ|eV|meV|"
    r"GHz|MHz|kHz|Hz|THz|ms|µs|ns|ps|fs|s|sec|min|h|hr|W|mW|µW|kW|J|mJ|Pa|kPa|MPa|GPa|Torr|mTorr|bar|mbar|N|mN|"
    r"kg|g|mg|µg|sccm|slm|rpm|µF|nF|pF|F|mol|M|mM|wt%|at%|cm²|cm2|µm²)\b")
FM_KEYS = ("xi:", "what:", "tags:", "aliases:", "date:", "status:", "kind: literature", "source:",
           "verified:", "review-when:", "domain:", "promoted-to:")
STOP = {"the", "and", "for", "with", "from", "that", "this", "what", "does", "are", "is", "of", "in",
        "on", "at", "to", "a", "an", "vs", "的", "與", "和", "在", "是", "有", "了"}


# ---------------------------------------------------------------- helpers
def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def fold(s) -> str:
    return unicodedata.normalize("NFKC", str(s or "")).casefold()


def home() -> Path:
    return Path(os.environ.get("LSE_RUN_HOME", str(DEFAULT_HOME)))


def home_available(h: Path | None = None) -> bool:
    """The home is available when its parent (the vault's literature/ area) exists — INV-13."""
    h = h or home()
    return h.parent.exists()


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(obj, name: str) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed — cannot validate (pip install jsonschema)"]
    v = jsonschema.Draft202012Validator(load_schema(name))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path))]


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def slugify(question: str, explicit: str | None = None) -> str:
    if explicit:
        s = re.sub(r"[^A-Za-z0-9_\-]+", "-", explicit).strip("-")
        if s:
            return s[:40]
    ascii_words = re.findall(r"[A-Za-z0-9]+", question)
    s = "-".join(w.lower() for w in ascii_words)[:40].strip("-")
    if len(s) < 4:
        s = "q-" + hashlib.sha1(question.encode("utf-8")).hexdigest()[:6]
    return s


def terms_of(question: str) -> list[str]:
    """Search terms for the reuse check: Latin/digit tokens plus CJK character BIGRAMS.

    A CJK run has no word boundaries; treating the run as one token made a pure-Chinese question
    match only its own near-verbatim copy (build-verification B-4). Bigrams are the standard
    segmenter-free answer: \u300c\u8868\u9762\u7c97\u7cd9\u5ea6\u300d\u2192 \u8868\u9762, \u9762\u7c97, \u7c97\u7cd9, \u7cd9\u5ea6 \u2014 enough overlap for a same-topic
    question phrased differently, few enough accidental hits for a different topic.
    """
    out: list[str] = []

    def add(t: str) -> None:
        f = fold(t).strip(".-")
        if len(f) >= 2 and f not in STOP and f not in out:
            out.append(f)

    for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-\.]*", question):
        add(t)
    for run in re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{2,}", question):
        if len(run) <= 3:
            add(run)
        for i in range(len(run) - 1):
            add(run[i:i + 2])
    return out


def load_index(h: Path) -> dict:
    p = h / "index.json"
    if not p.exists():
        return {"schema": "lse-runs/index@1", "home": str(h), "entries": []}
    return read_json(p)


def save_index(h: Path, idx: dict) -> None:
    write_json(h / "index.json", idx)


def load_run(run_dir: Path) -> dict:
    return read_json(Path(run_dir) / "run.json")


def save_run(run_dir: Path, run: dict) -> None:
    write_json(Path(run_dir) / "run.json", run)


def ledger_rows(run_dir: Path) -> list[dict]:
    p = Path(run_dir) / "ledger.jsonl"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"_malformed": line})
    return rows


def row_key(row: dict) -> str | None:
    r = idkey.key_from_identifier(row.get("source_id") or "")
    return r[1] if r else None


# ---------------------------------------------------------------- find (F-1)
def find_entries(h: Path, terms: list[str]) -> list[tuple[int, dict]]:
    idx = load_index(h)
    hits = []
    for e in idx["entries"]:
        hay = fold(" ".join([e.get("question", ""), " ".join(e.get("keys", [])),
                             " ".join(e.get("claims", [])), e.get("domain", ""),
                             " ".join(str(r) for r in e.get("related", []))]))
        score = sum(1 for t in terms if t and t in hay)
        if score:
            hits.append((score, e))
    hits.sort(key=lambda x: (-x[0], x[1].get("created", "")), reverse=False)
    return hits[:FIND_LIMIT]


def reuse_check(h: Path, question: str) -> dict:
    terms = terms_of(question)
    matches = []
    if h.exists():
        # with bigrams a question yields many terms; ask for a quarter of them (min 2) before calling it a match —
        # a false match only costs the executor a glance at the named run ids, a miss costs a re-search
        need = max(2, len(terms) // 4) if len(terms) >= 3 else 1
        matches = [e["run_id"] for score, e in find_entries(h, terms) if score >= need]
    line = (f"reuse check: {len(matches)} prior run(s) matched ({', '.join(matches)})"
            if matches else "reuse check: none (index searched: "
                            f"{'yes' if (h / 'index.json').exists() else 'no index yet'})")
    return {"ran_at": now_iso(), "terms": terms, "matches": matches, "trail_line": line}


# ---------------------------------------------------------------- init / open
def cmd_init(a) -> int:
    h = home()
    if not home_available(h):
        print(f"REFUSED: the home's parent does not exist: {h.parent}\n"
              "The vault is missing at this path — stop and ask the user; never recreate it "
              "(<vault>\\AGENTS.md). Set LSE_RUN_HOME to point elsewhere on purpose.")
        return 1
    h.mkdir(parents=True, exist_ok=True)
    idx = load_index(h)
    save_index(h, idx)
    if not (h / "reflux.jsonl").exists():
        (h / "reflux.jsonl").write_text("", encoding="utf-8")
    write_readme(h, idx)
    print(json.dumps({"home": str(h), "entries": len(idx["entries"]), "readme": str(h / "README.md")}, ensure_ascii=False))
    return 0


def cmd_open(a) -> int:
    h = home()
    filed = home_available(h) and (h / "index.json").exists()
    base = h if filed else _UNFILED()
    base.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().strftime("%Y%m%d")
    run_id = f"{today}_{slugify(a.question, a.slug)}"
    n = 2
    while (base / run_id).exists():
        run_id = f"{today}_{slugify(a.question, a.slug)}-{n}"
        n += 1
    run_dir = base / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "sources").mkdir()
    rc = reuse_check(h, a.question)
    if not filed:
        rc["trail_line"] += " — run not filed: home unavailable (INV-13); adopt later with `runs.py adopt`"
    run = {
        "schema": "lse-runs/run@1",
        "run": {"id": run_id, "created": now_iso(), "revision": 1, "mode": int(a.mode), "depth": a.depth,
                "state": "open", "filed": filed, "home": str(h), "wasRevisionOf": a.was_revision_of or None,
                "model": a.model or "", "skill_version": "loop@1"},
        "request": {"purpose": a.purpose or "", "question": a.question, "source_types": a.source_types or "any",
                    "scope": a.scope or "", "output_format": a.output_format or "inline summary",
                    "depth": a.depth, "language": a.language or "", "caller": a.caller or "user",
                    "preset": a.preset or None},
        "reuse_check": rc,
        "result": {"findings": "", "sources": [], "gaps": [], "confidence": [], "search_trail": [rc["trail_line"]]},
        "ledger": {"path": "ledger.jsonl", "rows": 0, "citecheck": None},
        "deliverables": [],
        "keys": [],
        "review_when": [],
        "handoff": [],
        "related": [],
        "domain": a.domain or "",
        "provenance": {"wasAttributedTo": a.model or "literature-search-extract session",
                       "wasGeneratedBy": "literature-search-extract P1–P5"},
        "invalidation": {"wasInvalidatedBy": None, "invalidatedAtTime": None, "claims": []},
    }
    errs = validate(run, "run")
    if errs:
        shutil.rmtree(run_dir, ignore_errors=True)
        print("BROKEN: the opened run does not validate — " + "; ".join(errs))
        return 2
    save_run(run_dir, run)
    print(json.dumps({"run_id": run_id, "path": str(run_dir), "filed": filed,
                      "reuse_check": rc["trail_line"], "matches": rc["matches"]}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- record.md / README
def _q(s: str) -> str:
    """Make a value safe inside a YAML double-quoted scalar: backslashes FIRST (B-5), then quotes, newlines."""
    return str(s or "").replace("\\", "\\\\").replace('"', "'").replace("\n", " ")


def footer_lines(run: dict) -> list[str]:
    keys = ", ".join(run.get("keys") or []) or "—"
    rw = run.get("review_when") or []
    lines = [f"—— 閉路 (loop) ——  run: {run['run']['id']} · keys: {keys} · 推翻條件 (review-when):"]
    if rw:
        lines += [f"{r['trigger']} {r['text']}" for r in rw]
    else:
        lines += ["T-1 任一引用來源被撤稿／勘誤（Crossref update-to；Zotero 收尾重掃會回報）",
                  "T-2 同題重跑找到 ≥10% 新來源，或出現與本表衝突的主張",
                  "T-3 任一消費者回報 correction（reflux）"]
    return lines


def wikilink_for(related: str) -> str:
    return f"[[{related}]]"


def record_md(run: dict, run_dir: Path) -> str:
    r, q = run["run"], run["request"]["question"]
    res, led = run["result"], run["ledger"]
    cc = led.get("citecheck") or {}
    n_src = len(res.get("sources") or [])
    what = (f"「{_q(q)[:60]}」證據查證紀錄 — {n_src} 來源、{led.get('rows', 0)} ledger 列、"
            f"gate {cc.get('fail', '-')}/{cc.get('warn', '-')} (evidence run {r['id']}: "
            f"literature-search-extract sources, ledger, retrieved text, review-when)")
    slug = r["id"].split("_", 1)[1] if "_" in r["id"] else r["id"]
    aliases = [r["id"], f"evidence run {slug}", f"證據查證紀錄 {slug}"]
    verified = (f"citecheck {cc.get('ran_at', '')[:10]}: {led.get('rows', 0)} rows, {cc.get('fail', 0)} FAIL, "
                f"{cc.get('warn', 0)} WARN" if cc else "citecheck not run (no ledger rows)")
    rw = "; ".join(f"{x['trigger']} {x['text']}" for x in run.get("review_when") or []) or \
        "T-1 撤稿/勘誐 · T-2 同題重跑 ≥10% 新來源或衝突 · T-3 消費者回報 correction"
    rw = rw.replace("勘誐", "勘誤")
    dom = run.get("domain") or ""
    fm = ["---", "xi: 1", f'what: "{_q(what)}"',
          "tags: [literature-search-extract, evidence-run, literature]",
          "aliases: [" + ", ".join(f'"{_q(x)}"' for x in aliases) + "]",
          f"date: {r['created'][:10]}", "status: live", "kind: literature",
          f'source: "literature-search-extract run {r["id"]}"', f'verified: "{_q(verified)}"',
          f'review-when: "{_q(rw)}"', f"domain: [{dom}]" if dom else "domain: []",
          'promoted-to: "-"', "---", ""]
    body = [f"# 【證據查證紀錄】{_q(q)}", "",
            f"run `{r['id']}` · depth `{r['depth']}` · mode {r['mode']} · caller `{run['request']['caller']}`"
            + (f" · preset `{run['request']['preset']}`" if run['request'].get('preset') else "")
            + (f" · revision of `{r['wasRevisionOf']}`" if r.get("wasRevisionOf") else ""),
            "", "## 問題 (question)", "", q, "",
            "## 交付內容 (findings, verbatim)", "", res.get("findings") or "_（尚未交付）_", "",
            "## 來源 (sources)", "",
            "| key | citation | access | locators | Zotero | aliases |", "|---|---|---|---|---|---|"]
    for s in res.get("sources") or []:
        body.append(f"| `{s['key']}` | {_q(s.get('citation'))} | [{s.get('access_level')}] | "
                    f"{', '.join(s.get('locators_used') or [])} | {s.get('zotero_key') or '—'} | "
                    f"{', '.join(s.get('aliases') or []) or '—'} |")
    if run.get("related"):
        body += ["", "相關 (related): " + " · ".join(wikilink_for(x) for x in run["related"])]
    body += ["", "## Gaps", ""] + ([f"- {g}" for g in res.get("gaps") or []] or ["- all targets filled"])
    body += ["", "## Confidence", ""]
    for c in res.get("confidence") or []:
        body.append(f"- {json.dumps(c, ensure_ascii=False) if isinstance(c, (dict, list)) else c}")
    if not res.get("confidence"):
        body.append("- no conflicts found")
    body += ["", "## search_trail", ""] + [f"- {t}" for t in res.get("search_trail") or []]
    body += ["", "## 證據帳本 (ledger)", "",
             f"`ledger.jsonl` {led.get('rows', 0)} 列 · {verified} · 原文在 `sources/`（不外流，INV-10）", ""]
    body += ["## 閉路 (loop)", ""] + footer_lines(run) + [""]
    return "\n".join(fm + body)


def write_readme(h: Path, idx: dict) -> None:
    rows = sorted(idx["entries"], key=lambda e: e.get("created", ""), reverse=True)
    today = dt.date.today().isoformat()
    lines = ["---", "xi: 1",
             "what: EvidenceRuns 文獻查證紀錄索引——每次 literature-search-extract 查證一列：問題、來源鍵、ledger 列數、gate 結果、狀態 (index of evidence runs, a paper/evidence list)",
             "tags: [literature-search-extract, evidence-run, index, topic-map]",
             "aliases: [文獻查證紀錄索引, 證據查證庫, evidence runs index, EvidenceRuns README]",
             f"date: {today}", "status: live", "kind: topic-map",
             'source: "literature-search-extract loop/runs.py register"', f'verified: "generated {today}"',
             'review-when: "lse-runs index schema changes"', "domain: []", 'promoted-to: "-"', "---", "",
             "# EvidenceRuns — literature-search-extract 文獻查證紀錄", "",
             f"由 `loop/runs.py register` 重建；共 {len(rows)} 次查證。搜尋：`python loop/runs.py find <詞>`；"
             "某來源被誰引用：`python loop/runs.py affected <key>`。", "",
             "每個 run 資料夾：`record.md`（人讀：問題、交付內容、來源表、Gaps、Confidence、閉路 footer）、"
             "`run.json`（契約，機器讀）、`ledger.jsonl` ＋ `sources/`（證據帳本與取回原文，不外流）、"
             "`citecheck.json`（關卡輸出）。回流事件在 `reflux.jsonl`。", "",
             "| run | 日期 | 問題 | 來源 | ledger | gate F/W | 狀態 |", "|---|---|---|---|---|---|---|"]
    for e in rows:
        lines.append(f"| [{e['run_id']}]({Path(e['path']).name}/record.md) | {e.get('created', '')[:10]} | "
                     f"{_q(e.get('question', ''))[:70]} | {e.get('n_sources', 0)} | {e.get('n_ledger_rows', 0)} | "
                     f"{e.get('citecheck_fail', '-')}/{e.get('citecheck_warn', '-')} | {e.get('state', '')} |")
    (h / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def index_entry(run: dict, run_dir: Path) -> dict:
    rows = ledger_rows(run_dir)
    cc = run["ledger"].get("citecheck") or {}
    return {"run_id": run["run"]["id"], "path": str(Path(run_dir).resolve()),
            "question": run["request"]["question"], "created": run["run"]["created"],
            "depth": run["run"]["depth"], "mode": run["run"]["mode"], "state": run["run"]["state"],
            "filed": run["run"]["filed"], "keys": list(run.get("keys") or []),
            "claims": [str(r.get("claim", "")) for r in rows if r.get("claim")],
            "n_sources": len(run["result"].get("sources") or []), "n_ledger_rows": len(rows),
            "citecheck_fail": cc.get("fail"), "citecheck_warn": cc.get("warn"),
            "domain": run.get("domain") or "", "related": list(run.get("related") or []),
            "caller": run["request"].get("caller", "user"), "registered": now_iso()}


def upsert_index(h: Path, run: dict, run_dir: Path) -> None:
    idx = load_index(h)
    e = index_entry(run, run_dir)
    idx["entries"] = [x for x in idx["entries"] if x["run_id"] != e["run_id"]] + [e]
    errs = validate(idx, "index")
    if errs:
        raise SystemExit("BROKEN index: " + "; ".join(errs))
    save_index(h, idx)
    write_readme(h, idx)


# ---------------------------------------------------------------- register / adopt
def refresh_ledger_stats(run: dict, run_dir: Path) -> None:
    rows = ledger_rows(run_dir)
    run["ledger"]["rows"] = len(rows)
    ccp = Path(run_dir) / "citecheck.json"
    if ccp.exists():
        try:
            cc = read_json(ccp)
            # citecheck.py --json emits a LIST of {claim_id, claim, checks: [[check, verdict, message], ...]};
            # the fixtures use a dict {ran_at, fail, warn, rows: [{checks: [{verdict}]}]} — accept both
            rows = cc.get("rows", []) if isinstance(cc, dict) else (cc if isinstance(cc, list) else [])
            fails = warns = 0
            for r in rows:
                for c in (r.get("checks") or []) if isinstance(r, dict) else []:
                    v = c.get("verdict") if isinstance(c, dict) else (c[1] if isinstance(c, (list, tuple)) and len(c) > 1 else None)
                    fails += (v == "FAIL")
                    warns += (v == "WARN")
            ran_at = cc.get("ran_at") if isinstance(cc, dict) else None
            run["ledger"]["citecheck"] = {
                "ran_at": ran_at or dt.datetime.fromtimestamp(ccp.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
                "fail": int(cc.get("fail", fails)) if isinstance(cc, dict) else fails,
                "warn": int(cc.get("warn", warns)) if isinstance(cc, dict) else warns,
                "path": "citecheck.json"}
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
    # keys: union of source keys and ledger source_id keys
    keys = list(run.get("keys") or [])
    for s in run["result"].get("sources") or []:
        if s.get("key") and s["key"] not in keys:
            keys.append(s["key"])
    for r in rows:
        k = row_key(r)
        if k and k not in keys:
            keys.append(k)
    run["keys"] = keys


def cmd_register(a) -> int:
    run_dir = Path(a.run_dir).resolve()
    run = load_run(run_dir)
    refresh_ledger_stats(run, run_dir)
    errs = validate(run, "run")
    if errs:
        print("FAIL register: run.json does not validate (nothing written) — " + "; ".join(errs))
        return 2
    rc = run.get("reuse_check") or {}
    if not rc.get("ran_at") or not str(rc.get("trail_line", "")).startswith("reuse check: "):
        print("FAIL register: no reuse_check in run.json (INV-4) — a run is opened with "
              "`runs.py open`, which performs the reuse check; nothing written")
        return 2
    if rc["trail_line"] not in (run["result"].get("search_trail") or []):
        run["result"].setdefault("search_trail", []).insert(0, rc["trail_line"])
    if run["run"]["state"] == "aborted":
        print("FAIL register: run is aborted — resume it first (revision+1); nothing written")
        return 2
    if not (run["result"].get("findings") or "").strip():
        print("FAIL register: result.findings is empty — register happens at P5, after the deliverable exists")
        return 2
    if run["ledger"]["rows"] > 0 and not run["ledger"].get("citecheck"):
        print("FAIL register: ledger rows exist but citecheck.json is missing — run `verify/citecheck.py "
              f"{run_dir / 'ledger.jsonl'} --json > {run_dir / 'citecheck.json'}` first (INV-1)")
        return 2
    if not run.get("deliverables"):
        run["deliverables"] = [{"kind": "inline", "path": None, "consumer": run["request"].get("caller", "user")}]
    if not run.get("review_when"):
        run["review_when"] = [
            {"trigger": "T-1", "text": "任一引用來源被撤稿／勘誤（Crossref update-to；Zotero 收尾重掃會回報）"},
            {"trigger": "T-2", "text": "同題重跑找到 ≥10% 新來源，或出現與本表衝突的主張"},
            {"trigger": "T-3", "text": "任一消費者回報 correction（reflux）"}]
    if run["run"]["state"] in ("open", "checked"):
        run["run"]["state"] = "delivered"
    save_run(run_dir, run)
    (run_dir / "record.md").write_text(record_md(run, run_dir), encoding="utf-8")
    if run["run"]["filed"]:
        upsert_index(home(), run, run_dir)
        where = "indexed"
    else:
        where = "NOT indexed (unfiled — `runs.py adopt` when the home is back)"
    print(json.dumps({"registered": run["run"]["id"], "state": run["run"]["state"], "index": where,
                      "keys": run["keys"], "ledger_rows": run["ledger"]["rows"],
                      "record": str(run_dir / "record.md")}, ensure_ascii=False))
    return 0


def cmd_adopt(a) -> int:
    src = Path(a.run_dir).resolve()
    run = load_run(src)
    h = home()
    if not home_available(h):
        print(f"REFUSED: home still unavailable ({h.parent} missing)")
        return 1
    h.mkdir(parents=True, exist_ok=True)
    dst = h / run["run"]["id"]
    if dst.exists():
        print(f"REFUSED: {dst} already exists — nothing moved")
        return 1
    shutil.move(str(src), str(dst))
    run = load_run(dst)
    run["run"]["filed"] = True
    run["run"]["home"] = str(h)
    save_run(dst, run)
    (dst / "record.md").write_text(record_md(run, dst), encoding="utf-8")
    if run["run"]["state"] in ("delivered", "invalidated", "superseded"):
        upsert_index(h, run, dst)
    print(json.dumps({"adopted": run["run"]["id"], "path": str(dst), "indexed": run["run"]["state"] != "open"}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- check
def check_run(run_dir: Path) -> list[tuple[str, str, str]]:
    """[(severity, rule, message)] — rules only on what a script can determine (INV-12)."""
    out: list[tuple[str, str, str]] = []
    run_dir = Path(run_dir)
    rp = run_dir / "run.json"
    if not rp.exists():
        return [("FAIL", "V1", f"no run.json in {run_dir}")]
    try:
        run = read_json(rp)
    except json.JSONDecodeError as e:
        return [("FAIL", "V1", f"run.json is not JSON: {e}")]
    errs = validate(run, "run")
    for e in errs:
        out.append(("FAIL", "V1", f"schema: {e}"))
    # keep going after schema errors so the OTHER rules still report (a bad run should name V1, V2, V3, V7)
    try:
        run.setdefault("run", {}).setdefault("state", "delivered")
        run.setdefault("result", {}).setdefault("sources", [])
        run.setdefault("ledger", {}).setdefault("rows", 0)
    except AttributeError:
        return out + [("FAIL", "V1", "run.json structure unreadable — the remaining rules cannot run")]
    rows = ledger_rows(run_dir)
    findings = run["result"].get("findings") or ""
    # V2 numeric/disputed claims => ledger + citecheck
    if rows:
        if any("_malformed" in r for r in rows):
            out.append(("FAIL", "V2", "ledger.jsonl has a malformed line"))
        if not (run_dir / "citecheck.json").exists():
            out.append(("FAIL", "V2", f"{len(rows)} ledger row(s) but no citecheck.json — the gate never ran (INV-1)"))
        elif not run["ledger"].get("citecheck"):
            out.append(("FAIL", "V2", "citecheck.json exists but run.json ledger.citecheck is null — re-run register"))
        if run["ledger"].get("rows") != len(rows):
            out.append(("FAIL", "V2", f"run.json ledger.rows={run['ledger'].get('rows')} but ledger.jsonl has {len(rows)}"))
    else:
        if NUM_UNIT_RE.search(findings) and run["run"]["state"] != "open":
            out.append(("FAIL", "V2", "findings carry a number with a unit but the ledger has no row — a numeric claim "
                                      "needs a row at EVERY depth (verification-gate.md §When to run it)"))
    # V3 record.md card
    rec = run_dir / "record.md"
    if run["run"]["state"] != "open":
        if not rec.exists():
            out.append(("FAIL", "V3", "record.md missing (run is past open)"))
        else:
            head = rec.read_text(encoding="utf-8")[:2500]
            missing = [k for k in FM_KEYS if k not in head]
            if missing:
                out.append(("FAIL", "V3", f"record.md front matter lacks: {', '.join(missing)}"))
            if "{{" in head:
                out.append(("FAIL", "V3", "record.md still carries a {{placeholder}}"))
    # V4 keys
    unresolved = 0
    for s in run["result"].get("sources") or []:
        if not idkey.is_key(s.get("key", "")):
            out.append(("FAIL", "V4", f"source key not well-formed: {s.get('key')!r} (citation {s.get('citation', '')[:40]!r})"))
        if s.get("unresolved"):
            unresolved += 1
            if not s.get("unresolved_basis"):
                out.append(("FAIL", "V4", f"unresolved key {s.get('key')} without unresolved_basis (D-L19)"))
    for k in run.get("keys") or []:
        if not idkey.is_key(k):
            out.append(("FAIL", "V4", f"keys[] entry not well-formed: {k!r}"))
    n_src = len(run["result"].get("sources") or [])
    if n_src and unresolved / n_src > 0.3:
        out.append(("WARN", "V4b", f"{unresolved}/{n_src} sources unresolved (> 30 %) — R3 precedence should be re-checked (design §10)"))
    # V5 footer
    if run["run"]["state"] != "open" and rec.exists():
        if "閉路 (loop)" not in rec.read_text(encoding="utf-8"):
            out.append(("WARN", "V5", "record.md has no loop footer (run_id · keys · review-when)"))
    # V6 related wikilinks resolve (PaperSurvey run dirs or SRG profile basenames)
    for rel in run.get("related") or []:
        ok = (PAPERSURVEY_HOME / rel).exists() or list(SRG_DOMAINS.rglob(f"{rel}.md")) if SRG_DOMAINS.exists() else False
        if not ok:
            out.append(("WARN", "V6", f"related '{rel}' resolves to neither a PaperSurvey run nor a domain profile"))
    # V7 reuse_check (F-1 gate — D-L18)
    rc = run.get("reuse_check") or {}
    if not rc.get("ran_at"):
        out.append(("FAIL", "V7", "no reuse_check — the run was not opened with `runs.py open` (INV-4)"))
    else:
        cc = run["ledger"].get("citecheck") or {}
        if cc.get("ran_at") and rc["ran_at"] > cc["ran_at"]:
            out.append(("FAIL", "V7", "reuse_check.ran_at is later than citecheck.ran_at — the reuse check did not precede P2"))
        if rc.get("trail_line") not in (run["result"].get("search_trail") or []) and run["run"]["state"] != "open":
            out.append(("FAIL", "V7", "reuse_check.trail_line is not in result.search_trail — the check was not logged"))
    return out


def print_findings(findings, as_json=False) -> int:
    fails = [f for f in findings if f[0] == "FAIL"]
    if as_json:
        print(json.dumps({"fail": len(fails), "warn": len(findings) - len(fails),
                          "findings": [{"severity": s, "rule": r, "message": m} for s, r, m in findings]}, ensure_ascii=False, indent=1))
    else:
        for s, r, m in findings:
            print(f"{s:5} {r:4} {m}")
        print(f"{len(fails)} FAIL, {len(findings) - len(fails)} WARN")
    return 2 if fails else 0


def registry_sha() -> str:
    return hashlib.sha256(_REGISTRY().read_bytes()).hexdigest()


def check_registry() -> list[tuple[str, str, str]]:
    out = []
    REGISTRY, BRIDGE = _REGISTRY(), _BRIDGE()
    if not REGISTRY.exists():
        return [("FAIL", "R1", f"registry missing: {REGISTRY}")]
    try:
        reg = read_json(REGISTRY)
    except json.JSONDecodeError as e:
        return [("FAIL", "R1", f"registry is not JSON: {e}")]
    for e in validate(reg, "consumer"):
        out.append(("FAIL", "R1", f"schema: {e}"))
    allowed = {("planned", "live"), ("live", "retired"), ("retired", "live"), ("planned", "retired")}
    ids = set()
    for row in reg.get("consumers", []):
        if row.get("id") in ids:
            out.append(("FAIL", "R2", f"duplicate consumer id {row.get('id')}"))
        ids.add(row.get("id"))
        hist = [x.get("status") for x in row.get("history") or []] + [row.get("status")]
        for a_, b_ in zip(hist, hist[1:]):
            if a_ != b_ and (a_, b_) not in allowed:
                out.append(("FAIL", "R3", f"{row.get('id')}: illegal status transition {a_} -> {b_} (design §3.8.1)"))
        if row.get("direction") in ("store", "indirect") and row.get("status") != "live":
            out.append(("FAIL", "R3", f"{row.get('id')}: direction {row['direction']} rows are live by definition"))
    if BRIDGE.exists():
        head = BRIDGE.read_text(encoding="utf-8")[:1500]
        m = re.search(r"generated-from: consumers/registry.json sha256:([0-9a-f]{64})", head)
        if not m:
            out.append(("FAIL", "R4", "references/bridge.md has no generated-from line — it must be rendered by `runs.py bridge`"))
        elif m.group(1) != registry_sha():
            out.append(("FAIL", "R4", "references/bridge.md is stale against consumers/registry.json — run `runs.py bridge`"))
    else:
        out.append(("WARN", "R4", "references/bridge.md not rendered yet — run `runs.py bridge`"))
    return out


def cmd_check(a) -> int:
    if a.registry:
        return print_findings(check_registry(), a.json)
    if not a.run_dir:
        print("usage: runs.py check <run_dir> | --registry")
        return 1
    return print_findings(check_run(Path(a.run_dir)), a.json)


# ---------------------------------------------------------------- bridge (derived)
def cmd_bridge(a) -> int:
    REGISTRY, BRIDGE = _REGISTRY(), _BRIDGE()
    reg = read_json(REGISTRY)
    sha = registry_sha()
    L = ["---", "xi: 1",
         "what: literature-search-extract 與每個消費者的橋接——依情況互相呼叫、共用什麼、什麼不跨越；由登錄表產生，勿手改 (bridge between the literature skill and its consumers, generated from consumers/registry.json)",
         "tags: [literature-search-extract, bridge, consumers, generated]",
         "aliases: [LSE 橋接, 文獻 skill 消費者橋接, lse bridge, literature-search-extract bridge]",
         f"date: {dt.date.today().isoformat()}", "status: live", "---",
         f"<!-- generated-from: consumers/registry.json sha256:{sha} — rendered by loop/runs.py bridge; never hand-edit (design D-L17) -->",
         "", "# Bridge — literature-search-extract and its consumers (generated)", "",
         "A consumer is a ROW in `consumers/registry.json`; this file is that registry rendered for reading.",
         "Edit the row, then `python loop/runs.py bridge`.", "",
         "## Shared by design", "",
         "- **Evidence run**: every LSE run that reaches P4.5 persists in the vault home (`references/feedback-loop.md`);",
         "  a Mode 2 return carries `run_id` and `sources[].key`, so a consumer can cite without re-resolving.",
         "- **Identity key**: one normalizer (`loop/idkey.py`); joins are computed at read time from each store's",
         "  identity field — no store is migrated.",
         "- **Reflux**: the only write path back is `loop/reflux.py` (consumed / correction / retraction / handoff / rerun).",
         "", "## What never crosses", "",
         "- Verdict words (provisional / leaning / hypothetical / withhold) are paper-distill's; LSE quotes, never invents.",
         "- Methodology (what to search for, how evidence bears on the user's study) stays with scientific-research-guide.",
         "- LSE never advises on the user's own study design and never writes into a consumer's store or into Zotero.",
         ""]
    for row in reg.get("consumers", []):
        L += [f"## {row['id']}", "",
              f"- status `{row['status']}` · direction `{row['direction']}` · registered {row['registered']}",
              f"- why it matters here: {row.get('why_it_matters_here', '')}"]
        calls = row.get("calls") or {}
        if calls.get("presets"):
            L.append("- request presets (fill the rest from context):")
            for name, p in calls["presets"].items():
                L.append(f"  - `{name}`: " + "; ".join(f"{k}={v}" for k, v in p.items()))
        if row.get("consumes"):
            L.append("- consumes: " + ", ".join(f"`{c}`" for c in row["consumes"]))
        if row.get("writes_back"):
            L.append("- writes back: " + ", ".join(f"`{c}`" for c in row["writes_back"]))
        st = row.get("store") or {}
        L.append(f"- artifact: {row.get('artifact_kind', '')} · store `{st.get('path', '')}` · identity field: {st.get('identity_field', '')} · run pointer: {st.get('run_pointer', '')}")
        if row.get("situations"):
            L.append("- calls by situation:")
            L += [f"  - {s}" for s in row["situations"]]
        L += [f"- review-when: {row.get('review_when', '')}", ""]
    BRIDGE.write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({"bridge": str(BRIDGE), "rows": len(reg.get('consumers', [])), "sha256": sha[:12]}))
    return 0


# ---------------------------------------------------------------- affected
def _load_profile_lint():
    p = SRG_DOMAINS.parent / "tools" / "profile-lint.py"
    if not p.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("profile_lint", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        return mod
    except Exception:  # noqa: BLE001 - the fallback parser below is used
        return None


def srg_rows() -> list[dict]:
    """Source-ledger rows across every profile: {profile, key_cell, identifier_cell, status_cell, line}."""
    out = []
    if not SRG_DOMAINS.exists():
        return out
    mod = _load_profile_lint()
    for md in sorted(SRG_DOMAINS.rglob("*.md")):
        if md.name.startswith("_") or md.name == "domain-expansion-guide.md":
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^##+ .*Source Ledger.*$", text, re.M)
        if not m:
            continue
        seg = text[m.end():]
        nxt = re.search(r"^## ", seg, re.M)
        seg = seg[:nxt.start()] if nxt else seg
        rows = None
        if mod and hasattr(mod, "ledger_rows"):
            try:
                rows = mod.ledger_rows(seg)
            except Exception:  # noqa: BLE001
                rows = None
        if rows is None:
            rows = [ln for ln in seg.splitlines() if ln.startswith("| [") or ln.startswith("| ❌")]
        for r in rows:
            line = r if isinstance(r, str) else "|".join(str(c) for c in r) if isinstance(r, (list, tuple)) else str(r)
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            out.append({"profile": md.relative_to(SRG_DOMAINS).as_posix(), "key_cell": cells[0],
                        "identifier_cell": cells[2] if len(cells) > 2 else "", "citation_cell": cells[1],
                        "status_cell": cells[4] if len(cells) > 4 else "", "line": line})
    return out


def papersurvey_entries() -> list[dict]:
    p = PAPERSURVEY_HOME / "index.json"
    if not p.exists():
        return []
    try:
        return read_json(p).get("entries", [])
    except json.JSONDecodeError:
        return []


def cmd_affected(a) -> int:
    h = home()
    target = a.key
    if not idkey.is_key(target):
        r = idkey.key_from_identifier(target)
        if not r:
            print(f"not a key or a valid identifier: {target!r}")
            return 1
        target = r[1]
    idx = load_index(h)
    runs_hit, claims_hit, bases = [], [], {}
    for e in idx["entries"]:
        run_dir = Path(e["path"])
        keys = set(e.get("keys") or [])
        rows = ledger_rows(run_dir) if run_dir.exists() else []
        claim_ids = [r.get("claim_id") for r in rows if row_key(r) == target]
        if target in keys or claim_ids:
            runs_hit.append({"run_id": e["run_id"], "state": e.get("state"), "claims": claim_ids, "path": e["path"]})
            claims_hit += [{"run_id": e["run_id"], "claim_id": c} for c in claim_ids]
            if target.startswith("unresolved:") and run_dir.exists():
                for s in load_run(run_dir)["result"].get("sources") or []:
                    if s.get("key") == target and s.get("unresolved_basis"):
                        bases.setdefault(json.dumps(s["unresolved_basis"], sort_keys=True, ensure_ascii=False), []).append(e["run_id"])
    events, consumers = [], {}
    rf = h / "reflux.jsonl"
    if rf.exists():
        run_ids = {r["run_id"] for r in runs_hit}
        for line in rf.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                events.append({"_quarantined": line[:80]})
                continue
            if ev.get("key") == target or ev.get("run_id") in run_ids:
                events.append(ev)
                if ev.get("kind") == "consumed":
                    consumers.setdefault(ev.get("actor"), []).append(ev.get("artifact"))
    res = {"key": target, "runs": runs_hit, "claims": claims_hit, "events": events,
           "consumers": {k: v for k, v in consumers.items()}, "collision": None}
    if len(bases) > 1:
        res["collision"] = {"bases": list(bases.keys()), "runs_by_basis": bases}
    # Zotero join (read-only)
    try:
        sys.path.insert(0, str(SKILL_DIR / "connectors"))
        import zotero_local  # type: ignore
        inv = zotero_local.registered()
        db = Path(inv.get("db", ""))
        snap = zotero_local.open_snapshot(db) if db.name else None
        if snap:
            con, tmp = snap
            try:
                items = zotero_local.load_items(con)
            finally:
                con.close()
                shutil.rmtree(tmp.parent, ignore_errors=True)
            zk = []
            for it in items:
                arch = (it.get("archiveID") or "").strip()          # Zotero 7 preprint field (B-2)
                cand = {"doi": it.get("DOI", ""), "arxiv": arch if arch.lower().startswith("arxiv") else "",
                        "identifier": it.get("extra", "")}
                k = idkey.normalize(cand)["key"] if (cand["doi"] or cand["arxiv"] or cand["identifier"]) else None
                if k == target:
                    zk.append({"item_key": it["item_key"], "doi_as_stored": it.get("DOI", ""),
                               "pdf": any(a["file"].lower().endswith(".pdf") for a in it.get("attachments", []))})
            res["zotero"] = zk
    except Exception as e:  # noqa: BLE001 - Zotero is optional
        res["zotero"] = f"not joined: {e.__class__.__name__}"
    if a.scan_papersurvey:
        ps = []
        for e in papersurvey_entries():
            k = idkey.normalize({"doi": e.get("doi", ""), "title": e.get("title", ""),
                                 "author": e.get("first_author", ""), "year": e.get("year", "")})
            if k["key"] == target:
                ps.append({"run_id": e.get("run_id"), "doi": e.get("doi", ""), "unresolved": k["unresolved"]})
        res["papersurvey"] = ps
    if a.scan_srg:
        hits, no_key = [], []
        for row in srg_rows():
            found = idkey.find_all(row["identifier_cell"] + " " + row["citation_cell"])
            if found:
                if any(f["key"] == target for f in found):
                    hits.append({"profile": row["profile"], "key_cell": row["key_cell"],
                                 "keys": [f["key"] for f in found]})
            else:
                no_key.append({"profile": row["profile"], "key_cell": row["key_cell"]})
        res["srg"] = {"rows": hits, "rows_without_derivable_key": no_key}
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(f"key {target}")
        print(f"  runs: {len(runs_hit)}  claims: {len(claims_hit)}  events: {len(events)}  consumers: {list(consumers)}")
        for r in runs_hit:
            print(f"  - run {r['run_id']} [{r['state']}] claims {r['claims']}")
        if res["collision"]:
            print(f"  COLLISION: {len(bases)} distinct bases share {target} — lists kept apart:")
            for b, ids in bases.items():
                print(f"    basis {b} -> runs {ids}")
        if isinstance(res.get("zotero"), list):
            for z in res["zotero"]:
                print(f"  - Zotero {z['item_key']} DOI as stored {z['doi_as_stored']!r} pdf={z['pdf']}")
        if a.scan_papersurvey:
            for p in res["papersurvey"]:
                print(f"  - PaperSurvey {p['run_id']} (doi {p['doi'] or 'empty -> unresolved'})")
        if a.scan_srg:
            for r in res["srg"]["rows"]:
                print(f"  - SRG {r['profile']} {r['key_cell']}")
            print(f"  SRG rows with no derivable key (next-touch retrofit, guide §3.8): {len(res['srg']['rows_without_derivable_key'])}")
            for r in res["srg"]["rows_without_derivable_key"][:12]:
                print(f"    WARN {r['profile']} {r['key_cell']}")
    return 0


# ---------------------------------------------------------------- list / readme / find / selftest
def cmd_list(a) -> int:
    idx = load_index(home())
    for e in sorted(idx["entries"], key=lambda x: x.get("created", ""), reverse=True):
        print(f"{e['run_id']}\t{e.get('state')}\t{e.get('question', '')[:70]}\tkeys={len(e.get('keys', []))}")
    print(f"{len(idx['entries'])} run(s) in {home()}")
    return 0


def cmd_readme(a) -> int:
    h = home()
    idx = load_index(h)
    write_readme(h, idx)
    print(str(h / "README.md"))
    return 0


def cmd_find(a) -> int:
    h = home()
    terms = [fold(t) for t in a.terms]
    hits = find_entries(h, terms)
    if not hits:
        print(f"no prior run matches {' '.join(a.terms)!r} in {h} — an empty result never means the "
              "literature was not searched before elsewhere; it means THIS index has nothing")
        return 1
    for score, e in hits:
        print(f"{score}\t{e['run_id']}\t[{e.get('state')}]\t{e.get('question', '')[:80]}")
    return 0


def selftest() -> int:
    good = HERE / "tests" / "fixtures" / "good-run"
    bad = HERE / "tests" / "fixtures" / "bad-run"
    if not good.exists() or not bad.exists():
        print("ONE-SIDED — fixtures missing; refusing to report")
        return 2
    g = check_run(good)
    b = check_run(bad)
    gf = [x for x in g if x[0] == "FAIL"]
    bf = [x for x in b if x[0] == "FAIL"]
    print(f"good-run: {len(gf)} FAIL / {len(g) - len(gf)} WARN  (must be 0 FAIL)")
    for s, r, m in g:
        print(f"   {s:5} {r:4} {m}")
    print(f"bad-run:  {len(bf)} FAIL / {len(b) - len(bf)} WARN  (must be >= 4 FAIL naming V1/V2/V3/V7)")
    for s, r, m in b:
        print(f"   {s:5} {r:4} {m}")
    rules = {r for _, r, _ in bf}
    ok = not gf and len(bf) >= 4 and {"V1", "V2", "V3", "V7"} <= rules
    print("calibrated" if ok else "BROKEN instrument")
    return 0 if ok else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("init")
    o = sub.add_parser("open")
    o.add_argument("--question", required=True)
    o.add_argument("--caller", default="user")
    o.add_argument("--preset", default="")
    o.add_argument("--depth", default="quick", choices=["quick", "standard", "exhaustive"])
    o.add_argument("--mode", default="1", choices=["1", "2"])
    for f in ("purpose", "source_types", "scope", "output_format", "language", "domain", "slug", "model", "was_revision_of"):
        o.add_argument(f"--{f.replace('_', '-')}", dest=f, default="")
    r = sub.add_parser("register"); r.add_argument("run_dir")
    f = sub.add_parser("find"); f.add_argument("terms", nargs="+")
    c = sub.add_parser("check"); c.add_argument("run_dir", nargs="?"); c.add_argument("--registry", action="store_true"); c.add_argument("--json", action="store_true")
    ad = sub.add_parser("adopt"); ad.add_argument("run_dir")
    af = sub.add_parser("affected"); af.add_argument("key"); af.add_argument("--scan-srg", action="store_true"); af.add_argument("--scan-papersurvey", action="store_true"); af.add_argument("--json", action="store_true")
    sub.add_parser("bridge"); sub.add_parser("list"); sub.add_parser("readme")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    return {"init": cmd_init, "open": cmd_open, "register": cmd_register, "find": cmd_find, "check": cmd_check,
            "adopt": cmd_adopt, "affected": cmd_affected, "bridge": cmd_bridge, "list": cmd_list,
            "readme": cmd_readme}.get(a.cmd, lambda _: (ap.print_help(), 1)[1])(a)


if __name__ == "__main__":
    sys.exit(main())
