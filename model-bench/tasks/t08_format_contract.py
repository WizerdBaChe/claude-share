"""T08 — many simultaneous output constraints, all machine-checked. Dispatch row: format-contract compliance (cheap, low)."""
import re
from _common import strip_fences, verdict

ID = "t08_format_contract"
CATEGORY = "instruction-following"
DISPATCH_ROW = "Explicit output-format contract (the cheap-tier substitute for tier quality)"
EXPECTED_TIER = "cheap"
TOOLS = "none"
MAX_TURNS = 1
TIMEOUT_S = 240

PROMPT = """Write a launch announcement for a fictional note-taking app called Quill.
Hard constraints — every one is checked by a program:
1. Exactly 7 lines, each a bullet starting with "- " followed by a capitalised English verb.
2. Each line is at most 72 characters long.
3. No commas anywhere in the output.
4. Exactly one line contains the word "offline" (any case).
5. The token QL-2026 appears exactly once in the whole output.
6. The last line ends with an exclamation mark; no other line ends with one.
7. Nothing before the first bullet and nothing after the last; no blank lines; no code fences."""


def check(result, workdir):
    text = strip_fences(result)
    lines = text.split("\n")
    probs = []
    if len(lines) != 7:
        probs.append(f"{len(lines)} lines")
    if any(not l.strip() for l in lines):
        probs.append("blank line")
    for i, l in enumerate(lines):
        if not re.match(r"^- [A-Z][a-z]+", l):
            probs.append(f"line {i + 1} does not start with '- Verb'"); break
    if any(len(l) > 72 for l in lines):
        probs.append("line > 72 chars")
    if "," in text:
        probs.append("comma present")
    if sum(1 for l in lines if re.search(r"(?i)\boffline\b", l)) != 1:
        probs.append("'offline' line count != 1")
    if text.count("QL-2026") != 1:
        probs.append("QL-2026 count != 1")
    if not lines[-1].rstrip().endswith("!"):
        probs.append("last line lacks '!'")
    if any(l.rstrip().endswith("!") for l in lines[:-1]):
        probs.append("'!' on a non-final line")
    if probs:
        return verdict(False, "; ".join(probs), score=max(0.0, 1 - len(probs) / 7))
    return verdict(True, "all 7 constraints hold")


def setup(workdir):
    pass


_GOOD = """- Meet Quill and write without friction on every device you own
- Capture ideas in plain text that stays yours forever
- Work offline on a train and sync the moment you reconnect
- Search thousands of notes in under a second
- Link notes together and watch your thinking take shape
- Join the launch with code QL-2026 for a year of Quill Pro
- Start writing today and never lose a thought again!"""
CONTROLS = [
    {"result": _GOOD, "expect": True},
    {"result": _GOOD.replace("Meet Quill and", "Meet Quill, and"), "expect": False},
    {"result": _GOOD.replace("Search thousands", "Search offline thousands"), "expect": False},
    {"result": _GOOD + "\n- Enjoy!", "expect": False},
    {"result": "Here you go:\n" + _GOOD, "expect": False},
]
