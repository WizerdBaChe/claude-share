"""PreToolUse guard: enforce the subagent model cost cap (haiku/sonnet only).

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

Known limitation — resume path bypass (observed 2026-07-10 in a local
transcript: cache_miss_reason model_changed, claude-sonnet-5 -> claude-fable-5):
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

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.
"""
import json
import re
import sys

BLOCKED = {"opus", "fable"}
APPROVAL_MARKER = "[user-approved-top-tier]"


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    if tool == "Agent":
        model = str(tool_input.get("model", "")).lower()
        prompt = str(tool_input.get("prompt", ""))
        if model in BLOCKED and APPROVAL_MARKER not in prompt:
            deny(
                f"Model cost cap: '{model}' is above the approved ceiling for "
                "subagents (policy: haiku/sonnet only; use sonnet + high "
                "effort instead). If the user explicitly approved a top-tier "
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

    sys.exit(0)


if __name__ == "__main__":
    main()
