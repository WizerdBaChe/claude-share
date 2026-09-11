"""Two-sided calibration for literature_host_guard.py — stdlib only, hermetic.

Run: python hooks/tests/test_literature_host_guard.py   (exit 0 = all pass)

WHY BOTH SIDES. This guard denies by LIST (a host's policy row), so a version
that denied every WebFetch and every shell command on the machine would still
look correct from the deny side. The A-* cases pin the traffic the hook must
never touch: the public scholarly APIs on every surface, an unlisted host, a
shell command with no URL in it. M-1 is the mutation that keeps the deny side
honest: with the banned host's row REMOVED from the policy the same call must
be allowed, or D-01 was passing on something other than the policy.

EXTENDING: a new denied shape gets a D-* case, a new allowed one an A-* case;
both go through `Box.run()`, so a case is one call.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "literature_host_guard.py"
HOME = Path(__file__).resolve().parents[2]
LIVE_POLICY = HOME / "hooks" / "literature-host-policy.json"
LIVE_LOG = HOME / "telemetry" / "literature-host-nav.jsonl"
LIVE_RECEIPTS = HOME / "telemetry" / "literature-host-guard.jsonl"

spec = importlib.util.spec_from_file_location("literature_host_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

WEBFETCH = "WebFetch"
PANE = "mcp__Claude_Browser__navigate"
PANE_PREVIEW = "mcp__Claude_Browser__preview_start"
PANE_BATCH = "mcp__Claude_Browser__browser_batch"
CHROME = "mcp__claude-in-chrome__navigate"
CHROME_BATCH = "mcp__claude-in-chrome__browser_batch"
PW = "mcp__playwright-headless__browser_navigate"

FAILS: list[str] = []


def check_that(name: str, cond: bool, detail="") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}" if detail else name)
    print(f"{'ok  ' if cond else 'FAIL'} {name}")


POLICY = {
    "schema": "literature-host-policy@1",
    "unlisted_default": {"class": "unlisted", "agent_surfaces": ["script", "webfetch"], "max_per_run": 1},
    "unmeasured_publisher_hosts": ["pubs.acs.example"],
    "hosts": [
        {"host": "arxiv.example", "class": "open", "agent_surfaces": ["script", "webfetch", "browser_headless"],
         "max_per_run": 30},
        {"host": "api.crossref.example", "class": "metadata_api", "agent_surfaces": ["script", "webfetch"], "max_per_run": 300},
        {"host": "landing.example", "class": "landing_page", "agent_surfaces": ["webfetch"], "max_per_run": 1},
        {"host": "banned.example", "class": "agent_banned", "agent_surfaces": [], "max_per_run": 0,
         "licence_basis": "Terms of Use forbid robots or intelligent agents (read 2026-09-10)"},
        {"host": "inst.example", "class": "institutional_only", "agent_surfaces": [], "max_per_run": 0},
    ],
}


class Box:
    """One isolated CLAUDE_CONFIG_DIR: its own policy file and telemetry."""

    def __init__(self, policy=POLICY, raw_policy: str | None = None):
        self.dir = Path(tempfile.mkdtemp(prefix="lit-host-guard-"))
        (self.dir / "hooks").mkdir(parents=True, exist_ok=True)
        p = self.dir / "hooks" / "literature-host-policy.json"
        if raw_policy is not None:
            p.write_text(raw_policy, encoding="utf-8")
        elif policy is not None:
            p.write_text(json.dumps(policy), encoding="utf-8")
        self.env = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.dir), PYTHONIOENCODING="utf-8")
        self.env.pop("CLAUDE_TELEMETRY_DIR", None)
        self.env.pop("LSE_HOST_POLICY", None)
        self.log = self.dir / "telemetry" / "literature-host-nav.jsonl"
        self.receipts = self.dir / "telemetry" / "literature-host-guard.jsonl"

    def run_raw(self, raw: str):
        return subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=raw,
                              capture_output=True, text=True, env=self.env, timeout=60)

    def run(self, tool: str, ti: dict):
        """-> (denied, reason, returncode)."""
        p = self.run_raw(json.dumps({"tool_name": tool, "tool_input": ti, "session_id": "test-session"}))
        out = (p.stdout or "").strip()
        if not out:
            return False, "", p.returncode
        try:
            spec_out = json.loads(out)["hookSpecificOutput"]
        except Exception:
            return False, out, p.returncode
        return (spec_out.get("permissionDecision") == "deny",
                spec_out.get("permissionDecisionReason", ""), p.returncode)

    def rows(self):
        if not self.log.is_file():
            return []
        return [json.loads(ln) for ln in self.log.read_text(encoding="utf-8").splitlines() if ln.strip()]


# ------------------------------------------------------------------ deny side
print("-- D: calls that MUST be denied")
box = Box()
for cid, tool, ti, why in [
    ("D-01", WEBFETCH, {"url": "https://banned.example/document/123"}, "WebFetch of an agent_banned host"),
    ("D-02", CHROME, {"url": "https://banned.example/document/123"}, "the user's Chrome driven at a banned host"),
    ("D-03", PANE, {"url": "https://banned.example/x"}, "the in-app pane at a banned host"),
    ("D-04", PW, {"url": "https://banned.example/x"}, "headless Playwright at a banned host"),
    ("D-05", "Bash", {"command": "curl -sL https://banned.example/document/123 -o d.html"},
     "a shell command carrying the banned host's URL literal"),
    ("D-06", "PowerShell", {"command": "Invoke-WebRequest 'https://banned.example/rest/search' -OutFile x"},
     "PowerShell too"),
    ("D-07", PANE_BATCH, {"actions": [{"name": "navigate", "input": {"url": "https://banned.example/x"}},
                                      {"name": "computer", "input": {"action": "screenshot"}}]},
     "a batch whose first action navigates to a banned host"),
    ("D-08", CHROME_BATCH, {"actions": [{"name": "computer", "input": {"action": "screenshot"}},
                                        {"name": "navigate", "input": {"url": "https://banned.example/x"}}]},
     "a batch whose LATER action navigates there"),
    ("D-09", WEBFETCH, {"url": "https://inst.example/search"}, "institutional_only grants no surface either"),
    ("D-10", PW, {"url": "https://landing.example/article/1"},
     "a landing-page row that grants webfetch but no browser"),
    ("D-11", CHROME, {"url": "https://landing.example/article/1"}, "nor the user's Chrome"),
    ("D-12", PANE, {"url": "https://pubs.acs.example/doi/10.1/x"},
     "an unmeasured publisher: a browser surface is not granted without a row"),
    ("D-13", WEBFETCH, {"url": "https://www.banned.example/x"}, "a subdomain of a banned host"),
    ("D-14", WEBFETCH, {"url": "HTTPS://BANNED.EXAMPLE/X"}, "the host compare is case-folded"),
    ("D-15", PANE_PREVIEW, {"url": "https://banned.example"}, "preview_start takes a URL too"),
    ("D-16", "Bash", {"command": "python fetch.py https://api.crossref.example/works/x https://banned.example/y"},
     "one banned literal among allowed ones is enough"),
    ("D-17", WEBFETCH, {"url": "https://banned.example./document/1"},
     "the absolute-FQDN form (trailing dot) is the same host (QA 2026-09-11 F-1)"),
    ("D-18", PW, {"url": "https://www.banned.example.:443/x"}, "trailing dot + port on a subdomain"),
]:
    denied, reason, rc = box.run(tool, ti)
    check_that(f"{cid} deny: {why}", denied and rc == 0, f"rc={rc} denied={denied} reason={reason[:90]!r}")

denied, reason, _ = box.run(WEBFETCH, {"url": "https://banned.example/document/123"})
check_that("D-01b the deny opens by naming the hook as local, names the host, class and basis",
           reason.startswith("Call denied by literature_host_guard (a local PreToolUse hook")
           and "banned.example" in reason and "agent_banned" in reason and "Terms of Use" in reason, reason[:240])
check_that("D-01c and names the hand-to-user route, the metadata APIs and the no-retry rule",
           "hand-to-user" in reason and "api.crossref.org" in reason and "headless browser" in reason, reason[-400:])
check_that("D-01d and carries the receipt nonce sentence + the misfire exit",
           "Recorded as row" in reason and "report_fp.py" in reason, reason[-300:])

# ------------------------------------------------------------------ allow side
print("\n-- A: traffic this hook must NEVER touch")
for cid, tool, ti, why in [
    ("A-01", WEBFETCH, {"url": "https://arxiv.example/abs/2305.14627"}, "an open host, WebFetch"),
    ("A-02", PW, {"url": "https://arxiv.example/abs/2305.14627"}, "an open host that lists browser_headless"),
    ("A-03", "Bash", {"command": "curl -s https://api.crossref.example/works/10.1/x"}, "a metadata API from a script"),
    ("A-04", WEBFETCH, {"url": "https://landing.example/article/1"}, "a landing-page host on its granted surface"),
    ("A-05", WEBFETCH, {"url": "https://example.com/some/page"}, "an unlisted host: ordinary web reading"),
    ("A-06", CHROME, {"url": "https://github.com/x/y"}, "the user's Chrome at an unlisted non-publisher host"),
    ("A-07", WEBFETCH, {"url": "https://pubs.acs.example/doi/10.1/x"}, "an unmeasured publisher gets its one plain fetch"),
    ("A-08", "Bash", {"command": "git status && python runs.py check ."}, "a shell command with no URL"),
    ("A-09", "PowerShell", {"command": "Get-ChildItem -Recurse | Select-Object -First 5"}, "PowerShell, no URL"),
    ("A-10", PANE_PREVIEW, {"name": "dev"}, "a launch.json server: no URL to judge"),
    ("A-11", PANE, {"url": "back"}, "history navigation carries no host"),
    ("A-12", PANE_BATCH, {"actions": [{"name": "computer", "input": {"action": "screenshot"}}]},
     "a batch with no navigation in it"),
    ("A-13", "Bash", {"command": "echo 'see banned.example in the notes'"},
     "a bare host name without a URL scheme is prose, not a fetch"),
    ("A-14", WEBFETCH, {"url": "https://notbanned.example/x"}, "a host that merely CONTAINS a banned name"),
    ("A-15", WEBFETCH, {"url": "https://banned.example.evil/x"}, "a banned host as a PREFIX of someone else's domain"),
]:
    denied, reason, rc = box.run(tool, ti)
    check_that(f"{cid} allow: {why}", not denied and rc == 0, f"rc={rc} reason={reason[:120]!r}")

# ------------------------------------------------ the mutation that tests D-01
print("\n-- M: mutations that keep the deny side honest")
mut = Box(policy={**POLICY, "hosts": [r for r in POLICY["hosts"] if r["host"] != "banned.example"]})
denied, _r, _rc = mut.run(WEBFETCH, {"url": "https://banned.example/document/123"})
check_that("M-1 with the banned host's row REMOVED the same WebFetch is allowed "
           "(so D-01 was reading the policy, not a name baked into the hook)", not denied)
mut2 = Box(policy={**POLICY, "hosts": [{**r, "agent_surfaces": ["webfetch", "browser_headless"]}
                                       if r["host"] == "landing.example" else r for r in POLICY["hosts"]]})
denied, _r, _rc = mut2.run(PW, {"url": "https://landing.example/article/1"})
check_that("M-2 granting browser_headless on the landing row flips D-10 to allow "
           "(the surface check reads agent_surfaces)", not denied)

# ------------------------------------------------------------------ recording
print("\n-- R: telemetry rows")
rbox = Box()
rbox.run(WEBFETCH, {"url": "https://arxiv.example/abs/1"})
rbox.run(WEBFETCH, {"url": "https://example.com/unlisted"})
rbox.run(WEBFETCH, {"url": "https://banned.example/x"})
rows = rbox.rows()
check_that("R-1 listed-host decisions are recorded (allow + deny), unlisted hosts are NOT",
           len(rows) == 2 and {r["decision"] for r in rows} == {"allow", "deny"}, rows)
check_that("R-2 the deny row is loud and carries the class",
           any(r["decision"] == "deny" and r.get("loud") and r.get("class") == "agent_banned" for r in rows), rows)
check_that("R-3 every row carries ts/session/tool/surface/url/host/decision",
           all({"ts", "session", "tool", "surface", "url", "host", "decision"} <= set(r) for r in rows), rows[:1])
check_that("R-4 the deny wrote a receipt row in the hook's own receipt log",
           rbox.receipts.is_file() and '"kind": "deny"' in rbox.receipts.read_text(encoding="utf-8"),
           str(rbox.receipts))

# ------------------------------------------------------------------ fail-open
print("\n-- FO: the hook's own inputs are broken")
for cid, raw, why in (
    ("FO-1", "not json at all", "unparsable stdin"),
    ("FO-2", '{"tool_name": "WebFetch"}', "no tool_input"),
    ("FO-3", "[1, 2]", "a payload that parses but is not an object"),
    ("FO-4", '{"tool_name": "WebFetch", "tool_input": ["url"]}', "a non-mapping tool_input"),
    ("FO-5", '{"tool_name": "WebFetch", "tool_input": {"url": {"unexpected": "shape"}}}', "a url that is not a string"),
    ("FO-6", '{"tool_name": "Bash", "tool_input": {"command": 42}}', "a command that is not a string"),
    ("FO-7", '{"tool_name": "mcp__Claude_Browser__browser_batch", "tool_input": {"actions": "nope"}}',
     "a batch whose actions is not a list"),
):
    p = box.run_raw(raw)
    check_that(f"{cid} {why}: exits 0 silently", p.returncode == 0 and not (p.stdout or "").strip(),
               f"rc={p.returncode} stdout={(p.stdout or '')[:80]!r}")
ubox = Box()
for raw in ('[1, 2]', '{"tool_name": "WebFetch", "tool_input": {"url": {"unexpected": "shape"}}}'):
    ubox.run_raw(raw)
check_that("FO-8 undetermined input leaves no telemetry row", not ubox.log.exists())

corrupt = Box(raw_policy="{ not json")
denied, _r, rc = corrupt.run(WEBFETCH, {"url": "https://banned.example/x"})
check_that("FO-9 an UNREADABLE policy fails OPEN (no rows = nothing banned; the skill side fails closed)",
           not denied and rc == 0)
check_that("FO-9b and says so loudly in telemetry",
           any(r["decision"] == "policy_unreadable" and r.get("loud") for r in corrupt.rows()), corrupt.rows())
missing = Box(policy=None)
denied, _r, rc = missing.run(WEBFETCH, {"url": "https://banned.example/x"})
check_that("FO-10 a MISSING policy also fails open", not denied and rc == 0)

# ------------------------------------------------------- the live policy file
print("\n-- L: the live policy, and isolation from the live telemetry")
live = guard.load_policy.__globals__["json"].loads(LIVE_POLICY.read_text(encoding="utf-8")) if LIVE_POLICY.exists() else None
check_that("L-1 the LIVE policy parses and carries hosts[]", isinstance(live, dict) and isinstance(live.get("hosts"), list))
if live:
    lbox = Box(policy=live)
    banned = [r["host"] for r in live["hosts"] if r.get("class") in ("agent_banned", "institutional_only")]
    check_that("L-2 the live policy lists at least the measured banned hosts",
               {"ieeexplore.ieee.org", "www.sciencedirect.com", "onlinelibrary.wiley.com"} <= set(banned), banned)
    for h in banned:
        denied, _r, _rc = lbox.run(WEBFETCH, {"url": f"https://{h}/x"})
        check_that(f"L-3 live banned row denies WebFetch: {h}", denied)
    for h in ("arxiv.org", "api.crossref.org", "api.semanticscholar.org"):
        denied, _r, _rc = lbox.run(WEBFETCH, {"url": f"https://{h}/x"})
        check_that(f"L-4 live open/API row allows WebFetch: {h}", not denied)
    denied, _r, _rc = lbox.run(CHROME, {"url": "https://link.springer.com/article/10.1007/x"})
    check_that("L-5 live landing row (link.springer.com) refuses the user's Chrome", denied)
    denied, _r, _rc = lbox.run(WEBFETCH, {"url": "https://link.springer.com/article/10.1007/x"})
    check_that("L-5b but grants WebFetch", not denied)

before = (LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1, LIVE_RECEIPTS.stat().st_size if LIVE_RECEIPTS.exists() else -1)
Box().run(WEBFETCH, {"url": "https://banned.example/x"})
after = (LIVE_LOG.stat().st_size if LIVE_LOG.exists() else -1, LIVE_RECEIPTS.stat().st_size if LIVE_RECEIPTS.exists() else -1)
check_that("I-1 the LIVE telemetry files were not written to by this suite", after == before, f"{before} -> {after}")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
