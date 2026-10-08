"""T11 — aggregate over a ~45k-token ledger given INLINE with no tools (long-context recall + arithmetic). New 5th-gen row."""
import json
import random
from _common import parse_json, verdict

ID = "t11_long_context_aggregate"
CATEGORY = "long-context-aggregate"
DISPATCH_ROW = "NEW — long-context recall and aggregation without tools"
EXPECTED_TIER = "mid"
TOOLS = "none"
MAX_TURNS = 1
TIMEOUT_S = 600

N_LINES = 2600
TARGET = "ACC-0472"


def _ledger():
    rng = random.Random(4242)
    accts = [f"ACC-{rng.randint(100, 999):04d}" for _ in range(40)] + [TARGET]
    lines, total, flagged = [], 0, 0
    for i in range(N_LINES):
        month = rng.choice(["01", "02", "03", "03", "03", "04"])
        day = rng.randint(1, 28)
        acct = rng.choice(accts)
        kind = rng.choice(["debit", "credit"])
        amt = rng.randint(100, 99999) / 100
        status = rng.choices(["ok", "FLAGGED", "pending"], weights=[40, 1, 4])[0]
        memo = rng.choice(["invoice", "refund", "transfer", "fee", "payroll", "subscription"])
        lines.append(f"2026-{month}-{day:02d} | {acct} | {kind} | {amt:9.2f} | {status:7s} | {memo}-{i:05d}")
        if acct == TARGET and kind == "debit" and month == "03":
            total += round(amt * 100)
        if status == "FLAGGED":
            flagged += 1
    return "\n".join(lines), total / 100, flagged


LEDGER, GOLD_TOTAL, GOLD_FLAGGED = _ledger()

PROMPT = f"""Below is a transaction ledger (one record per line: date | account | kind | amount | status | memo).
Answer two questions and output ONLY a JSON object {{"total_debit": <number>, "flagged": <integer>}}:
1. total_debit — the sum of `amount` over records where account is exactly {TARGET}, kind is `debit`,
   and the date is in March 2026 (2026-03-01 .. 2026-03-31). Round to 2 decimals.
2. flagged — the number of records whose status is exactly FLAGGED (any account, any month).
You have no tools; work from the text. No prose, no code fences.

<ledger>
{LEDGER}
</ledger>
"""


def setup(workdir):
    pass


def check(result, workdir):
    try:
        got = parse_json(result)
    except ValueError:
        return verdict(False, "output is not JSON")
    try:
        t = float(got["total_debit"]); f = int(got["flagged"])
    except (KeyError, TypeError, ValueError):
        return verdict(False, "missing or non-numeric fields")
    ok_t = abs(t - GOLD_TOTAL) < 0.011
    ok_f = f == GOLD_FLAGGED
    return verdict(ok_t and ok_f,
                   f"total_debit {'ok' if ok_t else f'off by {t - GOLD_TOTAL:+.2f}'}; flagged {'ok' if ok_f else f'{f} vs {GOLD_FLAGGED}'}",
                   score=(ok_t + ok_f) / 2)


CONTROLS = [
    {"result": json.dumps({"total_debit": GOLD_TOTAL, "flagged": GOLD_FLAGGED}), "expect": True},
    {"result": json.dumps({"total_debit": GOLD_TOTAL + 12.5, "flagged": GOLD_FLAGGED}), "expect": False},
    {"result": json.dumps({"total_debit": GOLD_TOTAL, "flagged": GOLD_FLAGGED + 1}), "expect": False},
    {"result": "I cannot compute this.", "expect": False},
]
