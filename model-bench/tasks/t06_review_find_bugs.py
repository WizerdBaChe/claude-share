"""T06 — review a module, report planted bugs with verbatim anchors. Dispatch row: 'Red-team / review' (mid, high)."""
import json
from _common import parse_json, verdict, write

ID = "t06_review_find_bugs"
CATEGORY = "code-review"
DISPATCH_ROW = "Red-team / review (reviewer != author)"
EXPECTED_TIER = "mid"
TOOLS = "default"
MAX_TURNS = 12
TIMEOUT_S = 600

PROMPT = """Review `inventory.py` in the current directory for REAL defects (bugs that produce wrong
results or crashes on realistic input) — not style, not naming, not missing type hints.
Output ONLY a JSON array; each element: {"line": <int>, "quote": "<the exact source line, verbatim,
whitespace-trimmed>", "issue": "<one sentence>"}. Report at most 6 findings. If you find none,
output []. No prose, no code fences."""

SRC = '''\
"""Tiny inventory ledger used by the warehouse CLI."""
from dataclasses import dataclass


@dataclass
class Item:
    sku: str
    qty: int
    unit_cost: float


class Inventory:
    def __init__(self):
        self.items = {}

    def add(self, sku, qty, unit_cost):
        if sku in self.items:
            self.items[sku].qty += qty
        else:
            self.items[sku] = Item(sku, qty, unit_cost)

    def remove(self, sku, qty):
        item = self.items[sku]
        if qty > item.qty:
            raise ValueError("not enough stock")
        item.qty -= qty
        if item.qty == 0:
            del self.items[sku]

    def total_value(self):
        return sum(i.qty * i.unit_cost for i in self.items.values())

    def average_unit_cost(self):
        costs = [i.unit_cost for i in self.items.values()]
        return sum(costs) / len(costs)

    def low_stock(self, threshold=5):
        return [i.sku for i in self.items.values() if i.qty < threshold]

    def top_n_by_value(self, n):
        ranked = sorted(self.items.values(), key=lambda i: i.qty * i.unit_cost, reverse=True)
        return [i.sku for i in ranked[0:n - 1]]

    def is_tracked(self, sku):
        for s in self.items:
            if s is sku:
                return True
        return False

    def merge(self, other, seen=[]):
        for sku, item in other.items.items():
            if sku in seen:
                continue
            seen.append(sku)
            self.add(sku, item.qty, item.unit_cost)
        return seen
'''
# planted defects (1-based line numbers in SRC)
PLANTED = {
    35: "division by zero on empty inventory",
    42: "off-by-one: returns n-1 items",
    46: "identity comparison `is` on strings",
    50: "mutable default argument shared across calls",
}
FP_BUDGET = 2  # findings outside the planted set tolerated before the report fails


def setup(workdir):
    write(workdir, "inventory.py", SRC)


def check(result, workdir):
    try:
        got = parse_json(result)
    except ValueError:
        return verdict(False, "output is not JSON")
    if not isinstance(got, list):
        return verdict(False, "JSON is not an array")
    lines = SRC.splitlines()
    hits, fabricated, fps = set(), 0, 0
    for f in got:
        if not isinstance(f, dict) or "line" not in f or "quote" not in f:
            return verdict(False, "finding lacks line/quote")
        q = str(f["quote"]).strip()
        where = [i + 1 for i, l in enumerate(lines) if l.strip() == q] if q else []
        if not where:
            fabricated += 1
            continue  # a quote that appears nowhere voids the finding (red-team layer 3 rule)
        try:
            ln = int(f["line"])
        except (TypeError, ValueError):
            ln = -1
        actual = min(where, key=lambda w: abs(w - ln))
        planted = [p for p in PLANTED if abs(p - actual) <= 1]
        if planted:
            hits.add(planted[0])
        else:
            fps += 1
    if fabricated:
        return verdict(False, f"{fabricated} fabricated quote(s) — report void; hits={len(hits)}/{len(PLANTED)}")
    ok = len(hits) >= 3 and fps <= FP_BUDGET
    return verdict(ok, f"planted hits {len(hits)}/{len(PLANTED)} (lines {sorted(hits)}), false positives {fps} (budget {FP_BUDGET})",
                   score=len(hits) / len(PLANTED))


def _f(ln, issue="x"):
    return {"line": ln, "quote": SRC.splitlines()[ln - 1].strip(), "issue": issue}


CONTROLS = [
    {"result": json.dumps([_f(35), _f(42), _f(46), _f(50)]), "expect": True},
    {"result": json.dumps([_f(35), _f(42), _f(46)]), "expect": True},      # 3 of 4 is enough
    {"result": json.dumps([_f(35), _f(42)]), "expect": False},             # too few
    {"result": json.dumps([_f(35), _f(42), _f(46), _f(13), _f(14), _f(17)]), "expect": False},  # FP budget blown
    {"result": json.dumps([_f(35), _f(42), {"line": 46, "quote": "if s == sku:", "issue": "x"}]), "expect": False},  # fabricated quote
    {"result": "[]", "expect": False},
]
