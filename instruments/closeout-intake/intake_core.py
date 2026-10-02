"""intake_core — pure functions for closeout-intake (text in, verdict/text out; no IO).

Implements the record contract of references/closeout-capture-r3-psm-2026-09-07.md §2
and the semantics of references/closeout-capture-r3-design-2026-09-07.md §4:
  * a record = xi-card front matter (parsed by tools/cross-index/xi_cards.extract_card,
    ONE parser shared with cross-index — never a copy) + a `## Record` key/value block
    + fixed body sections + a tool-only `## Events` list;
  * validation rules D1–D9 (design §4.5) — every rule has a stable id printed on reject;
  * hits / lifecycle state DERIVED from events (INV-4); front-matter `status:` is the
    projection of that state in xi vocabulary (S-9);
  * the index (ops/lessons.md) is a pure function of the record set (INV-5);
  * legacy parsers for the one-time import (INV-8) — they extract, they never rewrite.
SEVERITY: the validators are FAIL-CLOSED for the writer (a reject means nothing is
written) and the reject message names the rule and the repair; the derived-state code
never raises on a malformed event line — it reports it as an error entry instead.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_XI = os.path.join(os.path.dirname(_HERE), "cross-index")
if _XI not in sys.path:
    sys.path.insert(0, _XI)
from xi_cards import extract_card  # noqa: E402  (shared parser, PSM §1)

SECTIONS = ("Context", "Pitfall", "Fix", "Detection", "Narrative", "Events")
REQUIRED_SECTIONS = ("Context", "Pitfall", "Fix")
DEFAULT_CAPS = {"Context": 400, "Pitfall": 700, "Fix": 700, "Detection": 300}   # registry INTAKE_FIELD_CAPS
DEFAULT_BUDGET = (3, 1500)                                                        # registry INTAKE_INJECT_BUDGET
DORMANT_DAYS = 90
FM_TOOL_KEYS = ("xi", "aliases", "date", "status")
FM_AUTHORED_KEYS = ("what", "tags")
RECORD_TOOL_KEYS = ("id", "kind", "created", "session", "imported_from")
RECORD_AUTHORED_KEYS = ("locator", "project", "digest")
EVENT_KINDS = ("born", "recurrence", "fold", "supersede", "retract", "match", "imported")
TERMINAL = ("superseded", "retracted")
# Why a folded rule did not stop a recurrence (ops/40-maintenance.md §2a "re-fold loop").
# A re-fold must name one; each maps to a different repair, so a re-fold without a
# cause is a patch nobody can audit later.
REFOLD_CAUSES = ("trigger-gap",        # (a) the target never fires in the recurring situation
                 "inert-text",         # (b) it fires, its text does not change behaviour
                 "wrong-layer",        # (c) folded into the wrong layer / asset class
                 "different-pitfall",  # (d) the recurrences are a sibling mechanism
                 "misattributed")      # (e) the held=no note does not describe a fold failure
_CAUSE_RE = re.compile(r"\bcause=([a-z-]+)")
ID_RE = re.compile(r"^L-\d{3,}$")
_HITS_RE = re.compile(r"(?m)(^|\s)hits:\s")
_EVENT_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\w+)(?:\s+(.*))?$")

INDEX_HEADER = """# Lessons — generated index of ops/lessons/ (do not edit; the guard denies direct writes)

Every card below is a PROJECTION of one intake record `ops/lessons/L-nnn.md` — the record
is the authoritative, lossless text; the card is capped so a pre-task grep hit can be read
in one screen. Write a new lesson: draft a file with the Write tool (front matter `what`
(中文 (English)) + `tags` (≥1 task-type word from tools/closeout-intake/tags.txt), a
`## Record` block with `locator:`, sections `## Context` / `## Pitfall` / `## Fix`
(+ `## Detection`, `## Narrative`), then

    python tools/closeout-intake/intake.py add --from <draft.md>

Recurrence (the "same symptom a 2nd time" rule): grep this file for the MECHANISM first,
then `intake.py event L-nnn --kind recurrence --held yes|no --note "..."`. A card whose
hits reaches 2 is routed through `ops/40-maintenance.md` §2a (fold: `--kind fold --target
"<file §anchor>"`). Full text, recurrences and provenance: the `Record:` path on each card.
Rules and semantics: references/closeout-capture-r3-design-2026-09-07.md §4.
"""


# ----------------------------------------------------------------------------- parsing
def _nl(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter_block_including_fences, body) or (None, text)."""
    lines = _nl(text).split("\n")
    if not lines or lines[0].strip() != "---":
        return None, _nl(text)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[: i + 1]) + "\n", "\n".join(lines[i + 1:])
    return None, _nl(text)


def parse_kv_block(lines: list[str]) -> tuple[dict, list[str]]:
    kv, errs = {}, []
    for ln in lines:
        if not ln.strip():
            continue
        if ": " in ln:
            k, _, v = ln.partition(": ")
        elif ln.rstrip().endswith(":"):
            k, v = ln.rstrip()[:-1], ""
        else:
            errs.append(f"bad-record-line:{ln[:40]}")
            continue
        k = k.strip()
        if k in kv:
            errs.append(f"duplicate-record-key:{k}")
        kv[k] = v.strip()
    return kv, errs


def parse_events(lines: list[str]) -> tuple[list[dict], list[str]]:
    events, errs = [], []
    for ln in lines:
        if not ln.strip():
            continue
        m = _EVENT_RE.match(ln.rstrip())
        if not m:
            errs.append(f"bad-event-line:{ln[:60]}")
            continue
        date, kind, rest = m.group(1), m.group(2), (m.group(3) or "")
        if kind not in EVENT_KINDS:
            errs.append(f"bad-event-kind:{kind}")
            continue
        ev = {"date": date, "kind": kind, "rest": rest, "raw": ln.rstrip()}
        if kind == "supersede":
            mm = re.match(r"→\s*(L-\d+)", rest)
            ev["successor"] = mm.group(1) if mm else None
        if kind == "fold":
            body = rest[1:] if rest.startswith("→") else rest
            # `fold → <target> — <why>`: the reason is optional and everything after
            # the em-dash separator, so an older note-less line parses identically.
            ev["target"], _, why = body.partition(" — ")
            ev["target"] = ev["target"].strip()
            ev["why"] = why.strip() or None
            mm = _CAUSE_RE.search(why)
            ev["cause"] = mm.group(1) if mm else None
        if kind == "recurrence":
            # held=yes: an existing rule or detection caught it BEFORE the output reached
            # its consumer; held=no: it escaped. A line without the field is read as
            # escaped -- "caught" is a claim, and an absent claim is not made for it.
            mm = re.search(r"\bheld=(yes|no)\b", rest)
            ev["held"] = mm.group(1) if mm else None
        if kind == "imported":
            mm = re.search(r"hits=(\d+)", rest)
            ev["hits"] = int(mm.group(1)) if mm else 1
        events.append(ev)
    return events, errs


def parse_record(text: str) -> dict:
    """Parse a record (or a draft) into {fm, fm_raw, record, sections, events, errors}.
    Never raises. `fm` is the xi verdict dict from extract_card (kind none/card/rejected)."""
    out = {"fm": None, "fm_raw": {}, "record": {}, "sections": {}, "events": [], "errors": [], "order": []}
    fm_block, body = split_frontmatter(text)
    if fm_block is None:
        out["errors"].append("missing-frontmatter")
        return out
    out["fm"] = extract_card(fm_block)
    fm_lines = fm_block.split("\n")[1:-2]  # between the fences
    out["fm_raw"], e = parse_kv_block(fm_lines)
    out["errors"] += e
    # body sections
    cur, buf = None, []
    blocks: list[tuple[str, list[str]]] = []
    fenced = False   # `## ` lines inside a ``` fence are content (verbatim legacy text), not sections
    for ln in body.split("\n"):
        if ln.startswith("```"):
            fenced = not fenced
        m = None if fenced else re.match(r"^## (.+?)\s*$", ln)
        if m:
            if cur is not None:
                blocks.append((cur, buf))
            cur, buf = m.group(1), []
        else:
            if cur is None and ln.strip():
                out["errors"].append("text-before-first-section")
            buf.append(ln)
    if cur is not None:
        blocks.append((cur, buf))
    names = [n for n, _ in blocks]
    if not names or names[0] != "Record":
        out["errors"].append("missing-record-block")
    for n, lines in blocks:
        if n == "Record":
            kv, e = parse_kv_block(lines)
            out["record"], out["errors"] = kv, out["errors"] + e
        elif n in SECTIONS:
            if n in out["sections"]:
                out["errors"].append(f"duplicate-section:{n}")
            body_txt = "\n".join(lines).strip("\n")
            out["sections"][n] = body_txt
            out["order"].append(n)
            if n == "Events":
                out["events"], e = parse_events(lines)
                out["errors"] += e
        else:
            out["errors"].append(f"unknown-section:{n}")
    order_idx = [SECTIONS.index(n) for n in out["order"]]
    if order_idx != sorted(order_idx):
        out["errors"].append("section-order")
    return out


# ----------------------------------------------------------------------------- derivation
def derive(events: list[dict], today: _dt.date | None = None) -> dict:
    """hits and lifecycle state from events (INV-4). Returns {hits, state, successor, target, last_date}."""
    hits = 1
    state, successor, target = "live", None, None
    last = None
    for ev in events:
        k = ev["kind"]
        if k == "recurrence":
            hits += 1
        elif k == "imported":
            hits += max(ev.get("hits", 1) - 1, 0)
        elif k == "fold":
            state, target = "folded", ev.get("target")
        elif k == "supersede":
            state, successor = "superseded", ev.get("successor")
        elif k == "retract":
            state = "retracted"
        if k != "match":
            last = ev["date"]
    if state == "live" and hits == 1 and last and today is not None:
        try:
            d = _dt.date.fromisoformat(last)
            newest = max([d] + [_dt.date.fromisoformat(e["date"]) for e in events if e["kind"] == "match"])
            if (today - newest).days > DORMANT_DAYS:
                state = "dormant"
        except ValueError:
            pass
    return {"hits": hits, "state": state, "successor": successor, "target": target, "last_date": last}


def project_status(state: str, successor: str | None) -> str:
    """xi vocabulary for the front-matter status line (S-9 / SG-7)."""
    if state == "superseded" and successor:
        return f"superseded: {successor}"
    if state in ("folded", "retracted"):
        return "spent"
    return "live"


# transition table (design §4.4): (state, kind) -> "ok" | "ignored" | "illegal"
def transition(state: str, kind: str) -> str:
    if kind == "born":
        return "illegal"
    if state in TERMINAL:
        return "ignored" if kind == "match" else "illegal"
    if kind == "match":
        return "ok" if state == "dormant" else "ignored"
    if state == "folded" and kind == "fold":
        return "illegal"        # base table; a re-fold is admitted only by refold_allowed()
    return "ok"


def after_last_fold(events: list[dict]) -> dict:
    """Recurrences after the most recent fold, split by outcome. The ONE definition of
    "folded but recurring": `escaped` (held=no, or no held field) means the folded rule
    did not stop it; `caught` (held=yes) means it recurred and the rule worked.
    Both lists are empty when the record was never folded."""
    idx = [i for i, e in enumerate(events) if e["kind"] == "fold"]
    if not idx:
        return {"escaped": [], "caught": []}
    tail = [e for e in events[idx[-1] + 1:] if e["kind"] == "recurrence"]
    return {"escaped": [e for e in tail if e.get("held") != "yes"],
            "caught": [e for e in tail if e.get("held") == "yes"]}


def refold_allowed(state: str, events: list[dict]) -> bool:
    """A folded record may be folded again only after an ESCAPED recurrence: that is the
    evidence the current target did not hold. Without one a second fold is a relabel."""
    return state == "folded" and bool(after_last_fold(events)["escaped"])


# ----------------------------------------------------------------------------- validation
def _bytes(s: str) -> int:
    return len(s.encode("utf-8"))


def strip_fences(text: str) -> str:
    """Drop ``` fenced blocks (verbatim legacy content) so field checks see only live text."""
    out, fenced = [], False
    for ln in _nl(text).split("\n"):
        if ln.startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append(ln)
    return "\n".join(out)


def validate_draft(text: str, vocab: set[str], caps: dict | None = None) -> list[tuple[str, str]]:
    """Rules D1–D9 (+ tool-owned keys). Returns [] when the draft is acceptable, else
    [(rule_id, message)] with the FIRST failing rule first (short-circuit order kept)."""
    caps = caps or DEFAULT_CAPS
    p = parse_record(text)
    errs: list[tuple[str, str]] = []
    if "missing-frontmatter" in p["errors"]:
        return [("D1", "draft needs a front matter block with `what:` and `tags:`")]
    fm_raw = p["fm_raw"]
    for k in FM_TOOL_KEYS:
        if k in fm_raw:
            return [("D9", f"tool-owned-key:{k} — the tool fills it; remove it from the draft")]
    for k in RECORD_TOOL_KEYS:
        if k in p["record"]:
            return [("D9", f"tool-owned-key:{k} — the tool fills it; remove it from the draft")]
    if _HITS_RE.search(strip_fences(text)):
        return [("D8", "`hits:` is derived from events (INV-4); remove it")]
    if "Events" in p["sections"]:
        return [("D7", "`## Events` is tool-only; remove it from the draft")]
    # D1/D2 through the shared xi parser, on the front matter the tool WOULD write
    probe = synth_frontmatter(fm_raw, "L-000", "2026-01-01", "live")
    v = extract_card(probe)
    if v["kind"] != "card":
        reason = v.get("reason", "not-a-card")
        if reason in ("bilingual-no-cjk", "bilingual-no-latin"):
            return [("D2", "`what` must be bilingual: 中文 (English) — " + reason)]
        return [("D1", f"front matter rejected by xi grammar: {reason}")]
    tags = v["card"]["tags"]
    if not tags or not (set(tags) & vocab):
        return [("D3", "tags need ≥1 task-type word from tools/closeout-intake/tags.txt "
                       f"(got: {tags or 'none'})")]
    for e in p["errors"]:
        if e.startswith(("unknown-section", "duplicate-section", "section-order", "bad-record-line",
                         "duplicate-record-key", "text-before-first-section", "missing-record-block")):
            return [("D4", e)]
    for s in REQUIRED_SECTIONS:
        if not p["sections"].get(s, "").strip():
            return [("D4", f"section `## {s}` is required and must not be empty")]
    for s, cap in caps.items():
        n = _bytes(p["sections"].get(s, ""))
        if n > cap:
            return [("D5", f"{s} over cap by {n - cap} B ({n} > {cap}) — move at least {n - cap} B to ## Narrative")]
    loc = p["record"].get("locator", "")
    if not loc.strip():
        return [("D6", "locator required in ## Record (literal `unrecorded` is allowed)")]
    return errs


def synth_frontmatter(fm_raw: dict, rid: str, date: str, status: str) -> str:
    what = fm_raw.get("what", "")
    tags = fm_raw.get("tags", "[]")
    return "\n".join(["---", "xi: 1", f"what: {what}", f"tags: {tags}", f"aliases: [{rid}]",
                      f"date: {date}", f"status: {status}", "---", ""])


# ----------------------------------------------------------------------------- building
def build_record(draft_text: str, rid: str, created: str, session: str, project: str,
                 imported_from: str = "none", extra_events: list[str] | None = None,
                 narrative_override: str | None = None, fm_override: dict | None = None) -> str:
    """Compose the on-disk record text from a validated draft + tool fields."""
    p = parse_record(draft_text)
    fm_raw = dict(p["fm_raw"])
    if fm_override:
        fm_raw.update(fm_override)
    date = created[:10]
    rec = p["record"]
    lines = [synth_frontmatter(fm_raw, rid, date, "live").rstrip("\n")]
    lines += ["## Record", f"id: {rid}", "kind: lesson", f"created: {created}", f"session: {session}",
              f"project: {rec.get('project') or project or '-'}",
              f"locator: {rec.get('locator', 'unrecorded')}",
              f"digest: {rec.get('digest') or 'none'}",
              f"imported_from: {imported_from}", ""]
    for s in ("Context", "Pitfall", "Fix", "Detection", "Narrative"):
        body = narrative_override if (s == "Narrative" and narrative_override is not None) else p["sections"].get(s)
        if body is None or (s in ("Detection", "Narrative") and not body.strip()):
            continue
        lines += [f"## {s}", body.strip("\n"), ""]
    lines += ["## Events", f"- {date} born session={short_session(session)}"]
    lines += list(extra_events or [])
    return "\n".join(lines) + "\n"


def short_session(session: str) -> str:
    return session if session == "unrecorded" else session[:8]


def replace_status_line(text: str, status: str) -> str:
    fm, body = split_frontmatter(text)
    if fm is None:
        return text
    fm2 = re.sub(r"(?m)^status: .*$", f"status: {status}", fm, count=1)
    return fm2 + body


def append_event(text: str, line: str) -> str:
    t = _nl(text)
    if not t.endswith("\n"):
        t += "\n"
    return t + line.rstrip("\n") + "\n"


# ----------------------------------------------------------------------------- projection
def _trunc(s: str, cap: int) -> str:
    b = s.encode("utf-8")
    if len(b) <= cap:
        return s
    return b[:cap].decode("utf-8", errors="ignore").rstrip() + " …[record]"


def card_text(rid: str, p: dict, d: dict, caps: dict | None = None) -> str:
    caps = caps or DEFAULT_CAPS
    fm = p["fm"]["card"] if p["fm"] and p["fm"]["kind"] == "card" else {}
    tags = "|".join(fm.get("tags", []))
    st = d["state"]
    if st == "folded" and d.get("target"):
        st = f"folded→{d['target']}"
    elif st == "superseded" and d.get("successor"):
        st = f"superseded→{d['successor']}"
    out = [f"## {rid} {fm.get('date', '')} tags: {tags} hits: {d['hits']} state: {st}",
           f"what: {fm.get('what', '')}"]
    for s in ("Context", "Pitfall", "Fix", "Detection"):
        body = p["sections"].get(s, "").strip()
        if body:
            out.append(f"{s}: {_trunc(' '.join(body.split()), caps.get(s, 10**9))}")
    out.append(f"Record: ops/lessons/{rid}.md")
    return "\n".join(out) + "\n"


def record_set_hash(items: list[tuple[str, str]]) -> str:
    h = hashlib.sha256()
    for rid, text in sorted(items):
        h.update(rid.encode()); h.update(b"\0"); h.update(_nl(text).encode("utf-8")); h.update(b"\0")
    return h.hexdigest()


def render_index(items: list[tuple[str, str]], today: _dt.date | None = None,
                 caps: dict | None = None, generated_at: str = "") -> str:
    """items = [(id, record_text)]. Pure: same items → same bytes (generated_at excluded from hash)."""
    cards = []
    for rid, text in sorted(items, key=lambda x: int(x[0].split("-")[1])):
        p = parse_record(text)
        d = derive(p["events"], today)
        cards.append(card_text(rid, p, d, caps))
    head = (INDEX_HEADER.rstrip("\n") + "\n" +
            f"generated-from: {record_set_hash(items)}   generated-at: {generated_at}   records: {len(items)}\n\n")
    return head + "\n".join(cards)


# ----------------------------------------------------------------------------- match
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-_]+")


def match(items: list[tuple[str, str]], text: str, project: str | None,
          budget_cards: int, budget_bytes: int, today: _dt.date | None = None,
          caps: dict | None = None) -> list[tuple[str, int, str]]:
    """Return [(id, score, card)] within both budgets; every card starts with its id (INV-7)."""
    words = set(_WORD_RE.findall(text.lower()))
    scored = []
    for rid, rt in items:
        p = parse_record(rt)
        if not p["fm"] or p["fm"]["kind"] != "card":
            continue
        d = derive(p["events"], today)
        if d["state"] not in ("live", "dormant"):
            continue
        tags = {t.lower() for t in p["fm"]["card"]["tags"]}
        score = len(tags & words)
        if score == 0 and words:
            # The project bonus is a tie-breaker, never a qualifier: a prompt that
            # carries words but no tag word matches nothing (negative control C-71q),
            # otherwise every card of the current project would ride along on every
            # prompt. An EMPTY text is the project listing (`match --project X`,
            # 60-bootstrap §A.1) and is qualified by the project alone (C-71r).
            continue
        if project and project != "-" and p["record"].get("project", "").lower() == project.lower():
            score += 1
        if score > 0:
            scored.append((score, p["fm"]["card"].get("date") or "", rid, card_text(rid, p, d, caps)))
    scored.sort(key=lambda x: (-x[0], x[1]), reverse=False)
    scored.sort(key=lambda x: (-x[0], x[1] and -int(x[1].replace("-", "") or 0)))
    out, used = [], 0
    for score, _date, rid, card in scored:
        if len(out) >= budget_cards:
            break
        b = _bytes(card)
        if used + b > budget_bytes:
            continue
        out.append((rid, score, card)); used += b
    return out


# ----------------------------------------------------------------------------- legacy parsers (import only)
_LEG_HEAD = re.compile(r"^## (L-\d+) (\d{4}-\d{2}-\d{2}) tags: (\S+)(?: hits: (\d+))?", re.M)
_LEG_FIELD = re.compile(r"^(Context|Pitfall|Fix|Detection|Recurrences|Evidence|Detail)\b([^:\n]*):[ \t]*", re.M)
_LEG_BULLET = re.compile(r"^- \*\*(L-\d+)\*\* \((\d{4}-\d{2}-\d{2}) · ([^)]+)\)(?:\s+—\s*(.*))?$")


def parse_legacy_cards(text: str) -> dict[str, dict]:
    """Cards above `## Archived`: {id: {date, tags, hits, fields{name: text}, raw}} — verbatim slices."""
    t = _nl(text)
    cut = t.find("\n## Archived")
    region = t if cut < 0 else t[:cut]
    heads = list(_LEG_HEAD.finditer(region))
    out = {}
    for i, m in enumerate(heads):
        start = m.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(region)
        raw = region[start:end].rstrip("\n") + "\n"
        body = raw[m.end() - m.start():]
        fields, fmatches = {}, list(_LEG_FIELD.finditer(body))
        for j, fm in enumerate(fmatches):
            fend = fmatches[j + 1].start() if j + 1 < len(fmatches) else len(body)
            fields[fm.group(1)] = body[fm.end():fend].strip("\n")
        out[m.group(1)] = {"date": m.group(2), "tags": m.group(3).split("|"),
                           "hits": int(m.group(4) or 1), "fields": fields, "raw": raw}
    return out


def parse_legacy_bullets(text: str) -> dict[str, dict]:
    """Archived bullets: {id: {date, tags, text, raw}} — a bullet may wrap onto indented lines."""
    t = _nl(text)
    cut = t.find("\n## Archived")
    if cut < 0:
        return {}
    out, cur = {}, None
    for ln in t[cut:].split("\n"):
        m = _LEG_BULLET.match(ln)
        if m:
            cur = m.group(1)
            tags = [t.strip("*") for t in m.group(3).split("|")]
            out[cur] = {"date": m.group(2), "tags": tags, "text": (m.group(4) or "").strip(), "raw": ln}
        elif cur and ln.startswith("  ") and ln.strip():
            out[cur]["text"] = (out[cur]["text"] + " " + ln.strip()).strip(); out[cur]["raw"] += "\n" + ln
        else:
            cur = None
    return out


def parse_legacy_detail(text: str) -> dict[str, str]:
    """{id: verbatim section text including its heading line}."""
    t = _nl(text)
    heads = list(re.finditer(r"^## (L-\d+)\b.*$", t, re.M))
    out = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(t)
        out[m.group(1)] = t[m.start():end].rstrip("\n") + "\n"
    return out


def fold_target_from_bullet(text: str) -> str:
    """Legacy bullets say "Folded <date> (...): <where it lives now>". Take the first
    backticked path in that clause, else the first *.md/*.py token, else the clause itself."""
    m = re.search(r"[Ff]olded[^:]{0,60}:\s*(.+)", text)
    clause = (m.group(1) if m else text).strip()
    t = re.search(r"`([^`]+)`", clause)
    if t:
        tok = t.group(1)
        nxt = re.match(r"`[^`]*`\s*(§\S+)", clause[t.start():])
        return tok + (" " + nxt.group(1) if nxt else "")
    g = re.search(r"(global CLAUDE\.md|CLAUDE\.md|[\w./-]+\.(?:md|py))", clause)
    if g:
        return g.group(1)
    return (clause[:80].rstrip() + "…") if len(clause) > 80 else clause


def legacy_evidence(fields: dict) -> tuple[str, str]:
    """(session, locator) from a legacy Evidence line, else ('unrecorded','unrecorded')."""
    ev = fields.get("Evidence", "")
    if not ev.strip():
        return "unrecorded", "unrecorded"
    ms = re.search(r"session\s+([0-9a-f]{8}[0-9a-f\-]*)", ev)
    ml = re.search(r"locator\s+(.+?)(?:\s*\|\s*captured|\s*$)", ev, re.S)
    return (ms.group(1) if ms else "unrecorded"), (" ".join(ml.group(1).split()) if ml else " ".join(ev.split()))
