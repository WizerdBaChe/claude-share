"""T02 — extract ERROR records from a log into JSON; exact-match gate. Dispatch row: 'Translation / extraction' (cheap)."""
import json
import random
from _common import parse_json, verdict, write
from pathlib import Path

ID = "t02_extract_hard_gate"
CATEGORY = "extraction-hard-gate"
DISPATCH_ROW = "Translation / extraction / small to-spec scripts — hard machine-checkable gate"
EXPECTED_TIER = "cheap"
TOOLS = "default"
MAX_TURNS = 6
TIMEOUT_S = 300

PROMPT = """Read `app.log` in the current directory. Extract every line whose level is ERROR
(and ONLY those — not WARN, not lines that merely mention the word error in their message).
Output ONLY a JSON array, sorted by timestamp ascending, each element an object with exactly
these keys: "ts" (the timestamp string as written), "service", "code" (the integer after E),
"message" (the text after the code, trimmed). No prose, no code fences."""

SERVICES = ["auth", "billing", "search", "mailer", "gateway"]
MSGS = ["connection reset by peer", "upstream timeout after 30s", "schema mismatch on field qty",
        "quota exceeded for tenant 17", "retrying job 4412", "cache miss ratio above threshold",
        "an error-prone path was taken but recovered", "disk usage at 91 percent"]


def _lines(seed=20261008):
    rng = random.Random(seed)
    lines, gold = [], []
    t = 0
    for i in range(70):
        t += rng.randint(1, 40)
        ts = f"2026-09-30T08:{t // 60:02d}:{t % 60:02d}Z"
        svc = rng.choice(SERVICES)
        lvl = rng.choices(["INFO", "WARN", "ERROR", "DEBUG"], weights=[5, 3, 2, 2])[0]
        if lvl == "ERROR":
            code = rng.randint(100, 999)
            msg = rng.choice(MSGS[:6])
            lines.append(f"{ts} [{svc}] ERROR E{code} {msg}")
            gold.append({"ts": ts, "service": svc, "code": code, "message": msg})
        elif lvl == "WARN" and rng.random() < 0.4:
            lines.append(f"{ts} [{svc}] WARN W{rng.randint(10, 99)} {MSGS[6]}")  # decoy mentions 'error'
        else:
            lines.append(f"{ts} [{svc}] {lvl} {rng.choice(MSGS[4:])}")
    return "\n".join(lines) + "\n", gold


LOG, GOLD = _lines()


def setup(workdir):
    from bench import seed_for  # per-rep seed; rep 1 == the base fixture above
    log, gold = _lines(seed_for(Path(workdir), 20261008))
    write(workdir, "app.log", log)
    write(workdir, ".gold.json", json.dumps(gold))


def check(result, workdir):
    GOLD = json.loads((Path(workdir) / ".gold.json").read_text(encoding="utf-8"))
    try:
        got = parse_json(result)
    except ValueError:
        return verdict(False, "output is not JSON")
    if not isinstance(got, list):
        return verdict(False, "JSON is not an array")
    norm = []
    for e in got:
        if not isinstance(e, dict) or set(e) != {"ts", "service", "code", "message"}:
            return verdict(False, f"element keys wrong: {sorted(e) if isinstance(e, dict) else type(e).__name__}")
        try:
            norm.append({"ts": e["ts"], "service": e["service"], "code": int(e["code"]), "message": str(e["message"]).strip()})
        except (TypeError, ValueError):
            return verdict(False, "code is not an integer")
    if norm == GOLD:
        return verdict(True, f"{len(GOLD)}/{len(GOLD)} ERROR records exact")
    gs, ns = {json.dumps(g, sort_keys=True) for g in GOLD}, {json.dumps(n, sort_keys=True) for n in norm}
    missing, extra = len(gs - ns), len(ns - gs)
    order = "order wrong; " if (not missing and not extra) else ""
    return verdict(False, f"{order}missing={missing} extra={extra} of {len(GOLD)}",
                   score=max(0.0, 1 - (missing + extra) / len(GOLD)))


CONTROLS = [
    {"result": json.dumps(GOLD), "expect": True},
    {"result": "```json\n" + json.dumps(GOLD, indent=1) + "\n```", "expect": True},  # fence tolerated
    {"result": json.dumps(GOLD[:-1]), "expect": False},
    {"result": json.dumps(list(reversed(GOLD))), "expect": False},
    {"result": json.dumps(GOLD + [{"ts": "x", "service": "auth", "code": 1, "message": "an error-prone path was taken but recovered"}]), "expect": False},
]
