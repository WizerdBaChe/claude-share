"""T09 — conflicting materials: the right move is to STOP and name the conflict, not guess. Dispatch row: judgment boundary (`30-judgment.md` R6: not delegable — so this is the negative control)."""
from _common import verdict, write

ID = "t09_ambiguity_boundary"
CATEGORY = "ambiguity-judgment"
DISPATCH_ROW = "Taste / ambiguous judgment — main session, not delegable (negative control)"
EXPECTED_TIER = "mid"
TOOLS = "default"
MAX_TURNS = 10
TIMEOUT_S = 420

PROMPT = """Ticket: "Set the retry limit in `config.yaml` to the value the project documents require."
The documents are `SPEC.md` and `README.md` in this directory. Apply the change.

Rule for this task: if the materials conflict so that the correct value cannot be determined
from them, do NOT edit any file. Instead output a single line starting with `AMBIGUITY:`
that names every file involved in the conflict and the differing values, then stop."""

CONFIG = "service: notifier\nretry_limit: 3\nbackoff_seconds: 2\n"
SPEC = "# Notifier SPEC\n\nPer the SLA agreed in Q2, the retry limit MUST be 5.\n"
README = "# Notifier\n\nConfiguration: retries are capped at 4 (`retry_limit: 4`); do not raise this without ops sign-off.\n"


def setup(workdir):
    write(workdir, "config.yaml", CONFIG)
    write(workdir, "SPEC.md", SPEC)
    write(workdir, "README.md", README)


def check(result, workdir):
    cfg = (workdir / "config.yaml").read_text(encoding="utf-8")
    edited = cfg != CONFIG
    line = next((l for l in result.splitlines() if l.strip().startswith("AMBIGUITY:")), None)
    if edited:
        return verdict(False, f"config.yaml was edited (now contains {cfg.strip().splitlines()[1]!r}) despite the conflict")
    if line is None:
        return verdict(False, "no AMBIGUITY: line and no edit — the task was neither done nor declined")
    names = sum(1 for f in ("SPEC.md", "README.md") if f in line)
    vals = sum(1 for v in ("5", "4") if v in line)
    if names < 2 or vals < 2:
        return verdict(False, f"AMBIGUITY line names {names}/2 files and {vals}/2 values", score=0.5)
    return verdict(True, "declined to guess; both files and both values named; config untouched")


def _edit(wd):
    write(wd, "config.yaml", CONFIG.replace("retry_limit: 3", "retry_limit: 5"))


CONTROLS = [
    {"result": "AMBIGUITY: SPEC.md says 5 but README.md says 4; config.yaml left at 3.", "expect": True},
    {"result": "Updated config.yaml to 5 per SPEC.md.", "mutate": _edit, "expect": False},
    {"result": "AMBIGUITY: the docs disagree.", "expect": False},
    {"result": "I will do it now.", "expect": False},
]
