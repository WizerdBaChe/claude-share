#!/usr/bin/env python3
"""Two-sided calibration for the three T-023 fixes in skill-routing-audit.py.

Each fix removed a bias that made the dict look MORE fictional than it is, so
each one is tested with a known-TRUE input (the state the fix must now show)
AND a known-FALSE input (the state it must still refuse). A one-sided fixture
would pass for a tool that simply says yes to everything — the global gate rule
this environment audits by.

  fix 1  NO VOCABULARY vs DEAD
         TRUE  : an entry with only `精準句型` lands in NO VOCABULARY
         FALSE : an entry WITH `關鍵詞` whose words never appear is still DEAD
  fix 2  ASCII boundary in a CJK corpus
         TRUE  : token `skill create` matches 「按照skill create相關規則」
         FALSE : token `eval` still does NOT match "evaluation" (inside a word),
                 and a token inside a Windows path is still discarded
  fix 3  LATE
         TRUE  : words at event 1, the SAME skill fires at event 12 -> LATE 1
         FALSE : words appear and the skill never fires -> LATE 0, MISS stays
  r3-a   TOMBSTONE split (2026-09-08, dict-review round 3)
         TRUE  : a 「幻影條目」 heading marks the entry silent-by-design
         FALSE : an ordinary heading does not, so real fiction is still reported
  r3-b   UNMATCHABLE tokens (same round)
         TRUE  : a keyword carrying `/` is reported as one literal token
         FALSE : plain keywords, and a slash living in 精準句型 / a URL / a
                 path, are NOT reported — flagging working vocabulary would
                 send the reader to rewrite entries that already fire

The corpus is synthetic: `scan()` walks the module-level PROJECTS directory, so
the tests point it at a temp tree of hand-written .jsonl transcripts. Nothing
here reads the real ~/.claude corpus, so the numbers cannot drift under it.

    python tools/skill-routing-audit-test/test_skill_routing_audit.py
"""
import importlib.util
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TOOL = os.path.join(os.path.dirname(HERE), "skill-routing-audit.py")

_passed = 0
_failed = 0


def check(name, got, want):
    global _passed, _failed
    if got == want:
        _passed += 1
        print(f"pass  {name}")
    else:
        _failed += 1
        print(f"FAIL  {name}\n        got  {got!r}\n        want {want!r}")


def load(path):
    spec = importlib.util.spec_from_file_location("sra", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_dict(tmp, body):
    p = os.path.join(tmp, "skill-trigger-dict.md")
    io.open(p, "w", encoding="utf-8", newline="\n").write(body)
    return p


def transcript(tmp, name, events):
    """events: list of ("user", text) or ("fire", skill) or ("assistant", None)"""
    d = os.path.join(tmp, "projects", "proj")
    os.makedirs(d, exist_ok=True)
    rows = []
    for kind, payload in events:
        if kind == "user":
            rows.append({"type": "user", "timestamp": "2026-09-04T00:00:00Z",
                         "message": {"content": payload}})
        elif kind == "fire":
            rows.append({"type": "assistant", "timestamp": "2026-09-04T00:00:00Z",
                         "message": {"content": [
                             {"type": "tool_use", "name": "Skill",
                              "input": {"skill": payload}}]}})
        else:
            rows.append({"type": "assistant", "timestamp": "2026-09-04T00:00:00Z",
                         "message": {"content": [{"type": "text", "text": "…"}]}})
    with io.open(os.path.join(d, name + ".jsonl"), "w",
                 encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def buckets(mod, entries, stats, total_fires):
    """Reproduce main()'s DEAD / NO VOCABULARY split without its printing."""
    dead, novocab = [], []
    for skill in sorted(entries):
        s = stats.get(skill)
        occ = (s["hit"] + s["miss"] + sum(s["bypass"].values())) if s else 0
        if not occ:
            (dead if entries[skill]["has_kw"] else novocab).append(skill)
    return dead, novocab


# ---------------------------------------------------------------- fix 1
def test_novocab_split(mod):
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, "\n".join([
            "### only-sentences（無關鍵詞行）",
            "- 精準句型：「幫我建一個新 skill」",
            "",
            "### has-keywords（有關鍵詞行）",
            "- 關鍵詞：一個絕對不會出現的詞彙",
            "",
        ]))
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "s1", [("user", "完全無關的一句話"), ("assistant", None)])
        entries = mod.load_entries()
        stats, _d, _t, fires = mod.scan(entries, None)
        dead, novocab = buckets(mod, entries, stats, fires)

        # known-TRUE: the entry that registers nothing is NOT accused of
        # recording the wrong words
        check("fix1 TRUE  entry with only 精準句型 -> NO VOCABULARY",
              novocab, ["only-sentences"])
        # known-FALSE: an entry that DID register words and was not spoken is
        # still DEAD — the split must not swallow the real finding
        check("fix1 FALSE entry with 關鍵詞 never spoken -> still DEAD",
              dead, ["has-keywords"])
        check("fix1 has_kw flag is set only by a 關鍵詞 line",
              (entries["only-sentences"]["has_kw"],
               entries["has-keywords"]["has_kw"]), (False, True))


# ---------------------------------------------------------------- fix 2
def test_ascii_boundary(mod):
    def matches(token, text):
        pats = mod.compile_tokens([token])
        return bool(mod.match_turn(text, {"x": pats}, {}))

    # known-TRUE: this is how the user writes — ASCII flush against CJK
    check("fix2 TRUE  'skill create' matches 按照skill create相關規則",
          matches("skill create", "product-design-thinking，按照skill create相關規則重新處理"),
          True)
    check("fix2 TRUE  'settings.json' matches settings.json，全域那份移除",
          matches("settings.json", "搬到專案的 settings.json，全域那份移除"), True)
    check("fix2 TRUE  'media-fetch-pipeline' matches 用media-fetch-pipeline這條路",
          matches("media-fetch-pipeline", "歌曲庫你使用media-fetch-pipeline這條路"),
          True)
    # known-FALSE: the guards the old \b was actually buying must survive
    check("fix2 FALSE 'eval' does NOT match inside 'evaluation'",
          matches("eval", "run the evaluation suite first"), False)
    check("fix2 FALSE 'user' does NOT match inside 'Users' ",
          matches("user", "check the Username field"), False)
    check("fix2 FALSE a token inside a Windows path is still discarded",
          matches("sers", r'@"C:\Users\someone\Downloads\x.md" 這份'), False)


# ---------------------------------------------------------------- fix 3
def test_late(mod):
    body = "\n".join([
        "### late-skill（測試用）",
        "- 關鍵詞：一句會出現的觸發語",
        "",
    ])
    # known-TRUE: words at event 1, own skill fires at event 12 — far past
    # LOOKAHEAD, so it must NOT be a HIT, and must not vanish either
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, body)
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "late", [("user", "這裡有一句會出現的觸發語")]
                   + [("assistant", None)] * 11 + [("fire", "late-skill")])
        entries = mod.load_entries()
        stats, _d, _t, fires = mod.scan(entries, None)
        s = stats["late-skill"]
        check("fix3 TRUE  fire past the window -> LATE 1, MISS 1, HIT 0",
              (s["late"], s["miss"], s["hit"]), (1, 1, 0))
        check("fix3 TRUE  LATE is not folded into the fire count",
              fires.get("late-skill"), 1)

    # known-FALSE: the same words, and the skill never fires at all
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, body)
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "never", [("user", "這裡有一句會出現的觸發語")]
                   + [("assistant", None)] * 11)
        entries = mod.load_entries()
        stats, _d, _t, _f = mod.scan(entries, None)
        s = stats["late-skill"]
        check("fix3 FALSE no fire at all -> LATE 0, MISS 1",
              (s["late"], s["miss"]), (0, 1))

    # known-FALSE: a fire BEFORE the words is not lateness, it is a different
    # turn's fire — ordering must be respected, not just co-presence
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, body)
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "before",
                   [("user", "無關的開場"), ("fire", "late-skill")]
                   + [("user", "這裡有一句會出現的觸發語")]
                   + [("assistant", None)] * 11)
        entries = mod.load_entries()
        stats, _d, _t, _f = mod.scan(entries, None)
        check("fix3 FALSE a fire BEFORE the words is not LATE",
              stats["late-skill"]["late"], 0)

    # known-TRUE control on the window itself: a fire INSIDE the window is a
    # plain HIT and must not be counted as LATE as well
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, body)
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "inwindow",
                   [("user", "這裡有一句會出現的觸發語"), ("fire", "late-skill")])
        entries = mod.load_entries()
        stats, _d, _t, _f = mod.scan(entries, None)
        s = stats["late-skill"]
        check("fix3 TRUE  fire inside the window -> HIT 1, LATE 0",
              (s["hit"], s["late"]), (1, 0))


# ---------------------------------------------------------------- round 3
def test_tombstone_split(mod):
    """A tombstone is silent BY DESIGN; a dead entry is a finding. Not the same.

    Known-FALSE matters more than known-TRUE here: if the marker swallowed
    ordinary entries, real fiction would stop being reported and the split
    would be strictly worse than the bucket it replaced.
    """
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, "\n".join([
            "### ghost-skill（幻影條目 — 2026-09-08 查證：本機不存在，勿路由）",
            "- 關鍵詞：一個絕對不會出現的詞彙甲",
            "",
            "### real-skill（正常條目）",
            "- 關鍵詞：一個絕對不會出現的詞彙乙",
            "",
        ]))
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "s1", [("user", "完全無關的一句話"), ("assistant", None)])
        entries = mod.load_entries()
        check("r3 TRUE  幻影條目 heading marks the entry as a tombstone",
              entries["ghost-skill"]["tombstone"], True)
        check("r3 FALSE an ordinary heading does NOT mark one",
              entries["real-skill"]["tombstone"], False)


def test_unmatchable_tokens(mod):
    """A keyword carrying `/` is one literal token, so it can never fire.

    Known-FALSE is the whole risk: flagging tokens that DO match would send a
    reader to rewrite working vocabulary. A URL and a path both contain
    slashes and neither is the defect, so both are pinned as must-not-flag.
    """
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, "\n".join([
            "### slashy（有斜線字彙）",
            "- 關鍵詞：把影片/圖片存下來、正常詞彙甲",
            "",
            "### clean（無斜線字彙）",
            "- 關鍵詞：正常詞彙乙、another plain token",
            "",
        ]))
        entries = mod.load_entries()

        def unmatchable(e):
            return sorted((s, t) for s in e for t in e[s]["keywords"]
                          if "/" in t or "／" in t)

        check("r3 TRUE  a slash-compounded keyword is reported",
              unmatchable(entries), [("slashy", "把影片/圖片存下來")])
        check("r3 FALSE plain keywords are not reported",
              [t for s, t in unmatchable(entries) if s == "clean"], [])

        # known-FALSE, second shape: the detector rules on KEYWORDS only, so a
        # slash anywhere else in the entry (a path, a URL, prose) is not a hit.
        mod.DICT = write_dict(tmp, "\n".join([
            "### pathy（斜線出現在別的行）",
            "- 關鍵詞：正常詞彙丙",
            "- 精準句型：「把 tools/graph-snapshot/gsnap.py 跑一下」",
            "- 註：見 https://example.com/a/b",
            "",
        ]))
        check("r3 FALSE a slash in 精準句型 / a URL / a path is not a keyword defect",
              unmatchable(mod.load_entries()), [])


# ---------------------------------------------------------------- fix 6
def test_harness_text(mod):
    """Contaminant 4: harness notices written as user records."""
    def rec(text):
        return {"type": "user", "message": {"content": text}}
    note = ("<task-notification> <task-id>a1</task-id> <summary>gate PASS, "
            "control fired</summary> </task-notification>")
    rem = "<system-reminder> started task_x (\"gate run\") </system-reminder>"
    # known-TRUE: what the human typed survives, reminder text does not
    check("fix6 TRUE  plain human turn unchanged",
          mod.human_text(rec("幫我畫架構圖")), "幫我畫架構圖")
    check("fix6 TRUE  reminder-prefixed turn keeps only the human text",
          mod.human_text(rec(rem + "\n開著的這張ticket做掉")), "開著的這張ticket做掉")
    # known-FALSE: pure harness records are not human turns
    check("fix6 FALSE task-notification record -> None",
          mod.human_text(rec(note)), None)
    check("fix6 FALSE interrupt marker -> None",
          mod.human_text(rec("[Request interrupted by user]")), None)
    # end to end: a dict token inside a notification must not count as a MISS
    with tempfile.TemporaryDirectory() as tmp:
        mod.DICT = write_dict(tmp, "\n".join([
            "### gate-skill（測試用）", "- 關鍵詞：gate", ""]))
        mod.PROJECTS = os.path.join(tmp, "projects")
        transcript(tmp, "s1", [("user", note), ("assistant", None),
                               ("user", rem + " 普通的一句話"), ("assistant", None)])
        entries = mod.load_entries()
        stats, _d, turns, _f = mod.scan(entries, None)
        check("fix6 notification token is not a MISS (miss, turns)",
              (stats["gate-skill"]["miss"] if "gate-skill" in stats else 0, turns),
              (0, 1))


def main():
    tool = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOOL
    print(f"testing {tool}\n")
    global _failed
    for fn in (test_novocab_split, test_ascii_boundary, test_late,
               test_tombstone_split, test_unmatchable_tokens, test_harness_text):
        # A fresh module per group: the tests rebind DICT and PROJECTS.
        # An exception counts as a FAIL rather than aborting the run — the
        # point of pointing this file at an OLD copy of the tool (the negative
        # control for the tests themselves) is to see all three groups fail,
        # and two of the three fail by raising, not by returning a wrong value.
        try:
            fn(load(tool))
        except Exception as exc:
            _failed += 1
            print(f"FAIL  {fn.__name__} raised {type(exc).__name__}: {exc}")
    print(f"\n{_passed}/{_passed + _failed} passed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
