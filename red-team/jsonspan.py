#!/usr/bin/env python3
"""One JSON-span extractor for the whole dispatch layer.

Extracted 2026-08-16 by the retrospective's sibling scan, which found the same
scanner written twice and a third copy that had never been fixed:

    redteam_verify._find_verdict_object   balanced, objects only   (layer 5)
    peer_experiments._balanced_candidates balanced, objects+arrays (experiments)
    score_redteam.extract_findings        find("[") .. rfind("]")  (layer 2)

The third one is the point. L-019 is about a greedy first-to-last slice reading
prose braces as structure, we had already fixed it twice, and it was still live
in the STRUCTURE layer — the first gate every dispatched report passes through.
Two independent fixes of one bug is how a third copy survives: each fix looks
complete from where it was made.

Worse, `test_parser_rulers.py` imported the experiments copy, so the tested
implementation was not the one in the acceptance path. A test that covers a
duplicate is a test that reports on code nobody runs.

Three properties, in order:

  1. a fenced ```json block wins when present — the one span the model
     explicitly delimited;
  2. otherwise scan for BALANCED spans tracking depth, so a brace in prose opens
     and closes its own candidate instead of swallowing the payload;
  3. try later candidates first. Models put the reasoning before the answer, so
     the last well-formed span is the payload far more often than the first.

Deliberately NOT string-aware (a brace inside a JSON string literal is not
structural). `json.loads` is the real validator and a bad candidate costs one
loop iteration; string-awareness here would be a second parser to keep correct.
"""

from __future__ import annotations

import json
import re
from typing import Any

FENCE = re.compile(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", re.S)


def balanced_candidates(text: str) -> list[str]:
    """Plausible JSON spans, best-first. Never raises."""
    fenced = FENCE.findall(text)
    scanned: list[str] = []
    for opener, closer in (("{", "}"), ("[", "]")):
        depth, start = 0, None
        for index, char in enumerate(text):
            if char == opener:
                if depth == 0:
                    start = index
                depth += 1
            elif char == closer and depth:
                depth -= 1
                if depth == 0 and start is not None:
                    scanned.append(text[start : index + 1])
    return fenced + list(reversed(scanned))


def first_parsable(text: str, want: Any = None) -> Any | None:
    """The best candidate that parses, optionally filtered by a predicate.

    `want` is a callable taking the parsed value and returning True when it is
    the object being looked for — a verdict object needs a `refuted` key, a
    findings report needs a list. Without it, the first parsable span wins.
    """
    for candidate in balanced_candidates(text):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if want is None or want(value):
            return value
    return None
