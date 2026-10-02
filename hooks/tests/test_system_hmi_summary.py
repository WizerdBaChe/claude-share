"""Two-sided suite for hooks/system_hmi_summary.py (HMI-05 card + design 17).

Pure `compose()` cases never read the live tree; the two subprocess cases point the hook
at a temp dir through SYSTEM_HMI_OUT. Run: python hooks/tests/test_system_hmi_summary.py
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "system_hmi_summary.py"
sys.path.insert(0, str(HOOK.parent))
import system_hmi_summary as h  # noqa: E402

NOW = datetime.datetime(2026, 9, 22, 12, 0, tzinfo=datetime.timezone.utc)
RESULTS = []


def iso(days=0, hours=0):
    return (NOW - datetime.timedelta(days=days, hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def pt(pid, sub, state="pass", quality="good", since=None, remedy=None, disp="active"):
    return {"id": pid, "subsystem": sub, "remedy": remedy, "disposition": {"value": disp},
            "reading": {"quality": quality, "state": state, "since": since or iso(hours=1)}}


def snap(points, hours_old=1):
    return {"run": {"finished_at": iso(hours=hours_old)}, "points": points, "components": []}


KG = {"sha": "abcdef1234567", "marked_at": iso(hours=3)}


def case(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))


def t_missing_snapshot():
    out = h.compose(None, None, None, NOW)
    assert out[0].startswith(h.TAG) and "unavailable" in out[0] and len(out) == 2, out


def t_stale_snapshot_lists_nothing():
    out = h.compose(snap([pt("a.x", "a", "fail")], hours_old=40), KG, 2, NOW)
    assert "too old to list" in out[0] and not any("!!" in ln for ln in out), out


def t_fresh_snapshot_is_listed():  # negative of the stale case
    out = h.compose(snap([pt("a.x", "a", "fail")], hours_old=30), KG, 2, NOW)
    assert any(ln.startswith("  !! a: fail") for ln in out), out


def t_all_pass_says_nothing_needs_doing():
    out = h.compose(snap([pt("a.x", "a"), pt("b.y", "b")]), KG, 0, NOW)
    assert len(out) == 2 and "Nothing needs doing" in out[0] and "HEAD is that commit" in out[1], out


def t_nine_failing_prints_six_and_more():
    pts = [pt(f"s{i}.p", f"s{i}", "fail") for i in range(9)]
    out = h.compose(snap(pts), KG, 1, NOW)
    items = [ln for ln in out if ln.startswith("  !! ")]
    assert len(items) == 6 and any("and 3 more" in ln for ln in out), out
    assert out[1].startswith("  known-good"), "known-good must sit above the items"


def t_undetermined_is_counted_never_itemised():
    out = h.compose(snap([pt("a.x", "a", None, "undetermined"), pt("b.y", "b", None, "stale")]),
                    KG, 0, NOW)
    assert "2 unwatched" in out[0] and not any(ln.startswith("  !") for ln in out), out


def t_standing_marked_when_old():
    out = h.compose(snap([pt("a.x", "a", "fail", since=iso(days=3))]), KG, 0, NOW)
    assert "standing 3 d (since 2026-09-19)" in out[2], out


def t_standing_absent_when_new():  # negative
    out = h.compose(snap([pt("a.x", "a", "fail", since=iso(hours=5))]), KG, 0, NOW)
    assert out[2].startswith("  !! a: fail") and "standing" not in out[2], out


def t_deferred_counted_never_itemised():
    """2026-09-23: a holding deferral reads pass and is COUNTED (visible), never listed as an alarm;
    the same point with its trigger fired reads warn and IS listed (positive control)."""
    held = pt("m.x", "m")
    held["reading"]["deferral"] = {"status": "holding", "trigger": "a consumer exists"}
    out = h.compose(snap([held]), KG, 0, NOW)
    assert "1 deferred (trigger not fired)" in out[0] and "Nothing needs doing" in out[0], out
    assert not any(ln.startswith("  !") for ln in out), out
    fired = pt("m.x", "m", "warn")
    fired["reading"]["deferral"] = {"status": "fired", "trigger": "a consumer exists"}
    out = h.compose(snap([fired]), KG, 0, NOW)
    assert "deferred" not in out[0] and any(ln.startswith("  ! m: warn") for ln in out), out


def t_shelved_or_retired_not_itemised():
    p = pt("a.x", "a", "fail", disp="retired")
    out = h.compose(snap([p]), KG, 0, NOW)
    assert not any(ln.startswith("  !!") for ln in out), out


def t_fail_sorts_before_warn_and_python_remedy_is_run():
    pts = [pt("w.x", "w", "warn"), pt("f.x", "f", "fail", remedy="python -X utf8 tools/f/c.py")]
    out = h.compose(snap(pts), KG, 0, NOW)
    assert out[2] == "  !! f: fail -- run: python -X utf8 tools/f/c.py", out
    assert out[3] == "  ! w: warn", out


def t_known_good_lines():
    assert "no known-good commit recorded" in h.known_good_line(None, None, NOW)
    assert "HEAD is 4 commit(s) past it" in h.known_good_line(KG, 4, NOW)
    assert "abcdef1" in h.known_good_line(KG, 0, NOW)
    assert "not determined" in h.known_good_line(KG, None, NOW)


def t_byte_cap():
    long_remedy = "x" * 400
    pts = [pt(f"s{i}.p", f"s{i}", "fail", remedy=long_remedy) for i in range(6)]
    out = h.cap(h.compose(snap(pts), KG, 0, NOW))
    assert len("\n".join(out).encode("utf-8")) <= h.MAX_BYTES + 80 and "cut at" in out[-1], out
    assert any(ln.startswith("  known-good") for ln in out), "the cap must never cut known-good"


def t_byte_cap_not_hit_on_short_rows():  # negative
    out = h.cap(h.compose(snap([pt("a.x", "a", "fail")]), KG, 0, NOW))
    assert not any("cut at" in ln for ln in out), out


def t_text_shape_has_no_costume():
    out = "\n".join(h.compose(snap([pt("a.x", "a", "fail", since=iso(days=2))]), KG, 1, NOW))
    assert out.startswith(h.TAG)
    for bad in ("Policy:", "tell the user", "REPORT", "in your reply", "Detail:", "see "):
        assert bad not in out, bad


def _run_hook(outdir):
    env = dict(os.environ, SYSTEM_HMI_OUT=str(outdir))
    return subprocess.run([sys.executable, str(HOOK)], input="{}", capture_output=True,
                          text=True, encoding="utf-8", env=env, timeout=20)


def t_subprocess_corrupt_json_fails_open():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "snapshot.json").write_text("{not json", encoding="utf-8")
        proc = _run_hook(tmp)
        assert proc.returncode == 0 and "unavailable" in proc.stdout, (proc.returncode, proc.stdout)


def t_subprocess_real_shape_prints_block():
    with tempfile.TemporaryDirectory() as tmp:
        s = snap([pt("a.x", "a", "fail")])
        s["run"]["finished_at"] = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        (Path(tmp) / "snapshot.json").write_text(json.dumps(s), encoding="utf-8")
        proc = _run_hook(tmp)
        assert proc.returncode == 0 and "!! a: fail" in proc.stdout, proc.stdout


def t_reserved_slot_survives_older_alarms():
    # positive: 8 older fails + one fresh feedback-pool warn -> the pool row is among the 6 shown,
    # the total stays 6, and "...and 3 more" counts the displaced rows
    pts = [pt(f"s{i}.p", f"s{i}", "fail", since=iso(days=3)) for i in range(8)]
    pts.append(pt("feedback-pool.due", "feedback-pool", "warn", since=iso(hours=1)))
    out = h.compose(snap(pts), KG, 0, NOW)
    items = [ln for ln in out if ln.startswith("  !")]
    assert len(items) == 6 and any("feedback-pool: warn" in ln for ln in items), out
    assert any("and 3 more" in ln for ln in out), out
    # negative: the same fresh warn from a NON-reserved subsystem is displaced as before
    pts[-1] = pt("other.due", "other", "warn", since=iso(hours=1))
    out = h.compose(snap(pts), KG, 0, NOW)
    items = [ln for ln in out if ln.startswith("  !")]
    assert len(items) == 6 and not any("other: warn" in ln for ln in items), out
    # quiet: no pool alarm -> nothing reserved, no phantom line
    out = h.compose(snap([pt("a.x", "a", "fail")]), KG, 0, NOW)
    assert not any("feedback-pool" in ln for ln in out), out


CASES = [(n[2:], f) for n, f in sorted(globals().items()) if n.startswith("t_") and callable(f)]

if __name__ == "__main__":
    for name, fn in CASES:
        case(name, fn)
    for name, ok, detail in RESULTS:
        print(("PASS" if ok else "FAIL") + "  " + name + ("" if ok else f"  :: {detail}"))
    failed = [r for r in RESULTS if not r[1]]
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (" -- ALL PASS" if not failed else ""))
    sys.exit(1 if failed else 0)
