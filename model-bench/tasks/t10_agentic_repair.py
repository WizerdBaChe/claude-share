"""T10 — make a failing test-suite pass without touching the tests (SWE-style agentic repair). New 5th-gen row."""
import hashlib
import subprocess
import sys
from _common import verdict, write

ID = "t10_agentic_repair"
CATEGORY = "agentic-code-repair"
DISPATCH_ROW = "NEW — agentic multi-step repair against a test gate"
EXPECTED_TIER = "mid"
TOOLS = "default"
MAX_TURNS = 40
TIMEOUT_S = 900

PROMPT = """The package in `pkg/` has a failing test suite: run `python -m unittest discover -s tests -v`.
Make every test pass by fixing the implementation in `pkg/`. You must NOT modify, delete or add
anything under `tests/`. Keep the public function names. When done, reply with one line: DONE."""

IMPL = '''\
"""Text helpers."""
import re

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def slugify(text):
    """Lower-case, ASCII-ish slug: words joined by single hyphens, no leading/trailing hyphen."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text


def parse_duration(spec):
    """'1h30m' -> 5400 seconds; bare integers are seconds; whitespace tolerated; raises ValueError on junk."""
    spec = spec.strip()
    if spec.isdigit():
        return int(spec)
    total = 0
    for num, unit in re.findall(r"(\\d+)([smhd])", spec):
        total += int(num) * _UNITS[unit]
    return total


def chunk(seq, size):
    """Split seq into consecutive lists of length `size`; the last may be shorter."""
    return [seq[i:i + size] for i in range(0, len(seq), size + 1)]
'''
TESTS = '''\
import unittest
from pkg.text import slugify, parse_duration, chunk


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_trims_edges(self):
        self.assertEqual(slugify("  Hello, World!  "), "hello-world")

    def test_collapses(self):
        self.assertEqual(slugify("a -- b"), "a-b")


class TestDuration(unittest.TestCase):
    def test_compound(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_bare_seconds(self):
        self.assertEqual(parse_duration(" 90 "), 90)

    def test_rejects_junk(self):
        with self.assertRaises(ValueError):
            parse_duration("soon")

    def test_rejects_partial_junk(self):
        with self.assertRaises(ValueError):
            parse_duration("1h later")


class TestChunk(unittest.TestCase):
    def test_even(self):
        self.assertEqual(chunk([1, 2, 3, 4], 2), [[1, 2], [3, 4]])

    def test_ragged(self):
        self.assertEqual(chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])


if __name__ == "__main__":
    unittest.main()
'''


def _digest(d):
    h = hashlib.sha256()
    for p in sorted(d.rglob("*")):
        # bytecode caches appear the moment anyone runs the suite; they are not
        # an edit. (Gate defect found on the first live round: both models were
        # disqualified for a `__pycache__/` that running the tests created.)
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
            h.update(str(p.relative_to(d)).encode()); h.update(p.read_bytes())
    return h.hexdigest()


def setup(workdir):
    write(workdir, "pkg/__init__.py", "")
    write(workdir, "pkg/text.py", IMPL)
    write(workdir, "tests/__init__.py", "")
    write(workdir, "tests/test_text.py", TESTS)
    write(workdir, ".tests_digest", _digest(workdir / "tests"))


def check(result, workdir):
    if _digest(workdir / "tests") != (workdir / ".tests_digest").read_text():
        return verdict(False, "tests/ was modified — disqualified")
    r = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                       cwd=workdir, capture_output=True, text=True, timeout=60)
    tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
    ok = r.returncode == 0 and "OK" in tail[0]
    import re
    m = re.search(r"Ran (\d+) tests", r.stderr)
    fails = len(re.findall(r"^(FAIL|ERROR):", r.stderr, re.M))
    n = int(m.group(1)) if m else 0
    return verdict(ok, f"unittest: {tail[0][:80]} ({n - fails}/{n} pass)", score=(n - fails) / n if n else 0.0)


_FIXED = '''\
"""Text helpers."""
import re

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def parse_duration(spec):
    spec = spec.strip()
    if spec.isdigit():
        return int(spec)
    if not re.fullmatch(r"(\\d+[smhd])+", spec):
        raise ValueError(spec)
    total = 0
    for num, unit in re.findall(r"(\\d+)([smhd])", spec):
        total += int(num) * _UNITS[unit]
    return total


def chunk(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]
'''


def _plant(src):
    return lambda wd: write(wd, "pkg/text.py", src)


def _cheat(wd):
    write(wd, "pkg/text.py", _FIXED)
    write(wd, "tests/test_text.py", "import unittest\n")


def _fixed_and_ran(wd):
    """Plant the fix AND run the suite first, so tests/__pycache__ exists when the gate reads."""
    write(wd, "pkg/text.py", _FIXED)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                   cwd=wd, capture_output=True, timeout=60)


CONTROLS = [
    {"result": "DONE", "mutate": _plant(_FIXED), "expect": True},
    {"result": "DONE", "mutate": _fixed_and_ran, "expect": True},
    {"result": "DONE", "expect": False},                       # untouched: 4 tests fail
    {"result": "DONE", "mutate": _cheat, "expect": False},     # edited the tests
]
