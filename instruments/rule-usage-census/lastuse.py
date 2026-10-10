r"""lastuse — when was each READING-class component last used (path rules, local skills).

STATUS: LIVE since 2026-10-06 (user ruling 「同意做」 on the outside feedback item
"reading-class components: loading IS use"). system-hmi native source
`reading-use`, slow tier (daily `hmi.py verdict --full`).

WHY. A hook proves itself by running (pol.py); a path rule or a skill only acts
when it is READ, and nothing watched whether that ever happens: 123 of 211 HMI
components had no point on 2026-10-06, all 35 skills among them. Loading is the
use, so the last load date is the reading.

WHAT IT CAN DETERMINE, AND WHAT IT CANNOT. It determines the date of the last
load. It cannot determine that a component is dead: a domain rule (Android,
copyrighted pages) stays unloaded while no work of that domain happens. So the
state is WARN, never FAIL, and the finding says "review", not "retire". A
component the user has ruled dormant on purpose goes into `dormant.json` with a
reason and a review-when trigger and is reported, not warned.

SOURCES (existing records, nothing new is logged):
  path rules  telemetry/rule-loads.jsonl, InstructionsLoaded rows with
              load_reason == path_glob_match (hooks/instructions_loaded_logger.py)
  skills      the session archive (default ~/.claude/projects; a mirror of the same layout also works):
              a Skill tool_use naming the skill, a user `<command-name>/x`, or a
              Read of skills/<x>/SKILL.md (skills that other skills point at are
              loaded that way; an Edit is maintenance, not use).
              Scanned incrementally: cache/rule-usage-census/lastuse-cache.json
              keys every transcript by (mtime, size).
  agents      the same archive, its OWN cache (lastuse-agents-cache.json, so the
              skills cache and the two older points are untouched): an `Agent`
              tool_use whose input.subagent_type == the agent file's frontmatter
              `name`, or a Read of agents/<stem>.md (stem -> `name`: the file name
              and `name` differ for 6 of 10 files). Edit/Write is not use. Built-in
              types (general-purpose, Explore, Plan, claude-code-guide ...) have no
              file and are ignored; a Read of a file that no longer exists is too.
              Point `reading-use.agents` (snapshot-unification WC-05a, 02 §9.1).

RULE per component (STALE_DAYS = 30):
  used within STALE_DAYS            -> ok
  dormant.json row                  -> reported as dormant (no warn)
  never used, born < STALE_DAYS ago -> reported as young (no warn)
  otherwise                         -> warn "review" (last use or never)
A point whose source is missing is ran:true, state null, quality undetermined.

Usage:
  python -X utf8 tools/rule-usage-census/lastuse.py check     human table
  python -X utf8 tools/rule-usage-census/lastuse.py emit      hmi-report/1 on stdout
  python -X utf8 tools/rule-usage-census/lastuse.py --selftest
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
ARCHIVE = Path(os.environ.get("LASTUSE_ARCHIVE") or HOME / "projects")
CACHE = HOME / "cache" / "rule-usage-census" / "lastuse-cache.json"
DORMANT = Path(__file__).resolve().parent / "dormant.json"
SOURCE = "reading-use"
STALE_DAYS = 30
CMD_RE = re.compile(r"<command-name>/?([A-Za-z0-9_:\-]+)</command-name>")
SKILL_READ_RE = re.compile(r"skills[\\/]+([A-Za-z0-9_\-]+)[\\/]+SKILL\.md$")
CACHE_VERSION = 2   # bump when what _scan_transcript counts changes; a stale cache is rescanned
AGENTS_CACHE = HOME / "cache" / "rule-usage-census" / "lastuse-agents-cache.json"
# group = FILE STEM, not frontmatter name. Anchored on a `.claude` directory: a same-named file in another repo
# (another repo's agents/*.md, read 2026-09-07) is not a load of THIS machine's agent definition.
AGENT_READ_RE = re.compile(r"[\\/]\.claude[\\/]+agents[\\/]+([A-Za-z0-9_\-]+)\.md$")
AGENT_CACHE_VERSION = 2   # bump when what _scan_transcript_agents counts changes (v2: Read regex anchored on .claude)
FRONTMATTER_NAME_RE = re.compile(r"^name:[ \t]*(.+?)[ \t]*$", re.M)


def _iso(ts) -> str | None:
    """Normalise an ISO string or epoch seconds to YYYY-MM-DD."""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")
    return str(ts)[:10] if re.match(r"\d{4}-\d{2}-\d{2}", str(ts)) else None


def rule_uses(home=HOME) -> dict | None:
    """rules/<name>.md -> last date it was loaded by a path-glob match; None if no log."""
    p = home / "telemetry" / "rule-loads.jsonl"
    if not p.is_file():
        return None
    last = {}
    with p.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "path_glob_match" not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            pl = r.get("payload") if isinstance(r.get("payload"), dict) else {}
            fp = str(pl.get("file_path") or "").replace("\\", "/")
            if pl.get("load_reason") != "path_glob_match" or "/rules/" not in fp:
                continue
            k = "rules/" + fp.rsplit("/rules/", 1)[-1]
            d = _iso(r.get("ts"))
            if d and d > last.get(k, ""):
                last[k] = d
    return last


def _scan_transcript(path: str) -> dict:
    """skill name -> last date used in one transcript."""
    last = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if '"Skill"' not in line and "command-name" not in line and "SKILL.md" not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            d = _iso(r.get("timestamp"))
            if not d:
                continue
            m = r.get("message") if isinstance(r.get("message"), dict) else {}
            names = []
            if r.get("type") == "assistant":
                for b in m.get("content") or []:
                    if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                        continue
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    if b.get("name") == "Skill":
                        names.append(str(inp.get("skill") or ""))
                    elif b.get("name") == "Read":   # a skill another skill points at is loaded by Read
                        m2 = SKILL_READ_RE.search(str(inp.get("file_path") or ""))
                        if m2:
                            names.append(m2.group(1))
            elif r.get("type") == "user":
                c = m.get("content")
                text = c if isinstance(c, str) else " ".join(
                    b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
                names += CMD_RE.findall(text)
            for n in names:
                n = n.split(":")[-1].strip()
                if n and d > last.get(n, ""):
                    last[n] = d
    return last


def skill_uses(archive=ARCHIVE, cache_path=CACHE) -> dict | None:
    """skill name -> last date used across the archive; None if the archive is missing."""
    if not Path(archive).is_dir():
        return None
    try:
        doc = json.loads(Path(cache_path).read_text(encoding="utf-8"))
        cache = doc.get("files", {}) if doc.get("version") == CACHE_VERSION else {}
    except Exception:
        cache = {}
    fresh, last = {}, {}
    for f in glob.glob(str(archive) + "/**/*.jsonl", recursive=True):
        try:
            st = os.stat(f)
        except OSError:
            continue
        key = [int(st.st_mtime), st.st_size]
        hit = cache.get(f)
        per = hit[1] if hit and hit[0] == key else _scan_transcript(f)
        fresh[f] = [key, per]
        for n, d in per.items():
            if d > last.get(n, ""):
                last[n] = d
    try:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(cache_path) + ".tmp")
        tmp.write_text(json.dumps({"version": CACHE_VERSION, "files": fresh}), encoding="utf-8")
        os.replace(tmp, cache_path)
    except Exception:
        pass
    return last


def _scan_transcript_agents(path: str) -> dict:
    """One transcript -> {"d:<subagent_type>" | "r:<file stem>": last date}.

    Raw tokens are cached (not agent names) so the cache stays valid when agents/ gains or
    loses a file; the stem -> name mapping is applied at merge time in agent_uses()."""
    last = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if "subagent_type" not in line and "agents/" not in line and "agents\\\\" not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("type") != "assistant":
                continue
            d = _iso(r.get("timestamp"))
            if not d:
                continue
            m = r.get("message") if isinstance(r.get("message"), dict) else {}
            for b in m.get("content") or []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                if b.get("name") == "Agent":
                    k = "d:" + str(inp.get("subagent_type") or "").strip()
                elif b.get("name") == "Read":      # Edit/Write are maintenance, not use
                    m2 = AGENT_READ_RE.search(str(inp.get("file_path") or ""))
                    k = "r:" + m2.group(1) if m2 else ""
                else:
                    k = ""
                if len(k) > 2 and d > last.get(k, ""):
                    last[k] = d
    return last


def agent_uses(stem2name: dict, archive=ARCHIVE, cache_path=AGENTS_CACHE) -> dict | None:
    """agent frontmatter name -> last date dispatched or read across the archive; None if the
    archive is missing. Own cache file keyed (mtime, size) per transcript, like skill_uses."""
    if not Path(archive).is_dir():
        return None
    try:
        doc = json.loads(Path(cache_path).read_text(encoding="utf-8"))
        cache = doc.get("files", {}) if doc.get("version") == AGENT_CACHE_VERSION else {}
    except Exception:
        cache = {}
    names = set(stem2name.values())
    fresh, last = {}, {}
    for f in glob.glob(str(archive) + "/**/*.jsonl", recursive=True):
        try:
            st = os.stat(f)
        except OSError:
            continue
        key = [int(st.st_mtime), st.st_size]
        hit = cache.get(f)
        per = hit[1] if hit and hit[0] == key else _scan_transcript_agents(f)
        fresh[f] = [key, per]
        for tok, d in per.items():
            n = tok[2:] if tok.startswith("d:") else stem2name.get(tok[2:])
            if n in names and d > last.get(n, ""):
                last[n] = d
    try:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(str(cache_path) + ".tmp")
        tmp.write_text(json.dumps({"version": AGENT_CACHE_VERSION, "files": fresh}), encoding="utf-8")
        os.replace(tmp, cache_path)
    except Exception:
        pass
    return last


def agent_components(home=HOME) -> tuple:
    """-> (components [(label, name)], stem2name, label -> repo-relative file). Key = frontmatter
    `name` (file stem when a file has none); built-in agent types have no file, so none appear."""
    comps, stem2name, files = [], {}, {}
    for p in sorted((home / "agents").glob("*.md")):
        try:
            head = p.read_text(encoding="utf-8", errors="replace").split("\n---", 1)[0]
            m = FRONTMATTER_NAME_RE.search(head) if head.lstrip().startswith("---") else None
        except OSError:
            continue
        name = m.group(1).strip().strip("\"'") if m else p.stem
        comps.append((f"agents/{name}", name))
        stem2name[p.stem] = name
        files[f"agents/{name}"] = f"agents/{p.name}"
    return comps, stem2name, files


def born(home: Path, rel: str) -> str | None:
    """Date the file first entered git history in ~/.claude (None when untracked)."""
    try:
        p = subprocess.run(["git", "-C", str(home), "log", "--diff-filter=A", "--format=%as", "--", rel],
                           capture_output=True, text=True, encoding="utf-8", timeout=20)
        out = [l for l in p.stdout.split() if l]
        return out[-1] if out else None
    except Exception:
        return None


def judge(components: list, uses: dict | None, dormant: dict, today: str, birth) -> tuple:
    """-> (state, quality, rows). rows: (component, last, verdict)."""
    if uses is None:
        return None, "undetermined", []
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=STALE_DAYS)).isoformat()
    rows = []
    for comp, key in components:
        last = uses.get(key)
        if last and last >= cut:
            v = "ok"
        elif comp in dormant:
            v = "dormant"
        elif not last and (birth(comp) or "0000") >= cut:
            v = "young"
        else:
            v = "review"
        rows.append((comp, last, v))
    return ("warn" if any(v == "review" for _, _, v in rows) else "pass"), "good", rows


def components(home=HOME):
    rules = [(f"rules/{p.name}", f"rules/{p.name}") for p in sorted((home / "rules").glob("*.md"))]
    skills = [(f"skills/{p.parent.name}", p.parent.name) for p in sorted((home / "skills").glob("*/SKILL.md"))]
    return rules, skills


def _point(slug, alias, state, quality, rows, src, notes=None) -> dict:
    """One hmi-report/1 point from judge() output. notes: component -> text prefix (agents only)."""
    notes = notes or {}
    review = [r for r in rows if r[2] == "review"]
    findings = [{"severity": "warn", "label": f"{c}: review (loading is use)",
                 "text": f"{notes.get(c, '')}last use {last or 'never on record'}; older than {STALE_DAYS} days. "
                         "Dormant on purpose -> add a dormant.json row with reason + review_when."}
                for c, last, _ in review]
    findings += [{"severity": "info", "label": f"{c}: {v}", "text": f"{notes.get(c, '')}last use {last or 'never'}"}
                 for c, last, v in rows if v in ("dormant", "young")]
    return {
        "id": f"{SOURCE}.{slug}", "alias": alias,
        "class": "integrity", "ran": True, "skip_reason": None,
        "state": state, "quality": quality,
        "findings": findings if quality == "good" else [
            {"severity": "undetermined", "label": "source missing", "text": src}],
        "remedy": "python -X utf8 tools/rule-usage-census/lastuse.py check"}


def build(home=HOME, archive=ARCHIVE, cache_path=CACHE, today=None, dormant_path=DORMANT,
          agents_cache_path=AGENTS_CACHE) -> dict:
    today = today or time.strftime("%Y-%m-%d")
    try:
        dormant = json.loads(Path(dormant_path).read_text(encoding="utf-8"))
    except Exception:
        dormant = {}
    rules, skills = components(home)
    points = []
    for slug, comps, uses, src in (
            ("path-rules", rules, rule_uses(home), "telemetry/rule-loads.jsonl"),
            ("skills", skills, skill_uses(archive, cache_path), str(archive))):
        state, quality, rows = judge(comps, uses, dormant, today, lambda c: born(home, c))
        points.append(_point(slug, f"{slug}：多久沒被載入", state, quality, rows, src))
    # agents: own cache, own component rule (frontmatter name); no agent file at all is undetermined, never pass
    acomps, stem2name, afiles = agent_components(home)
    auses = agent_uses(stem2name, archive, agents_cache_path) if acomps else None
    state, quality, rows = judge(acomps, auses, dormant, today, lambda c: born(home, afiles.get(c, c)))
    notes = {c: f"file {f}; " for c, f in afiles.items() if f != f"{c}.md"}
    points.append(_point("agents", "代理人定義：多久沒被派工或讀取", state, quality, rows,
                         str(archive) if acomps else "agents/*.md", notes))
    return {"protocol": "hmi-report/1", "source": SOURCE,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "points": points}


def cmd_check():
    doc = build()
    for p in doc["points"]:
        print(f"{p['id']}: {p['state']} ({p['quality']})")
        for f in p["findings"]:
            print(f"  [{f['severity']}] {f['label']} -- {f['text'][:90]}")


def selftest() -> int:
    fails = []

    def expect(name, got, want):
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  (got {got!r}, want {want!r})"))
        if not ok:
            fails.append(name)

    today = "2026-10-06"
    comps = [("rules/a.md", "rules/a.md"), ("rules/b.md", "rules/b.md"), ("rules/c.md", "rules/c.md"),
             ("rules/d.md", "rules/d.md")]
    births = {"rules/c.md": "2026-10-01"}
    uses = {"rules/a.md": "2026-10-05", "rules/b.md": "2026-08-01"}
    st, q, rows = judge(comps, uses, {"rules/d.md": {"reason": "x"}}, today, lambda c: births.get(c, "2026-07-01"))
    v = {c: x for c, _, x in rows}
    expect("recent use -> ok", v["rules/a.md"], "ok")
    expect("use older than 30 d -> review", v["rules/b.md"], "review")
    expect("never used, born 5 d ago -> young", v["rules/c.md"], "young")
    expect("never used, ruled dormant -> dormant", v["rules/d.md"], "dormant")
    expect("any review -> point warns (never fails)", st, "warn")
    st2, _, _ = judge(comps[:1], uses, {}, today, lambda c: "2026-07-01")
    expect("all recent -> pass", st2, "pass")
    st3, q3, rows3 = judge(comps, None, {}, today, lambda c: None)
    expect("undetermined: source missing -> state None, quality undetermined, no verdicts",
           (st3, q3, rows3), (None, "undetermined", []))

    with tempfile.TemporaryDirectory() as td:
        arch = Path(td) / "arch" / "proj"
        arch.mkdir(parents=True)
        t = arch / "s.jsonl"
        recs = [
            {"type": "assistant", "timestamp": "2026-09-01T00:00:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "paper-story"}}]}},
            {"type": "user", "timestamp": "2026-09-20T00:00:00Z",
             "message": {"content": "<command-name>/paper-story</command-name>"}},
            {"type": "assistant", "timestamp": "2026-09-21T00:00:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "anthropic-skills:pdf"}}]}},
            {"type": "assistant", "timestamp": "2026-09-22T00:00:00Z",
             "message": {"content": [{"type": "text", "text": "I could use the Skill paper-distill"}]}},
            {"type": "assistant", "timestamp": "2026-09-23T00:00:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Read",
                                      "input": {"file_path": "C:\\Users\\x\\.claude\\skills\\render-perf\\SKILL.md"}}]}},
            {"type": "assistant", "timestamp": "2026-09-24T00:00:00Z",
             "message": {"content": [{"type": "tool_use", "name": "Edit",
                                      "input": {"file_path": "C:/Users/x/.claude/skills/motion-design/SKILL.md"}}]}},
        ]
        t.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
        cache = Path(td) / "cache.json"
        u = skill_uses(Path(td) / "arch", cache)
        expect("user slash command is a use and the later date wins", u.get("paper-story"), "2026-09-20")
        expect("plugin-qualified name maps to its bare name", u.get("pdf"), "2026-09-21")
        expect("a skill only MENTIONED in text is not a use", "paper-distill" in u, False)
        expect("Read of a SKILL.md is a use; an Edit of one is not", (u.get("render-perf"), "motion-design" in u), ("2026-09-23", False))
        expect("cache written, versioned, keyed by transcript",
               str(t) in json.loads(cache.read_text(encoding="utf-8")).get("files", {}), True)
        expect("missing archive -> None (undetermined)", skill_uses(Path(td) / "nope", cache), None)

        # ---- agents class (WC-05a) ----
        home = Path(td) / "home"
        (home / "agents").mkdir(parents=True)
        for stem, name in (("engineering-code-reviewer", "code-reviewer"), ("engineering-backend-architect", "backend-architect"),
                           ("engineering-security-engineer", "security-engineer"), ("cheap-worker", "cheap-worker"),
                           ("testing-new", "testing-new"), ("old-unused", "old-unused")):
            (home / "agents" / f"{stem}.md").write_text(
                f"---\nname: {name}\ndescription: x: y\n---\nbody\nname: not-this-one\n", encoding="utf-8")
        (home / "agents" / "nofront.md").write_text("no frontmatter here\nname: ignored\n", encoding="utf-8")
        acomps, s2n, afiles = agent_components(home)
        expect("agent key = frontmatter name, not file stem; no frontmatter -> stem; body `name:` ignored",
               (dict(acomps).get("agents/code-reviewer"), s2n["engineering-code-reviewer"], s2n["nofront"], "agents/not-this-one" in dict(acomps)),
               ("code-reviewer", "code-reviewer", "nofront", False))
        expect("component -> file map keeps the real file name", afiles["agents/backend-architect"], "agents/engineering-backend-architect.md")

        def agent(ts, subagent_type):
            return {"type": "assistant", "timestamp": ts, "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {"subagent_type": subagent_type, "prompt": "p"}}]}}

        def tool(ts, name, path):
            return {"type": "assistant", "timestamp": ts, "message": {"content": [
                {"type": "tool_use", "name": name, "input": {"file_path": path}}]}}

        arecs = [
            agent("2026-09-20T00:00:00Z", "code-reviewer"),
            agent("2026-09-25T00:00:00Z", "code-reviewer"),
            agent("2026-09-26T00:00:00Z", "general-purpose"),
            agent("2026-09-26T00:00:00Z", "Explore"),
            tool("2026-09-27T00:00:00Z", "Read", "C:\\Users\\x\\.claude\\agents\\engineering-backend-architect.md"),
            tool("2026-08-01T00:00:00Z", "Read", "C:/Users/x/.claude/agents/cheap-worker.md"),
            tool("2026-09-28T00:00:00Z", "Edit", "C:/Users/x/.claude/agents/engineering-security-engineer.md"),
            tool("2026-09-28T00:00:00Z", "Write", "C:/Users/x/.claude/agents/old-unused.md"),
            tool("2026-09-29T00:00:00Z", "Read", "C:/Users/x/.claude/agents/engineering-ai-engineer.md"),
            tool("2026-09-29T00:00:00Z", "Read", "/work/other-repo/agents/old-unused.md"),
            {"type": "assistant", "timestamp": "2026-09-30T00:00:00Z",
             "message": {"content": [{"type": "text", "text": 'subagent_type "security-engineer" agents/old-unused.md'}]}},
            {"type": "user", "timestamp": "2026-09-30T00:00:00Z", "message": {"content": 'subagent_type "old-unused"'}},
        ]
        (arch / "a.jsonl").write_text("\n".join(json.dumps(r) for r in arecs) + "\n", encoding="utf-8")
        acache = Path(td) / "agents-cache.json"
        skills_cache_before = cache.read_bytes()
        au = agent_uses(s2n, Path(td) / "arch", acache)
        expect("dispatch is a use and the later dispatch date wins", au.get("code-reviewer"), "2026-09-25")
        expect("Read of agents/<stem>.md maps stem -> frontmatter name (stem != name)", au.get("backend-architect"), "2026-09-27")
        expect("Read where stem == name is a use", au.get("cheap-worker"), "2026-08-01")
        expect("Edit / Write of an agent file, a Read of another repo's agents/<same>.md, a text-only mention: not use",
               ("security-engineer" in au, "old-unused" in au), (False, False))
        expect("built-in types and a Read of a deleted agent file are ignored",
               sorted(au), ["backend-architect", "cheap-worker", "code-reviewer"])
        expect("agents cache written, versioned, keyed by transcript; skills cache not touched",
               (str(arch / "a.jsonl") in json.loads(acache.read_text(encoding="utf-8")).get("files", {}),
                json.loads(acache.read_text(encoding="utf-8")).get("version"), cache.read_bytes() == skills_cache_before),
               (True, AGENT_CACHE_VERSION, True))
        expect("second pass served from the cache gives the same answer", agent_uses(s2n, Path(td) / "arch", acache), au)
        expect("missing archive -> None (undetermined)", agent_uses(s2n, Path(td) / "nope", acache), None)
        abirths = {"agents/testing-new.md": "2026-10-01"}
        st, q, rows = judge(acomps, au, {}, today, lambda c: abirths.get(afiles.get(c, c), "2026-07-01"))
        v = {c: x for c, _, x in rows}
        expect("agents: used within 30 d -> ok; stale -> review; never used + born 5 d ago -> young",
               (v["agents/code-reviewer"], v["agents/cheap-worker"], v["agents/testing-new"], v["agents/old-unused"]),
               ("ok", "review", "young", "review"))
        bp = build(home, Path(td) / "arch", Path(td) / "sk-cache.json", today, Path(td) / "none.json", Path(td) / "ag2.json")
        ap = [p for p in bp["points"] if p["id"] == "reading-use.agents"]
        expect("build() emits path-rules, skills, agents in that order; agents alias as carded",
               ([p["id"] for p in bp["points"]], ap[0]["alias"] if ap else None),
               (["reading-use.path-rules", "reading-use.skills", "reading-use.agents"], "代理人定義：多久沒被派工或讀取"))
        expect("agents point: state warn, quality good", (ap[0]["state"], ap[0]["quality"]), ("warn", "good"))
        ftext = {f["label"].split(":")[0]: f["text"] for f in ap[0]["findings"]}
        expect("a stem != name row names its real file in the finding; a stem == name row does not",
               (ftext["agents/security-engineer"].startswith("file agents/engineering-security-engineer.md; last use never"),
                ftext["agents/cheap-worker"].startswith("last use 2026-08-01")), (True, True))
        bp2 = build(Path(td) / "empty-home", Path(td) / "arch", Path(td) / "sk2.json", today, Path(td) / "none.json", Path(td) / "ag3.json")
        a2 = [p for p in bp2["points"] if p["id"] == "reading-use.agents"][0]
        expect("no agent file at all -> state None, quality undetermined (never pass on nothing)",
               (a2["state"], a2["quality"]), (None, "undetermined"))
    print("ALL PASS" if not fails else f"FAILED: {', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        sys.exit(selftest())
    if a[:1] == ["emit"]:
        print(json.dumps(build(), ensure_ascii=False))
    elif a[:1] == ["check"]:
        cmd_check()
    else:
        print(__doc__)
