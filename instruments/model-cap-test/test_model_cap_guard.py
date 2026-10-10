#!/usr/bin/env python3
"""Two-sided calibration for hooks/model_cap_guard.py.

Run:  python tools/model-cap-test/test_model_cap_guard.py

  MUST-DENY  (positive control) — every route by which a dispatch could reach an
             opus/fable-tier model. If any passes, the cost cap is decorative.
             The inheritance route (M-05..M-08) is the one that was silently
             open until 2026-09-05: an Agent call that OMITS `model` inherits
             the main loop's model, and 46 of 155 such dispatches ran on
             opus/fable before the rule changed.
  MUST-PASS  (negative control) — the dispatches that must stay cheap and
             frictionless: sonnet/haiku, the approval marker, and above all a
             `subagent_type` naming a local definition whose frontmatter already
             pins a within-cap model. 109 of those 155 dispatches were this
             shape; denying them would break every local-agent dispatch. Each is
             ALSO asserted silent — see MUST-NOTICE for why that matters.
  MUST-NOTICE (M-40..M-43) — a model name in NEITHER set. Until 2026-09-09 the
             guard asked one question ("is this opus or fable?"), so a tier that
             ships tomorrow took the same silent exit 0 as sonnet: the input
             matching no declared class was folded into the nearest one, and the
             count stayed plausible. These assert the BRANCH, not the decision —
             both paths end in rc 0 with no permissionDecision, so a case
             asserting only the label could not fail on this defect. They
             require the announcement to NAME the model, and the must-pass cases
             require silence, which is the other half: inverted 2026-09-09 in
             both directions (tier_of() folded -> M-40..M-43 fail and every
             must-pass stays green; WITHIN_CAP emptied -> 8 must-pass cases fail
             and M-40..M-43 stay green).

TWO FIXTURES, DELIBERATELY. Most cases run the LIVE hook against the LIVE
`agents/` directory, because "what does the real frontmatter resolve to" is the
production question. The frontmatter-pins-opus class (M-09..M-11) has no live
instance — every local definition pins sonnet today — so it runs a COPY of the
live hook in a temp tree whose sibling `agents/` holds planted definitions
(`AGENTS_DIR` is derived from the hook's own `__file__`). The copy is taken from
the live source at run time, so a broken hook still fails these cases; what the
temp tree replaces is the corpus, never the code under test.

EXTENDING (PH-11 / AP-61, `ops/references/principle-design-guide.md`): a model
name added to the hook's BLOCKED set with no specimen here fails M-COV — the
coverage check reads the live set. A new DISPATCH SURFACE (a third tool that can
carry a model, beside Agent and Workflow) needs a case in both lists.

UNDETERMINED is a third result class, ASSERTED and counted in no verdict
(AP-62). The guard's model-resolution classes are enumerated by main(): an
explicit `model` argument on an Agent call, a `model:` pinned in a local
agents/*.md frontmatter, and a `model` literal inside an inline Workflow
`script`. A dispatch that carries its model through none of those routes matches
no declared class — the guard has nothing to read — so it emits no decision.

Both cases are DECLARED degradations, which is why they are specimens and not
defect reports; both are named in the hook's own docstring with their evidence.
A scriptPath Workflow puts the model in a FILE, and file content is not on
stdin, so the cap for those is forwarded to the rules layer (ops/20-dispatch.md
section 4). SendMessage-resume inherits the MAIN session's model, and the
2026-07-10 check against the hooks docs found no interception point that carries
one; its mitigation is likewise rules-side. Downgrade-and-forward, never veto.

Until 2026-09-09 this block was PRINTED and not asserted, which made it a
decorative third class: whatever the guard did with these inputs, the suite
printed it and moved on. They are now asserted — no decision emitted, rc 0 —
so the day an interception point appears and the guard starts ruling, the case
fails here rather than going unnoticed. Each ships with its DETERMINABLE TWIN:
the same top-tier intent expressed through a route the guard CAN read, which
must deny. Without the twin, "no decision" would be indistinguishable from a
guard that has stopped working altogether.

Isolation: CLAUDE_CONFIG_DIR points the deny receipt at a temp dir (M-01).
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
HOOK = HOME / "hooks" / "model_cap_guard.py"
REAL_RECEIPTS = HOME / "telemetry" / "model-cap-guard.jsonl"
SETTINGS = HOME / "settings.json"
TIMEOUT_FLOOR = 30          # seconds; see M-T1 in main() and the hook's docstring


def hook_timeouts(settings_text: str, hook_stem: str) -> list[int]:
    """Every `timeout` settings.json gives a command hook whose script is
    hooks/<hook_stem>.py, in file order. An entry with no `timeout` key counts
    as the engine default (600); an unparsable file yields [] so M-T1 FAILS
    rather than passing on nothing."""
    try:
        s = json.loads(settings_text)
    except Exception:
        return []
    found: list[int] = []
    for groups in (s.get("hooks") or {}).values():
        for g in groups or []:
            for h in g.get("hooks", []) or []:
                if f"hooks/{hook_stem}.py" in str(h.get("command", "")):
                    found.append(int(h.get("timeout", 600)))
    return found


def hook_on_failure(settings_text: str, hook_stem: str) -> list[str]:
    """Every `onFailure` settings.json gives hooks/<hook_stem>.py, in file order;
    a missing key reads as the engine default 'continue'. Unparsable -> []."""
    try:
        s = json.loads(settings_text)
    except Exception:
        return []
    return [str(h.get("onFailure", "continue"))
            for groups in (s.get("hooks") or {}).values()
            for g in groups or [] for h in g.get("hooks", []) or []
            if f"hooks/{hook_stem}.py" in str(h.get("command", ""))]
MARKER = "[user-approved-top-tier]"

# (id, tool, tool_input, note) — run against the LIVE hook and LIVE agents/.
MUST_DENY = [
    ("M-01", "Agent", {"model": "opus", "prompt": "review this"},
     "explicit opus"),
    ("M-02", "Agent", {"model": "claude-opus-5", "prompt": "x"},
     "full model id, matched as a substring"),
    ("M-03", "Agent", {"model": "fable", "prompt": "x"}, "explicit fable"),
    ("M-04", "Agent", {"model": "Opus", "prompt": "x"}, "case-insensitive"),
    ("M-05", "Agent", {"subagent_type": "general-purpose", "prompt": "x"},
     "no model + built-in type -> inherits the main loop (42 of 46 in 2026-09)"),
    ("M-06", "Agent", {"subagent_type": "Explore", "prompt": "x"},
     "no model + built-in type"),
    ("M-07", "Agent", {"subagent_type": "claude-code-guide", "prompt": "x"},
     "no model + built-in type"),
    ("M-08", "Agent", {"prompt": "x"}, "no model and no subagent_type at all"),
    ("M-12", "Workflow", {"script": "stage(model: 'opus', effort: 'high')"},
     "workflow script sets opus"),
    ("M-13", "Workflow", {"script": 'run(model = "fable")'},
     "workflow script sets fable, = spelling"),
    ("M-14", "Agent", {"model": "opus", "prompt": f"approved {MARKER[1:]}"},
     "a marker missing its opening bracket is not the marker"),
    # Effort axis (2026-10-10, user ruling): ceiling is sonnet + high; Agent took a
    # per-call `effort` in 2.1.292. A model-only check passed all three before the fix.
    ("M-E1", "Agent", {"model": "sonnet", "effort": "max", "prompt": "x"},
     "within-cap model, effort above the ceiling"),
    ("M-E2", "Agent", {"subagent_type": "code-reviewer", "effort": "XHigh", "prompt": "x"},
     "pinned definition, per-call xhigh, case-insensitive"),
    ("M-E3", "Workflow", {"script": "stage(model: 'sonnet', effort: 'max')"},
     "workflow script sets effort above the ceiling"),
]

MUST_PASS = [
    ("M-20", "Agent", {"model": "sonnet", "prompt": "x"}, "the default tier"),
    ("M-21", "Agent", {"model": "haiku", "prompt": "x"}, "read/search-only tier"),
    ("M-22", "Agent", {"model": "claude-sonnet-5", "prompt": "x"}, "full sonnet id"),
    ("M-23", "Agent", {"model": "opus", "prompt": f"{MARKER} user approved this"},
     "the declared per-instance escape"),
    ("M-24", "Agent", {"model": "fable", "prompt": f"do x {MARKER}"},
     "the escape, marker anywhere in the prompt"),
    ("M-25", "Agent", {"subagent_type": "code-reviewer", "prompt": "x"},
     "local definition, matched by its `name:` alias, pins sonnet"),
    ("M-26", "Agent", {"subagent_type": "testing-bug-fixer", "prompt": "x"},
     "local definition, matched by file stem, pins sonnet"),
    ("M-27", "Agent", {"subagent_type": "work-card-executor", "prompt": "x"},
     "local definition, pins sonnet"),
    ("M-28", "Workflow", {"script": "stage(model: 'sonnet')"}, "within cap"),
    ("M-29", "Workflow", {"script": f"stage(model: 'opus')  # {MARKER}"},
     "the escape, workflow surface"),
    ("M-30", "Bash", {"command": "python tools/model-effort-audit/audit.py --opus"},
     "not a dispatch surface -- out of scope"),
    ("M-31", "Agent", {"model": "", "subagent_type": "api-tester", "prompt": "x"},
     "empty model string falls through to the frontmatter, which pins sonnet"),
    ("M-E4", "Agent", {"model": "sonnet", "effort": "high", "prompt": "x"},
     "the ceiling itself: sonnet + high"),
    ("M-E5", "Agent", {"model": "sonnet", "effort": "max", "prompt": f"{MARKER} approved"},
     "the escape, effort axis"),
    ("M-E6", "Workflow", {"script": "stage(model: 'sonnet', effort: 'medium')"},
     "workflow effort within cap"),
]

# MUST-NOTICE — a model name in NEITHER set. The guard must say so and let the
# call through; folding it into "within cap" is the defect these pin.
MUST_NOTICE = [
    ("M-40", "Agent", {"model": "claude-titan-9", "prompt": "x"}, "claude-titan-9",
     "a tier that is neither blocked nor capped: announced, never folded"),
    ("M-41", "Agent", {"model": "gpt-5-codex", "prompt": "x"}, "gpt-5-codex",
     "a non-Anthropic id is equally unclassifiable, and just as expensive"),
    ("M-42", "Workflow", {"script": "stage(model: 'titan-9', effort: 'high')"},
     "titan-9",
     "the same question one route over -- the deny regex only knows opus|fable"),
]

# Asserted, counted in no verdict: the guard cannot see these.
# (id, tool, tool_input, twin, escapes) — `twin` is the same top-tier intent on
# a route the guard CAN read, and must deny.
UNDETERMINED = [
    ("M-U1", "Workflow", {"scriptPath": "workflows/heavy.md"},
     ("Workflow", {"script": "stage(model: 'opus', effort: 'high')"}),
     "scriptPath: the model literal lives in a FILE, and file content is not "
     "on stdin -- none of the three declared routes (Agent model arg, "
     "frontmatter pin, inline script) can be read (docstring; forwarded to "
     "ops/20-dispatch.md section 4)"),
    ("M-U2", "SendMessage", {"to": "agent-1", "message": "continue"},
     ("Agent", {"model": "opus", "prompt": "continue"}),
     "resume carries no model and no resume indicator in its payload, so there "
     "is nothing to classify; the resumed agent inherits the MAIN session's "
     "model (verified 2026-07-10 against the hooks docs)"),
]

# Unclassifiable SHAPE (AP-62): stdin that parses but is not the object the
# guard reads. (id, raw stdin) -- must fail open: rc 0, silent, no receipt row.
UNCLASSIFIABLE = [
    ("M-UC1", "[]"),
    ("M-UC2", "null"),
    ("M-UC3", json.dumps({"tool_name": "Agent", "tool_input": ["opus"]})),
]

# Planted definitions for the class with no live instance.
PLANTED = {
    "opus-pinned.md": "---\nname: opus-pinned\nmodel: opus\n---\nbody\n",
    "fable-alias.md": "---\nname: costly-helper\nmodel: 'fable'\n---\nbody\n",
    "no-model.md": "---\nname: no-model\ndescription: forgot the key\n---\nbody\n",
    "unknown-tier.md": "---\nname: unknown-tier\nmodel: titan-9\n---\nbody\n",
}
PLANTED_CASES = [
    ("M-09", {"subagent_type": "opus-pinned", "prompt": "x"},
     "local definition pinning opus is denied like an explicit argument"),
    ("M-10", {"subagent_type": "costly-helper", "prompt": "x"},
     "matched by `name:` alias, pins fable"),
    ("M-11", {"subagent_type": "no-model", "prompt": "x"},
     "local definition with NO model: key -- `model` is required, not inherited"),
]
PLANTED_NOTICE = [
    ("M-43", {"subagent_type": "unknown-tier", "prompt": "x"}, "titan-9",
     "the frontmatter route: a pin the guard has no word for is announced too"),
]


def announced(hook: Path, tool: str, ti: dict, expect: str,
              env: dict) -> tuple[bool, str, int]:
    """-> (ok, what it said, rc). Three conditions, because a notice that fails
    any one of them is not a notice: it must not rule, it must not be silent,
    and it must NAME the model -- a reader who cannot see which name was
    unclassifiable cannot classify it."""
    out, rc = raw_of(hook, tool, ti, env)
    spoke = said(out)
    ok = (rc == 0 and decision_of(out) is None
          and expect.lower() in spoke.lower() and "undetermined" in spoke.lower())
    return ok, spoke, rc


def raw_of(hook: Path, tool: str, tool_input: dict, env: dict,
           cwd: str = "", session_id: str = "") -> tuple[str, int]:
    """-> (stdout, returncode). Cases assert on THIS, not only on the decision.

    An unrecognised tier and a within-cap one both end in rc 0 with no
    permissionDecision, so a case that asserted only the decision label could
    not fail on the fold M-40..M-43 exist for. `cwd` goes into the payload as
    the engine sends it (project .claude/agents lookup, M-P1/M-P2)."""
    payload = {"tool_name": tool, "tool_input": tool_input}
    if cwd:
        payload["cwd"] = cwd
    if session_id:
        payload["session_id"] = session_id
    proc = subprocess.run([sys.executable, str(hook)],
                          input=json.dumps(payload),
                          capture_output=True, text=True, env=env, timeout=20)
    return (proc.stdout or "").strip(), proc.returncode


def said(out: str) -> str:
    """The text the hook put in front of the agent ("" if it said nothing)."""
    try:
        return json.loads(out)["hookSpecificOutput"].get("additionalContext") or ""
    except Exception:
        return ""


def decision_of(out: str) -> str | None:
    """None = no decision emitted, which is not the same event as an allow."""
    try:
        return json.loads(out)["hookSpecificOutput"].get("permissionDecision")
    except Exception:
        return None


def verdict_of(hook: Path, tool: str, tool_input: dict,
               env: dict) -> tuple[str | None, int]:
    """-> (permissionDecision or None, returncode)."""
    out, rc = raw_of(hook, tool, tool_input, env)
    return decision_of(out), rc


def denied(hook: Path, tool: str, tool_input: dict, env: dict) -> tuple[bool, int]:
    decision, rc = verdict_of(hook, tool, tool_input, env)
    return decision == "deny", rc


def label(tool: str, ti: dict) -> str:
    bits = [f"{k}={v!r}" for k, v in ti.items() if k != "prompt"]
    if MARKER in str(ti.get("prompt", "")):
        bits.append("prompt=<marker>")
    return f"{tool}({', '.join(bits) or '...'})"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="model-cap-test-"))
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(tmp), PYTHONIOENCODING="utf-8")
    real_before = REAL_RECEIPTS.stat().st_size if REAL_RECEIPTS.exists() else -1
    failures: list[str] = []
    try:
        print(f"{'id':6} {'side':10} {'verdict':8} case")
        print("-" * 108)
        for cid, tool, ti, note in MUST_DENY:
            hit, rc = denied(HOOK, tool, ti, env)
            print(f"{cid:6} {'MUST-DENY':10} {'deny' if hit else 'PASS!!':8} "
                  f"{label(tool, ti)[:52]:52}  {note}")
            if not hit or rc != 0:
                failures.append(f"{cid} MUST-DENY leaked: {label(tool, ti)} "
                                f"({note}, rc {rc})")
        for cid, tool, ti, note in MUST_PASS:
            out, rc = raw_of(HOOK, tool, ti, env)
            hit = decision_of(out) == "deny"
            state = "DENY!!" if hit else ("SPOKE!" if out else "pass")
            print(f"{cid:6} {'MUST-PASS':10} {state:8} "
                  f"{label(tool, ti)[:52]:52}  {note}")
            if hit or rc != 0:
                failures.append(f"{cid} MUST-PASS blocked: {label(tool, ti)} "
                                f"({note}, rc {rc})")
            elif out:
                # The negative half of M-40..M-43. Without it, a tier_of() that
                # called EVERYTHING unrecognised would still pass every case in
                # this list -- none of them asserts on more than the deny label.
                failures.append(
                    f"{cid} MUST-PASS was not silent: the guard emitted "
                    f"{out[:110]!r} on a model it recognises ({note}). An "
                    f"announcement on every dispatch is the notice branch going "
                    f"off in the negative direction, and it trains the reader to "
                    f"skip the one that matters.")

        # --- must-notice: the third tier value, announced not folded --------
        for cid, tool, ti, expect, note in MUST_NOTICE:
            ok, spoke, rc = announced(HOOK, tool, ti, expect, env)
            print(f"{cid:6} {'MUST-NOTE':10} {'said' if ok else 'FOLD!!':8} "
                  f"{label(tool, ti)[:52]:52}  {note}")
            if not ok:
                failures.append(
                    f"{cid} MUST-NOTICE folded: {label(tool, ti)} produced "
                    f"{spoke[:110]!r} (rc {rc}). A model in neither BLOCKED nor "
                    f"WITHIN_CAP must be announced by name as undetermined and "
                    f"let through -- silence here is the guard reporting 'within "
                    f"cap' about a tier it has never heard of, which is the "
                    f"shape that stayed plausible for two months.")

        # --- planted corpus: the class with no live instance ----------------
        (tmp / "hooks").mkdir()
        (tmp / "agents").mkdir()
        copy = tmp / "hooks" / "model_cap_guard.py"
        shutil.copy(HOOK, copy)                       # live source, planted corpus
        shutil.copy(HOME / "hooks" / "deny_receipt.py", tmp / "hooks")
        for name, body in PLANTED.items():
            (tmp / "agents" / name).write_text(body, encoding="utf-8")
        for cid, ti, note in PLANTED_CASES:
            hit, rc = denied(copy, "Agent", ti, env)
            print(f"{cid:6} {'MUST-DENY':10} {'deny' if hit else 'PASS!!':8} "
                  f"{label('Agent', ti)[:52]:52}  {note}")
            if not hit or rc != 0:
                failures.append(f"{cid} MUST-DENY leaked (planted corpus): "
                                f"{label('Agent', ti)} ({note}, rc {rc})")
        for cid, ti, expect, note in PLANTED_NOTICE:
            ok, spoke, rc = announced(copy, "Agent", ti, expect, env)
            print(f"{cid:6} {'MUST-NOTE':10} {'said' if ok else 'FOLD!!':8} "
                  f"{label('Agent', ti)[:52]:52}  {note}")
            if not ok:
                failures.append(
                    f"{cid} MUST-NOTICE folded (planted corpus): "
                    f"{label('Agent', ti)} produced {spoke[:110]!r} (rc {rc}) -- "
                    f"the frontmatter route resolves a model the same way the "
                    f"`model` argument does, so it must classify it the same way.")

        # --- project definitions: <cwd>/.claude/agents is read first --------
        # 2026-10-09: a haiku worker defined only in an isolated workspace's
        # .claude/agents read as "no pin" and was denied (lab r22 pilot); cases M-P1/M-P2.
        # Values per case: the decision with cwd, and without it (the defect's
        # view, where the project file is invisible).
        proj = tmp / "proj"
        (proj / ".claude" / "agents").mkdir(parents=True)
        for name, model in (("proj-haiku", "claude-haiku-5-5"), ("proj-opus", "claude-opus-5-5")):
            (proj / ".claude" / "agents" / f"{name}.md").write_text(
                f"---\nname: {name}\nmodel: {model}\n---\nx\n", encoding="utf-8")
        for cid, typ, want_with, want_without in (("M-P1", "proj-opus", "deny", "deny"),
                                                  ("M-P2", "proj-haiku", None, "deny")):
            ti = {"subagent_type": typ, "prompt": "x"}
            bare = {k: v for k, v in env.items() if k != "CLAUDE_PROJECT_DIR"}   # the payload cwd alone
            out_with, rc = raw_of(copy, "Agent", ti, bare, cwd=str(proj))
            out_without, _ = raw_of(copy, "Agent", ti, bare)
            got = (decision_of(out_with), decision_of(out_without))
            ok = rc == 0 and got == (want_with, want_without) and (want_with or not out_with)
            print(f"{cid:6} {'PROJECT':10} {'ok' if ok else 'WRONG!!':8} "
                  f"{label('Agent', ti)[:52]:52}  with cwd {got[0]} / without {got[1]}")
            if not ok:
                failures.append(f"{cid} project-definition lookup: {typ} gave {got}, "
                                f"want {(want_with, want_without)} (with cwd / without)")

        # M-P3: after a shell `cd`, the payload cwd is a sub-folder; the project root
        # (CLAUDE_PROJECT_DIR) still resolves the pin. Values: decision with the root
        # in env vs with the moved cwd alone (the second is the r22 rerun defect).
        ti = {"subagent_type": "proj-haiku", "prompt": "x"}
        (proj / "build").mkdir()
        out_root, rc = raw_of(copy, "Agent", ti, dict(env, CLAUDE_PROJECT_DIR=str(proj)), cwd=str(proj / "build"))
        out_moved, _ = raw_of(copy, "Agent", ti, {k: v for k, v in env.items() if k != "CLAUDE_PROJECT_DIR"},
                              cwd=str(proj / "build"))
        got = (decision_of(out_root), decision_of(out_moved))
        ok = rc == 0 and got == (None, "deny") and not out_root
        print(f"{'M-P3':6} {'PROJECT':10} {'ok' if ok else 'WRONG!!':8} "
              f"{label('Agent', ti)[:52]:52}  root in env {got[0]} / moved cwd only {got[1]}")
        if not ok:
            failures.append(f"M-P3 project root after cd: got {got}, want (None, 'deny')")

        # --- deferral to the mod's resolved-model judge (2026-10-09 ruling) ---
        # An omitted `model` with no definition found here is deferred ONLY for a
        # session the mod wrote a heartbeat for; the copy's MOD_HEARTBEAT is
        # tmp/telemetry/model-cap-mod-alive.json. Each case pairs the deferral with
        # its control: the same call from an unlisted session must still deny (the
        # 2026-10-02 escape shape when the mod is not running).
        beat = tmp / "telemetry" / "model-cap-mod-alive.json"
        beat.parent.mkdir(parents=True, exist_ok=True)
        beat.write_text(json.dumps({"sess-live": 1}), encoding="utf-8")
        bare = {k: v for k, v in env.items() if k != "CLAUDE_PROJECT_DIR"}
        omitted = {"subagent_type": "plugin-only-worker", "prompt": "x"}
        hcases = [
            ("M-H1", omitted, bare, "sess-live", None,
             "omitted, no definition here, mod heartbeat for this session -> deferred (silent)"),
            ("M-H1n", omitted, bare, "sess-other", "deny",
             "same call, session without a heartbeat -> deny stands"),
            ("M-H1z", omitted, bare, "", "deny",
             "same call, no session_id in payload -> deny stands"),
            ("M-H2", {"subagent_type": "proj-opus", "prompt": "x"},
             dict(env, CLAUDE_PROJECT_DIR=str(proj)), "sess-live", "deny",
             "definition found here pins opus -> deny even with the mod alive"),
            ("M-H3", {"subagent_type": "general-purpose", "model": "opus", "prompt": "x"},
             bare, "sess-live", "deny", "explicit opus -> deny even with the mod alive"),
        ]
        for cid, ti, cenv, sid, want, note in hcases:
            out, rc = raw_of(copy, "Agent", ti, cenv, session_id=sid)
            got = decision_of(out)
            ok = rc == 0 and got == want and (want or not out)
            print(f"{cid:6} {'MOD-DEFER':10} {'ok' if ok else 'WRONG!!':8} "
                  f"{label('Agent', ti)[:52]:52}  {note}: {got}")
            if not ok:
                failures.append(f"{cid} mod deferral: got {got!r} (out {out[:80]!r}), want {want!r} -- {note}")
        beat.write_text("{not json", encoding="utf-8")
        out, rc = raw_of(copy, "Agent", omitted, bare, session_id="sess-live")
        ok = rc == 0 and decision_of(out) == "deny"
        print(f"{'M-H4':6} {'MOD-DEFER':10} {'ok' if ok else 'WRONG!!':8} "
              f"{label('Agent', omitted)[:52]:52}  unreadable heartbeat -> deny stands: {decision_of(out)}")
        if not ok:
            failures.append("M-H4 unreadable heartbeat deferred the dispatch; it must fail toward the deny")
        beat.unlink()

        # --- fail-open ------------------------------------------------------
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json {{{",
                              capture_output=True, text=True, env=env, timeout=20)
        ok = proc.returncode == 0 and not proc.stdout.strip()
        print("-" * 108)
        print(f"{'ok  ' if ok else 'FAIL'} M-FO garbage stdin fails open: "
              f"rc {proc.returncode}, silent")
        if not ok:
            failures.append("M-FO: garbage stdin did not fail open (a guard bug "
                            "must never block a dispatch)")

        # --- unclassifiable shape: parses, but is not an object (AP-62) -----
        # M-FO never reaches the two `not isinstance` guards in main(): its
        # stdin fails json.load first. These payloads parse, so the only thing
        # between them and `payload.get` / `tool_input.get` is the guard --
        # without it the hook raises (rc 1, traceback) instead of staying
        # silent. The inner one needs a TRUTHY non-dict: `tool_input or {}`
        # turns [] into {} before the guard ever sees it. Silence is asserted
        # on stdout AND on the receipt file, which earlier cases have already
        # grown, so the measure is its size before and after.
        receipts = tmp / "telemetry" / "model-cap-guard.jsonl"
        for cid, raw in UNCLASSIFIABLE:
            size_before = receipts.stat().st_size if receipts.exists() else -1
            proc = subprocess.run([sys.executable, str(HOOK)], input=raw,
                                  capture_output=True, text=True, env=env,
                                  timeout=20)
            size_after = receipts.stat().st_size if receipts.exists() else -1
            ok = (proc.returncode == 0 and not proc.stdout.strip()
                  and size_before == size_after)
            print(f"{'ok  ' if ok else 'FAIL'} {cid} unclassifiable payload "
                  f"fails open: {raw[:60]!r} -> rc {proc.returncode}, "
                  f"{'silent' if not proc.stdout.strip() else 'SPOKE'}, "
                  f"receipts {size_before} -> {size_after} bytes")
            if not ok:
                failures.append(
                    f"{cid}: unclassifiable payload {raw!r} did not fail open "
                    f"(rc {proc.returncode}, stdout {proc.stdout.strip()[:80]!r}, "
                    f"stderr {proc.stderr.strip()[-80:]!r}, receipts "
                    f"{size_before} -> {size_after}) -- a JSON value that is "
                    f"not an object matches no payload class, so the guard "
                    f"must exit 0 silently and write no row.")

        # --- coverage over the hook's OWN blocked set -----------------------
        sys.path.insert(0, str(HOME / "hooks"))
        spec = importlib.util.spec_from_file_location("mcg_under_test", HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        def corpus(cases):
            return " ".join(str(ti.get("model", "")) + " " + str(ti.get("script", ""))
                            for _c, _t, ti, *_r in cases).lower()

        # Both enumerations, because both decide a verdict: an unlisted BLOCKED
        # name is a leak, an unlisted WITHIN_CAP name is a notice on every
        # ordinary dispatch. Neither set can be complete -- this only makes sure
        # nothing was added to one without a specimen here.
        uncovered = ([("BLOCKED", b, "MUST_DENY")
                      for b in mod.BLOCKED if b not in corpus(MUST_DENY)]
                     + [("WITHIN_CAP", w, "MUST_PASS")
                        for w in mod.WITHIN_CAP if w not in corpus(MUST_PASS)])
        ok = not uncovered
        print(f"{'ok  ' if ok else 'FAIL'} M-COV every tier the hook names has a "
              f"specimen: blocked {sorted(mod.BLOCKED)} + within-cap "
              f"{sorted(mod.WITHIN_CAP)}, {len(uncovered)} uncovered")
        for set_name, u, where in uncovered:
            failures.append(f"M-COV: '{u}' is in the hook's {set_name} set with "
                            f"no specimen in {where} -- add one to this file")

        # --- timeout floor: a gate whose timeout is a PASS (2026-10-02) -----
        # One session: eight parallel no-`model` dispatches, this hook
        # answered deny on all eight, the engine honoured six. The two it did
        # not honour arrived after the 5 s `timeout` settings.json gave the
        # hook, and the hooks docs say a timed-out command hook does not block
        # the call. Both subagents ran on claude-fable-5-1. The floor is 30 s,
        # 4.6x the worst latency measured (6.5 s). Two-sided: the live
        # settings.json must satisfy it, and a planted settings text with the
        # old 5 s must FAIL the same reader -- a floor check that cannot fail
        # on the old value proves nothing.
        live_timeouts = hook_timeouts(SETTINGS.read_text(encoding="utf-8"),
                                      "model_cap_guard")
        planted = ('{"hooks":{"PreToolUse":[{"matcher":"Agent|Workflow","hooks":['
                   '{"type":"command","command":"\\"py\\" \\"<CLAUDE_HOME>/hooks/model_cap_guard.py\\"",'
                   '"timeout":5}]}]}}')
        planted_timeouts = hook_timeouts(planted, "model_cap_guard")
        ok_live = bool(live_timeouts) and min(live_timeouts) >= TIMEOUT_FLOOR
        ok_planted = bool(planted_timeouts) and min(planted_timeouts) < TIMEOUT_FLOOR
        print(f"{'ok  ' if ok_live else 'FAIL'} M-T1 settings.json gives this hook "
              f"timeout {live_timeouts} (floor {TIMEOUT_FLOOR} s; a timed-out "
              f"command hook is a pass)")
        print(f"{'ok  ' if ok_planted else 'FAIL'} M-T1c planted 5 s settings is "
              f"read as {planted_timeouts} and would fail the floor")
        if not ok_live:
            failures.append(
                f"M-T1: settings.json timeout for model_cap_guard is "
                f"{live_timeouts}, under the {TIMEOUT_FLOOR} s floor (or the "
                f"entry was not found). Under load this hook has needed 6.5 s; "
                f"a command hook that times out does not block the call "
                f"(hooks docs), so a short timeout turns the cap into a pass.")
        if not ok_planted:
            failures.append(
                "M-T1c: the planted 5 s settings text did not read as under the "
                "floor -- the reader is blind, so M-T1 passing means nothing.")

        # --- M-T2: onFailure "block" (2.1.295; user ruling 2026-10-10) -------
        # A crash, missing interpreter or timeout used to PASS the dispatch.
        live_of = hook_on_failure(SETTINGS.read_text(encoding="utf-8"),
                                  "model_cap_guard")
        planted_of = hook_on_failure(json.dumps({"hooks": {"PreToolUse": [{"hooks": [
            {"type": "command", "command": "python hooks/model_cap_guard.py"}]}]}}),
            "model_cap_guard")
        ok_of = bool(live_of) and all(v == "block" for v in live_of)
        ok_ofc = planted_of == ["continue"]
        print(f"{'ok  ' if ok_of else 'FAIL'} M-T2 settings.json gives this hook "
              f"onFailure {live_of} (must be 'block' on every entry)")
        print(f"{'ok  ' if ok_ofc else 'FAIL'} M-T2c planted entry without the key "
              f"reads as {planted_of} (engine default) and would fail M-T2")
        if not ok_of:
            failures.append(
                f"M-T2: settings.json onFailure for model_cap_guard is {live_of}; "
                f"without 'block' a crashed or timed-out guard lets the dispatch through.")
        if not ok_ofc:
            failures.append("M-T2c: the reader did not see a missing key as "
                            "'continue' -- M-T2 passing means nothing.")

        # --- undetermined: asserted, counted in no verdict (AP-62) ----------
        for cid, tool, ti, (twin_tool, twin_ti), escapes in UNDETERMINED:
            decision, rc = verdict_of(HOOK, tool, ti, env)
            ok = decision is None and rc == 0
            print(f"{cid:6} {'UNDET':10} {'undet' if ok else 'RULED!':8} "
                  f"{label(tool, ti)[:52]:52}  no decision emitted")
            print(f"{'':6} {'':10} {'':8} escapes: {escapes}")
            if not ok:
                failures.append(
                    f"{cid} UNDETERMINED ruled on: {label(tool, ti)} -- the guard "
                    f"emitted {decision!r} (rc {rc}) on a dispatch whose model it "
                    f"cannot read. AP-62: an input matching no declared class is "
                    f"undetermined and excluded from every verdict count. If an "
                    f"interception point now carries the model, move this case "
                    f"into MUST_DENY and keep its twin as the regression.")
            twin_hit, twin_rc = denied(HOOK, twin_tool, twin_ti, env)
            if not twin_hit or twin_rc != 0:
                failures.append(
                    f"{cid} UNDETERMINED twin leaked: {label(twin_tool, twin_ti)} "
                    f"(rc {twin_rc}) -- the twin of {cid} must deny, or {cid} "
                    f"proves nothing: 'no decision' would then be indistinguish"
                    f"able from a guard that has stopped ruling on anything.")

        real_after = REAL_RECEIPTS.stat().st_size if REAL_RECEIPTS.exists() else -1
        ok = real_before == real_after
        print(f"{'ok  ' if ok else 'FAIL'} M-01 the live receipt file was not "
              f"touched: {real_before} -> {real_after} bytes")
        if not ok:
            failures.append(
                "M-01: this run wrote to the LIVE telemetry/model-cap-guard.jsonl"
                " -- CLAUDE_CONFIG_DIR isolation broke and every sweep would "
                "inflate the deny denominator. Fix the env in main().")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    n_deny = len(MUST_DENY) + len(PLANTED_CASES)
    n_note = len(MUST_NOTICE) + len(PLANTED_NOTICE)
    total = (n_deny + len(MUST_PASS) + n_note + 2 * len(UNDETERMINED)
             + len(UNCLASSIFIABLE) + 3)
    print("-" * 108)
    print(f"must-deny: {n_deny}   must-pass: {len(MUST_PASS)}   "
          f"must-notice: {n_note}   "
          f"undetermined + twins (not counted): {len(UNDETERMINED)}   "
          f"failures: {len(failures)}")
    if failures:
        for f in failures:
            print("  FAIL " + f)
        return 1
    # Interpolated, never typed: this line is quoted in the hook's docstring and
    # in integrity-sweep, and a hand-written total goes stale the first time a
    # case is added -- while still reading as a full result.
    print(f"ALL PASS {total}/{total} ({n_deny} must-deny incl. "
          f"{len(PLANTED_CASES)} on a planted corpus, {len(MUST_PASS)} must-pass "
          f"(each also asserted silent), {n_note} must-notice, "
          f"{len(UNDETERMINED)} undetermined + {len(UNDETERMINED)} determinable "
          f"twins, fail-open + {len(UNCLASSIFIABLE)} unclassifiable-shape, "
          f"coverage, isolation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
