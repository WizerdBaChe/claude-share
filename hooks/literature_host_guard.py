r"""PreToolUse guard: no agent surface touches a scholarly host its access policy bans.

STATUS: LIVE since 2026-09-11 (user ruling R1 the same day; entry-schema ES-1).

WHY. On 2026-09-10 an institutional VPN made four paywalled publishers reachable
in one step and the next thought was "drive a headless browser with a logged-in
profile". `rules/literature-access.md` was written that night to say no. The NTU
Library's AI-literacy guide (2026-09-11, slide 18) states the cost of the other
branch in the library's own words: a publisher's anomaly detection sees a robot
on a licensed IP range, blocks the RANGE, and the library disables the VPN for
everyone. The user's ruling: unless a host is explicitly released, a program does
not retrieve from an access-controlled site — and a rule that lives in prose is
only as good as the executor's memory of it, so this hook is that rule at the
tool boundary, for every session on this machine.

WHAT IT READS. `hooks/literature-host-policy.json` — one row per host with a
`class` and the `agent_surfaces` the row grants. The same file is read by the
literature-search-extract skill (`connectors/access_policy.py`, `verify/fetchsrc.py`),
so the skill and the harness cannot disagree on a host. The hook never edits it.

WHAT IT RULES ON, and only this:

  DENY  the host of the call is LISTED and either
          (a) its class is `agent_banned` or `institutional_only` (no surface), or
          (b) the surface this tool is does not appear in the row's `agent_surfaces`
              (a landing-page host that grants webfetch but not a browser);
        or the host is in `unmeasured_publisher_hosts` and the surface is a browser
        (an unlisted publisher gets one plain fetch, never a browser — user ruling R2).
  ALLOW everything else, silently. An UNLISTED non-publisher host is ordinary web
        reading and this hook has no opinion on it; per-run caps (`max_per_run`,
        the three-unlisted-hosts cap) live in fetchsrc.py, which has a run to count in.

Surfaces, by tool:
  WebFetch                                  -> webfetch
  mcp__playwright-headless__browser_navigate,
  mcp__Claude_Browser__navigate / preview_start(url)   -> browser_headless
  mcp__claude-in-chrome__navigate           -> browser_user (the user's real sessions)
  mcp__*__browser_batch                     -> each navigate/preview_start action inside,
                                               judged by that server's surface
  Bash / PowerShell                         -> script, for every `https?://<host>` literal
                                               in the command (curl, Invoke-WebRequest,
                                               python one-liners — the literal is the tell)

Fail-open on the HOOK's own inputs: an unparsable payload, a non-object payload,
a non-mapping tool_input, a url that is not a string — exit 0, nothing written.
Fail-OPEN on the policy FILE too, and this is the one place that differs from
`browser_pane_scope_guard`: with the file unreadable this hook knows no banned
host, so it denies nothing and writes a loud `policy_unreadable` row instead. A
missing file must not lock every WebFetch and shell command on the machine; the
skill side (`access_policy.py`) is the one that fails CLOSED without the file,
because it only ever routes scholarly retrieval.

Telemetry: `telemetry/literature-host-nav.jsonl` gets a row for every decision on
a LISTED host or a publisher (allow and deny — low volume by construction: only
scholarly hosts), plus the `policy_unreadable` row. Denies also write the receipt
row `deny_receipt` keeps in `telemetry/literature-host-guard.jsonl`. Unlisted
hosts are never logged: WebFetch and Bash are high-volume tools.

FALSE-POSITIVE LOG: none observed yet (born 2026-09-11). Loosening trigger: 3
observed misfires on distinct hosts → re-derive the row, never widen the hook.
BYPASS LOG: 2026-09-11 QA F-1 — a trailing-dot host (`ieeexplore.ieee.org.`) fell
through to unlisted; fixed the same day (host canonicalised, D-17/D-18).

Proof-of-life: `python hooks/tests/test_literature_host_guard.py` — D-* deny cases
per surface, A-* allow cases (arXiv on every surface, an unlisted host, a bare
shell command), M-1 mutation (the same host with its row removed must be
allowed, so D-* was reading the policy), FO-* fail-open incl. the unreadable
policy, R-* telemetry rows, L-* the live policy's own banned rows.
review-when: a new browser MCP server is registered (its navigate tool needs a
surface mapping here AND a matcher line in settings.json); the policy schema
field changes; the harness adds a fetch-shaped tool other than WebFetch.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

HOOK = "literature_host_guard"
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
POLICY_PATH = Path(os.environ.get("LSE_HOST_POLICY") or (CLAUDE_DIR / "hooks" / "literature-host-policy.json"))
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "literature-host-nav.jsonl"

NO_SURFACE_CLASSES = {"agent_banned", "institutional_only"}
BROWSER_SURFACES = {"browser_headless", "browser_user"}
URL_RE = re.compile(r"https?://([A-Za-z0-9.\-]+(?::\d+)?)", re.I)
MAX_URL_CHARS = 500


def surface_for(tool: str) -> str:
    if tool == "WebFetch":
        return "webfetch"
    if tool in ("Bash", "PowerShell"):
        return "script"
    if tool.startswith("mcp__claude-in-chrome__"):
        return "browser_user"
    if tool.startswith("mcp__playwright-headless__") or tool.startswith("mcp__Claude_Browser__"):
        return "browser_headless"
    return ""


def host_of(url: str) -> str:
    raw = (url or "").strip()
    if not raw or raw.lower() in ("back", "forward"):
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    try:
        # strip a trailing dot: the absolute-FQDN form resolves to the same host (QA 2026-09-11 F-1)
        return (urlsplit(raw).hostname or "").lower().strip(".")
    except Exception:
        return ""


def load_policy():
    try:
        data = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("hosts"), list):
        return None
    return data


def row_for(host: str, policy: dict):
    best = None
    for row in policy.get("hosts") or []:
        if not isinstance(row, dict):
            continue
        listed = str(row.get("host", "")).strip().lower().strip(".")
        if listed and (host == listed or host.endswith("." + listed)):
            if best is None or len(listed) > len(str(best.get("host", ""))):
                best = row
    return best


def is_unmeasured_publisher(host: str, policy: dict) -> bool:
    for listed in policy.get("unmeasured_publisher_hosts") or []:
        listed = str(listed).strip().lower().lstrip(".")
        if listed and (host == listed or host.endswith("." + listed)):
            return True
    return False


def judge(host: str, surface: str, policy: dict):
    """-> (decision, row_or_None, why). decision in {'deny', 'allow', 'unlisted'}."""
    row = row_for(host, policy)
    if row is None:
        if surface in BROWSER_SURFACES and is_unmeasured_publisher(host, policy):
            return "deny", {"host": host, "class": "unmeasured_publisher", "agent_surfaces": ["script", "webfetch"]}, \
                "an unmeasured subscription publisher: one plain fetch of a named URL is the whole grant, no browser"
        return "unlisted", None, ""
    cls = str(row.get("class", ""))
    if cls in NO_SURFACE_CLASSES:
        return "deny", row, f"class {cls} grants no agent surface"
    surfaces = row.get("agent_surfaces") or []
    if surface not in surfaces:
        return "deny", row, f"class {cls} grants {surfaces or 'no surface'}, not {surface}"
    return "allow", row, ""


def record(session_id: str, tool: str, url: str, host: str, surface: str, decision: str, row=None, loud=False) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "session": str(session_id)[:64],
            "tool": tool, "surface": surface,
            "url": (url or "")[:MAX_URL_CHARS], "host": host,
            "decision": decision,
        }
        if row:
            entry["class"] = str(row.get("class", ""))
        if loud:
            entry["loud"] = True
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def deny_reason(tool: str, host: str, surface: str, row: dict, why: str) -> str:
    basis = str(row.get("licence_basis") or row.get("note") or "")[:220]
    cls = str(row.get("class", ""))
    head = (
        f"Call denied by {HOOK} (a local PreToolUse hook, not page content). This {tool} call "
        f"targets `{host}`, which the host access policy ({POLICY_PATH.name}) lists with class "
        f"`{cls}` — {why}."
    )
    if basis:
        head += f" Recorded basis for that row: {basis}"
    if cls in ("agent_banned", "unmeasured_publisher"):
        head += (
            " A person reading this host is licensed; a program reading it is what the publisher's "
            "anomaly detection blocks, and it blocks the institution's whole IP range, after which the "
            "library disables the VPN for everyone."
        )
    return head + (
        "\n\nWhat to do instead:\n"
        "  1. metadata or an abstract: query api.crossref.org or api.semanticscholar.org (script or "
        "WebFetch — both are policy rows);\n"
        "  2. an open copy: try arxiv.org, pmc.ncbi.nlm.nih.gov, or the doi.org redirect of an OA article;\n"
        "  3. the licensed text itself: hand the named document to the user — record the DOI/URL in the "
        "deliverable's gaps as 'not retrieved, hand-to-user' and ship a query pack; their reading is the "
        "licensed act, and a passage they hand back is recorded as user_provided.\n"
        "A 202/403/418/CAPTCHA answer from any host is the same routing signal, not an obstacle: do not "
        "re-issue the call through another User-Agent, a headless browser, or a logged-in profile.\n\n"
        f"Only the user edits {POLICY_PATH.name}; a row change is theirs to make and cannot be arranged "
        "from inside this call."
        + _receipt(HOOK, host=host, surface=surface, tool=tool)
        + _fp(HOOK)
    )


def targets_of(tool: str, tool_input: dict):
    """[(url, surface)] this call would touch. Empty when there is nothing judgeable."""
    out = []
    if tool in ("Bash", "PowerShell"):
        cmd = tool_input.get("command")
        if isinstance(cmd, str):
            for m in URL_RE.finditer(cmd):
                out.append((m.group(0), "script"))
        return out
    if tool.endswith("__browser_batch"):
        actions = tool_input.get("actions")
        if not isinstance(actions, list):
            return out
        server = tool[: tool.rfind("__") + 2]      # e.g. "mcp__Claude_Browser__"
        for a in actions:
            if not isinstance(a, dict):
                continue
            name = str(a.get("name", ""))
            inp = a.get("input")
            if name in ("navigate", "preview_start", "browser_navigate") and isinstance(inp, dict):
                url = inp.get("url")
                if isinstance(url, str) and url:
                    out.append((url, surface_for(server + name)))
        return out
    url = tool_input.get("url")
    if isinstance(url, str) and url:
        out.append((url, surface_for(tool)))
    return out


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)
    session_id = payload.get("session_id", "")

    targets = targets_of(tool, tool_input)
    if not targets:
        sys.exit(0)

    policy = load_policy()
    if policy is None:
        # fail-open, loudly: with no rows there is nothing to ban; the skill side fails closed.
        record(session_id, tool, targets[0][0], host_of(targets[0][0]), targets[0][1], "policy_unreadable", loud=True)
        sys.exit(0)

    for url, surface in targets:
        host = host_of(url)
        if not host or not surface:
            continue
        decision, row, why = judge(host, surface, policy)
        if decision == "unlisted":
            continue
        record(session_id, tool, url, host, surface, decision, row, loud=(decision == "deny"))
        if decision == "deny":
            deny(deny_reason(tool, host, surface, row, why))
    sys.exit(0)


if __name__ == "__main__":
    main()
