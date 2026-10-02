r"""SessionStart: inject a compressed project-registry gist (cross-project awareness).

STATUS: LIVE since 2026-08-26 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).
Proof-of-life: `python hooks/tests/test_project_registry_gist.py` -- the parser
cases below plus L-1/L-2, which parse the LIVE registry and then a mutated copy
of it, executed by integrity-sweep check 31. This hook prints or stays silent
and fails open either way: a parser that stopped matching is indistinguishable
from a quiet registry until something runs the suite (AP-63).
Live-reads: `references/PROJECTS.md` (golive_check runs the suite when it is edited)

User ruling 2026-08-26 (retrieval pain point 1): "related prior art exists"
must be mechanical, not a recall bet. At project granularity the registry is
small enough to ENUMERATE into every session's context; semantic matching
(a zh request against an en project name) is then the model's native job —
no keyword matcher, no embeddings. Finer granularity stays on-demand
(gsnap query / vault indexes / session-find); this gist is the map that
makes the model reach for those.

Source: references/PROJECTS.md, the registry of record (columns
|project|status|path|last-checkpoint|next|predecessor|). The parser truncates, never
guesses: status is cut at the first "(" or em-dash (drops the
ops-relaxation boilerplate), the checkpoint cell keeps its leading date.

ANCHORED ON THE DECLARED HEADER (2026-09-09). Until then any five-cell row
parsed, so a registry whose COLUMNS WERE RENAMED still produced a full gist —
the foreign header included, shipped as a project line. That input belonged to
neither declared class, and with no third class to put it in it folded into
`row`; five plausible lines read exactly like five real ones, which is why the
review-when above could sit here and catch nothing. Rows are now read only after
a header matching DECLARED, and `layout_note()` reports the drift instead: a
table with some other header withholds the gist and SAYS so, because a silent
non-injection is the same failure as a silently wrong one.
review-when: that column layout changes — and it now fails loudly when it does,
which is the whole point; DECLARED and the suite's fixtures move together.

Cost: one line per project (~16 now), ~350 tokens per session start.
Caps below keep a runaway registry from flooding context.
Fail-open, silent: any error exits 0 with no output.
"""
import sys
from pathlib import Path

REG = Path.home() / ".claude" / "references" / "PROJECTS.md"

STATUS_MAX = 48        # status cell after boilerplate cut
LINE_MAX = 120         # one gist row
TOTAL_MAX = 4000       # whole injection, chars


DECLARED = ("project", "status", "path", "last-checkpoint", "next", "predecessor")
# predecessor (2026-09-19, L-039): the gist prints it BESIDE the status, before the
# path, so LINE_MAX truncation can never cut it -- it is the one field that makes a
# new root read as "deliverable N of a series" at session start. A registry that
# drops the column is a renamed layout and is withheld, like any other.


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.split("|")]


def _is_declared_header(cells: list[str]) -> bool:
    n = len(DECLARED)
    return len(cells) >= n + 2 and tuple(c.lower() for c in cells[1:n + 1]) == DECLARED


def _is_separator(cells: list[str]) -> bool:
    return set("".join(cells)) <= {"-", ":", " "}


def layout_note(text: str) -> str:
    """"" when the table is anchored by the declared header; else what it says.

    The parser's declared classes are `project row` and `ignored line`, and a
    table whose COLUMNS WERE RENAMED is neither: nothing in it is a project row,
    and there was no third class to put it in, so it folded into `row` and the
    foreign header shipped as a gist line. Silent, because five plausible lines
    are indistinguishable from five real ones. This is the third class.
    """
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) < 7 or _is_separator(cells):
            continue
        if _is_declared_header(cells):
            return ""
        return " | ".join(cells[1:len(DECLARED) + 1])[:LINE_MAX]
    return ""              # no table at all: the quiet-registry case, not this one


def gist_rows(text: str) -> list[str]:
    """Pure (L-031): registry markdown in, gist lines out.

    Rows are read only AFTER the declared header. An unanchored row is not a
    project row this parser can vouch for -- it is five cells in some order.
    """
    rows = []
    anchored = False
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) < 7:                       # |a|b|c|d|e| -> 7 pieces
            continue
        if _is_declared_header(cells):
            anchored = True
            continue
        if not anchored:
            continue
        name = cells[1]
        if not name or name == "project" or set(name) <= {"-", ":", " "}:
            continue
        status, path, checkpoint = cells[2], cells[3], cells[4]
        for cut in ("(", "—"):              # "(" and em-dash
            idx = status.find(cut)
            if idx > 0:
                status = status[:idx]
        status = " ".join(status.split())[:STATUS_MAX].strip()
        checkpoint = checkpoint.split()[0] if checkpoint.split() else "-"
        pred = cells[6] if len(cells) >= 8 else ""    # |a|b|c|d|e|f| -> 8 pieces
        lineage = f" (continues {pred})" if pred and pred != "-" else ""
        rows.append(f"- {name} [{status}]{lineage} {path}  (ckpt {checkpoint})"[:LINE_MAX])
    return rows


def fit(head: str, rows: list[str]) -> str:
    """Join head + rows within TOTAL_MAX without dropping a project NAME.

    A plain [:TOTAL_MAX] cut silently hid every row past ~4000 chars (2026-09-27:
    66 rows, the last ~25 never reached a session -- a prior-art check cannot
    find a project it was never shown). Rows that do not fit collapse into one
    names-only tail line; if even the names overflow, the tail says how many
    names it could not show."""
    full = "\n".join([head] + rows)
    if len(full) <= TOTAL_MAX:
        return full
    names = [r[2:].split(" [", 1)[0] for r in rows]
    for keep in range(len(rows), -1, -1):
        rest = names[keep:]
        tail = (f"- (+{len(rest)} more, names only; full rows in references/PROJECTS.md): "
                + ", ".join(rest))
        text = "\n".join([head] + rows[:keep] + [tail])
        if len(text) <= TOTAL_MAX:
            return text
    # names alone overflow: show as many as fit and count the rest
    shown, tail = [], ""
    for i, n in enumerate(names):
        cand = f"- ({len(names)} projects, names only; full rows in references/PROJECTS.md): " \
               + ", ".join(shown + [n]) + f" (+{len(names) - i - 1} not shown)"
        if len(head) + 1 + len(cand) > TOTAL_MAX:
            break
        shown.append(n)
        tail = cand
    return "\n".join([head, tail]) if tail else head[:TOTAL_MAX]


def main() -> None:
    try:
        text = REG.read_text(encoding="utf-8", errors="replace")
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        drift = layout_note(text)
        if drift:
            print("[project-registry] NOT injected: the first table in "
                  "references/PROJECTS.md heads its columns `" + drift + "` "
                  "where this parser reads `" + " | ".join(DECLARED) + "`. Five "
                  "cells in an unknown order are not a project registry, and the "
                  "gist is what every session's prior-art check leans on, so it "
                  "is withheld instead of filled with them. Restore the declared "
                  "header, or change DECLARED in hooks/project_registry_gist.py "
                  "and hooks/tests/test_project_registry_gist.py together.")
            return
        rows = gist_rows(text)
        if not rows:
            return
        head = ("[project-registry] Known projects, compressed (full rows: "
                "references/PROJECTS.md). Prior-art check before building "
                "anything new, and when the user refers to past work "
                "(global CLAUDE.md rule). A row marked (continues X) takes X's "
                "deliverables, conventions and review records as mandatory "
                "inputs for its own deliverables:")
        print(fit(head, rows))
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
