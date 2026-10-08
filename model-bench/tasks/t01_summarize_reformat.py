"""T01 — summarize / reformat into a fixed table. Dispatch row: 'Summarize / reformat' (cheap, low)."""
from _common import strip_fences, verdict

ID = "t01_summarize_reformat"
CATEGORY = "summarize-reformat"
DISPATCH_ROW = "Summarize / reformat / dictionary-style lookups"
EXPECTED_TIER = "cheap"
TOOLS = "none"
MAX_TURNS = 1
TIMEOUT_S = 240

NOTES = """\
Release notes, as dictated by the team lead (unedited)

So the 2.3.0 build went out on the fourteenth of March this year, 2026, and the big
thing there was the new export-to-CSV panel, a feature people had been asking for.
Before that, on 2026-02-02, we shipped 2.2.4 which was purely a fix for the crash
when the sidebar is collapsed. Then 2.2.5 followed quickly on Feb 19 2026, also a fix,
the one for timezone drift in reminders. Hmm, the one everyone remembers is 3.0.0 on
2026-05-01 — breaking: we dropped the v1 sync protocol, so old clients cannot connect.
2.3.1 came out 2026-03-28 as a fix for the CSV export writing BOMs. In between, on
April 10th 2026, we did 2.4.0, a feature: dark mode for the mobile shell. After the big
release, 3.0.1 (2026-05-09) fixed the migration script hang. And lastly 3.1.0 on the
third of June, 2026, added a feature, keyboard shortcuts for the editor.
"""

PROMPT = f"""Below are release notes dictated as prose. Produce ONLY a GitHub-flavoured
markdown table with exactly these columns, in this order: Version | Date | Type | Summary.
- Date in YYYY-MM-DD.
- Type is exactly one of: feature, fix, breaking.
- One row per release, sorted by Date ascending.
- No text before or after the table. No code fences.

<notes>
{NOTES}</notes>
"""

GOLD = [  # (version, date, type)
    ("2.2.4", "2026-02-02", "fix"),
    ("2.2.5", "2026-02-19", "fix"),
    ("2.3.0", "2026-03-14", "feature"),
    ("2.3.1", "2026-03-28", "fix"),
    ("2.4.0", "2026-04-10", "feature"),
    ("3.0.0", "2026-05-01", "breaking"),
    ("3.0.1", "2026-05-09", "fix"),
    ("3.1.0", "2026-06-03", "feature"),
]


def setup(workdir):  # nothing on disk — the task is inline
    pass


def _rows(text):
    rows = []
    for line in strip_fences(text).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or set(cells[0]) <= set("-: "):
            continue
        if cells[0].lower() == "version":
            continue
        rows.append(cells)
    return rows


def check(result, workdir):
    text = result.strip()
    non_table = [l for l in text.splitlines() if l.strip() and not l.strip().startswith("|")]
    if non_table:
        return verdict(False, f"text outside the table: {non_table[0][:60]!r}")
    rows = _rows(text)
    if len(rows) != len(GOLD):
        return verdict(False, f"expected {len(GOLD)} rows, got {len(rows)}")
    got = [(r[0].strip("`* "), r[1], r[2].lower()) for r in rows if len(r) >= 4]
    if len(got) != len(GOLD):
        return verdict(False, "a row has fewer than 4 cells")
    bad = [(g, e) for g, e in zip(got, GOLD) if g != e]
    if bad:
        return verdict(False, f"{len(bad)} row(s) differ, first: got {bad[0][0]} want {bad[0][1]}",
                       score=1 - len(bad) / len(GOLD))
    return verdict(True, "8/8 rows match (version, date, type) in order")


def _table(rows):
    out = ["| Version | Date | Type | Summary |", "|---|---|---|---|"]
    out += [f"| {v} | {d} | {t} | something |" for v, d, t in rows]
    return "\n".join(out)


CONTROLS = [
    {"result": _table(GOLD), "expect": True},
    {"result": "Here is the table:\n" + _table(GOLD), "expect": False},  # prose leak
    {"result": _table(GOLD[1:] + GOLD[:1]), "expect": False},  # wrong order
    {"result": _table([(v, d, "fix" if t == "feature" else t) for v, d, t in GOLD]), "expect": False},
]
