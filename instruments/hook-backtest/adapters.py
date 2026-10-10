r"""Predicates for hooks that do not expose one (tool, input) -> verdict function.

A hook's entry point is main() reading stdin and exiting, so a backtest needs a
function with the predicate signature. Each adapter below COMPOSES what the
hook module exports (payload_for, analyze, the compiled patterns, MARKER /
OVERRIDE) in the order its main() applies them. It never copies a regex or a
threshold: change the hook and the adapter measures the change.

Residual drift risk, named: the ORDER of the branches is restated here (which
tool goes where, which escape is checked first). When a hook's main() gains or
reorders a branch, its adapter must follow -- the calibration case in
tests/test_harness.py pins one known-true and one known-false input per
adapter against the live hook so a silent split shows up as a failed test.

Attributes on each function are the CLI defaults (hook_backtest.py reads them):
  tools          -- the tool names the hook is registered or measured on
  dedupe         -- "ts-head" | "content" (harness.DEDUPE)
  assistant_only -- record filter, see harness.iter_calls
"""
from harness import load_hook


def _attrs(tools, dedupe="ts-head", assistant_only=True):
    def deco(f):
        f.tools, f.dedupe, f.assistant_only = tools, dedupe, assistant_only
        return f
    return deco


@_attrs(("PowerShell", "Write", "Edit", "Bash"))
def ps_errorpref(tool, inp):
    """hooks/ps_errorpref_guard.py: native exe under EAP='Stop' without a check."""
    g = load_hook("ps_errorpref_guard")
    text, _label = g.payload_for(tool, inp)
    if not text or g.MARKER in text:
        return None
    return "fire" if g.analyze(text) else None


@_attrs(("PowerShell", "Write", "Edit", "Bash"))
def ps_pipeline_close(tool, inp):
    """hooks/ps_pipeline_close_guard.py as shipped (FIRE_TIERS); kind = tiers."""
    g = load_hook("ps_pipeline_close_guard")
    text, _label = g.payload_for(tool, inp)
    if not text or g.MARKER in text:
        return None
    f = g.analyze(text)
    return ",".join(f["tiers"]) if f else None


@_attrs(("Bash", "PowerShell", "Grep"), dedupe="content", assistant_only=False)
def secret_print(tool, inp):
    """hooks/secret_file_guard.py PROPERTY 2: a credential VALUE may not be printed.

    Mirrors main(): the OVERRIDE marker passes a shell command; a property-1
    name hit denies FIRST (that call is a property-1 fire, not counted here);
    then env-dump, then cred-grep. Grep: property 1 on the target, then a
    content-mode pattern naming a credential key over a config-shaped target.
    """
    g = load_hook("secret_file_guard")
    if tool in ("Bash", "PowerShell"):
        cmd = str(inp.get("command") or "")
        if g.OVERRIDE in cmd or g.hit(" " + cmd):
            return None
        s = g.MESSAGE_BODY.sub(" ", cmd)
        if g.env_dump(s):
            return "env-dump"
        if g.cred_grep_command(s):
            return "cred-grep"
        return None
    if tool == "Grep":
        target = inp.get("file_path") or inp.get("path") or ""
        if g.hit(" " + str(target)):
            return None
        if inp.get("output_mode") != "content":
            return None
        where = " ".join(str(inp.get(k) or "") for k in ("path", "glob", "type"))
        if g.CRED_KEY.search(str(inp.get("pattern") or "")) and g.CONFIG_SHAPED.search(where):
            return "cred-grep"
    return None
