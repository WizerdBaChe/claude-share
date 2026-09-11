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
reports/2026-09-05-model-effort-inventory.md): an Agent call that OMITS `model`
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

Proof-of-life: `python tools/model-cap-test/test_model_cap_guard.py` (37 cases
as of 2026-09-09, printed by the suite rather than typed: 14 must-deny / 12
must-pass, each also asserted SILENT / 4 must-notice / 2 undetermined + 2 twins
/ fail-open / coverage / isolation). Three of the
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

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.
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
APPROVAL_MARKER = "[user-approved-top-tier]"
AGENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents")


def local_agent_model(subagent_type: str) -> str | None:
    """Return the `model:` pinned in agents/<subagent_type>.md frontmatter, or None.

    Definitions are named by their `name:` frontmatter when present, else by file
    stem; both are matched. None means: no local definition, or no `model:` key.
    """
    if not subagent_type:
        return None
    try:
        for fn in os.listdir(AGENTS_DIR):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(AGENTS_DIR, fn)
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
            return model.group(1).strip().strip("'\"").lower() if model else None
    except Exception:
        return None
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
        if not model:
            pinned = local_agent_model(subagent_type)
            if pinned is None:
                deny(
                    "Model cost cap: `model` is required on Agent dispatch — "
                    f"subagent_type '{subagent_type or '(none)'}' has no local "
                    "definition pinning a model, so omitting `model` inherits "
                    "the main loop's model (opus/fable on this machine) and "
                    "bypasses the cap. Re-dispatch with model: 'sonnet' "
                    "(default) or 'haiku' (read/search-only)."
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
                "effort instead. If the user explicitly approved a top-tier "
                f"model for THIS task, re-dispatch with {APPROVAL_MARKER} in "
                "the prompt."
            )

    elif tool == "Workflow":
        script = str(tool_input.get("script", ""))
        if APPROVAL_MARKER in script:
            sys.exit(0)
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
