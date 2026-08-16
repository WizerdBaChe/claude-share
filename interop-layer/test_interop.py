#!/usr/bin/env python3
"""test_interop.py — self-test for interop.py's own mechanics.

Born 2026-08-16 from verified review findings
(outputs/experiments/2026-08-16-q2-schema-order/): the compiler had no test
for BLOCK_RE or the leak gate, while the very content it ships demands
two-sided gate calibration (known-TRUE and known-FALSE inputs).

Run:  python interop/test_interop.py     exit 0 = all pass
No third-party dependencies. Every secret-shaped string below is FAKE.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import interop

PASS, FAIL = [], []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ok   {name}")
    except AssertionError as e:
        FAIL.append(name)
        print(f"  FAIL {name}: {e}")
    except SystemExit as e:
        FAIL.append(name)
        print(f"  FAIL {name}: unexpected SystemExit: {e}")


def expect_exit(text, needle):
    try:
        interop.parse_blocks(text)
    except SystemExit as e:
        assert needle in str(e), f"exit message {e!r} lacks {needle!r}"
        return
    raise AssertionError(f"expected SystemExit containing {needle!r}, none raised")


BLOCK = "<!-- block:a profiles:light,full -->\nbody A\n<!-- /block -->\n"


# --- parser: positive controls -----------------------------------------------
def t_good():
    b = interop.parse_blocks(BLOCK)
    assert [x["id"] for x in b] == ["a"], b
    assert b[0]["profiles"] == ["light", "full"], b[0]


def t_space_after_colon():
    # the exact shape that used to be dropped SILENTLY (verified 2026-08-16)
    b = interop.parse_blocks(
        "<!-- block:a profiles: light,full -->\nX\n<!-- /block -->\n")
    assert b[0]["profiles"] == ["light", "full"], b[0]


def t_space_after_comma():
    b = interop.parse_blocks(
        "<!-- block:a profiles:light, full -->\nX\n<!-- /block -->\n")
    assert b[0]["profiles"] == ["light", "full"], b[0]


def t_crlf():
    b = interop.parse_blocks(
        "<!-- block:a profiles:full -->\r\nX\r\n<!-- /block -->\r\n")
    assert b[0]["id"] == "a" and b[0]["body"] == "X", b[0]


def t_doc_example_inert():
    # the header's placeholder example must neither parse nor trip the guard
    b = interop.parse_blocks(
        "<!-- block:<id> profiles:<p1>,<p2> -->\n...markdown content...\n"
        "<!-- /block -->\n" + BLOCK)
    assert [x["id"] for x in b] == ["a"], b


def t_live_file():
    b = interop.parse_blocks()
    assert len(b) >= 16, f"live portable-core.md parsed only {len(b)} blocks"


# --- parser: negative controls (must fail LOUDLY, never drop silently) -------
def t_missing_close():
    expect_exit(BLOCK + "<!-- block:b profiles:full -->\nno close\n",
                "NOT parsed")


def t_bad_profile_word():
    expect_exit("<!-- block:a profiles:Full -->\nX\n<!-- /block -->\n",
                "unknown profile")


def t_trailing_comma():
    expect_exit("<!-- block:a profiles:light,full, -->\nX\n<!-- /block -->\n",
                "unknown profile")


def t_light_without_full():
    expect_exit("<!-- block:a profiles:light -->\nX\n<!-- /block -->\n",
                "subset")


def t_duplicate_id():
    expect_exit(BLOCK + BLOCK.replace("body A", "body A2"), "duplicate")


# --- leak gate: two-sided calibration ----------------------------------------
KNOWN_TRUE = [
    ("sk- key",          "sk-FAKEFAKEFAKEFAKEFAKE123"),
    ("sk_live_ key",     "sk_live_FAKEFAKEFAKE123"),
    ("AIza key",         "AIza" + "A" * 35),
    ("ghp_ token",       "ghp_" + "A" * 20),
    ("AKIA id",          "AKIAABCDEFGHIJKL"),
    ("xoxb token",       "xoxb-abc123def456"),
    ("JWT",              "eyJ" + "a" * 15 + "." + "b" * 15),
    ("email",            "someone@example.com"),
    ("32-hex",           "a" * 32),
    ("secret assignment", 'api_key = "ABCDEFGHIJKLMNOP1234"'),
    ("windows path",     "C:\\Users\\" + interop._USER + "\\x"),
    ("git-bash path",    "/c/Users/" + interop._USER + "/x"),
    ("wsl path",         "/mnt/c/Users/" + interop._USER + "/x"),
    ("macos path",       "/Users/" + interop._USER + "/x"),
    ("linux home path",  "/home/" + interop._USER + "/x"),
]

KNOWN_FALSE = [
    ("prose about keys", "rotate your API keys regularly"),
    ("git short hash",   "source: 79e3517"),
    ("masked password",  "password: ****"),
    ("short hex",        "deadbeef"),
    ("profile words",    "the profiles light and full"),
]


def t_leak_known_true():
    misses = []
    for name, sample in KNOWN_TRUE:
        hits = interop.scan_text(sample, "calibration")
        if hits:
            print(f"         caught [{name}] by ruler [{hits[0][1]}]")
        else:
            misses.append(name)
    assert not misses, f"known-TRUE samples NOT caught: {misses}"


def t_leak_known_false():
    false_pos = []
    for name, sample in KNOWN_FALSE:
        hits = interop.scan_text(sample, "calibration")
        if hits:
            false_pos.append((name, hits[0][1]))
    assert not false_pos, f"known-FALSE samples tripped the gate: {false_pos}"


def t_truncation_boundary():
    # SHARE-REPO EDIT: tools/sharelib.py truncates at a different width and
    # returns 4-tuples (label, kind, line_no, sample), where the source's
    # inline gate returned 3. Same property under test — a match at the
    # boundary must not be printed whole — restated against this gate's
    # contract. Do not back-flow: the source has no sharelib.py.
    m25 = "a" * 11 + "@" + "b" * 10 + ".cd"        # 25 chars: printed whole
    assert len(m25) == 25, len(m25)
    hits = interop.scan_text(m25, "calibration")
    assert hits and hits[0][3] == m25, hits
    m26 = "a" * 12 + "@" + "b" * 10 + ".cd"        # 26 chars: must truncate
    assert len(m26) == 26, len(m26)
    hits = interop.scan_text(m26, "calibration")
    assert hits and hits[0][3] == m26[:24] + "…", hits


if __name__ == "__main__":
    for fn in [t_good, t_space_after_colon, t_space_after_comma, t_crlf,
               t_doc_example_inert, t_live_file, t_missing_close,
               t_bad_profile_word, t_trailing_comma, t_light_without_full,
               t_duplicate_id, t_leak_known_true, t_leak_known_false,
               t_truncation_boundary]:
        check(fn.__name__, fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    sys.exit(1 if FAIL else 0)
