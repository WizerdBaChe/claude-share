"""Controls for cc_delta.py's feature-delta mode and stamp gate.

Each judgement gets a known-TRUE and a known-false input. The end-to-end
control runs the real CLI and asserts that a stamp without a record is refused
and leaves ops/cc-reconciled.json byte-identical.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cc_delta  # noqa: E402

LO, HI = (2, 1, 276), (2, 1, 281)
SECTIONS = [((2, 1, 281), "2.1.281", [
    "Added a thing everyone gets",
    "[VSCode] Added a panel button",
    "Self-hosted runner: Changed lifecycle git",
    "Added `assume_role` on Claude apps gateway Bedrock upstreams",
    "Fixed a SessionStart hook losing output",
    "Fixed the /skills list scrollbar",
    "Windows: Added a Windows-only switch",
]), ((2, 1, 276), "2.1.276", ["Added something already reconciled"])]


def test_features_split():
    cands, oos, skipped = cc_delta.features(SECTIONS, LO, HI, ["SessionStart"])
    got = {(k, b) for _, k, b in cands}
    assert ("feature", "Added a thing everyone gets") in got
    assert ("feature", "Windows: Added a Windows-only switch") in got
    assert ("local", "Fixed a SessionStart hook losing output") in got
    assert oos == 3                      # VSCode, runner, gateway
    assert skipped == 1                  # the /skills scrollbar fix
    assert all("already reconciled" not in b for _, _, b in cands)


def test_features_without_local_terms_keeps_only_feature_verbs():
    cands, _, skipped = cc_delta.features(SECTIONS, LO, HI, [])
    assert {k for _, k, _ in cands} == {"feature"}
    assert skipped == 2


def test_local_terms_are_distinctive():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "settings.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"model": "haiku", "theme": "auto", "effortLevel": "medium",
                       "hooks": {"SubagentStart": []}, "env": {"CLAUDE_CODE_X": "1"}}, f)
        terms = cc_delta.local_terms(p)
    assert "effortLevel" in terms and "SubagentStart" in terms and "CLAUDE_CODE_X" in terms
    assert "model" not in terms and "theme" not in terms


def _record(text, name="t.md"):
    os.makedirs(cc_delta.RECORD_DIR, exist_ok=True)
    path = os.path.join(cc_delta.RECORD_DIR, "_test_" + name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


GOOD = ("# 2.1.276 -> 2.1.281\n## 新機制\n## 新功能\n## 衝突\n## 相關\n## 不適用\n")


def test_good_record_passes():
    p = _record(GOOD)
    try:
        assert cc_delta.check_record(p, LO, HI) == []
    finally:
        os.remove(p)


def test_missing_heading_fails():
    p = _record(GOOD.replace("## 衝突\n", ""))
    try:
        assert any("衝突" in x for x in cc_delta.check_record(p, LO, HI))
    finally:
        os.remove(p)


def test_wrong_range_fails():
    p = _record(GOOD.replace("2.1.276", "2.1.270"))
    try:
        assert any("range" in x for x in cc_delta.check_record(p, LO, HI))
    finally:
        os.remove(p)


def test_record_outside_folder_fails():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "r.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(GOOD)
        assert cc_delta.check_record(p, LO, HI) == ["record must live in reports/cc-upgrade-delta/"]


def test_no_record_fails():
    assert cc_delta.check_record(None, LO, HI) == ["no --record given"]


def test_end_to_end_stamp_without_record_is_refused():
    before = open(cc_delta.STAMP, "rb").read()
    r = subprocess.run([sys.executable, cc_delta.__file__, "--stamp",
                        "--assume-version", "9.9.9"], capture_output=True, text=True)
    assert r.returncode == 2 and "REFUSED" in r.stdout
    assert open(cc_delta.STAMP, "rb").read() == before
