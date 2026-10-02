#!/usr/bin/env python3
"""Mechanical routing audit for skill-trigger-dict.md.

WHY THIS IS A SCRIPT AND NOT A JUDGEMENT CALL
---------------------------------------------
`skill-trigger-dict.md` claims, per skill, which words route to it. Nothing
ever checked that claim. The 2026-08-15 audit found `workflow-checkpoint`
firing proactively 1 time in 37 while its dict entry advertised a phrase
("這個階段完成了，做一次 checkpoint") the user had never once said in 43 days.
A dictionary that records an imagined vocabulary is worse than none: it looks
maintained.

This tool answers three MECHANICAL questions so the model only has to judge
what is left:
    HIT     the entry's vocabulary appeared and its own skill fired
    BYPASS  it appeared and a DIFFERENT skill fired  (names the thief)
    MISS    it appeared and nothing fired
    LATE    of those MISSes, how many were followed by the entry's OWN skill
            firing later in the same session, past the attribution window
plus two ways to be silent, which are NOT the same finding:
    DEAD          the entry registers vocabulary and it never appeared --
                  the dict is describing traffic that does not exist
    NO VOCABULARY the entry registers no 關鍵詞 line at all, so this tool has
                  nothing to match and its silence says nothing about the dict

Every one of LATE / NO VOCABULARY exists because the plain reading was WRONG in
a way that flattered the tool: before 2026-09-04 both states printed as DEAD or
MISS, and the resulting numbers were quoted as settled fact in
`ops/rule-registry.md`. Tests: tools/skill-routing-audit-test/.

Machine first, LLM second: the numbers below are countable. Whether a MISS was
CORRECT (the words appeared but the situation genuinely did not call for the
skill) is not countable, and is deliberately left to a reader.

USAGE
    python tools/skill-routing-audit.py                 # full corpus
    python tools/skill-routing-audit.py --since 2026-08-15
    python tools/skill-routing-audit.py --skill workflow-checkpoint --detail
    python tools/skill-routing-audit.py --snapshot      # append to telemetry

Stdlib only, pinned to ~/.claude, read-only except for --snapshot.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

HOME = os.path.expanduser("~/.claude")
DICT = os.path.join(HOME, "skill-trigger-dict.md")
CLASSES = os.path.join(HOME, "ops", "references", "skill-trigger-classes.md")
SKILLS = os.path.join(HOME, "skills")
PROJECTS = os.path.join(HOME, "projects")
SNAP = os.path.join(HOME, "telemetry", "skill-routing-audit.jsonl")

# How far after a human turn a fire still counts as caused by it. A skill that
# fires eleven assistant turns later was routed by something else.
LOOKAHEAD = 6

# Contaminants, each one found the expensive way during the 2026-08-15 audit.
# Do not relax these without re-reading why they are here.
#   1. `type=="user"` is dominated by tool_result records and skill-body
#      injections -- 25,138 records collapse to ~810 human turns.
#   2. subagent transcripts persist their DISPATCH PROMPT as a user record, so
#      a model-authored prompt reads as a user request.
#   3. a bare ASCII token matches inside words ('PR' in 'PRISMA', 'sers' in
#      'C:\\Users\\'), and a token inside a path is not a request.
#   4. the harness writes its own notices as plain user records (found
#      2026-09-26 by tools/routing-loop, measured on the live corpus):
#      <task-notification> blocks (721 records, never with human text, and
#      they carry subagent summaries -- the source of the noisy comsol
#      tokens gate/PASS/control), <system-reminder> blocks PREPENDED to a
#      real human turn (52 records, human text follows every one), and the
#      bare "[Request interrupted by user]" marker (55). Strip the blocks,
#      keep what the human typed, drop the record if nothing is left.
PATHISH = re.compile(r"[A-Za-z]:\\|/Users/|tool-use-id|output-file")
HARNESS_BLOCK = re.compile(
    r"<(task-notification|system-reminder)>.*?</\1>", re.S)
HARNESS_MARKERS = ("[Request interrupted by user",)

# A zero is only a finding for a class that was supposed to fire. Without this,
# a phase-gated skill with no phase and a skill that should fire on every coding
# task print identically. Source of the classes: ops/references/skill-trigger-classes.md
NOISY_ZERO = {"always-on", "conditional"}


def zero_verdict(meta):
    """What a zero means for this skill — the REGISTRY decides, not the class.

    Deriving the verdict from the class alone got two rows wrong on first run:
    scientific-research-guide (conditional, but no research question was ever
    asked) printed as a defect, and ai-coding-guardrails — the one genuine
    defect in the set — printed as expected because its declared class is
    user-manual while the user expects it always-on. So an ALL-CAPS opening
    token in `zero-means` overrides the class-derived guess.
    """
    lead = (meta.get("zero", "").split() or [""])[0].strip(":—-,")
    if len(lead) > 2 and lead.isupper():
        return f"{lead} — read the registry entry"
    cls = meta["class"].split()[0]
    if cls == "always-on":
        return "A DEFECT: this class must fire"
    if cls == "conditional":
        return "adjudicate: did the situation arise?"
    if cls == "second-order":
        return "read with the UPSTREAM skill's count, not alone"
    return "expected for this class"


CJK = re.compile(r"[　-鿿＀-￯]")


def folded_breaks(skills):
    """Line breaks in a `>-` description that corrupt a trigger token.

    A folded scalar joins lines with a SPACE. Break after a slash inside a
    compound token, or between two CJK characters, and that space lands inside
    the very string the router is meant to match. Shipped once, undetected:
    "package/export/ share this skill" (2026-08-15). `X / Y` is safe -- the
    space before the slash means the injected one lands where a space belongs.
    """
    out = []
    for sk in skills:
        p = os.path.join(SKILLS, sk, "SKILL.md")
        if not os.path.isfile(p):
            continue
        m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n",
                     io.open(p, encoding="utf-8").read(), re.S)
        d = re.search(r"^description:(.*?)(?=^\w[\w-]*:|\Z)", m.group(1),
                      re.S | re.M) if m else None
        if not d:
            continue
        lines = [l.strip() for l in d.group(1).splitlines()
                 if l.strip() and l.strip() != ">-"]
        for a, b in zip(lines, lines[1:]):
            if a.endswith(("/", "(", "[")) and not a.endswith((" /", " (", " [")):
                out.append((sk, f"ends with {a[-1]!r} mid-token", a, b))
            elif CJK.match(a[-1]) and CJK.match(b[0]) and a[-1] not in "」）、。":
                out.append((sk, "CJK/CJK join", a, b))
    return out


def desc_cap():
    """DESC_CAP read from the hook by name, never copied.

    A duplicated constant drifts silently: integrity-sweep check 15 exists
    because a cap raised in one place stayed stale in another.
    """
    p = os.path.join(HOME, "hooks", "ops_health_nudge.py")
    m = re.search(r"^DESC_CAP\s*=\s*(\d+)", io.open(p, encoding="utf-8").read(),
                  re.M) if os.path.isfile(p) else None
    return int(m.group(1)) if m else 800


DESC_CAP = desc_cap()


def load_classes():
    """Parse the class registry into {skill: {class, source, zero, proc[]}}."""
    out = {}
    if not os.path.isfile(CLASSES):
        return out
    cur = None
    for line in io.open(CLASSES, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^## ([\w-]+)\s*$", line)
        if m:
            cur = {"class": "?", "source": "?", "on-fire": "?",
                   "zero": "", "proc": []}
            out[m.group(1)] = cur
            continue
        if cur is None:
            continue
        m = re.match(r"^(class|source|on-fire|zero-means|proc):\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if k == "proc":
                cur["proc"].append(v)
            else:
                # `on-fire: execute  # why` — the rationale is for the reader
                if k != "zero-means":
                    v = v.split("#")[0].strip()
                cur["zero" if k == "zero-means" else k] = v
        elif cur.get("zero") and line.startswith("  ") and line.strip():
            cur["zero"] += " " + line.strip()          # continuation line
    return out


def description(skill):
    """(raw, flat) for a skill's description, or None.

    Two lengths on purpose. `flat` is the prose a reader judges; `raw` is the
    YAML slice INCLUDING indentation, which is what ops_health_nudge.py measures
    against DESC_CAP. Reporting flat as if it were the cap measurement is proxy
    promotion (ops/lessons.md L-012) and understates every skill by ~20 chars.
    """
    p = os.path.join(SKILLS, skill, "SKILL.md")
    if not os.path.isfile(p):
        return None
    txt = io.open(p, encoding="utf-8").read()
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", txt, re.S)
    if not m:
        return None
    d = re.search(r"^description:(.*?)(?=^\w[\w-]*:|\Z)", m.group(1), re.S | re.M)
    if not d:
        return None
    return len(d.group(1).rstrip()), " ".join(d.group(1).split())


def proc_ratio(skill, meta):
    """(raw_chars, desc_chars, procedure_chars, [stale fragments]).

    Fragments are stored ASCII-normalised; em/en dashes in the description are
    folded before matching so the registry stays typeable.
    """
    got = description(skill)
    if got is None:
        return None
    raw, d = got
    norm = d.replace("—", "-").replace("–", "-")
    tot, stale = 0, []
    for frag in meta.get("proc", []):
        if frag in norm:
            tot += len(frag)
        else:
            stale.append(frag)
    return raw, len(d), tot, stale


def load_entries():
    """Parse the dict into {skill: {'keywords': [...], 'avoid': [...]}}.

    A heading may name more than one target (`### /loop、/schedule`), and one
    section explicitly declares itself NOT a skill (`~/.claude/ops/`, marked
    「不是 skill、無觸發句」). Both are structural, not typos -- handle them
    here rather than letting them surface as phantom dict entries.

    `has_kw` records whether the entry carried a `關鍵詞：` line AT ALL. Only
    that line and `避免說法：` are parsed; the dict's other routing line,
    `精準句型：`, is prose written as example sentences and is deliberately NOT
    tokenised -- folding it in was measured on 2026-09-04 and added 205
    occurrences with ZERO extra hits, i.e. pure noise. But an entry with no
    keyword line has an EMPTY pattern list and therefore cannot match anything,
    so it used to print as DEAD ("the dict records the wrong words") when the
    truth is that it records no words at all. 10 of 13 DEAD entries were this.
    The flag lets the report separate the two (T-023 fix 1).
    """
    text = io.open(DICT, encoding="utf-8").read()
    entries, cur = {}, []
    for line in text.splitlines():
        m = re.match(r"^### +(.+)$", line)
        if m:
            raw_head = m.group(1)
            head = re.sub(r"[（(].*$", "", raw_head).strip()
            # A tombstone is an entry the dict KEEPS on purpose after verifying
            # the skill does not exist here, so nothing routes to it by mistake
            # and nobody re-researches it next quarter. It is silent BY DESIGN;
            # printing it beside real dead entries makes the reader adjudicate
            # the same four names every sweep, which is how a report stops being
            # read (2026-09-08: 4 of 8 DEAD entries were tombstones).
            tomb = "幻影條目" in raw_head
            cur = [h.strip().lstrip("/") for h in re.split(r"[、,]", head)
                   if h.strip()]
            for c in cur:
                entries.setdefault(c, {"keywords": [], "avoid": [],
                                       "has_kw": False, "tombstone": tomb})
            continue
        if not cur:
            continue
        if "不是 skill" in line or "無觸發句" in line:
            for c in cur:
                entries.pop(c, None)      # declared non-routable by the dict
            cur = []
            continue
        m = re.match(r"^- *關鍵詞[：:](.*)$", line)
        if m:
            for c in cur:
                entries[c]["keywords"] = split_tokens(m.group(1))
                entries[c]["has_kw"] = True
        m = re.match(r"^- *避免說法[：:](.*)$", line)
        if m:
            for c in cur:
                entries[c]["avoid"] = split_tokens(m.group(1))
    return entries


# Characters that, inside one keyword, mean the author wrote a CHOICE the
# matcher reads as a single literal token.
ALTERNATION_JOINERS = ("/", "／", "・", "·")


def split_tokens(raw):
    """`階段完成 (phase done)、存檔 (checkpoint)` -> both forms, separately.

    Each parenthetical is an ALTERNATE spelling of the same trigger, not a
    gloss to discard: the user types either one.
    """
    out = []
    for chunk in re.split(r"[、,，]", raw):
        chunk = chunk.strip().strip("`*")
        if not chunk:
            continue
        inner = re.findall(r"[（(]([^）)]+)[）)]", chunk)
        base = re.sub(r"[（(][^）)]*[）)]", "", chunk).strip()
        for t in [base] + inner:
            t = t.strip().strip("「」\"'")
            # a 1-char CJK token or a 2-char ASCII token matches everything
            if len(t) >= 2 and not (t.isascii() and len(t) < 4):
                out.append(t)
    return out


def compile_tokens(tokens):
    """ASCII tokens get an ASCII-only word boundary, never `\\b`.

    Python's `\\w` includes CJK, so `\\bskill create\\b` cannot match
    "按照skill create相關規則" -- there is no boundary between "create" and
    "相". The same silence hit "用media-fetch-pipeline這條路" and
    "settings.json，全域那份". That is how this user writes, so `\\b` was
    suppressing real matches across the whole dict: replacing it moved HIT
    21->28 over the 2026-09-04 corpus and workflow-checkpoint's coverage
    16%->24% (T-023 fix 2, evidence: the source environment's dict-review round-2 output).
    The lookarounds below spell the boundary in ASCII word chars only, so CJK
    COUNTS as a boundary while the guards that matter are unchanged: a token
    still cannot match inside an ASCII word ('eval' in 'evaluation', 'sers' in
    'Users'), which with PATHISH is what keeps paths from reading as requests.
    """
    pats = []
    for t in tokens:
        if t.isascii():
            pats.append((t, re.compile(
                r"(?<![0-9A-Za-z_])" + re.escape(t) + r"(?![0-9A-Za-z_])",
                re.I)))
        else:
            pats.append((t, re.compile(re.escape(t))))
    return pats


def human_text(rec):
    """The 810-of-25,138 filter. See contaminant note above."""
    if rec.get("isSidechain") or rec.get("isMeta") or rec.get("isCompactSummary"):
        return None
    if "toolUseResult" in rec or "agentId" in rec:
        return None
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return None
    c = msg.get("content")
    if isinstance(c, str):
        txt = c
    elif isinstance(c, list):
        txt = " ".join(b.get("text", "") for b in c
                       if isinstance(b, dict) and b.get("type") == "text")
    else:
        return None
    if not txt or "<local-command" in txt:
        return None
    txt = HARNESS_BLOCK.sub(" ", txt).strip()
    if not txt or txt.startswith(HARNESS_MARKERS):
        return None
    return txt


def walk_tool_uses(node, out):
    if isinstance(node, dict):
        if node.get("type") == "tool_use":
            out.append(node)
        for v in node.values():
            walk_tool_uses(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_tool_uses(v, out)


def scan(entries, since):
    """Replay every session as (human turn, then what fired) pairs."""
    pats = {s: compile_tokens(e["keywords"]) for s, e in entries.items()}
    avoid = {s: compile_tokens(e["avoid"]) for s, e in entries.items()}
    stats = defaultdict(lambda: {"hit": 0, "bypass": defaultdict(int),
                                 "miss": 0, "late": 0,
                                 "tokens": defaultdict(int)})
    detail = defaultdict(list)
    total_fires = defaultdict(int)
    turns = 0

    for dirpath, _, names in os.walk(PROJECTS):
        for name in sorted(names):
            if not name.endswith(".jsonl"):
                continue
            pending = None     # (skill_candidates, date, session)
            seen_since = 0
            # LATE bookkeeping (T-023 fix 3). LOOKAHEAD deliberately refuses to
            # attribute a fire six assistant events after the turn -- a fire
            # eleven turns later was routed by something else, and widening the
            # window would manufacture causation. But scoring those turns as a
            # plain MISS hides a third state: the words appeared, and the same
            # skill DID fire later in the same session. Live case: the corrected
            # skill-creator vocabulary matches its real 2026-07-07 turn and
            # still reads 0% coverage. LATE counts that state without claiming
            # it -- it is an upper bound on attribution loss, never a HIT.
            ev = 0                        # assistant events seen in this file
            session_miss = []             # [(skill, ev index at MISS)]
            session_fire = defaultdict(list)   # skill -> [ev index]
            # A transcript can carry the SAME human turn several times (a retry
            # re-emits it). Counting each copy inflates one utterance into five
            # occurrences and would silently distort every trend this tool is
            # meant to track, so identical text within a session counts once.
            seen_turns = set()
            try:
                fh = io.open(os.path.join(dirpath, name), encoding="utf-8",
                             errors="replace")
            except OSError:
                continue
            with fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        rec = json.loads(raw)
                    except Exception:
                        continue
                    date = (rec.get("timestamp") or "")[:10]
                    if since and date and date < since:
                        continue

                    if rec.get("type") == "user":
                        txt = human_text(rec)
                        if txt is None:
                            continue
                        # an explicit slash command is not a routing decision
                        if "<command-name>" in txt:
                            pending = None
                            continue
                        key = hash(txt)
                        if key in seen_turns:
                            pending = None
                            continue
                        seen_turns.add(key)
                        turns += 1
                        cands = match_turn(txt, pats, avoid)
                        pending = (cands, date, name[:-6][:8]) if cands else None
                        seen_since = 0
                        continue

                    if rec.get("isSidechain"):
                        continue
                    ev += 1
                    blocks = []
                    walk_tool_uses(rec.get("message"), blocks)
                    fired = [(b.get("input") or {}).get("skill")
                             for b in blocks if b.get("name") == "Skill"]
                    fired = [f for f in fired if f]
                    # Count EVERY fire, attributed or not. A skill that fires
                    # often while its dict entry never matches is the loudest
                    # defect this tool can find, and it is invisible unless the
                    # denominator is the real total (config-self-audit: 30
                    # fires, 0 dict matches, found 2026-08-15).
                    for f in fired:
                        total_fires[f] += 1
                        session_fire[f].append(ev)
                    if pending is None:
                        continue
                    seen_since += 1
                    if fired:
                        record(stats, detail, pending, fired[0])
                        pending = None
                    elif seen_since >= LOOKAHEAD:
                        session_miss += [(sk, ev) for sk in
                                         record(stats, detail, pending, None)]
                        pending = None
            if pending is not None:
                session_miss += [(sk, ev) for sk in
                                 record(stats, detail, pending, None)]
            for sk, idx in session_miss:
                if any(i > idx for i in session_fire.get(sk, ())):
                    stats[sk]["late"] += 1
    return stats, detail, turns, total_fires


def match_turn(txt, pats, avoid):
    """Which dict entries claim this turn?

    Returns [(skill, token, kind, excerpt)] where the excerpt is centred on the
    MATCH, not on the start of the turn. A report whose excerpt does not show
    the matched word cannot be adjudicated: the first run printed turn-openings
    and made true matches look like false ones (2026-08-15).
    """
    out = []
    for skill, plist in pats.items():
        for tok, pat in plist:
            m = pat.search(txt)
            if not m:
                continue
            i = m.start()
            if PATHISH.search(txt[max(0, i - 40):i + 40]):
                continue                       # the token lives inside a path
            exc = txt[max(0, i - 45):i + 75].replace("\n", " ")
            out.append((skill, tok, "keyword", ("…" if i > 45 else "") + exc))
            break
    for skill, plist in avoid.items():
        for tok, pat in plist:
            if pat.search(txt):
                out.append((skill, tok, "avoid", ""))
                break
    return out


def record(stats, detail, pending, fired):
    """Score one matched turn. Returns the skills that scored MISS, so the
    caller can ask the LATE question about them once the session is read."""
    cands, date, sess = pending
    missed = []
    for skill, tok, kind, excerpt in cands:
        if kind == "avoid":
            continue                # 避免說法 belongs to a NEIGHBOUR, not here
        s = stats[skill]
        s["tokens"][tok] += 1
        if fired == skill:
            s["hit"] += 1
            verdict = "HIT"
        elif fired:
            s["bypass"][fired] += 1
            verdict = "BYPASS->" + fired
        else:
            s["miss"] += 1
            verdict = "MISS"
            missed.append(skill)
        detail[skill].append((date, sess, tok, verdict, excerpt))
    return missed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="ignore turns before this date")
    ap.add_argument("--skill", help="restrict the report to one dict entry")
    ap.add_argument("--detail", action="store_true",
                    help="print every matched turn, not just counts")
    ap.add_argument("--surface", action="store_true",
                    help="report each description's procedure share and cap use")
    ap.add_argument("--snapshot", action="store_true",
                    help="append today's counts to telemetry/ for trend")
    args = ap.parse_args()

    if not os.path.isfile(DICT):
        print("skill-trigger-dict.md not found", file=sys.stderr)
        return 2
    entries = load_entries()
    classes = load_classes()
    local = {n for n in os.listdir(os.path.join(HOME, "skills"))
             if os.path.isfile(os.path.join(HOME, "skills", n, "SKILL.md"))}
    stats, detail, turns, total_fires = scan(entries, args.since)

    print(f"dict entries: {len(entries)}   human turns scanned: {turns}"
          f"{'   since ' + args.since if args.since else ''}")
    # The class registry decides whether a zero is news, and the `quiet`
    # population below is built from the DICT -- so a skill with no block was
    # not printed as a bad verdict, it was printed as NOTHING, and this
    # report's silence about it read exactly like a clean bill. Measured
    # 2026-09-08: the registry covered 15 of 29 skills and said so nowhere.
    # An instrument states its own coverage or its silence is unreadable.
    unclassified = sorted(local - set(classes))
    print(f"class registry: {len(local) - len(unclassified)}/{len(local)} local "
          f"skill(s) classified"
          + (f" — NO BLOCK for {len(unclassified)}: {', '.join(unclassified)}; "
             f"this report says nothing about them (add a block to "
             f"ops/references/skill-trigger-classes.md)" if unclassified else ""))
    print(f"lookahead: {LOOKAHEAD} assistant events after a turn\n")
    print(f"{'dict entry':30} {'occ':>4} {'HIT':>4} {'BYP':>4} {'MISS':>5}"
          f" {'LATE':>5} {'fires':>6} {'cov':>5}  bypassed-to")
    print("-" * 98)

    dead, novocab = [], []
    for skill in sorted(entries):
        if args.skill and skill != args.skill:
            continue
        s = stats.get(skill)
        occ = (s["hit"] + s["miss"] + sum(s["bypass"].values())) if s else 0
        fires = total_fires.get(skill, 0)
        if not occ:
            # An entry with no 關鍵詞 line registers NOTHING, so a zero here is
            # the instrument's silence, not the dict's fiction. Keeping the two
            # in one bucket accused 10 entries of "recording the wrong words"
            # when they recorded no words at all (T-023 fix 1).
            (dead if entries[skill]["has_kw"] else novocab).append(
                (skill, fires))
            continue
        rate = 100.0 * s["hit"] / occ
        # coverage: of every time this skill ACTUALLY fired, how much can the
        # dict explain? Low coverage with high fires means routing works and
        # the dict is fiction.
        cov = f"{100.0 * s['hit'] / fires:4.0f}%" if fires else "   -"
        thief = ", ".join(f"{k}x{v}" for k, v in
                          sorted(s["bypass"].items(), key=lambda kv: -kv[1])[:3])
        # Most zeros land HERE, not in the DEAD block: the dict words appeared
        # (occ>0) but the skill never fired. Whether that is a defect depends
        # entirely on the class, so print it on the same line as the zero.
        meta = classes.get(skill)
        note = thief
        if not fires and meta:
            note = f"ZERO — {meta['class'][:22]}, {zero_verdict(meta)}"
        elif meta and meta["source"] == "omission":
            # A non-zero here bounds nothing: this skill's failure mode is a
            # check that never ran, and a check that never ran emits no event.
            note = f"{fires} fires bound NOTHING — omission-shaped trigger"
        print(f"{skill:30} {occ:4} {s['hit']:4} {sum(s['bypass'].values()):4}"
              f" {s['miss']:5} {s['late']:5} {fires:6} {cov}  {note}")

    if novocab and not args.skill:
        print(f"\nNO VOCABULARY — the entry registers no 關鍵詞 line, so this "
              f"tool has nothing to match ({len(novocab)}):")
        print("  Not a verdict on the entry. `精準句型` is not tokenised (it is "
              "prose, and folding it in\n  measured +205 occurrences / +0 hits "
              "on 2026-09-04). Give the entry keywords to make it\n  "
              "measurable, or leave it if it is a tombstone.")
        for d, f in sorted(novocab, key=lambda x: -x[1]):
            fired = f"fired {f}x — unexplained, and unexplainABLE here" if f \
                else "never fired"
            print(f"    {d:30} {fired}")

    tombs = [(d, f) for d, f in dead if entries[d].get("tombstone")]
    dead = [(d, f) for d, f in dead if not entries[d].get("tombstone")]
    if tombs and not args.skill:
        print(f"\nTOMBSTONES — verified absent from this machine, kept so nothing "
              f"routes to them ({len(tombs)}); silent BY DESIGN, not findings:")
        for d, f in sorted(tombs):
            extra = f" — BUT IT FIRED {f}x, so the tombstone is wrong" if f else ""
            print(f"    {d}{extra}")

    if dead and not args.skill:
        print(f"\nDEAD entries — dict vocabulary never appeared ({len(dead)}):")
        firing = [(d, f) for d, f in dead if f]
        quiet = [d for d, f in dead if not f]
        if firing:
            print("  *** FIRING ANYWAY — the dict records the wrong words ***")
            for d, f in sorted(firing, key=lambda x: -x[1]):
                src = classes.get(d, {}).get("source", "")
                why = f"  ({src} — the dict models utterances only)" \
                    if src in ("artifact-context", "omission") else ""
                print(f"    {d:30} fired {f}x, dict explains 0{why}")
        # A zero is only news for a class that was supposed to fire. Splitting
        # here is the whole point of the class registry: before it, motion-design
        # (phase-gated, no UI phase) and ai-coding-guardrails printed alike.
        for d in quiet:
            meta = classes.get(d)
            if meta and meta["class"].split()[0] not in NOISY_ZERO:
                continue
            mark = "" if d in local else "   (not a local skill)"
            print(f"    {d}{mark}  — never fired either; may simply have had "
                  f"no occasion")
        expected = [d for d in quiet if classes.get(d)
                    and classes[d]["class"].split()[0] not in NOISY_ZERO]
        if expected:
            print(f"  quiet AND EXPECTED to be, per class ({len(expected)}), "
                  f"not findings:")
            for d in expected:
                print(f"    {d:30} {classes[d]['class']}")

    # A keyword written as an ALTERNATION (`把影片/圖片存下來`, `GLSL/shader`)
    # is one literal token to the matcher: it fires only if the user types the
    # slash too, which nobody does. This is a property of the TOKEN, so it is
    # detected rather than listed -- a new entry written the same way is caught
    # the day it lands. Measured 2026-09-08: media-fetch-pipeline fired once
    # with its dict explaining zero, and its keyword line was slash-compounded.
    # 2026-09-22: the same class appeared with a middle dot as the joiner
    # (`機制架構檢查・系統架構盤點・檢查項`, diagram-authoring), which the slash
    # test could not see; the separator set is the class, not the character.
    unmatchable = []
    for skill in sorted(entries):
        if args.skill and skill != args.skill:
            continue
        for tok in entries[skill]["keywords"]:
            if any(c in tok for c in ALTERNATION_JOINERS):
                unmatchable.append((skill, tok))
    if unmatchable and not args.skill:
        print(f"\nUNMATCHABLE AS WRITTEN — a keyword carrying `/` or `・` is ONE literal "
              f"token, not a choice ({len(unmatchable)}):")
        print("  It matches only a turn that types the slash as well. Repair: "
              "spell each alternative\n  as its own 、-separated keyword. Not "
              "scored above — these tokens inflate no count,\n  they simply "
              "never match, so every MISS and coverage figure here is a FLOOR.")
        for skill, tok in unmatchable:
            print(f"    {skill:30} {tok}")

    if args.surface and not args.skill:
        print("\nROUTING SURFACE composition — procedure text is charged every "
              "session and buys no routing:")
        print(f"  {'skill':28} {'desc':>5} {'proc%':>6} {'%cap':>6}  "
              f"{'class':<14} {'on-fire':<10}")
        rows = []
        for sk in sorted(local):
            meta = classes.get(sk)
            if not meta:
                rows.append((0, sk, None, None, "NOT CLASSIFIED", "?", []))
                continue
            r = proc_ratio(sk, meta)
            if r is None:
                continue
            raw, dl, pl, stale = r
            rows.append((pl / dl * 100, sk, raw, dl, pl,
                         meta["class"], meta["on-fire"], stale))
        for row in sorted(rows, key=lambda r: -r[0]):
            if row[2] is None:
                print(f"  {row[1]:28} {'':>5} {'':>6} {'':>6}  {row[4]}")
                continue
            pct, sk, raw, dl, pl, cls, fire, stale = row
            # DESC_CAP mirrors hooks/ops_health_nudge.py; >=95% is the
            # saturation case of integrity-sweep check 15.
            cap = raw / DESC_CAP * 100
            flag = "  SATURATED" if cap >= 95 else ""
            print(f"  {sk:28} {dl:5} {pct:5.1f}% {cap:5.1f}%  {cls[:26]:<26} "
                  f"{fire:<10}{flag}")
            for s in stale:
                print(f"      STALE fragment, re-classify: {s[:60]}")
        for sk, why, a, b in folded_breaks(sorted(local)):
            print(f"  BROKEN TOKEN in {sk} ({why}) — the folded newline puts a "
                  f"space inside a trigger string:\n      ...{a[-38:]}"
                  f"\n      {b[:38]}...")
        unclassified = [r[1] for r in rows if r[2] is None]
        if unclassified:
            print(f"  {len(unclassified)} skill(s) missing from "
                  f"ops/references/skill-trigger-classes.md")

    print("\nNOT COUNTABLE HERE, left to a reader: whether a MISS was correct."
          "\nThe words appearing does not prove the situation called for the "
          "skill.")
    # What this ruler still cannot see. Printed with every run BECAUSE the
    # three biases fixed under T-023 were invisible for weeks and the numbers
    # were quoted as settled while they were understating the dict; the way a
    # gate stops doing that is to report itself beside its rate.
    print("REMAINING BLIND SPOTS of this instrument, by construction:"
          "\n  1. It models UTTERANCES. A skill routed by artifact context or "
          "by a decision the\n     model made from a description of a need "
          "(measured: 2 of skill-creator's 6 fires)\n     cannot be described "
          "by any dict entry, so its coverage is bounded below 100%."
          "\n  2. LATE counts turns whose words appeared and whose own skill "
          "fired LATER in the same\n     session, past the "
          f"{LOOKAHEAD}-event attribution window. It is an upper bound on lost "
          "attribution,\n     not evidence of causation — it is deliberately "
          "NOT added to HIT or to coverage."
          "\n  3. A MISS is scored per TURN, a fire per EVENT; one turn that "
          "matches several entries\n     scores each of them, so occurrences "
          "sum higher than turns and are not a turn count.")

    if args.detail:
        for skill in sorted(detail):
            if args.skill and skill != args.skill:
                continue
            print(f"\n=== {skill} ===")
            for date, sess, tok, verdict, exc in sorted(detail[skill]):
                print(f"  {date} {sess} {verdict:16} [{tok}] {exc}")

    if args.snapshot:
        os.makedirs(os.path.dirname(SNAP), exist_ok=True)
        row = {"date": __import__("datetime").date.today().isoformat(),
               "since": args.since, "turns": turns,
               "entries": {k: {"hit": v["hit"], "miss": v["miss"],
                               "late": v["late"],
                               "bypass": dict(v["bypass"])}
                           for k, v in stats.items()}}
        with io.open(SNAP, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"\nsnapshot appended -> {SNAP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
