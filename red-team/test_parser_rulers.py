#!/usr/bin/env python3
"""Where exactly does the greedy regex fail? Constructed cases, no API calls.

R509 handed over their parse rule verbatim:

    jm = re.search(r"\\{.*\\}|\\[.*\\]", body_out, re.S)
    json.loads(jm.group())

"Greedy is bad" is not an actionable answer. The useful answer is the BOUNDARY:
which shapes it reads correctly and which it cannot, so they can tell whether
their C-11 failures fall inside it. Their raw responses were not kept, so this is
the only way left to narrow that diagnosis.

The result below is not what either side assumed. A payload that CONTAINS braces
inside its string values is fine -- the last `}` is still the payload's own. What
defeats the rule is braces OUTSIDE the payload: prose, a second JSON block, or a
trailing note. That distinction matters to them, because their quote-field
hypothesis and this rule are different suspects.

Run:  python test_parser_rulers.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import the SHARED implementation, not a wrapper. Before jsonspan existed this
# file imported peer_experiments' private copy while acceptance layer 5 ran a
# different one -- the test covered code the gate did not use.
from jsonspan import balanced_candidates as _balanced_candidates  # noqa: E402

PEER = re.compile(r"\{.*\}|\[.*\]", re.S)

CASES = [
    ("clean object", '{"ok": true, "n": 2}', True,
     "baseline -- both rulers must read this"),

    ("clean array", '[{"id": 1}, {"id": 2}]', True,
     "baseline"),

    ("braces INSIDE a string value",
     r'{"quote": "^\\{\"id\":\\s*(\\d+)\\}$", "verdict": "match"}', True,
     "R509's quote-field hypothesis, isolated: the last } is still the payload's "
     "own, so greedy capture lands correctly. NOT the failure they are looking for"),

    ("newline + escaped quotes inside a string value",
     '{"quote": "he said \\"ok\\"\\nthen left", "id": 3}', True,
     "the other half of the quote-field hypothesis, also survives"),

    ("prose before an array, prose contains a brace",
     'Using {curly} notation:\n[{"id": 1}, {"id": 2}]', False,
     "search hits the prose brace first, prefers the {...} branch, and runs to the "
     "LAST } -- the enclosing [ ] are lost before json.loads ever runs"),

    ("two JSON blocks, verdict last",
     '{"draft": 1}\n\nOn reflection:\n{"answer": 2}', False,
     "first { to last } swallows both blocks and the prose between them"),

    ("JSON then a trailing note containing a brace",
     '{"ok": true}\n\nNote: use {n} as the count placeholder.', False,
     "the payload is first and perfect; a single brace afterwards destroys it"),

    ("fenced block then a trailing note",
     '```json\n{"ok": true}\n```\n\nLet me know if {x} should differ.', False,
     "the model did everything the instruction asked -- fenced, single block -- "
     "and still fails"),
]


def read_peer(text: str) -> tuple[bool, str]:
    match = PEER.search(text)
    if not match:
        return False, "no {...} or [...] span found"
    try:
        json.loads(match.group())
    except json.JSONDecodeError as exc:
        return False, str(exc)[:70]
    return True, "parsed"


def read_ours(text: str) -> tuple[bool, str]:
    for candidate in _balanced_candidates(text):
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return True, f"parsed candidate of {len(candidate)} chars"
    return False, "no candidate parsed"


def main() -> int:
    print("=== greedy regex vs balanced scan ===\n")
    print(f"{'case':<44} {'greedy':>7} {'balanced':>9}   note")
    disagreements = 0
    wrong = 0
    for name, text, peer_should_pass, why in CASES:
        peer_ok, peer_why = read_peer(text)
        ours_ok, _ = read_ours(text)
        if peer_ok != peer_should_pass:
            wrong += 1
        if peer_ok != ours_ok:
            disagreements += 1
        print(f"{name:<44} {str(peer_ok):>7} {str(ours_ok):>9}   {why}")
        if not peer_ok:
            print(f"{'':<44} {'':>7} {'':>9}   greedy failed with: {peer_why}")

    print(f"\ndisagreements: {disagreements}/{len(CASES)} — in every one the "
          f"balanced scan reads it and the greedy rule does not.")
    print("boundary: the greedy rule is CORRECT whenever the payload is the only "
          "brace-bearing\nspan in the reply, INCLUDING when its own string values "
          "contain braces, quotes and\nnewlines. It fails when anything outside the "
          "payload carries a brace.")
    if wrong:
        print(f"\nWARNING: {wrong} case(s) did not behave as this file predicts; "
              "the boundary claim above is stale.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
