"""intake.py — the ONLY writer of ops/lessons/ (closeout-intake CLI).

Sole build basis: references/closeout-capture-r3-psm-2026-09-07.md (§3 CLI contract).
Semantics owner: references/closeout-capture-r3-design-2026-09-07.md §4.

Subcommands: add · event · render · check · match · report · import
Exit codes: 0 ok · 2 reject (validation; nothing written; first failing rule named)
            · 3 IO/lock failure (nothing written) · 4 check found violations.
SEVERITY: `add`/`event` are FAIL-CLOSED gates for the writer (a reject writes nothing and
names the repair); `check`/`report` are read by a human/model (WARN-grade output, exit 4 so a
sweep can see it). Every non-zero exit prints `intake: <code> <rule> <message>` first.

Store layout, record format, lock and id allocation: PSM §1–§2, design §4.6 (O_EXCL
allocation; `<id>.lock` with a stale-age break).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import intake_core as core  # noqa: E402

HOME = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STORE = os.path.join(HOME, "ops", "lessons")
INDEX = os.path.join(HOME, "ops", "lessons.md")
TAGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tags.txt")
SESSION_FILE = os.path.join(HOME, "cache", "handoff", "current-session.json")
PROJECTS = os.path.join(HOME, "references", "PROJECTS.md")
LOCK_WAIT_S = 2.0
LOCK_STALE_S = 10.0          # registry INTAKE_LOCK_STALE_S
ALLOC_RETRIES = 20


# ----------------------------------------------------------------------------- helpers
def _fail(code: int, rule: str, msg: str, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({"ok": False, "code": code, "rule": rule, "message": msg}, ensure_ascii=False))
    else:
        print(f"intake: {code} {rule} {msg}")
    return code


def _read(path: str) -> str:
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def _write_atomic(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def _today() -> _dt.date:
    return _dt.date.today()


def load_vocab(path: str = TAGS) -> set[str]:
    try:
        return {ln.strip() for ln in _read(path).split("\n") if ln.strip() and not ln.startswith("#")}
    except OSError:
        return set()


UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _env_session() -> str | None:
    """This process's OWN session id, from the harness environment.

    Shape-checked so a truncated or placeholder value falls through to the pointer
    rather than stamping a junk id into a record that can never be rewritten.
    """
    v = (os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    return v if UUID_RE.match(v) else None


def session_id(explicit: str | None) -> tuple[str, str | None]:
    """(session, warning). Explicit wins; else this process's env id; else the runway
    pointer; else unrecorded (design G-6).

    ENV FIRST (2026-09-07, ported from `tools/process-ledger/ledger.py`, which
    measured the failure): `cache/handoff/current-session.json` is a GLOBAL single
    file that every session's every prompt overwrites, so under concurrency it names
    whichever session prompted last — fresh, correct, and somebody else's. A record
    is born once and never rewritten (INV-2), so a `session:` taken from the pointer
    is a misattribution nothing downstream can correct. Observed that day: a
    `--dry-run` from one session produced a record header naming a concurrent
    session in another project dir.
    review-when: `CLAUDE_CODE_SESSION_ID` comes back empty in a shell call (harness
    renamed or dropped it) — the pointer fallback still works, but the concurrency
    defect returns with it, so re-probe for the new variable.
    """
    if explicit and explicit != "auto":
        return explicit, None
    env = _env_session()
    try:
        ptr = json.loads(_read(SESSION_FILE))["session"]
    except Exception:
        ptr = None
    if env:
        if ptr and ptr != env:
            return env, (f"current-session.json names {ptr[:8]} but this process is {env[:8]} "
                         "(concurrent session); recording under this process")
        return env, None
    if ptr:
        return ptr, None
    return "unrecorded", "session pointer missing — recorded as `unrecorded`"


def project_name(explicit: str | None) -> str:
    if explicit:
        return explicit
    cwd = os.getcwd().replace("/", "\\").casefold()
    try:
        for ln in _read(PROJECTS).split("\n"):
            if not ln.startswith("| ") or ln.startswith("| ---") or ln.startswith("| project"):
                continue
            cols = [c.strip() for c in ln.strip("|").split("|")]
            if len(cols) < 3:
                continue
            for p in cols[2].split(";"):
                p = p.strip().split(" ")[0].replace("/", "\\").casefold()
                if p and cwd.startswith(p.rstrip("\\")):
                    return cols[0]
    except OSError:
        pass
    return "-"


def store_items(store: str) -> list[tuple[str, str]]:
    items = []
    if not os.path.isdir(store):
        return items
    for fn in sorted(os.listdir(store)):
        if fn.endswith(".md") and core.ID_RE.match(fn[:-3]):
            items.append((fn[:-3], _read(os.path.join(store, fn))))
    return items


def next_id(store: str) -> int:
    ids = [int(fn[2:-3]) for fn in os.listdir(store) if fn.endswith(".md") and core.ID_RE.match(fn[:-3])] if os.path.isdir(store) else []
    return (max(ids) + 1) if ids else 1


def alloc_and_write(store: str, text_for_id, start: int | None = None) -> tuple[str, str, bool]:
    """Atomic allocation: O_CREAT|O_EXCL on L-<n>.md, retrying +1 (INV-3). Returns (id, path, bumped)."""
    os.makedirs(store, exist_ok=True)
    n = start if start is not None else next_id(store)
    first = n
    for _ in range(ALLOC_RETRIES):
        rid = f"L-{n:03d}"
        path = os.path.join(store, rid + ".md")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            n += 1
            continue
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text_for_id(rid))
        return rid, path, n != first
    raise OSError(f"could not allocate an id after {ALLOC_RETRIES} attempts from L-{first:03d}")


class Lock:
    def __init__(self, store: str, rid: str):
        self.path = os.path.join(store, rid + ".lock")
        self.broke_stale = False

    def __enter__(self):
        deadline = time.monotonic() + LOCK_WAIT_S
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w") as f:
                    f.write(f"{os.getpid()} {time.time():.0f}\n")
                return self
            except FileExistsError:
                try:
                    age = time.time() - os.path.getmtime(self.path)
                except OSError:
                    age = 0
                if age > LOCK_STALE_S:
                    try:
                        os.remove(self.path); self.broke_stale = True
                        continue
                    except OSError:
                        pass
                if time.monotonic() > deadline:
                    raise TimeoutError(f"lock held: {self.path}")
                time.sleep(0.05)

    def __exit__(self, *a):
        try:
            os.remove(self.path)
        except OSError:
            pass


def do_render(store: str, out: str, quiet: bool = False) -> str:
    items = store_items(store)
    text = core.render_index(items, _today(), generated_at=_now_iso())
    _write_atomic(out, text)
    h = core.record_set_hash(items)
    if not quiet:
        print(f"rendered {out}: {len(items)} records, generated-from {h[:12]}")
    return h


# ----------------------------------------------------------------------------- subcommands
def cmd_add(a) -> int:
    try:
        draft = _read(a.src)
    except OSError as e:
        return _fail(3, "IO", f"cannot read draft: {e}", a.json)
    errs = core.validate_draft(draft, load_vocab(), core.DEFAULT_CAPS)
    if errs:
        return _fail(2, errs[0][0], errs[0][1], a.json)
    sess, warn = session_id(a.session)
    proj = project_name(a.project)
    created = _now_iso()
    if a.dry_run:
        print(core.build_record(draft, "L-000", created, sess, proj))
        return 0
    try:
        rid, path, bumped = alloc_and_write(a.store, lambda rid: core.build_record(draft, rid, created, sess, proj))
    except OSError as e:
        return _fail(3, "ALLOC", str(e), a.json)
    if a.store == STORE:
        do_render(STORE, INDEX, quiet=True)
    p = core.parse_record(_read(path))
    card = core.card_text(rid, p, core.derive(p["events"], _today()))
    if a.json:
        print(json.dumps({"ok": True, "id": rid, "path": path, "bumped": bumped, "warning": warn}, ensure_ascii=False))
    else:
        note = f" (a lower id was taken concurrently)" if bumped else ""
        print(f"{rid} written: {os.path.relpath(path, HOME)}{note}")
        if warn:
            print("warning: " + warn, file=sys.stderr)
        print(card, end="")
    return 0


def cmd_event(a) -> int:
    path = os.path.join(a.store, a.id + ".md")
    if not os.path.isfile(path):
        return _fail(2, "NO-RECORD", f"{a.id} not found in {a.store}", a.json)
    if a.kind == "fold" and not a.target:
        return _fail(2, "ARGS", "fold needs --target \"<path §anchor>\"", a.json)
    # held is the field the whole folded-but-recurring report turns on; a silent default
    # of "no" mislabelled caught recurrences as escapes (2026-09-23, five lessons).
    if a.kind == "recurrence" and not a.held:
        return _fail(2, "ARGS", "recurrence needs --held yes (an existing rule/detection caught it "
                     "before the output reached its consumer) | no (it escaped)", a.json)
    if a.cause and a.kind != "fold":
        return _fail(2, "ARGS", "--cause belongs to a re-fold only", a.json)
    if a.kind == "supersede":
        if not a.successor or not core.ID_RE.match(a.successor) or a.successor == a.id:
            return _fail(2, "ARGS", "supersede needs --successor L-mmm (≠ self)", a.json)
        if not os.path.isfile(os.path.join(a.store, a.successor + ".md")):
            return _fail(2, "NO-SUCCESSOR", f"{a.successor} does not exist", a.json)
    if a.kind == "fold":
        tfile = a.target.split(" §")[0].split("#")[0].strip()
        if not os.path.isfile(os.path.join(HOME, tfile)) and not os.path.isfile(tfile):
            return _fail(2, "NO-TARGET", f"fold target file not found: {tfile}", a.json)
    try:
        with Lock(a.store, a.id) as lk:
            text = _read(path)
            p = core.parse_record(text)
            d = core.derive(p["events"], _today())
            verdict = core.transition(d["state"], a.kind)
            refold = d["state"] == "folded" and a.kind == "fold"
            if refold:
                # Re-fold loop (ops/40-maintenance.md §2a): admitted only after an ESCAPED
                # recurrence, and only with a cause and a reason -- the audit trail of why
                # the first target was not the owner.
                if not core.refold_allowed(d["state"], p["events"]):
                    return _fail(2, "ILLEGAL-EVENT", "folded×fold — no held=no recurrence since the last "
                                 "fold, so there is no evidence the current target failed", a.json)
                if not a.cause or not a.note:
                    return _fail(2, "ARGS", "re-fold needs --cause {%s} and --note \"<why the new target owns it>\""
                                 % "|".join(core.REFOLD_CAUSES), a.json)
                verdict = "ok"
            elif a.cause:
                return _fail(2, "ARGS", "--cause belongs to a re-fold (a fold on a folded record)", a.json)
            if verdict == "illegal":
                hint = f" — record it on the successor {d['successor']}" if d["state"] == "superseded" else ""
                return _fail(2, "ILLEGAL-EVENT", f"{d['state']}×{a.kind}{hint}", a.json)
            sess, _ = session_id(a.session)
            date = _today().isoformat()
            note = f" — {a.note}" if a.note else ""
            if a.kind == "recurrence":
                held = a.held or "no"
                line = f"- {date} recurrence session={core.short_session(sess)} project={project_name(a.project)} held={held}{note}"
            elif a.kind == "fold":
                # The note is WHY this target is where the fix now lives -- the one
                # thing a later reader needs and cannot re-derive from the path. It
                # was accepted and silently dropped until 2026-09-08; supersede and
                # retract even demand it ("(no reason given)"), so a fold losing it
                # was a hole in one instrument, not a policy.
                if refold:
                    note = f" — cause={a.cause}; {a.note}"
                line = f"- {date} fold → {a.target}{note or ' — (no reason given)'}"
            elif a.kind == "supersede":
                line = f"- {date} supersede → {a.successor}{note or ' — (no reason given)'}"
            elif a.kind == "retract":
                line = f"- {date} retract{note or ' — (no reason given)'}"
            else:
                line = f"- {date} match session={core.short_session(sess)} shadow"
            if verdict == "ignored" and a.kind == "match":
                print(f"{a.id}: match ignored in state {d['state']}")
                return 0
            new = core.append_event(text, line)
            d2 = core.derive(core.parse_record(new)["events"], _today())
            new = core.replace_status_line(new, core.project_status(d2["state"], d2["successor"]))
            _write_atomic(path, new)
            if lk.broke_stale:
                print("stale lock broken")
    except TimeoutError as e:
        return _fail(3, "LOCK", str(e), a.json)
    if a.store == STORE:
        do_render(STORE, INDEX, quiet=True)
    extra = ""
    if d["state"] == "folded" and a.kind == "recurrence":
        extra = (" (folded, recurred, caught — the fold held)" if a.held == "yes"
                 else " (folded but recurring — route through ops/40-maintenance.md §2a re-fold loop)")
    print(f"{a.id} hits {d2['hits']}, state {d2['state']}{extra}")
    return 0


def cmd_render(a) -> int:
    try:
        do_render(a.store, a.out)
    except OSError as e:
        return _fail(3, "IO", str(e))
    return 0


def _git_show(relpath: str) -> str | None:
    try:
        r = subprocess.run(["git", "show", f"HEAD:{relpath.replace(os.sep, '/')}"], cwd=HOME,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def check_store(store: str, against_head: bool, index: str | None, vocab: set[str]) -> list[str]:
    """Pure-ish: returns violation lines (empty = clean)."""
    out = []
    items = store_items(store)
    for rid, text in items:
        p = core.parse_record(text)
        if not p["fm"] or p["fm"]["kind"] != "card":
            out.append(f"{rid}: front matter not a valid xi card ({(p['fm'] or {}).get('reason', 'none')})")
        for e in p["errors"]:
            out.append(f"{rid}: {e}")
        if core._HITS_RE.search(core.strip_fences(text).split("## Events")[0]):
            out.append(f"{rid}: stored `hits:` key (INV-4)")
        if p["record"].get("id") != rid:
            out.append(f"{rid}: Record id mismatch ({p['record'].get('id')})")
        if not p["record"].get("locator", "").strip():
            out.append(f"{rid}: empty locator (INV-6)")
        for s in core.REQUIRED_SECTIONS:
            if not p["sections"].get(s, "").strip():
                out.append(f"{rid}: missing section {s}")
        if not p["events"] or p["events"][0]["kind"] != "born":
            out.append(f"{rid}: first event must be born")
        d = core.derive(p["events"], _today())
        want = core.project_status(d["state"], d["successor"])
        have = p["fm_raw"].get("status", "")
        if have != want:
            out.append(f"{rid}: status line `{have}` inconsistent with events (want `{want}`)")
        if against_head:
            old = _git_show(os.path.relpath(os.path.join(store, rid + ".md"), HOME))
            if old is not None:
                o = core.parse_record(old)
                for s in ("Context", "Pitfall", "Fix", "Detection", "Narrative"):
                    if o["sections"].get(s) != p["sections"].get(s):
                        out.append(f"{rid}: section {s} changed since HEAD (INV-2)")
                for k, v in o["record"].items():
                    if p["record"].get(k) != v:
                        out.append(f"{rid}: Record key {k} changed since HEAD (INV-2)")
                for k, v in o["fm_raw"].items():
                    if k != "status" and p["fm_raw"].get(k) != v:
                        out.append(f"{rid}: front-matter {k} changed since HEAD (INV-2)")
                oe = [e["raw"] for e in o["events"]]
                ne = [e["raw"] for e in p["events"]]
                if ne[:len(oe)] != oe:
                    out.append(f"{rid}: Events not append-only since HEAD (INV-2)")
    if index:
        try:
            cur = _read(index)
        except OSError:
            out.append(f"index missing: {index}")
        else:
            fresh = core.render_index(items, _today(), generated_at="")
            strip = lambda t: "\n".join(l for l in t.split("\n") if not l.startswith("generated-from:"))
            if strip(core._nl(cur)) != strip(fresh):
                out.append("index differs from a fresh render (INV-5) — run `intake.py render`")
    return out


def cmd_check(a) -> int:
    v = check_store(a.store, a.against == "HEAD", (a.index_path if a.index else None), load_vocab())
    for ln in v:
        print(ln)
    if v:
        return _fail(4, "CHECK", f"{len(v)} violation(s)")
    return 0


def cmd_match(a) -> int:
    text = a.text or (_read(a.text_file) if a.text_file else "")
    res = core.match(store_items(a.store), text, a.project or project_name(None),
                     a.budget_cards, a.budget_bytes, _today())
    if a.json:
        print(json.dumps({"n": len(res), "bytes": sum(len(c.encode()) for _, _, c in res),
                          "ids": [r for r, _, _ in res], "top_score": res[0][1] if res else 0}, ensure_ascii=False))
    else:
        for _, _, card in res:
            print(card, end="")
    return 0


def cmd_report(a) -> int:
    items = store_items(a.store)
    unfolded, refolded, caught, dormant, inconsistent = [], [], [], [], []
    for rid, text in items:
        p = core.parse_record(text)
        d = core.derive(p["events"], _today())
        kinds = [e["kind"] for e in p["events"]]
        if d["state"] in ("live", "dormant") and d["hits"] >= 2 and "fold" not in kinds:
            unfolded.append(rid)
        if d["state"] == "folded":
            post = core.after_last_fold(p["events"])
            if post["escaped"]:
                refolded.append(rid)
            elif post["caught"]:
                caught.append(rid)
        if d["state"] == "dormant":
            dormant.append(rid)
        if p["fm_raw"].get("status", "") != core.project_status(d["state"], d["successor"]):
            inconsistent.append(rid)
    if a.nudge:
        if unfolded:
            print(f"intake: {len(unfolded)} card(s) with hits>=2 never folded ({', '.join(unfolded[:6])}) — route through ops/40-maintenance.md S2a")
        if refolded or inconsistent:
            print(f"intake: folded-but-recurring {refolded or '-'}; status inconsistent {inconsistent or '-'} — run intake.py report, then the ops/40-maintenance.md §2a re-fold loop")
        return 0
    print(f"records {len(items)}")
    print(f"(a) hits>=2, never folded: {unfolded or '-'}")
    print(f"(b) folded but recurring (held=no since the last fold): {refolded or '-'}")
    print(f"(b') folded, recurred, caught (held=yes only — the fold held): {caught or '-'}")
    print(f"(c) dormant: {dormant or '-'}")
    print(f"(d) status inconsistent: {inconsistent or '-'}")
    return 0


def cmd_import(a) -> int:
    cards_txt, detail_txt = _read(a.legacy_cards), _read(a.legacy_detail)
    cards = core.parse_legacy_cards(cards_txt)
    bullets = core.parse_legacy_bullets(cards_txt)
    detail = core.parse_legacy_detail(detail_txt)
    if os.path.isdir(a.store) and store_items(a.store) and not a.force:
        return _fail(3, "STORE-NOT-EMPTY", f"{a.store} already holds records; pass --force to add missing ids only")
    os.makedirs(a.store, exist_ok=True)
    written, relaxed = [], []
    ids = sorted(set(cards) | set(bullets), key=lambda x: int(x[2:]))
    for rid in ids:
        path = os.path.join(a.store, rid + ".md")
        if os.path.exists(path):
            continue
        det = detail.get(rid, "(none)\n")
        if rid in cards:
            c = cards[rid]
            f = c["fields"]
            sess, loc = core.legacy_evidence(f)
            ctx, pit, fix, dtc = f.get("Context", ""), f.get("Pitfall", ""), f.get("Fix", ""), f.get("Detection", "")
            for name, val in (("Context", ctx), ("Pitfall", pit), ("Fix", fix)):
                if not val.strip():
                    relaxed.append(f"{rid}:{name}")
            ctx = ctx or "(legacy card had no Context field — see Narrative)"
            pit = pit or "(legacy card had no Pitfall field — see Narrative)"
            fix = fix or "(legacy card had no Fix field — see Narrative)"
            first = " ".join(ctx.split())[:80]
            what = f"{rid} 舊帳本搬入 (legacy import): {first}"
            tags = c["tags"]; date = c["date"]; hits = c["hits"]
            narrative = (f"### Legacy card (verbatim)\n```\n{c['raw'].rstrip(chr(10))}\n```\n\n"
                         f"### Legacy full record (verbatim)\n```\n{det.rstrip(chr(10))}\n```")
            events = [f"- {date} imported hits={hits} from ops/references/lessons-detail.md §{rid}"]
        else:
            b = bullets[rid]
            relaxed.append(f"{rid}:bullet")
            sess, loc = "unrecorded", "unrecorded"
            btxt = " ".join(b["text"].split()).lstrip("—- ").strip()
            target = core.fold_target_from_bullet(btxt)
            ctx = btxt; dtc = ""
            pit = "(archived bullet — the mechanism is in the legacy full record under ## Narrative)"
            fix = f"folded → {target}"
            what = f"{rid} 舊帳本搬入 (legacy import, folded): {btxt[:80]}"
            tags = b["tags"]; date = b["date"]
            narrative = (f"### Legacy archived bullet (verbatim)\n```\n{b['raw']}\n```\n\n"
                         f"### Legacy full record (verbatim)\n```\n{det.rstrip(chr(10))}\n```")
            events = [f"- {date} imported hits=1 from ops/lessons.md Archived",
                      f"- {date} fold → {target}"]
        draft = "\n".join(["---", f"what: {what}", f"tags: [{', '.join(tags)}]", "---", "## Record",
                           f"locator: {loc}", "", "## Context", ctx, "", "## Pitfall", pit, "", "## Fix", fix, ""]
                          + (["## Detection", dtc, ""] if dtc.strip() else []))
        text = core.build_record(draft, rid, f"{date}T00:00:00+08:00", sess, "claude-config",
                                 imported_from=f"ops/references/lessons-detail.md §{rid}" if rid in detail else "ops/lessons.md",
                                 extra_events=events, narrative_override=narrative)
        d = core.derive(core.parse_record(text)["events"])
        text = core.replace_status_line(text, core.project_status(d["state"], d["successor"]))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(rid)
    print(f"imported {len(written)} records into {a.store}; relaxed D4 on {len(relaxed)}: {', '.join(relaxed) or '-'}")
    if a.verify:
        bad = verify_import(a.store, cards, bullets, detail)
        if bad:
            for b in bad:
                print(b)
            return _fail(4, "VERIFY", f"{len(bad)} mismatch(es); nothing archived")
        print(f"verify: {len(ids)} ids both ways; Narrative bytes match the sources")
    if a.archive_to:
        os.makedirs(a.archive_to, exist_ok=True)
        shutil.copy2(a.legacy_cards, os.path.join(a.archive_to, "lessons.md"))
        with open(os.path.join(a.archive_to, "NOTE.md"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# lessons cutover 2026-09 — archived pre-cutover index\n\n"
                     "`lessons.md` here is the hand-written ledger as it stood at the cutover to intake records "
                     "(`ops/lessons/L-nnn.md`, tool `tools/closeout-intake/intake.py`). Every card and Archived bullet "
                     "was imported verbatim into the matching record's `## Narrative`; `ops/references/lessons-detail.md` "
                     "stays in place, FROZEN. Provenance only — never spec. Pre-cutover git copy: "
                     "`git show fa08fa3:ops/lessons.md`.\n")
        print(f"archived legacy index to {a.archive_to}")
    return 0


def verify_import(store: str, cards: dict, bullets: dict, detail: dict) -> list[str]:
    bad = []
    have = {rid for rid, _ in store_items(store)}
    want = set(cards) | set(bullets)
    for rid in sorted(want - have):
        bad.append(f"{rid}: source id has no record")
    for rid in sorted(have - want):
        bad.append(f"{rid}: record has no source id")
    for rid in sorted(have & want):
        p = core.parse_record(_read(os.path.join(store, rid + ".md")))
        nar = p["sections"].get("Narrative", "")
        src = cards[rid]["raw"].rstrip("\n") if rid in cards else bullets[rid]["raw"]
        if src not in nar:
            bad.append(f"{rid}: legacy card/bullet text not verbatim in Narrative")
        det = detail.get(rid)
        if det and det.rstrip("\n") not in nar:
            bad.append(f"{rid}: legacy detail section not verbatim in Narrative")
    return bad


# ----------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="intake.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add"); p.add_argument("--from", dest="src", required=True)
    p.add_argument("--store", default=STORE); p.add_argument("--project"); p.add_argument("--session", default="auto")
    p.add_argument("--dry-run", action="store_true"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_add)

    p = sub.add_parser("event"); p.add_argument("id"); p.add_argument("--kind", required=True, choices=("recurrence", "fold", "supersede", "retract", "match"))
    p.add_argument("--held", choices=("yes", "no")); p.add_argument("--target"); p.add_argument("--successor"); p.add_argument("--note")
    p.add_argument("--cause", choices=core.REFOLD_CAUSES, help="re-fold only: why the current target did not hold")
    p.add_argument("--store", default=STORE); p.add_argument("--project"); p.add_argument("--session", default="auto")
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_event)

    p = sub.add_parser("render"); p.add_argument("--store", default=STORE); p.add_argument("--out", default=INDEX); p.set_defaults(fn=cmd_render)

    p = sub.add_parser("check"); p.add_argument("--store", default=STORE); p.add_argument("--index", action="store_true")
    p.add_argument("--index-path", default=INDEX); p.add_argument("--against", choices=("HEAD",)); p.set_defaults(fn=cmd_check)

    p = sub.add_parser("match"); p.add_argument("--text"); p.add_argument("--text-file"); p.add_argument("--project")
    p.add_argument("--budget-cards", type=int, default=core.DEFAULT_BUDGET[0]); p.add_argument("--budget-bytes", type=int, default=core.DEFAULT_BUDGET[1])
    p.add_argument("--store", default=STORE); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_match)

    p = sub.add_parser("report"); p.add_argument("--store", default=STORE); p.add_argument("--nudge", action="store_true"); p.set_defaults(fn=cmd_report)

    p = sub.add_parser("import"); p.add_argument("--legacy-cards", required=True); p.add_argument("--legacy-detail", required=True)
    p.add_argument("--store", required=True); p.add_argument("--verify", action="store_true"); p.add_argument("--archive-to")
    p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_import)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
