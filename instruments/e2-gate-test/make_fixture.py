#!/usr/bin/env python3
r"""Build a disposable sandbox for exercising the E2 delivery gate (T-009).

The shadow gate can only be trusted once it has seen a REAL SubagentStop event
-- synthetic stdin payloads prove the classifier, not the payload shape
(ops/lessons.md L-012). This script builds a throwaway project so real
subagents can be pointed at something deterministic instead of at a live repo.

    python make_fixture.py            # build (idempotent: wipes and rebuilds)
    python make_fixture.py --path .\somewhere\else
    python make_fixture.py --prompts  # just print the three agent prompts

Verification command used by the fixture is `python -m unittest` -- chosen
because pytest is NOT installed on this machine (checked 2026-08-11), and a
gate test whose verify step cannot run proves nothing.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Inside the session's working tree on purpose: a subagent inherits cwd-scoped
# file permissions, so a fixture under %TEMP% gets its edits refused and the
# test measures the permission layer instead of the gate. drafts/ is gitignored.
DEFAULT = Path.home() / ".claude" / "drafts" / "e2-gate-fixture"

CALC = '''"""Toy module for the delivery-gate fixture. Not real code."""


def add(a, b):
    return a + b


def scale(value, factor):
    return value * factor
'''

TEST = '''import unittest

from calc import add, scale


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_scale(self):
        self.assertEqual(scale(3, 4), 12)


if __name__ == "__main__":
    unittest.main()
'''

PROMPTS = [
    (
        "A / read-only",
        "wrote=False, verified=False, would_block=False",
        "Read every .py file in {path} and reply with a one-line summary of what "
        "each function does. Do not modify any file and do not run any command.",
    ),
    (
        "B / write + verify",
        "wrote=True, verified=True, would_block=False",
        "In {path}: add a function `subtract(a, b)` to calc.py and a matching test "
        "to test_calc.py. Then run `python -m unittest discover -s . -v` in that "
        "directory and paste the last 3 lines of output. Reply with DONE plus that "
        "output.",
    ),
    (
        "C / write, no verify",
        "wrote=True, verified=False, would_block=True",
        "In {path}: add a module-level docstring line to calc.py describing the "
        "module. Do NOT run any test, linter, or other command -- editing only. "
        "Reply with DONE.",
    ),
]


def build(path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    (path / "calc.py").write_text(CALC, encoding="utf-8")
    (path / "test_calc.py").write_text(TEST, encoding="utf-8")
    return path


def show_prompts(path):
    print(f"\nFixture: {path}\n")
    print("Dispatch these three subagents (model: haiku -- cost cap, "
          "ops/environment.md), then run check_shadow_log.py:\n")
    for label, expected, prompt in PROMPTS:
        print(f"--- {label}   EXPECT {expected}")
        print(prompt.format(path=path))
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(DEFAULT))
    ap.add_argument("--prompts", action="store_true",
                    help="print the agent prompts without rebuilding")
    args = ap.parse_args()
    path = Path(args.path)

    if not args.prompts:
        build(path)
        print(f"built fixture at {path}")
    show_prompts(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
