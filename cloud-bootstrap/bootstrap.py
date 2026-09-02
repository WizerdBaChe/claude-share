#!/usr/bin/env python3
"""bootstrap.py — make a Claude Code cloud container behave like the source
~/.claude environment this repo was extracted from ("LikeLocal").

    python3 cloud-bootstrap/bootstrap.py install    # copy + render into ~/.claude (idempotent)
    python3 cloud-bootstrap/bootstrap.py verify     # every mounted hook fails open; two guards deny
    python3 cloud-bootstrap/bootstrap.py status     # what is installed, from which repo commit
    python3 cloud-bootstrap/bootstrap.py summary    # the one-line card the SessionStart hook prints

Why this file exists
--------------------
Claude Code on the web runs each session in an ephemeral container: the repo
is cloned fresh, and ~/.claude is regenerated with nothing of the operator's
own environment in it. Every share in this repo already documents how to put
itself onto a machine by hand (environment-guide/OPERATOR-GUIDE.md Part 3,
each folder's README). This script is that procedure made mechanical, so the
SessionStart hook in .claude/settings.json can run it before the first turn.

What it does NOT do, and why (each is a documented boundary, not a gap):
  * memory — `projects/<slug>/memory/` never leaves the source machine
    (OPERATOR-GUIDE.md 2.2); nothing here can recreate it.
  * interop targets — no other agent CLI exists in the container; the layer's
    freshness screen (ops_health_nudge check 12) is silent when interop/ is
    absent, so it is not installed rather than installed-and-alarming.
  * settings.json `model` / `effortLevel` — the cloud host picks both per
    session; a pin here would fight the picker the operator actually used.
  * the SessionEnd memory-pipeline mount — the digest it writes dies with the
    container; the PreCompact/SessionStart pair still runs (its cards are
    useful within one container's life).

Hook mounting lives in .claude/settings.json (project scope), not in the
user-scope settings.json this script writes. Project-scope mounts are live
from the first tool call of the first session; a user-scope file written by a
SessionStart hook is not guaranteed to be read before the same session's
first hook fires. Each mount goes through .claude/hooks/run-hook.sh, which
execs the REPO copy of the hook (always present) and exits 0 when it is not —
the fail-open property every hook in hooks/ already claims, extended to the
mount itself.

Every path the installed files resolve at runtime goes through Path.home() /
CLAUDE_CONFIG_DIR inside the hooks themselves; this script only decides WHERE
the copies land (CLAUDE_CONFIG_DIR, else ~/.claude), matching the source
layout the rule files assume (global-claude-md/README.md "path table").
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
MARKER = CLAUDE_HOME / "cloud-bootstrap.json"

# ---------------------------------------------------------------------------
# Environment values rendered into the global CLAUDE.md's four placeholders.
# These are the ONLY machine facts this script asserts about the container;
# everything else is measured and dated in ops-environment.cloud.md.
# ---------------------------------------------------------------------------
RENDER = {
    "<OS_NAME>": "Linux (Ubuntu 24.04 — Claude Code cloud container)",
    "<DEFAULT_SHELL_NAME>": "bash",
    "<LINE_ENDING_CONVENTION>": "LF",
}
# The secondary-shell clause has no referent in the container (one shell, no
# PowerShell); the README's own instruction is "drop that clause".
SECONDARY_CLAUSE = re.compile(
    r"; `<SECONDARY_SHELL_NAME>` takes a manual second launch on the user's side\."
)
PLACEHOLDER_NOTE = re.compile(r"^\s*<!-- Placeholder note:.*?-->\s*\n", re.M | re.S)
LEFTOVER_TOKEN = re.compile(r"<[A-Z][A-Z_]+>")

# ---------------------------------------------------------------------------
# Copy map: (repo-relative source, ~/.claude-relative destination, kind).
# kind: "file" copies one file; "tree" mirrors a directory (overwrite, never
# delete extras); "glob" copies matching files from a directory (no recurse).
# Order matters only for ops/: the cloud environment.md overlays the source
# machine's copy after the tree lands.
# ---------------------------------------------------------------------------
COPY_MAP = [
    ("global-claude-md/rules", "rules", "glob:*.md"),
    ("claude-ops/ops", "ops", "tree"),
    ("cloud-bootstrap/ops-environment.cloud.md", "ops/environment.md", "file"),
    ("claude-ops/references/PROJECTS.md", "references/PROJECTS.md", "file"),
    ("skill-toolkit/skill-trigger-dict.md", "skill-trigger-dict.md", "file"),
    ("skill-toolkit/skills", "skills", "tree"),
    ("hooks", "hooks", "glob:*.py"),
    ("hooks", "hooks", "glob:*.json"),
    ("agents", "agents", "glob:engineering-*.md"),
    ("agents", "agents", "glob:testing-*.md"),
    ("environment-guide/PHILOSOPHY.md", "PHILOSOPHY.md", "file"),
    ("environment-guide/OPERATOR-GUIDE.md", "OPERATOR-GUIDE.md", "file"),
    ("environment-guide/COMMIT-TEMPLATES.md", "COMMIT-TEMPLATES.md", "file"),
    ("compact-recovery/preserve.py", "tools/memory-pipeline/preserve.py", "file"),
    ("architecture-diagramming/archdiag", "tools/archdiag", "tree"),
    ("thinking-notes", "thinking-notes", "glob:*.md"),
]

# hooks/settings.example.json keys carried into the user-scope settings.json.
# `hooks` is NOT carried (project scope mounts them, see module docstring);
# `model` and `effortLevel` are NOT carried (host-managed in the cloud).
SETTINGS_KEYS = ("permissions", "disableWorkflows", "cleanupPeriodDays", "env")

# The hooks whose deny path must be PROVEN by verify, with a payload each.
# A guard that has never been seen to deny is not evidence (global CLAUDE.md,
# "calibrate with a known-TRUE input and a known-false one").
DENY_PROBES = [
    ("model_cap_guard.py",
     {"hook_event_name": "PreToolUse", "tool_name": "Agent",
      "tool_input": {"model": "opus", "prompt": "x"}}),
    ("dangerous_command_guard.py",
     {"hook_event_name": "PreToolUse", "tool_name": "Bash",
      "tool_input": {"command": "git push --force origin main"}}),
]
ALLOW_PROBES = [
    ("model_cap_guard.py",
     {"hook_event_name": "PreToolUse", "tool_name": "Agent",
      "tool_input": {"model": "sonnet", "prompt": "x"}}),
    ("dangerous_command_guard.py",
     {"hook_event_name": "PreToolUse", "tool_name": "Bash",
      "tool_input": {"command": "git status"}}),
]


def log(msg: str, quiet: bool) -> None:
    if not quiet:
        print(msg)


def repo_head() -> str:
    try:
        out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def copy_file(src: Path, dst: Path) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    shutil.copymode(src, dst)
    return 1


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    for p in src.rglob("*"):
        if p.is_dir() or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(src)
        n += copy_file(p, dst / rel)
    return n


def render_claude_md() -> tuple[str, list[str]]:
    text = (REPO / "global-claude-md" / "CLAUDE.md").read_text(encoding="utf-8")
    text = SECONDARY_CLAUSE.sub(" (single shell; no secondary shell to distinguish).", text)
    for token, value in RENDER.items():
        text = text.replace(token, value)
    text = PLACEHOLDER_NOTE.sub("", text)
    leftovers = sorted(set(LEFTOVER_TOKEN.findall(text)))
    return text, leftovers


def install_settings(quiet: bool) -> str:
    """User-scope settings.json from the template, minus what the cloud owns.

    Written only when absent or when the existing file carries our marker key;
    a file someone else wrote is never touched (that is their settings, and the
    hooks work without this file anyway).
    """
    target = CLAUDE_HOME / "settings.json"
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "left (unparseable, not ours)"
        if "_cloud_bootstrap" not in existing:
            return "left (present, not ours)"
    template = json.loads((REPO / "hooks" / "settings.example.json").read_text(encoding="utf-8"))
    out = {"_cloud_bootstrap": {
        "note": "Written by cloud-bootstrap/bootstrap.py from hooks/settings.example.json. "
                "Hooks are mounted by the repo's .claude/settings.json (project scope); "
                "model and effortLevel are host-managed in the cloud and deliberately absent.",
        "repo_head": repo_head(),
    }}
    for key in SETTINGS_KEYS:
        if key in template:
            out[key] = template[key]
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "written"


def cmd_install(quiet: bool) -> int:
    CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for src_rel, dst_rel, kind in COPY_MAP:
        src, dst = REPO / src_rel, CLAUDE_HOME / dst_rel
        if not src.exists():
            log(f"  skip  {src_rel} (not in repo)", quiet)
            continue
        if kind == "file":
            n = copy_file(src, dst)
        elif kind == "tree":
            n = copy_tree(src, dst)
        elif kind.startswith("glob:"):
            n = sum(copy_file(p, dst / p.name) for p in sorted(src.glob(kind[5:])) if p.is_file())
        else:
            raise ValueError(kind)
        counts[dst_rel] = counts.get(dst_rel, 0) + n
        log(f"  {n:4d}  {src_rel} -> {dst_rel}", quiet)

    text, leftovers = render_claude_md()
    (CLAUDE_HOME / "CLAUDE.md").write_text(text, encoding="utf-8")
    counts["CLAUDE.md"] = 1
    log(f"     1  global-claude-md/CLAUDE.md -> CLAUDE.md (rendered: "
        f"{', '.join(RENDER.values())})", quiet)
    if leftovers:
        log(f"  WARN  unrendered placeholder(s) in CLAUDE.md: {leftovers}", quiet)

    settings_state = install_settings(quiet)
    log(f"  settings.json: {settings_state}", quiet)
    (CLAUDE_HOME / "telemetry").mkdir(exist_ok=True)

    marker = {
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo_head": repo_head(),
        "repo_path": str(REPO),
        "claude_home": str(CLAUDE_HOME),
        "python": sys.executable,
        "files": sum(counts.values()),
        "by_destination": counts,
        "unrendered_placeholders": leftovers,
        "settings_json": settings_state,
    }
    MARKER.write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    log(f"installed {marker['files']} files into {CLAUDE_HOME} from {marker['repo_head']}", quiet)
    return 0


def run_hook(name: str, payload: dict) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(REPO / "hooks" / name)],
                       input=json.dumps(payload), capture_output=True, text=True, timeout=60)
    return p.returncode, p.stdout


def decision(stdout: str) -> str:
    try:
        return json.loads(stdout)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return "allow" if not stdout.strip() else "other"


def cmd_verify() -> int:
    failures = []
    # 1. every installed file class is present
    for dst_rel in ("CLAUDE.md", "ops/OPS.md", "ops/environment.md", "skill-trigger-dict.md",
                    "rules", "skills", "hooks/ops_health_nudge.py", "agents", "PHILOSOPHY.md",
                    "tools/memory-pipeline/preserve.py", "tools/archdiag/index.mjs"):
        if not (CLAUDE_HOME / dst_rel).exists():
            failures.append(f"missing after install: {dst_rel}")
    # 2. the rendered CLAUDE.md carries no placeholder
    text = (CLAUDE_HOME / "CLAUDE.md").read_text(encoding="utf-8") if (CLAUDE_HOME / "CLAUDE.md").exists() else ""
    left = sorted(set(LEFTOVER_TOKEN.findall(text)))
    if left:
        failures.append(f"CLAUDE.md still carries {left}")
    # 3. every mounted hook fails open on an empty / minimal payload
    mounted = sorted(p.name for p in (REPO / "hooks").glob("*.py"))
    for name in mounted:
        rc, _ = run_hook(name, {})
        status = "ok" if rc == 0 else f"exit {rc}"
        print(f"  fail-open  {name:36s} {status}")
        if rc != 0:
            failures.append(f"{name} exit {rc} on empty payload (must be 0)")
    # 4. the two deny guards deny a known-bad input and pass a known-good one
    for name, payload in DENY_PROBES:
        rc, out = run_hook(name, payload)
        d = decision(out)
        print(f"  deny-probe {name:36s} {d}")
        if d != "deny":
            failures.append(f"{name} did not deny a known-bad payload")
    for name, payload in ALLOW_PROBES:
        rc, out = run_hook(name, payload)
        d = decision(out)
        print(f"  allow-probe {name:35s} {d}")
        if d != "allow":
            failures.append(f"{name} denied a known-good payload")
    # 5. the project-scope mounts point at hooks that ship
    settings = json.loads((REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))
    mounts = [h["command"].split()[-1] for blocks in settings["hooks"].values()
              for b in blocks for h in b["hooks"] if "run-hook.sh" in h["command"]]
    # ops_health_nudge.py is chained inside session-start.sh (sequenced after
    # the install), not mounted through the shim — count that as its mount.
    chained = re.findall(r"hooks/([a-z_]+\.py)",
                         (REPO / ".claude" / "hooks" / "session-start.sh").read_text(encoding="utf-8"))
    for m in mounts:
        if not (REPO / "hooks" / m).is_file():
            failures.append(f".claude/settings.json mounts {m}, which hooks/ does not ship")
    for name in mounted:
        if name not in mounts and name not in chained:
            failures.append(f"{name} ships but .claude/settings.json does not mount it")
    print(f"  mounts     {len(mounts)} sites over {len(set(mounts))} hooks; "
          f"{len(mounted)} hooks ship")
    if failures:
        print("VERIFY FAILED")
        for f in failures:
            print("  - " + f)
        return 1
    print("VERIFY OK")
    return 0


def cmd_status() -> int:
    if not MARKER.exists():
        print(f"not installed: {MARKER} absent (run `install`)")
        return 1
    m = json.loads(MARKER.read_text(encoding="utf-8"))
    head = repo_head()
    print(json.dumps(m, indent=2))
    if m.get("repo_head") != head:
        print(f"repo HEAD is {head}, installed from {m.get('repo_head')} — re-run install")
        return 1
    return 0


def cmd_summary() -> int:
    """One line, injected into the session's context by the SessionStart hook."""
    if not MARKER.exists():
        print("[cloud-bootstrap] not installed — run: python3 cloud-bootstrap/bootstrap.py install")
        return 0
    m = json.loads(MARKER.read_text(encoding="utf-8"))
    extra = ""
    if m.get("unrendered_placeholders"):
        extra = f"; UNRENDERED {m['unrendered_placeholders']}"
    print(f"[cloud-bootstrap] ~/.claude installed from repo {m.get('repo_head')} "
          f"({m.get('files')} files: CLAUDE.md, rules/, ops/, skills/, hooks/, agents/) — "
          f"the cloud container now carries the source environment's rules layer; "
          f"facts: ops/environment.md{extra}")
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "install"
    quiet = "--quiet" in argv
    if cmd == "install":
        return cmd_install(quiet)
    if cmd == "verify":
        return cmd_verify()
    if cmd == "status":
        return cmd_status()
    if cmd == "summary":
        return cmd_summary()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
