"""xi_cards — card parser + validators for cross-index (M0).

Pure functions with injected inputs (L-031): text in, verdict out; callers own
all IO. Implements the flat-subset grammar of `references/cross-index-psm.md`
SS3 and the card constraints of `references/cross-index-design.md` SS2.2.
ONE implementation, imported by BOTH the emit pipeline and the M3 hook —
the two must never drift.

Grammar (deliberately small — no PyYAML in this environment, and a parser
that guesses is worse than one that rejects: design INV-5 / BR-6):
    frontmatter = first line "---", lines until the next "---" line
    line        = key ": " value          (split on the FIRST ": ")
    value       = scalar (matching surrounding quotes stripped)
                | "[a, b, c]" flow list (no nesting, items free of , [ ])

Verdicts (never raises):
    {"kind": "none"}                              not a card (no frontmatter,
                                                  or frontmatter without `xi`
                                                  — ordinary files pass by)
    {"kind": "card", "card": ..., "unknown_keys": [...], "evidence_line": n}
    {"kind": "rejected", "reason": str, "line": n}   goes to the coverage
                                                  report's rejected bucket
"""
from __future__ import annotations

AUTHORED_KEYS = ("xi", "what", "tags", "aliases", "date", "status")
STATUS_ENUM = ("live", "spent", "draft")

# CJK Unified Ideographs + Extension A — the bilingual shape check
# (design SS2.2) is a codepoint test, mechanical by design (INV-8).
_CJK_RANGES = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF))


def _has_cjk(text: str) -> bool:
    return any(a <= ord(c) <= b for c in text for a, b in _CJK_RANGES)


def _has_latin(text: str) -> bool:
    return any(c.isascii() and c.isalpha() for c in text)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


def _parse_value(raw: str):
    """Scalar or flow list. Returns (value, error|None)."""
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return [], None
        items = []
        for part in inner.split(","):
            item = _unquote(part)
            if not item:
                return None, "empty-list-item"
            if "[" in item or "]" in item:
                return None, "nested-list"
            items.append(item)
        return items, None
    return _unquote(raw), None


def extract_card(text: str) -> dict:
    """Parse one file's text. See module docstring for the verdict shapes."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {"kind": "none"}
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break

    entries: dict[str, object] = {}
    errors: list[tuple[int, str]] = []   # (1-based line, reason)
    xi_line = None
    body = lines[1:close] if close else lines[1:]
    for offset, line in enumerate(body, start=2):
        if not line.strip():
            continue
        if ": " in line:
            key, _, raw = line.partition(": ")
        elif line.rstrip().endswith(":"):
            key, raw = line.rstrip()[:-1], ""
        else:
            errors.append((offset, "bad-line"))
            continue
        key = key.strip()
        value, err = _parse_value(raw)
        if err:
            errors.append((offset, err))
            continue
        if key == "xi" and xi_line is None:
            xi_line = offset
        entries.setdefault(key, value)

    if "xi" not in entries:
        return {"kind": "none"}          # ordinary frontmatter, not our card

    def rejected(reason: str, line: int | None = None) -> dict:
        return {"kind": "rejected", "reason": reason, "line": line or xi_line or 1}

    if close is None:
        return rejected("unterminated-frontmatter", 1)
    if errors:
        line, reason = errors[0]
        return rejected(reason, line)

    # ---- validators (PSM SS3) ------------------------------------------
    xi = entries["xi"]
    if not (isinstance(xi, str) and xi.isdigit() and int(xi) >= 1):
        return rejected("xi-not-positive-int")

    what = entries.get("what")
    if isinstance(what, list):
        return rejected("what-not-scalar")
    if not what:
        return rejected("missing-what")   # D-12: required keys are xi + what

    def as_list(key: str) -> list[str] | None:
        v = entries.get(key)
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]        # scalar coerced to singleton — unambiguous, not a guess

    tags, aliases = as_list("tags"), as_list("aliases")

    date = entries.get("date")
    if date is not None:
        d = date if isinstance(date, str) else ""
        parts = d.split("-")
        if not (len(d) == 10 and len(parts) == 3
                and all(p.isdigit() for p in parts)
                and (len(parts[0]), len(parts[1]), len(parts[2])) == (4, 2, 2)):
            return rejected("bad-date")

    status = entries.get("status")
    superseded_by = None
    if status is not None:
        s = status if isinstance(status, str) else ""
        if s.startswith("superseded"):
            _, _, successor = s.partition(":")
            successor = successor.strip()
            if not successor:
                return rejected("superseded-without-successor")
            superseded_by = successor
            status = "superseded"
        elif s not in STATUS_ENUM:
            return rejected("bad-status")

    combined = " ".join([str(what)] + tags + aliases)
    if not _has_cjk(combined):
        return rejected("bilingual-no-cjk")
    if not _has_latin(combined):
        return rejected("bilingual-no-latin")

    unknown = sorted(k for k in entries if k not in AUTHORED_KEYS)
    return {
        "kind": "card",
        "card": {
            "xi": int(xi), "what": str(what), "tags": tags, "aliases": aliases,
            "date": date, "status": status or "live",
            "superseded_by": superseded_by,
        },
        "unknown_keys": unknown,
        "evidence_line": xi_line,
    }
