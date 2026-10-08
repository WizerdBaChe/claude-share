"""T05 — write a small to-spec CLI script; hidden tests gate. Dispatch row: 'Write a script/module' (mid)."""
import subprocess
import sys
from _common import verdict, write

ID = "t05_write_script"
CATEGORY = "write-script"
DISPATCH_ROW = "Write a script/module"
EXPECTED_TIER = "mid"
TOOLS = "default"
MAX_TURNS = 30
TIMEOUT_S = 900

PROMPT = """Create `dedupe.py` in the current directory (Python 3, standard library only) with this contract:

    python dedupe.py INPUT.csv            # writes the deduplicated CSV to stdout
    python dedupe.py INPUT.csv --dry-run  # prints ONLY the number of rows that would be removed

Rules:
1. Rows are duplicates when their `customer_id` matches after trimming whitespace and
   ignoring case (so " ab-12 " and "AB-12" are the same customer).
2. Among duplicates keep the row with the LATEST `updated` value (ISO date YYYY-MM-DD).
   If two share the same latest date, keep the one that appears LAST in the input.
3. Output keeps the original header and column order; rows are sorted by the normalized
   customer_id (trimmed, upper-cased) ascending; the kept row's cells are written unchanged
   (do not normalize the stored customer_id).
4. Exit code 0 on success; exit code 2 with a message on stderr if the header lacks
   `customer_id` or `updated`.
5. Use `csv` module quoting defaults; write `\\n` line endings.

An example input `sample.csv` is in the directory. Do not print anything else to stdout."""

SAMPLE = """customer_id,name,updated,plan
ab-12,Ann,2026-01-05,free
 AB-12 ,Ann B,2026-03-01,pro
cd-77,Carl,2026-02-10,free
ef-01,Eve,2026-02-10,team
CD-77,Carl D,2026-02-10,pro
"""
SAMPLE_OUT = """customer_id,name,updated,plan
 AB-12 ,Ann B,2026-03-01,pro
CD-77,Carl D,2026-02-10,pro
ef-01,Eve,2026-02-10,team
"""
IN2 = """plan,customer_id,updated
a,x-1,2025-12-31
b,X-1,2026-01-01
c,y-2,2026-01-01
"""
OUT2 = """plan,customer_id,updated
b,X-1,2026-01-01
c,y-2,2026-01-01
"""
IN3 = """customer_id,name
q,1
"""


def setup(workdir):
    write(workdir, "sample.csv", SAMPLE)


def _run(workdir, *args):
    return subprocess.run([sys.executable, "-I", "dedupe.py", *args], cwd=workdir,
                          capture_output=True, text=True, timeout=30)


def check(result, workdir):
    if not (workdir / "dedupe.py").exists():
        return verdict(False, "dedupe.py not written")
    write(workdir, "in2.csv", IN2)
    write(workdir, "in3.csv", IN3)
    tests = []
    r = _run(workdir, "sample.csv"); tests.append(("sample", r.returncode == 0 and r.stdout.replace("\r\n", "\n") == SAMPLE_OUT))
    r = _run(workdir, "sample.csv", "--dry-run"); tests.append(("dry-run", r.returncode == 0 and r.stdout.strip() == "2"))
    r = _run(workdir, "in2.csv"); tests.append(("column-order+tie", r.returncode == 0 and r.stdout.replace("\r\n", "\n") == OUT2))
    r = _run(workdir, "in3.csv"); tests.append(("bad-header exit 2", r.returncode == 2 and r.stderr.strip() != "" and r.stdout == ""))
    failed = [n for n, ok in tests if not ok]
    if failed:
        return verdict(False, f"{len(tests) - len(failed)}/{len(tests)} hidden tests pass; failed: {failed}",
                       score=(len(tests) - len(failed)) / len(tests))
    return verdict(True, f"{len(tests)}/{len(tests)} hidden tests pass")


_REF = r'''import csv, sys
def main():
    a = sys.argv[1:]
    dry = "--dry-run" in a
    path = [x for x in a if not x.startswith("--")][0]
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f)); hdr = f.seek(0) or csv.reader(open(path, newline="", encoding="utf-8")).__next__()
    if "customer_id" not in hdr or "updated" not in hdr:
        sys.stderr.write("missing columns\n"); sys.exit(2)
    best = {}
    for r in rows:
        k = r["customer_id"].strip().upper()
        if k not in best or r["updated"] >= best[k]["updated"]:
            best[k] = r
    if dry:
        print(len(rows) - len(best)); return
    w = csv.DictWriter(sys.stdout, fieldnames=hdr, lineterminator="\n")
    w.writeheader()
    for k in sorted(best):
        w.writerow(best[k])
main()
'''
_BROKEN = _REF.replace('r["updated"] >= best[k]["updated"]', 'r["updated"] > best[k]["updated"]')  # tie rule wrong


def _plant(src):
    return lambda wd: write(wd, "dedupe.py", src)


CONTROLS = [
    {"result": "done", "mutate": _plant(_REF), "expect": True},
    {"result": "done", "mutate": _plant(_BROKEN), "expect": False},
    {"result": "done", "expect": False},  # nothing written
]
