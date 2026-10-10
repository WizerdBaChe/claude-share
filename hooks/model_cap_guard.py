"""PreToolUse guard: enforce the subagent model cost cap (haiku/sonnet only).

STATUS: LIVE since 2026-07-07 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

Policy (owner: user, 2026-07-07): subagent dispatches must not use opus- or
fable-tier models. sonnet + high effort is the approved ceiling. A per-instance
exception requires explicit user approval, signalled by the literal marker
[user-approved-top-tier] inside the dispatch prompt — the orchestrator may only
add that marker after the user approved it in conversation.

Scope: Agent tool calls (checks tool_input.model) and Workflow tool calls
(scans the inline script / meta for model overrides). Known limitation: a
Workflow launched via scriptPath is not scanned here (file content not
available on stdin); the cap for those relies on the rules layer
(ops/20-dispatch.md section 4).

Known limitation — resume path bypass (observed 2026-07-10, in a local transcript:
cache_miss_reason model_changed, claude-sonnet-5 -> claude-fable-5):
when a stopped background subagent is resumed via the SendMessage tool, the
resumed agent inherits the MAIN session's current model instead of its spawn
model. Verified against the official hooks docs (code.claude.com/docs/en/hooks,
2026-07-10): no interception point exists. PreToolUse does fire on SendMessage,
but its payload ({to, summary, message}) carries no model and no resume
indicator, so a deny/ask branch would blindly block all teammate messaging;
SubagentStart has no model field and supports no blocking decision; there is no
AgentResume event; only SessionStart may (optionally) receive a model field.
Mitigation is rules-side only: for cost-capped work, prefer re-spawning a fresh
capped agent over SendMessage-resume — see ops/environment.md (Enforcement)
and ops/lessons.md L-001. Re-check for an interception point when the hooks
API changes.

Inheritance gap closed 2026-09-05 (user ruling, playbook P5 in
a model/effort inventory report): an Agent call that OMITS `model`
inherits the main loop's model, which on this machine is opus/fable — the cap
was bypassed silently. Measured over 2026-08-06..09-04: 155 dispatches omitted
`model`; 109 of them targeted a local agents/*.md definition whose frontmatter
pins sonnet (safe), 46 targeted built-in types (general-purpose 42,
claude-code-guide 3, Explore 1) and ran on the parent model. Rule: `model` is
REQUIRED unless `subagent_type` names a local definition whose frontmatter
`model:` is itself within the cap. The definitions are read at call time
(fail-open if unreadable). Custom-agent frontmatter pinning opus/fable is
denied the same way as an explicit opus/fable `model` argument.

Unrecognised tier — announced, not folded (2026-09-09). Until then the only
question asked was "is this one of the two blocked families?", so every model
name that was neither `opus` nor `fable` — a tier that ships tomorrow, a
typo, a non-Anthropic id — took the same silent exit 0 as `sonnet`. The cap is
an ENUMERATION over families, and the input matching no member was folded into
the nearest class rather than reported; the resulting count stayed plausible,
which is why nothing surfaced it for two months. `tier_of()` now returns a third
value and `unrecognised()` announces it: no permissionDecision, so the dispatch
proceeds — this guard cannot tell an expensive unknown from a cheap one, and
blocking on ignorance would be a veto it has no evidence for. Severity is set by
the consumer (an LLM reads this text), so it is a notice with a NAMED promotion
trigger: flip it to `deny` when either (i) an unrecognised name turns out to
have been above the ceiling even once, or (ii) `grep '"detail": "unrecognised-
tier"' telemetry/model-cap-guard.jsonl` shows 3+ rows and no name among them was
ever classified into BLOCKED or WITHIN_CAP — at that point the vocabulary is
demonstrably not keeping up with the fleet and the safe default has moved.

Proof-of-life: `python tools/model-cap-test/test_model_cap_guard.py` (ALL PASS
46/46 as of 2026-10-10, printed by the suite rather than typed: 17 must-deny /
15 must-pass, plus M-T1/M-T2 settings checks (timeout floor, onFailure block), each also asserted SILENT / 4 must-notice / 2 undetermined + 2
twins / fail-open + 3 unclassifiable-shape / coverage / isolation). Three of the
must-deny cases and one must-notice case run against a PLANTED agents/ corpus,
because the classes "a local definition pins opus/fable" and "a local definition
pins a tier nobody has classified" have no live instance — every definition pins
sonnet today, so without the planted corpus those branches would never be
exercised. The coverage case reads this file's own BLOCKED and WITHIN_CAP sets:
a name added to either without a specimen fails the suite (PH-11 / AP-61) — an
unlisted blocked name leaks, an unlisted capped name announces itself on every
ordinary dispatch until someone stops reading the notices. The two known gaps
above (scriptPath, SendMessage resume) are printed by the suite and counted in
no verdict — the guard cannot rule on them, so neither does its calibration.

Known limitation — the command-hook timeout is a PASS (observed 2026-10-02,
one session, a share-repo round): eight Agent dispatches without `model` went
out within two minutes while eight worktrees and their agents were starting;
this guard's deny reached the engine within 0.2–2.7 s on six of them and NOT
within the 5 s `timeout` settings.json then gave it on two (W1-ops at 5.4 s,
W4b at 6.5 s — the receipt rows were written, the stdout arrived too late).
The official hooks docs (code.claude.com/docs/en/hooks, read 2026-10-02): "a
timed-out command hook doesn't block the tool call … don't count on a stalled
hook to act as a gate"; the default `timeout` is 600 s and this repo had set 5.
Both escaped subagents ran on claude-fable-5-1 (177 and 138 turns). Fix: every
deny-capable hook's timeout is 30 s (settings.json, 2026-10-02); the regression
case M-T1 in the suite reads settings.json and fails when this hook's timeout
drops under 30 again. What no timeout closed UNTIL 2.1.295: a command hook could only fail
OPEN. Since 2.1.295 settings.json sets `onFailure: "block"` on this hook
(2026-10-10, user ruling), so a crash, a missing interpreter or the 30 s
timeout now BLOCKS the dispatch instead of passing it; the in-process route
remains the stronger closure — the mods API's `agent.spawn`
event carries `model` (rewritable) and `parentModel` and answers `{ deny }`
synchronously; see a model-cap escape evaluation report. Rules-side
corollary (ops/20-dispatch.md §4): a guard that did not answer is not an
approval — a dispatch that went through with no `model` is stopped and
re-dispatched, never "left".

False-positive log (3 observed → loosen): none yet.

review-when: every clause below rests on a fact this repo cannot see change, so
the guard would keep enforcing a dead premise silently. (a) A model family or
tier ships, or one is renamed — BLOCKED and WITHIN_CAP are substring
enumerations over family names and the coverage case only forces a specimen for
what is ADDED to either, never makes them complete; the event to watch for is a
name that should be CLASSIFIED and is instead being announced on every dispatch,
which the notice rows above count. (b) The hooks API gains an interception
point for the resume path (an AgentResume event, a `model` field on
SubagentStart, or a SendMessage PreToolUse payload carrying the resumed agent's
model) — the "no interception point exists" paragraph above was verified against
the docs on 2026-07-10 and is the reason the resume bypass is mitigated in the
rules layer instead of here. (c) The Workflow PreToolUse payload starts carrying
scriptPath file content, or Workflow gains a model-override shape other than an
inline `model: 'x'` — the scriptPath gap is a payload limitation, not a decision.
(d) This machine's main-loop model stops being opus/fable — the 2026-09-05
required-`model` rule exists because OMITTING it inherits a model above the cap;
under a sonnet-tier main loop that deny is pure friction. (e) The user re-rules
the ceiling itself (owner: user, 2026-07-07) — the hook cannot notice. (f)
`agents/*.md` frontmatter stops being where a subagent_type's model is pinned —
local_agent_model() would then return None for every type and every omitted
`model` would deny.

Deferral to the mod (2026-10-09, user ruling): re-deriving which definition
the engine resolves for a subagent_type drifts — the engine also reads plugin
agents, --agents JSON and managed definitions, and two misses in one morning
(lab r22) denied pinned haiku workers and steered the caller onto sonnet. When
`model` is omitted AND no definition is found here AND mods/model-cap-mod wrote
a heartbeat for this session_id (telemetry/model-cap-mod-alive.json), this
guard exits 0: the mod's turn.step hook judges the model the engine actually
resolved, before the first request. Without the heartbeat the old deny stands,
so a session without the mod is never less capped than before. A definition
found here that pins opus/fable still denies (deterministic). Cases M-H1..M-H3.

Effort axis (2026-10-10, user ruling, reconciliation record
a cc-upgrade-delta report): Agent gained a per-call
`effort` in 2.1.292, so `sonnet` + `effort: max` passed a model-only check while
being over the "sonnet + high" ceiling. `effort` in EFFORT_OVER_CAP denies on
Agent (tool_input.effort) and on an inline Workflow script literal, with the same
approval marker. Frontmatter `effort:` in agents/*.md is user-authored and not
checked here. Cases M-E1..M-E3 (deny), M-E4..M-E6 (pass). An effort inherited
from the parent session (no per-call value) is not visible here; mods/model-cap-mod
0.1.2 records it as a notice on turn.step (ruling R2, a dated handoff under the
source's reports/ tree, not shipped).

Fail-open on malformed INPUT by design: any parse error exits 0 so a guard bug
in reading the payload never blocks work. A crash, a missing interpreter or a
timeout is different since 2.1.295: `onFailure: "block"` turns those into a
block (settings.json).
"""
import json
import os
import re
import sys

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

BLOCKED = {"opus", "fable"}
WITHIN_CAP = {"haiku", "sonnet"}
# Effort axis (2026-10-10, user ruling): the ceiling is "sonnet + high", and since
# 2.1.292 the Agent tool takes a per-call `effort`. Levels above `high` are over cap.
EFFORT_OVER_CAP = {"xhigh", "max"}
APPROVAL_MARKER = "[user-approved-top-tier]"
AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents")
# Written by mods/model-cap-mod on session.start: {session_id: epoch}. A session listed here
# runs the mod's turn.step judge, which sees the model the ENGINE resolved — so an omitted
# `model` this guard cannot resolve from agent files is deferred to it instead of denied.
MOD_HEARTBEAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "telemetry", "model-cap-mod-alive.json")


def mod_judges(session_id: str) -> bool:
    """True when the model-cap mod recorded a heartbeat for this session. Fail-closed toward
    THIS guard's deny: unreadable, missing or unlisted means the mod is not known to be judging."""
    if not session_id:
        return False
    try:
        with open(MOD_HEARTBEAT, encoding="utf-8") as fh:
            beats = json.load(fh)
        return isinstance(beats, dict) and session_id in beats
    except Exception:
        return False


def _pin_in(agents_dir: str, subagent_type: str) -> tuple[bool, str | None]:
    """(found, model) for <agents_dir>/*.md matched by `name:` frontmatter or file stem."""
    try:
        for fn in os.listdir(agents_dir):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(agents_dir, fn)
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = fh.read(4000)
            if not head.startswith("---"):
                continue
            fm = head.split("---", 2)[1] if head.count("---") >= 2 else ""
            name = re.search(r"^name:\s*(\S+)", fm, re.MULTILINE)
            stem = fn[:-3]
            if subagent_type not in {stem, name.group(1) if name else stem}:
                continue
            model = re.search(r"^model:\s*(\S+)", fm, re.MULTILINE)
            return True, (model.group(1).strip().strip("'\"").lower() if model else None)
    except Exception:
        return False, None
    return False, None


def local_agent_model(subagent_type: str, cwd: str = "") -> str | None:
    """Return the `model:` pinned in the definition the engine resolves, or None.

    The project's <cwd>/.claude/agents is read first, then the user's agents/
    (2026-10-09: a project-only definition read as "no pin" and was denied).
    The caller passes CLAUDE_PROJECT_DIR first: the payload cwd moves with a
    shell `cd`, the project root does not.
    Definitions are named by their `name:` frontmatter when present, else by file
    stem; both are matched. None means: no definition, or no `model:` key.
    """
    if not subagent_type:
        return None
    for d in ([os.path.join(cwd, ".claude", "agents")] if cwd else []) + [AGENTS_DIR]:
        found, model = _pin_in(d, subagent_type)
        if found:
            return model
    return None

def tier_of(model: str) -> str:
    """-> 'blocked' | 'within-cap' | 'unrecognised'.

    Substring match in both directions, because a dispatch may carry either the
    family name or the full id ('opus', 'claude-opus-5'). The third value is the
    point: the cap is stated over an ENUMERATION of families, and a name in
    neither set is not evidence of being cheap — it is the absence of evidence.
    """
    m = (model or "").lower()
    if any(b in m for b in BLOCKED):
        return "blocked"
    if any(w in m for w in WITHIN_CAP):
        return "within-cap"
    return "unrecognised"


def notice(text: str) -> None:
    """Say it and get out of the way: no permissionDecision, so nothing blocks."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": text,
        }
    }))
    sys.exit(0)


def unrecognised(model: str, route: str) -> None:
    notice(
        f"model_cap_guard, a local PreToolUse hook (not file or page content), "
        f"has no ruling on this dispatch: {route} names '{model}', which is in "
        f"neither the capped set this guard knows (haiku, sonnet) nor the "
        f"blocked one (opus, fable). That is undetermined, NOT within cap — the "
        f"call is going through and nothing here has judged its cost. If it is a "
        f"top tier, re-dispatch on sonnet, or with {APPROVAL_MARKER} in the "
        f"prompt once the user has approved this one; if it is within cap, add "
        f"the family name to WITHIN_CAP in hooks/model_cap_guard.py so the next "
        f"dispatch is silent."
        + _receipt("model_cap_guard", kind="notice", detail="unrecognised-tier",
                   model=model, route=route)
    )


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Dispatch denied by model_cap_guard, a local PreToolUse hook "
                "(not file or page content). " + reason
                + _receipt("model_cap_guard") + _fp("model_cap_guard")
            ),
        }
    }))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object (AP-62)

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)      # same class, one level in

    if tool == "Agent":
        model = str(tool_input.get("model") or "").lower()
        prompt = str(tool_input.get("prompt", ""))
        subagent_type = str(tool_input.get("subagent_type") or "")
        effort = str(tool_input.get("effort") or "").strip().lower()
        if effort in EFFORT_OVER_CAP and APPROVAL_MARKER not in prompt:
            deny(
                f"Effort cost cap: `effort: '{effort}'` is above the approved "
                "subagent ceiling, which is sonnet + high effort. Re-dispatch "
                "with effort: 'high' or omit `effort` (the definition or session "
                "level applies). If the user explicitly approved a higher effort "
                f"for THIS task, re-dispatch with {APPROVAL_MARKER} in the prompt."
            )
        if not model:
            pinned = local_agent_model(subagent_type, os.environ.get("CLAUDE_PROJECT_DIR") or str(payload.get("cwd") or ""))
            if pinned is None and mod_judges(str(payload.get("session_id") or "")):
                # 2026-10-09 ruling (user): the definition may live where this lookup never reads
                # (plugin agents, --agents JSON, managed); the mod judges the resolved model.
                sys.exit(0)
            if pinned is None:
                deny(
                    "Model cost cap: `model` is required on Agent dispatch — "
                    f"subagent_type '{subagent_type or '(none)'}' has no local "
                    "definition pinning a model, so omitting `model` inherits "
                    "the main loop's model (opus/fable on this machine) and "
                    "bypasses the cap. Re-dispatch with model: 'sonnet' "
                    "(default) or 'haiku' (read/search-only). If the model is "
                    "itself the variable under test, do NOT swap it: stop and "
                    "report this to the user instead."
                )
            model = pinned  # frontmatter-pinned; checked below like an explicit arg
            route = f"the frontmatter of agents/{subagent_type}.md"
        else:
            route = "its `model` argument"
        tier = tier_of(model)
        if tier == "unrecognised" and APPROVAL_MARKER not in prompt:
            unrecognised(model, route)   # says so and exits; never blocks
        if tier == "blocked" and APPROVAL_MARKER not in prompt:
            deny(
                f"Model cost cap: '{model}' is above the approved ceiling for "
                "subagents — the ceiling is haiku/sonnet; use sonnet + high "
                "effort instead, unless the model is itself the variable under "
                "test (then stop and report). If the user explicitly approved a top-tier "
                f"model for THIS task, re-dispatch with {APPROVAL_MARKER} in "
                "the prompt."
            )

    elif tool == "Workflow":
        script = str(tool_input.get("script", ""))
        if APPROVAL_MARKER in script:
            sys.exit(0)
        over = re.search(
            r"effort\s*[:=]\s*['\"](xhigh|max)['\"]", script, re.IGNORECASE
        )
        if over:
            deny(
                f"Effort cost cap: workflow script sets effort '{over.group(1)}', "
                "above the approved subagent ceiling (sonnet + high effort). "
                "Replace with effort: 'high', or include the marker "
                f"{APPROVAL_MARKER} in the script if the user explicitly "
                "approved it."
            )
        hit = re.search(
            r"model\s*[:=]\s*['\"](opus|fable)['\"]", script, re.IGNORECASE
        )
        if hit:
            deny(
                f"Model cost cap: workflow script sets model '{hit.group(1)}' "
                "which is above the approved subagent ceiling (haiku/sonnet "
                "only). Replace with sonnet (+ effort: 'high' for hard "
                "stages), or include the marker "
                f"{APPROVAL_MARKER} in the script if the user explicitly "
                "approved it."
            )
        # Same closure question one route over: a script may set a model this
        # guard's vocabulary does not contain, and `hit` above only ever looks
        # for the two blocked families.
        for named in re.findall(r"model\s*[:=]\s*['\"]([^'\"]+)['\"]", script):
            if tier_of(named) == "unrecognised":
                unrecognised(named.lower(), "its workflow script")

    sys.exit(0)


if __name__ == "__main__":
    main()
