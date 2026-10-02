#!/usr/bin/env python3
"""spannorm — the one place the span-matching normal form is defined.

WHY THIS FILE EXISTS. The same rule used to live twice: `citecheck.norm()` (regex over the
whole string) decided whether a support span is present in a source, and `fetchsrc.norm_with_map()`
(a hand-written char walk that also returns an index map) decided where to cut the excerpt that
citecheck would later read. Two implementations of one rule are one input with two outputs, and
they did diverge: measured 2026-09-12, 3171 of 4000 random strings folded differently, because one
NFKC-folded the whole string and the other folded character by character, so a decomposed accent
("u" + U+0308) stayed decomposed on one side and composed to "ü" on the other. In 247 of those the
divergence went further and changed a HYPHEN ruling, because the lookbehind then saw a combining
mark instead of a letter: `Fiévet-\\nstyle` folds to two different strings, one of which the gate
accepts and the other of which the cutter cannot locate. Neither fixture suite could see it.

So there is now ONE implementation. `norm_with_map()` carries the index map; `norm()` is its first
return value. Nothing else may define this rule.

THE NORMAL FORM (ruled 2026-09-12, SSLD T00; the reasoning belongs to the rule, not to a caller):
extracted PDF text cannot say whether the hyphen in "high-\\ndensity" was the author's or the
typesetter's, so no rule may rule on it. Every reading of a word folds to the SAME string, on both
sides of a comparison, and the fold never turns on where the line happened to break:
  1. NFKC per CLUSTER (a base character plus the combining marks that follow it), then the
     ligature/dash/quote table. Per cluster, not per character, because an index map has to point
     somewhere: a composition that spans two BASE characters (Hangul jamo) therefore does not
     compose. That is the one documented gap; this corpus is Latin-script scientific text.
     Measured 2026-09-12: conjoining U+1112 U+1161 U+11AB and precomposed U+D55C are the same
     word on screen and two different strings here. The direction is the safe one — a span typed
     in the other spelling reads as ABSENT, which the writer sees, never as present — and the
     gap is pinned in selfcheck() rather than described. review-when: a run whose sources are in
     a conjoining script (Hangul is the case that exists; anything whose composition spans two
     bases behaves the same). Closing it means giving the map somewhere to point, not widening
     the cluster.
  2. A line break inside a hyphenated word is layout: the break goes, the hyphen stays. The hyphen
     must JOIN two word characters — a lone "-" cell meaning "not reported" is data and survives.
  3. A hyphen between two LETTERS is orthography and goes ("high-density" == "high-\\ndensity" ==
     "highdensity"); a hyphen touching a DIGIT is content and stays (ranges "1550-1600",
     identifiers "SMF-28", the sign in "-1.50"). Rule 2 without rule 3 fused "1550-\\n1600".
  4. Whitespace runs collapse to one space; the result is stripped and casefolded.
Rules 2 and 3 compose into ONE ordered alternation (_RULES) so a single pass is exactly what
applying them in sequence used to produce — see selfcheck().

Deliberately NOT fuzzy: it undoes typography and line wrapping, never wording. "roughly 200" never
becomes "200", and 'um' vs 'µm' stays a difference (NFKC folds the micro sign to Greek mu, never
to "u").

review-when: a caller needs a fold this does not do — extend it HERE, never in the caller.
"""
from __future__ import annotations

import functools
import re
import unicodedata

# NFKC already folds ligatures, the non-breaking spaces and the micro sign; this table covers what
# it leaves alone (curly quotes, the dash family). Its ligature/space entries are no-ops kept for
# readability, not a second normalization rule.
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
             "ﬄ": "ffl", "’": "'", "‘": "'", "“": '"',
             "”": '"', "–": "-", "—": "-", "−": "-",
             " ": " ", " ": " ", " ": " "}

_LETTER = r"[^\W\d_]"       # a word character that is not a digit or underscore
# The two hyphen rules as one ordered alternation over the FOLDED text. Order is the rule:
# `join` (letter, break, letter) must be tried before `keep`, and both before the inline `orth`.
# `_EOL` is "whitespace up to and including the line break" — [^\S\n] is whitespace that is not a
# newline, so a CRLF source folds exactly like an LF one. Spelling it [ \t] instead silently stopped
# folding CRLF text, which is the file class L-089 is about; the acceptance differential caught it.
_EOL = r"[^\S\n]*\n\s*"
_RULES = re.compile(
    rf"(?P<join>(?<={_LETTER})-{_EOL}(?={_LETTER}))"        # break + hyphen both go
    rf"|(?P<keep>(?<=\w)-{_EOL}(?=\w))"                     # break goes, hyphen stays (digits)
    rf"|(?P<orth>(?<={_LETTER})-(?={_LETTER}))"             # inline letter-letter hyphen goes
    r"|(?P<ws>\s+)")                                        # whitespace run collapses


def _fold(text: str) -> tuple[str, list[int]]:
    """NFKC per cluster + the table above. Returns the folded text and one raw index per char."""
    out: list[str] = []
    idx: list[int] = []
    i, n = 0, len(text)
    while i < n:
        # A run of plain ASCII is NFKC-stable and folds to itself: take it whole, not per character.
        # It must not end on the base of the NEXT cluster, or that base never meets its combining
        # mark and "e" + U+0301 stays decomposed while the rest of the file composes — the very
        # split that made the two old implementations disagree (selfcheck catches this).
        m = _ASCII_RUN.match(text, i)
        if m:
            end = m.end()
            if end < n and unicodedata.combining(text[end]):
                end -= 1
            if end > i:
                out.append(text[i:end])
                idx.extend(range(i, end))
                i = end
                continue
        j = i + 1
        while j < n and unicodedata.combining(text[j]):
            j += 1
        piece = unicodedata.normalize("NFKC", text[i:j])
        piece = "".join(LIGATURES.get(c, c) for c in piece)
        out.append(piece)
        idx.extend([i] * len(piece))       # every char of a cluster points at the cluster's start
        i = j
    return "".join(out), idx


_ASCII_RUN = re.compile(r"[ -~]+")         # printable ASCII: no NFKC change, no combining marks


def norm_with_map(text: str) -> tuple[str, list[int]]:
    """The normal form, plus one index into the ORIGINAL string per character of the result.

    The map is what lets a caller cut a window out of the raw text around a span it located in the
    normalized text (fetchsrc's excerpt pass). idx[k] is the raw offset the k-th normalized
    character came from; characters that a fold expanded or merged all point at the source cluster.
    """
    if not text:
        return "", []
    folded, fmap = _fold(text)
    out: list[str] = []
    idx: list[int] = []
    pos = 0

    def emit(chunk: str, start: int) -> None:
        low = chunk.casefold()
        out.append(low)
        if len(low) == len(chunk):                      # the common case: index runs straight
            idx.extend(fmap[start:start + len(chunk)])
        else:                                           # a fold that changed length (e.g. ß -> ss)
            for k, ch in enumerate(chunk):
                idx.extend([fmap[start + k]] * len(ch.casefold()))

    for m in _RULES.finditer(folded):
        if m.start() > pos:
            emit(folded[pos:m.start()], pos)
        kind = m.lastgroup
        if kind == "keep":
            out.append("-")
            idx.append(fmap[m.start()])
        elif kind == "ws":
            if out:                                     # leading whitespace is dropped, not kept
                out.append(" ")
                idx.append(fmap[m.start()])
        # "join" and "orth" emit nothing: the hyphen (and the break with it) is gone
        pos = m.end()
    if pos < len(folded):
        emit(folded[pos:], pos)

    s = "".join(out)
    if s.endswith(" "):                                 # the trailing collapsed space, if any
        s = s[:-1]
    return s, idx[:len(s)]


@functools.lru_cache(maxsize=64)
def norm(text: str) -> str:
    """The normal form. Cached: a citecheck run normalizes the same handful of source texts once
    per ledger row, and the function is pure, so the cache is the same value, not a second one."""
    return norm_with_map(text)[0]


def norm_span(span: str) -> str:
    """Alias kept for readability at call sites that normalize a needle rather than a haystack."""
    return norm(span)


# --------------------------------------------------------------------------
# selfcheck — properties of the RULE, not of any caller. Both tools run this.
# --------------------------------------------------------------------------
def _sequential_reference(text: str) -> str:
    """The rules applied one after another, the way they were written before they were merged
    into _RULES. The single pass must equal this for every input, or the merge changed the rule."""
    if not text:
        return ""
    folded, _ = _fold(text)
    folded = re.sub(rf"(?<=\w)-{_EOL}(?=\w)", "-", folded)
    folded = re.sub(rf"(?<={_LETTER})-(?={_LETTER})", "", folded)
    return re.sub(r"\s+", " ", folded).strip().casefold()


def selfcheck(samples: int = 4000, seed: int = 20260912) -> list[str]:
    """Returns a list of failure descriptions; empty means the rule holds. Two-sided by
    construction: the canonical cases say what must fold together, the controls what must not."""
    import random

    fails: list[str] = []
    same = [("a high-\ndensity array", "a high-density array", "a highdensity array"),
            ("propa-\ngation length", "propagation length"),
            # a CRLF source must fold exactly like an LF one: writing the rule as [ \t]*\n once
            # stopped folding CRLF text entirely, and no fixture here could see it (2026-09-12)
            ("propa-\r\ngation length", "propa-\ngation length", "propagation length"),
            ("1550-\r\n1600 nm", "1550-1600 nm"),
            ("El-\nFiky et al.", "El-Fiky et al.", "ElFiky et al."),
            ("Fiévet-\nstyle", "Fiévet-style", "Fiévetstyle")]
    for group in same:
        got = {norm(s) for s in group}
        if len(got) != 1:
            fails.append(f"one word, {len(got)} outputs: {group!r} -> {got!r}")
    apart = [("1550-1600 nm", "15501600 nm"),      # a range is content, not orthography
             ("SMF-28 fiber", "SMF28 fiber"),      # so is an identifier
             ("a - - b", "a b"),                   # "not reported" cells are data
             ("200 um", "200 µm")]            # 'um' vs micro sign is wording
    for a, b in apart:
        if norm(a) == norm(b):
            fails.append(f"two different texts folded together: {a!r} == {b!r}")

    # The documented gap, pinned so it is refutable rather than folklore. Per-cluster NFKC cannot
    # compose Hangul jamo -- the composition spans two BASE characters and the index map would
    # have nowhere to point -- so the conjoining and precomposed spellings of one word stay two
    # strings. This is NOT a property the rule wants; it is the price of the map, recorded here so
    # that closing it is a deliberate edit with a new answer for the map, and so that nobody
    # rediscovers it from a failing run. See the review-when in the module docstring.
    jamo, precomposed = "한국", "한국"   # the same word
    if norm(jamo) == norm(precomposed):
        fails.append("the Hangul-jamo gap has closed -- intended or not, the module docstring's "
                     "review-when and this pin must now say what the index map points at")

    rng = random.Random(seed)
    alphabet = list("abzAZ019 ") + ["\n", "\r\n", "\t", "-", "–", "−", "µ",
                                    "μ", "ﬁ", " ", "’", "é", "ü",
                                    "́", "_", ".", "|", "(", ")"]
    bad_ref = bad_map = bad_idem = 0
    for _ in range(samples):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
        n1, idx = norm_with_map(s)
        if n1 != _sequential_reference(s):
            bad_ref += 1
        if len(idx) != len(n1) or any(not (0 <= k < max(len(s), 1)) for k in idx):
            bad_map += 1
        if norm(n1) != n1:
            bad_idem += 1
    if bad_ref:
        fails.append(f"{bad_ref}/{samples} random strings differ from the sequential reference")
    if bad_map:
        fails.append(f"{bad_map}/{samples} random strings returned a map that does not index the input")
    if bad_idem:
        fails.append(f"{bad_idem}/{samples} random strings are not idempotent (normalizing twice moved)")
    return fails


if __name__ == "__main__":
    import sys
    problems = selfcheck()
    for p in problems:
        print("BROKEN  ", p)
    print(f"spannorm selfcheck: {len(problems)} broken — "
          + ("the normal form holds" if not problems else "THE RULE IS NOT ONE RULE"))
    sys.exit(1 if problems else 0)
