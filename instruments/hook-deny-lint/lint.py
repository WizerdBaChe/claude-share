r"""hook-deny-lint — shape check on every string a hook sends into a tool result.

Enforces rules/hook-deny-message.md over TWO surfaces (2026-09-09, F-8):

    block   permissionDecisionReason, a `block` reason   — text attached to a refusal
    notice  additionalContext, systemMessage             — text attached to nothing

The contract is a property of the TEXT, so it does not care whether the text
blocks anything; ruling on `block` alone left 12 messages in 8 hooks unchecked,
three of them carrying a defect the other surface would have failed on sight.
Which requirements bind which surface is the ruling recorded in the rule file
(R2/R3 are compensations for a BLOCKED call; the notice surface carries R2n and
R3n instead).

Run:
    python tools/hook-deny-lint/lint.py            # all hooks + all four controls
    python tools/hook-deny-lint/lint.py --hook X   # one hook (accepts a draft path)
    python tools/hook-deny-lint/lint.py --controls # calibration only
    python tools/hook-deny-lint/lint.py --dump     # every rendered message, verbatim

WHY STATIC, NOT BY EXECUTION. Two of the hooks cannot be made to deny in a test
without a side effect the environment then has to adjudicate (browser_pane's
deny appends a `"loud": true` telemetry row that the integrity sweep surfaces
for the USER). Reading the text out of the AST has no side effects and covers
sites no synthetic payload would reach.

WHAT THIS INSTRUMENT CANNOT DETERMINE (downgrade-and-forward, never veto):
whether a sentence a human would call an unverifiable identity claim is one.
That needs meaning. The FAIL checks are therefore all structural — a literal
token, a path governed by a read-verb, an interpolated copular assertion, a
missing self-identification. Everything else is emitted as WARN with the span
quoted, for the author to rule on. A gate that vetoed on the semantic question
would be ruling on what it cannot see.

CALIBRATION IS TWO-SIDED PER SURFACE AND PRINTS ON EVERY RUN. block known-bad is
the verbatim 2026-08-29 deny text recovered from git 7836b74^ — the message two
subagents correctly classified as prompt injection; block known-good is the
current transcript_read_guard text. The notice pair was authored on 2026-09-09
with the surface, and its known-bad is required to fail EVERY notice-side check
(P1, P2, R1, R2n, R3n): a check with no known-true positive is an assertion
about new code, not a control. A run that does not print all four controls, or
where a known-bad passes, is reporting nothing.

WHERE A MESSAGE IS REPORTED. At the site that EMITS it, never at the line of the
builder that composed the words — two hooks put the hook's identity and its
receipt on the transport, so the text a reader receives is prefix + built text +
suffix. Builder calls (`notice(compose(...))`, `deny(deny_reason(...))`,
`hs.notice(...)` across modules), `.format()`, `%`, and `SEP.join(parts)` are
resolved inline for that reason. A message assembled across branches is checked
as the UNION of its branches: sound for the prohibitions, an over-approximation
for the requirements, and the summary line says so.
"""
import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = ROOT / "hooks"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# --------------------------------------------------------------------------
# Extraction: pull deny-message text out of the AST.
# --------------------------------------------------------------------------

# TWO SURFACES, NAMED (F-8, 2026-09-09). A hook sends agent-facing text through
# two shapes of channel, and the contract is a property of the TEXT, not of the
# channel: `block` = text attached to a refusal, `notice` = text attached to
# nothing, which arrives in the tool result all the same. Ruling on only the
# first left 9 sites in 8 hooks unchecked — the object-vocabulary failure of
# ops/lessons.md L-044, in this instrument's own design.
BLOCK_KEYS = ("permissionDecisionReason",)
NOTICE_KEYS = ("additionalContext", "systemMessage")
SURFACE_KEYS = {"block": BLOCK_KEYS, "notice": NOTICE_KEYS}
# A helper that prints one surface is named for it. Both prefixes are checked
# against the same registry so a notice helper resolves exactly as `deny` does;
# without that, 8 of the 9 notice sites render UNRESOLVED and the extension
# rules on nothing.
SURFACE_PREFIX = {"deny": "block", "notice": "notice"}
SURFACES = ("block", "notice")

# MEASURED BUT NOT RULED ON (F-9, 2026-09-09). A third transport carries hook
# text into an agent's context: bare stdout of a SessionStart or
# UserPromptSubmit hook, which the harness injects verbatim. Their text is
# composed from file data at runtime, so a static render would be mostly
# UNRESOLVED — this instrument would look extended while ruling on nothing. It
# is named in the summary line so the gap is reported rather than implied.
#
# The entry list is READ from settings.json on every run, never written here:
# the count was hand-copied into four places (this comment said 8, the summary
# constant 10, the rule file 10, the registry 7) and all four were stale by
# 2026-09-23, when settings.json held 12. The rule file and the registry now
# name this summary line as the live count instead of carrying a number.
UNRULED_EVENTS = ("SessionStart", "UserPromptSubmit")


def unruled_transport(settings: Path | None = None) -> str:
    """The F-9 summary clause, with the entry list as settings.json has it now."""
    import json
    settings = settings or (ROOT / "settings.json")
    try:
        hooks = json.loads(settings.read_text(encoding="utf-8")).get("hooks") or {}
        names = []
        for event in UNRULED_EVENTS:
            for group in hooks.get(event) or []:
                for h in group.get("hooks") or []:
                    parts = str(h.get("command", "")).replace('"', "").split()
                    script = next((p for p in parts if p.endswith(".py")), None)
                    label = Path(script).stem if script else (parts[0] if parts else "?")
                    extra = parts[parts.index(script) + 1:] if script else []
                    names.append(" ".join([label] + extra))
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        return ("bare stdout of SessionStart/UserPromptSubmit hooks (harness-injected): "
                "entry count undetermined (%s: %s), not ruled on (F-9)" % (type(exc).__name__, exc))
    return ("bare stdout of SessionStart/UserPromptSubmit hooks (harness-injected): "
            "%d entries in settings.json (%s), not ruled on (F-9)" % (len(names), ", ".join(names)))

UNRESOLVED = "\x00UNRESOLVED\x00"


def _msg_surface(node) -> str:
    """'block' | 'notice' | '' for `deny…`/`notice…`, as a call or a def."""
    name = (getattr(node, "id", None) or getattr(node, "attr", None)
            or getattr(node, "name", None) or "")
    for prefix, surface in SURFACE_PREFIX.items():
        if name.startswith(prefix):
            return surface
    return ""


class Scope:
    """One function body (or the module) plus the names bound inside it."""

    def __init__(self, consts: dict, multi: dict, lists=None, builders=None,
                 aliases=None, path=None):
        self.consts = dict(consts)
        self.multi = dict(multi)
        # `parts = [...]` + `parts.append(...)`: the shape every composed
        # message in this environment uses. Held per scope so `" ".join(parts)`
        # renders instead of dropping the whole message.
        self.lists = dict(lists or {})
        # name -> FunctionDef, for the builders a message expression calls.
        self.builders = dict(builders or {})
        self.aliases = dict(aliases or {})
        self.path = path


def render(node, scope: Scope, depth=0):
    """Render a message expression to text. Returns (text, resolved: bool).

    A runtime placeholder becomes `{name}` — the shape checks care where an
    interpolation sits, not what it will hold. A name bound from a module-level
    table of alternatives expands to every alternative (see `multi`).
    """
    if node is None:
        return "", True
    if isinstance(node, ast.Constant):
        return (node.value, True) if isinstance(node.value, str) else (UNRESOLVED, False)
    if isinstance(node, ast.JoinedStr):
        out, ok = [], True
        for part in node.values:
            text, good = render(part, scope, depth)
            out.append(text)
            ok = ok and good
        return "".join(out), ok
    if isinstance(node, ast.FormattedValue):
        inner = node.value
        name = getattr(inner, "id", None)
        if name and name in scope.consts:
            return scope.consts[name], True
        if name and name in scope.multi:
            return "\x01" + name + "\x01", True      # expanded by callers
        return "{%s}" % (name or _dotted(inner) or ""), True
    if isinstance(node, ast.Call):
        text = _shared_clause(node, scope)
        if text is not None:
            return text, True
        text, ok = _render_call(node, scope, depth)
        if text is not None:
            return text, ok
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, lok = render(node.left, scope, depth)
        right, rok = render(node.right, scope, depth)
        return left + right, lok and rok
    # `"template %s" % (...)`: the operands are runtime values and `%s` is
    # already the placeholder convention this renderer uses, so the template
    # IS the renderable text. Without this, every message ps_errorpref_guard
    # and ps_pipeline_close_guard compose drops out of the check.
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return render(node.left, scope, depth)
    # `x if cond else ""` is an OPTIONAL FRAGMENT of a message. It is rendered
    # as PRESENT: the reader may receive it, so it is text this instrument must
    # look at. Rendering it as absent would let a fragment carry the costume
    # unchecked (published_record_guard's line hint).
    if isinstance(node, ast.IfExp):
        text, ok = render(node.body, scope, depth)
        if ok and text != UNRESOLVED:
            return text, True
        return render(node.orelse, scope, depth)
    if isinstance(node, ast.Name):
        if node.id in scope.consts:
            return scope.consts[node.id], True
        if node.id in scope.multi:
            return "\x01" + node.id + "\x01", True
        return UNRESOLVED, False
    return UNRESOLVED, False


MAX_BUILDER_DEPTH = 3


def _render_call(node, scope: Scope, depth=0):
    """(text, resolved) for the three call shapes a message is built with.

    Returns (None, False) when the call is none of them, so `render` can fall
    through to its own verdict.
    """
    func = node.func
    attr = getattr(func, "attr", "")

    # `TEMPLATE.format(hits=…)` — the braces in TEMPLATE are the placeholders,
    # so rendering the receiver is the faithful text (appdata_view_guard).
    if attr == "format":
        return render(func.value, scope, depth)

    # `"; ".join(problems)` where `problems` is a list built by appends. The
    # union of every appended branch is reported: for a PROHIBITION that is
    # sound (a costume in any branch is a costume), for a REQUIREMENT it is an
    # over-approximation, which is why composed messages are marked as such.
    if attr == "join" and node.args:
        sep, sep_ok = render(func.value, scope, depth)
        parts = _list_items(node.args[0], scope, depth)
        if sep_ok and parts is not None:
            return sep.join(parts), True
        # A joined PARAMETER is runtime data (published_record_guard joins the
        # matched class names). Placeholder, exactly as an f-string
        # interpolation is: the shape checks care where it sits, not its value.
        if sep_ok and isinstance(node.args[0], ast.Name):
            return "{%s}" % node.args[0].id, True

    # A local (or imported-hook) text builder: `reason(...)`, `compose(...)`,
    # `hs.notice(...)`.
    if depth < MAX_BUILDER_DEPTH:
        alts = _builder_alternatives(node, scope, depth + 1)
        if alts:
            if len(alts) == 1:
                return alts[0], True
            key = "\x03%s" % (getattr(func, "id", None) or attr)
            scope.multi[key] = alts
            return "\x01" + key + "\x01", True
    return None, False


def _list_items(node, scope: Scope, depth=0):
    """Rendered elements of a list literal or of a name bound to one."""
    if isinstance(node, ast.Name):
        return scope.lists.get(node.id)
    if isinstance(node, (ast.List, ast.Tuple)):
        out = []
        for elt in node.elts:
            text, ok = render(elt, scope, depth)
            if ok and text != UNRESOLVED:
                out.append(text)
        return out
    return None


def _builder_target(node, scope: Scope):
    """(FunctionDef, its module scope) for a call that builds message text."""
    func = node.func
    name = getattr(func, "id", None)
    if name and name in scope.builders:
        return scope.builders[name], scope
    # `import handoff_snapshot as hs` … `hs.notice(...)`: the emitting hook is
    # the one that owns the text, so it is rendered at the CALL site here.
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        mod = scope.aliases.get("mod:" + func.value.id)
        if mod:
            info = _module_info(HOOKS_DIR / (mod + ".py"))
            if info and func.attr in info.builders:
                return info.builders[func.attr], info
    return None, None


def _builder_alternatives(node, scope: Scope, depth):
    """One rendered text per `return` in the builder ('' returns dropped)."""
    fnode, fscope = _builder_target(node, scope)
    if fnode is None:
        return []
    inner = Scope(fscope.consts, fscope.multi, fscope.lists, fscope.builders,
                  fscope.aliases, fscope.path)
    _collect_assigns(fnode.body, inner)
    _collect_lists(fnode.body, inner)
    out = []
    for stmt in fnode.body:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Return) and sub.value is not None:
                text, ok = render(sub.value, inner, depth)
                if ok and text != UNRESOLVED and text.strip():
                    for expanded in _expand(text, inner):
                        if expanded not in out:
                            out.append(expanded)
    return out


sys.path.insert(0, str(HOOKS_DIR))
try:
    import deny_receipt as _dr
except Exception:                       # pragma: no cover - lint still runs
    _dr = None

# The two shared sentence builders every conforming hook appends. Rendered
# through the real module (pure template form — no telemetry row is written),
# so the lint checks the text that is actually emitted rather than declaring
# every conforming hook unreadable.
_RECEIPT_FNS = {"clause", "_receipt_clause"}
_FP_FNS = {"fp_clause", "_fp_clause"}
_NOTICE_FNS = {"notice_clause"}
_ALIASES = {}       # local name -> deny_receipt name, per file being linted


def _load_aliases(tree) -> dict:
    """`from deny_receipt import clause as _receipt` — follow the local name.

    Without this the hooks that adopt the shared helpers read as unresolved,
    i.e. adopting the contract would remove a hook from the check. `mod:<name>`
    rows record `import handoff_snapshot as hs`, so a message built by another
    hook module can be rendered at the site that emits it.
    """
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("deny_receipt"):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if (HOOKS_DIR / (alias.name + ".py")).is_file():
                    aliases["mod:" + (alias.asname or alias.name)] = alias.name
    _ALIASES.clear()
    _ALIASES.update(aliases)
    return aliases


def _shared_clause(node, scope=None):
    name = getattr(node.func, "id", None) or getattr(node.func, "attr", "")
    table = getattr(scope, "aliases", None) or _ALIASES
    name = table.get(name, name)
    if _dr is None or name not in (_RECEIPT_FNS | _FP_FNS | _NOTICE_FNS):
        return None
    arg = node.args[0] if node.args else None
    hook = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else "{hook}"
    if name in _NOTICE_FNS:
        # arg 2 is the telemetry file stem when it differs from the hook name.
        log = node.args[1].value if len(node.args) > 1 and isinstance(
            node.args[1], ast.Constant) else ""
        kw = {k.arg: k.value for k in node.keywords if isinstance(k.value, ast.Constant)}
        if not log and "log" in kw:
            log = kw["log"].value
        return _dr.notice_clause(hook, log)
    return _dr.fp_clause(hook) if name in _FP_FNS else _dr.clause_template(hook)


def _dotted(node):
    if isinstance(node, ast.Attribute):
        return getattr(node.value, "id", "") + "." + node.attr
    return ""


def _collect_assigns(body, scope: Scope) -> None:
    """Bind simple `NAME = <renderable>` in this scope (module or function).

    Also `a, b = builder(...)`: the message half of a builder that returns a
    (decision, text) pair reaches the emit site only through that name
    (dispatch_commit_notice, published_record_guard).
    """
    for stmt in body:
        # A `try:` or `with` body runs unconditionally, so a name bound there is
        # bound for the message below it — dispatch_commit_notice's emit site
        # reads its text from a name assigned inside `try:`. Branch bodies (`if`)
        # are deliberately NOT followed: binding one arm would silently pick a
        # winner among alternatives.
        if isinstance(stmt, (ast.Try, ast.With)):
            _collect_assigns(stmt.body, scope)
            continue
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if isinstance(target, ast.Name):
            text, ok = render(stmt.value, scope)
            if ok and text != UNRESOLVED:
                scope.consts[target.id] = text
        elif isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Call):
            _bind_tuple(target, stmt.value, scope)


def _bind_tuple(target, call, scope: Scope) -> None:
    """`decision, text = decide(payload)` -> bind each name positionally."""
    fnode, fscope = _builder_target(call, scope)
    if fnode is None:
        return
    inner = Scope(fscope.consts, fscope.multi, fscope.lists, fscope.builders,
                  fscope.aliases, fscope.path)
    _collect_assigns(fnode.body, inner)
    _collect_lists(fnode.body, inner)
    columns = {}
    for stmt in fnode.body:
        for sub in ast.walk(stmt):
            if not (isinstance(sub, ast.Return) and isinstance(sub.value, (ast.Tuple, ast.List))):
                continue
            for pos, elt in enumerate(sub.value.elts):
                text, ok = render(elt, inner, 1)
                if ok and text != UNRESOLVED and text.strip():
                    for expanded in _expand(text, inner):
                        if expanded.strip():
                            columns.setdefault(pos, [])
                            if expanded not in columns[pos]:
                                columns[pos].append(expanded)
    for pos, name in enumerate(target.elts):
        values = columns.get(pos)
        if isinstance(name, ast.Name) and values:
            if len(values) == 1:
                scope.consts[name.id] = values[0]
            else:
                scope.multi[name.id] = values


def _collect_lists(body, scope: Scope) -> None:
    """Bind `parts = [...]` plus every `parts.append(<renderable>)`.

    Branches are collected together: a composed message's alternatives all
    reach the same reader, and the union is what this instrument can determine.
    """
    for stmt in body:
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Assign) and len(sub.targets) == 1 \
                    and isinstance(sub.targets[0], ast.Name) \
                    and isinstance(sub.value, (ast.List, ast.Tuple)):
                items = _list_items(sub.value, scope)
                if items is not None:
                    scope.lists[sub.targets[0].id] = list(items)
            elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                    and sub.func.attr == "append" and isinstance(sub.func.value, ast.Name) \
                    and sub.args:
                text, ok = render(sub.args[0], scope)
                if ok and text != UNRESOLVED:
                    scope.lists.setdefault(sub.func.value.id, []).append(text)


_MODULE_CACHE = {}


def _module_info(path: Path):
    """Module scope + builder table for another hook file (cached)."""
    key = str(path)
    if key in _MODULE_CACHE:
        return _MODULE_CACHE[key]
    _MODULE_CACHE[key] = None                 # guards a cyclic import chain
    if not path.is_file():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None
    scope = Scope({}, {}, path=path)
    scope.aliases = _load_aliases(tree)
    scope.builders = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    _collect_assigns(tree.body, scope)
    _collect_tables(tree, scope)
    _collect_lists(tree.body, scope)
    _MODULE_CACHE[key] = scope
    return scope


def _collect_tables(tree, scope: Scope) -> None:
    """Bind `for a, b, reason in TABLE:` to every string at that position.

    dangerous_command_guard's rule reasons live in a module-level list of
    tuples and reach the deny text through the loop variable; without this the
    lint would report eight sites as unresolved and check none of them.
    """
    tables = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            if isinstance(stmt.value, (ast.List, ast.Tuple)):
                tables[stmt.targets[0].id] = stmt.value.elts
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        src = getattr(node.iter, "id", None)
        if src not in tables or not isinstance(node.target, ast.Tuple):
            continue
        for pos, tgt in enumerate(node.target.elts):
            if not isinstance(tgt, ast.Name):
                continue
            values = []
            for row in tables[src]:
                if isinstance(row, (ast.Tuple, ast.List)) and pos < len(row.elts):
                    text, ok = render(row.elts[pos], scope)
                    if ok and text != UNRESOLVED and text.strip():
                        values.append(text)
            if values:
                scope.multi[tgt.id] = values


def _msg_exprs(body, wraps=None):
    """[(expr, surface)] in this statement list, not descending into defs.

    Each expression carries the prefix/suffix its helper will wrap around it,
    so the checked text is what the tool result actually receives.
    """
    wraps = wraps or {}
    found = []
    for stmt in body:
        # Function bodies are scanned in their own scope pass; walking into
        # them from the module level emitted each helper's own dict as if it
        # were a separate message (17 phantom sites for one 2-site hook).
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(stmt):
            if isinstance(node, ast.FunctionDef) and node is not stmt:
                continue
            if isinstance(node, ast.Dict):
                keys = {k.value: v for k, v in zip(node.keys, node.values)
                        if isinstance(k, ast.Constant)}
                for surface in SURFACES:
                    for key in SURFACE_KEYS[surface]:
                        if key in keys:
                            found.append((keys[key], surface))
                if "reason" in keys and isinstance(keys.get("decision"), ast.Constant) \
                        and keys["decision"].value == "block":
                    found.append((keys["reason"], "block"))
            elif isinstance(node, ast.Call) and _msg_surface(node.func):
                fname = getattr(node.func, "id", None) or getattr(node.func, "attr", "")
                # Only a registered pass-through helper receives message TEXT.
                # A builder like `deny_reason(host, entry)` receives data, and
                # its message is its return value, scanned in its own scope —
                # collecting its args reported `host` as an unreadable message.
                if fname not in wraps:
                    continue
                for arg in node.args:
                    # `deny(deny_reason(...))` is kept: the inner builder now
                    # resolves inline (`_builder_alternatives`). Skipping it —
                    # which was right while builders were scanned at their own
                    # `return` — dropped browser_pane_scope_guard's only deny
                    # message out of the check entirely.
                    arg._denywrap = wraps[fname][:2]
                    found.append((arg, wraps[fname][2]))
            elif isinstance(node, ast.Return) and node.value is not None:
                pass  # handled per-function below
    return found


def _surface_key_sites(tree) -> bool:
    """True when this file itself prints a dict carrying a surface key."""
    keys = {k for surface in SURFACES for k in SURFACE_KEYS[surface]}
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and k.value in keys:
                    return True
            if any(isinstance(k, ast.Constant) and k.value == "decision" for k in node.keys):
                return True
    return False


PARAM = "\x02"


def _flatten_add(node):
    """`a + b + c` -> [a, b, c] (a left-nested Add chain, one level deep)."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _flatten_add(node.left) + _flatten_add(node.right)
    return [node]


def _render_all(nodes, scope: Scope) -> str:
    out = []
    for node in nodes:
        text, ok = render(node, scope)
        out.append(text if ok and text != UNRESOLVED else "")
    return "".join(out)


def _transforms(tree, module: Scope):
    """Prefix/suffix a `deny(reason)` helper wraps around its caller's text.

    `deny(reason)` bodies commonly emit `reason + " Per-instance override: …"`.
    Checking the call-site string alone reports the helper's suffix as missing
    — extdispatch_entrypoint_guard was scored "no retry mechanics" for exactly
    that reason, when the retry mechanic is in the suffix. The emitted message
    is prefix + call-site + suffix, so that is what gets checked.
    """
    out = {}
    for node in tree.body:
        surface = _msg_surface(node) if isinstance(node, ast.FunctionDef) else ""
        if not surface:
            continue
        params = [a.arg for a in node.args.args]
        if not params:
            continue
        scope = Scope(module.consts, module.multi, module.lists, module.builders,
                      module.aliases, module.path)
        for expr, _surf in _msg_exprs(node.body):
            # A wrapper passes its caller's text through as a BARE name:
            # `reason` or `reason + "<suffix>"`. A message that merely
            # INTERPOLATES its parameters (`f"...{target}..."`) is the message
            # itself and must be checked here, not skipped as a wrapper.
            if isinstance(expr, ast.Name) and expr.id in params:
                out[node.name] = ("", "", surface)
                break
            # `"prefix " + reason + receipt() + fp()` parses as a nested Add
            # chain, so the parameter is not an immediate operand — flatten
            # first, or a helper that gained a prefix silently stops being
            # recognised and every call site drops out of the check.
            operands = _flatten_add(expr)
            hit = next((i for i, op in enumerate(operands)
                        if isinstance(op, ast.Name) and op.id in params), None)
            if hit is not None:
                out[node.name] = (_render_all(operands[:hit], scope),
                                  _render_all(operands[hit + 1:], scope), surface)
                break
    return out


def messages_of(path: Path):
    """[(lineno, text, resolved, surface)] for every message a hook can emit."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    module = Scope({}, {}, path=path)
    module.aliases = _load_aliases(tree)
    module.builders = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    _collect_assigns(tree.body, module)
    _collect_tables(tree, module)
    _collect_lists(tree.body, module)
    wraps = _transforms(tree, module)

    sites, seen = [], set()

    def emit(node, scope, surface, wrap=("", "")):
        text, ok = render(node, scope)
        if text == UNRESOLVED:
            rendered_all = [UNRESOLVED]
        else:
            rendered_all = [wrap[0] + t + wrap[1] for t in _expand(text, scope)]
        for rendered in rendered_all:
            key = (node.lineno, rendered, surface)
            if key in seen:
                continue
            seen.add(key)
            sites.append((node.lineno, rendered, ok and rendered != UNRESOLVED, surface))

    # EVERY message is reported at the site that EMITS it, never at the line of
    # the builder that composed the words. Two hooks now carry the hook's
    # identity and its receipt on the TRANSPORT, so the emitted text is
    # prefix + built text + suffix: checking a builder's own `return` line
    # scored ps_errorpref_guard "no actor named" while the actor sat in the
    # sentence the transport prepends. It also stops one message from being
    # counted twice (dispatch_commit_notice reported its notice at both lines).
    # Builder calls resolve inline instead — see `_builder_alternatives`.
    def walk_scope(body, scope, fn_name=None):
        _collect_assigns(body, scope)
        _collect_lists(body, scope)
        # A helper that only wraps its caller's text is not itself a message.
        if fn_name in wraps:
            return
        for node, surface in _msg_exprs(body, wraps):
            emit(node, scope, surface, _wrap_for(node, wraps))

    walk_scope(tree.body, module)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            inner = Scope(module.consts, module.multi, module.lists,
                          module.builders, module.aliases, module.path)
            walk_scope(node.body, inner, fn_name=node.name)
    return sorted(sites)


def _wrap_for(node, wraps):
    return getattr(node, "_denywrap", ("", ""))


def _expand(text: str, scope: Scope):
    """One rendered message per alternative of a table-bound placeholder."""
    if "\x01" not in text:
        return [text]
    name = text.split("\x01")[1]
    return [text.replace("\x01%s\x01" % name, v) for v in scope.multi.get(name, ["{%s}" % name])]


# --------------------------------------------------------------------------
# Checks. FAIL = structural and determinable. WARN = needs a human ruling.
# --------------------------------------------------------------------------

RULE_ID = re.compile(r"(?m)(?:^|\A)\s*[A-Z]{1,4}-\d+[a-z]?\b[^\n:]{0,20}:")
POLICY = re.compile(r"(?i)\bpolic(?:y|ies)\s*:")

# A path token must be RECOGNISABLE as a path, not merely contain a slash:
# either anchored (~, a drive, a known root dir of this environment) or
# carrying a known extension. Without the anchor list, English with a slash in
# it ("compaction/digesting") matches and the finding cites the wrong span —
# the verdict may still be right, but an instrument that prints the wrong
# evidence cannot be audited, so it is not a usable instrument.
_SEG = r"[\w.~*{}-]+"
_ROOTS = (r"ops|rules|references|skills|hooks|tools|telemetry|cache|reports|"
          r"memory-archive|outputs|projects|agents|connectors|digests")
PATH = (r"(?:(?:~|\{[A-Za-z_.]*\}|[A-Za-z]:)[/\\]?%(seg)s(?:[/\\]%(seg)s)*"
        r"|\b(?:%(roots)s)[/\\]%(seg)s(?:[/\\]%(seg)s)*"
        r"|\b[\w.~-]+\.(?:md|py|txt|json|jsonl|example|yml|yaml)\b)"
        % {"seg": _SEG, "roots": _ROOTS})
BARE_PATH = re.compile(PATH)
BACKTICKED = re.compile(r"`[^`]*`")

# The three determinable read-elsewhere shapes (rules/hook-deny-message.md P2).
# `(?<![-\w])` and `(?![-\w])`: a verb inside a hyphenated filename is not a
# verb — `transcript-read-guard.jsonl` is not an instruction to read anything.
_V = r"(?<![-\w])(?:%s)(?![-\w])"
POINTER_FORM = re.compile(r"(?im)" + (_V % r"details?|reference|refer to|see also")
                          + r"\s*:?\s+" + PATH)
READ_VERB = re.compile(r"(?i)" + (_V % r"read|see|consult|refer to")
                       + r"[^\n]{0,25}?" + PATH)
# The measured habit: all four violators point into this environment's own
# knowledge base. That set is a literal list, so it is determinable.
KB_PATH = re.compile(r"(?i)(?:~[/\\]\.claude|\b(?:ops|rules|references|skills|memory-archive)"
                     r"[/\\])[\w.~/\\-]*")

# A verb must IMMEDIATELY govern the path (<=25 chars) to count as a redirect
# or a receipt. The known-bad's "Grep a specific term (<=3 hits, small -C) in
# the digest card under <dir>" puts 66 chars between them: that is a pointer
# to another directory wearing a command's clothes, not a redirect.
GOVERNS = 25
RECEIPT = re.compile(r"(?i)\b(?:saved|written|recorded|logged|appended|receipt)\b[^\n]{0,%d}?%s"
                     % (GOVERNS, PATH))
RUN_TARGET = re.compile(r"(?i)\b(?:python|run|use|write|node|npx|grep|echo|cat|git)\b"
                        r"[^\n]{0,%d}?%s" % (GOVERNS, PATH))
# A path named as the OBJECT of the constraint ("ops/lessons.md is tool-owned")
# is the denied target, not a place to go read. Without this exemption the lint
# forbids a guard from naming what it gates — intake_guard was scored P2 for
# saying which files it owns.
TARGET_PREDICATE = re.compile(
    r"(?i)%s[^\n]{0,40}?\b(?:is|are)\s+(?:tool-owned|gated|blocked|denied|protected|"
    r"not gated|owned by|the target)" % PATH)
IDENTITY = re.compile(r"(?:\{[A-Za-z_.]*\}|\{\})\s+is\s+an?\b")
OUTPUT_DIRECTIVE = re.compile(
    r"(?i)\b(?:report this to the user|tell the user|inform the user|in your reply)\b")
RETRY = re.compile(
    r"(?i)\b(?:re-run|re-issue|re-dispatch|retry|instead|use|override|marker|"
    r"offset|split the command)\b")
# Two accepted forms of the misfire exit: the shared reporter, or a hook that
# reports itself (`--report`, as published_record_guard already shipped).
FP_EXIT = re.compile(r"report_fp\.py|--report\b")
FIRST_CLAUSE = 200

# --- the notice surface's two requirements (H-1, 2026-09-09) ---------------
# A notice blocks nothing, so R2's "how to proceed" and R3's "how to get
# unblocked" have no subject: there is nothing to unblock. What survives the
# downgrade is stated as R2n and R3n, and the rule file records which surface
# each requirement binds.
#
# R2n — say what the reader may DO about it. An explicit "nothing needs doing"
# satisfies it; silence does not. Wider vocabulary than RETRY because a notice's
# action is an ordinary imperative ("run it through the PowerShell tool"), not a
# retry of a blocked call.
ACTION = re.compile(
    r"(?i)\b(?:re-run|re-issue|re-dispatch|retry|instead|use|using|override|"
    r"marker|offset|split|run|prefix|route|rerun|add|check|confirm|verify|"
    r"read|write|rewrite|save|scope|ask|keep|stop|wait|drop|remove|"
    r"carry on|carries on|proceed|proceeds|going through|"
    r"nothing (?:you|to|here|needs|is)|no action|need not|does not block)\b")
# R3n — name the receipt this notice left. A notice is a pure claim with no
# refusal to make the reader suspicious, so the row is the only thing about it
# a reader can check sideways: injected text cannot write a local file. The
# nonce form (deny_receipt.clause) is stronger than naming the file alone,
# which pins the class of row and not the row; both are accepted, and the
# difference is stated in rules/hook-deny-message.md.
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def situation_text(text: str) -> str:
    """The message minus its provenance sentences, for the R2n check.

    R2n asks what the reader can do about the SITUATION. The receipt sentence
    R3n requires says "grep it there to confirm … cannot write a local file",
    which contains three action verbs and made R2n pass on every notice that
    carried a receipt — measured by probe I-4, which could not make R2n fire on
    a notice stripped of every actionable sentence. A requirement satisfied by
    the text that satisfies a different requirement is not a check.
    """
    keep = [s for s in SENTENCE.split(text)
            if not RECEIPT.search(s) and not FP_EXIT.search(s)]
    return " ".join(keep)


NOTICE_REQUIRED = {"R2n": (ACTION, situation_text), "R3n": (RECEIPT, None)}
BLOCK_REQUIRED = {"R2": (RETRY, None), "R3": (FP_EXIT, None)}
REQUIRED_DETAIL = {
    "R2": "no retry mechanics",
    "R3": "no false-positive exit",
    "R2n": "says nothing the reader can do about it (an explicit "
           "'nothing to do' counts)",
    "R3n": "names no receipt — nothing in it can be checked sideways",
}


def self_id_tokens(stem: str):
    """Names that count as the hook identifying itself.

    The bare stem-without-suffix is deliberately NOT one of them: `intake` on
    its own matched the phrase "an intake record" and scored intake_guard as
    self-identified when it names no actor at all.
    """
    base = stem[:-6] if stem.endswith("_guard") else stem
    return {stem, stem.replace("_", "-"), stem.replace("_", " "),
            base.replace("_", "-") + " guard", base.replace("_", " ") + " guard"}


def check(text: str, stem: str, surface: str = "block"):
    """(fails, warns) for one message. Codes match rules/hook-deny-message.md.

    The four prohibitions and R1 bind BOTH surfaces — the costume is a property
    of the text, and a notice wears it more easily precisely because it blocks
    nothing, so nobody writing it feels they are refusing anything. Only the
    two compensating requirements differ (see NOTICE_REQUIRED).
    """
    fails, warns = [], []
    head = text[:FIRST_CLAUSE]

    if POLICY.search(text):
        fails.append(("P1", _span(POLICY, text)))
    elif RULE_ID.search(text):
        fails.append(("P1", _span(RULE_ID, text)))

    # A backticked token is a literal to type or run, not a document to go
    # read — `tools/ui-shot` in "the one-shot `tools/ui-shot` probe" was scored
    # as a read-elsewhere pointer because the word "read" happened to sit
    # nearby. The explicit `Detail:`/`See` forms are still checked on the raw
    # text, so backticks cannot be used to smuggle a pointer past the rule.
    masked = BACKTICKED.sub(lambda m: " " * len(m.group(0)), text)

    p2 = None
    if POINTER_FORM.search(text):
        p2 = _span(POINTER_FORM, text)
    elif READ_VERB.search(masked):
        p2 = _span(READ_VERB, masked)
    if p2 is None:
        for m in KB_PATH.finditer(masked):
            around = masked[max(0, m.start() - GOVERNS - 12):m.end()]
            if RECEIPT.search(around) or RUN_TARGET.search(around):
                continue
            if TARGET_PREDICATE.search(masked[m.start():m.end() + 60]):
                continue
            p2 = "knowledge-base path, no run/receipt verb governing it: " + m.group(0)[:44]
            break
    if p2:
        fails.append(("P2", p2))
    else:
        for m in BARE_PATH.finditer(masked):
            around = masked[max(0, m.start() - GOVERNS - 12):m.end()]
            if RECEIPT.search(around) or RUN_TARGET.search(around):
                continue
            warns.append(("P2?", "path mention with no run/write/receipt verb: "
                          + m.group(0)[:44]))

    if IDENTITY.search(text):
        fails.append(("P3", _span(IDENTITY, text)))

    if OUTPUT_DIRECTIVE.search(text):
        fails.append(("P4", _span(OUTPUT_DIRECTIVE, text)))

    if not any(tok and tok in head.lower() for tok in self_id_tokens(stem.lower())):
        fails.append(("R1", "no actor named in the first %d chars" % FIRST_CLAUSE))
    elif "hook" not in head.lower() and "local" not in head.lower():
        warns.append(("R1?", "names itself but does not say it is local"))

    required = NOTICE_REQUIRED if surface == "notice" else BLOCK_REQUIRED
    for code, (rx, scoper) in required.items():
        if not rx.search(scoper(text) if scoper else text):
            fails.append((code, REQUIRED_DETAIL[code]))
    return fails, warns


def _span(rx, text, width=52):
    m = rx.search(text)
    s = text[m.start():m.start() + width].replace("\n", " ")
    return repr(s.strip())


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def lint_file(path: Path, verbose=True):
    """(fails, warns, unresolved, per-surface site counts) for one hook."""
    stem = path.stem
    try:
        sites = messages_of(path)
    except SyntaxError as exc:
        print("  !! %s could not be parsed: %s" % (path.name, exc))
        return 1, 0, 0, {}
    n_fail = n_warn = n_unres = 0
    counts = {}
    for lineno, text, resolved, surface in sites:
        counts[surface] = counts.get(surface, 0) + 1
        if not resolved:
            n_unres += 1
            if verbose:
                print("  L%-4d [%s] UNRESOLVED  message not statically renderable — "
                      "not ruled on, check by hand" % (lineno, surface))
            continue
        fails, warns = check(text, stem, surface)
        n_fail += len(fails)
        n_warn += len(warns)
        if verbose and (fails or warns):
            print("  L%-4d [%s] %s" % (lineno, surface, _preview(text)))
            for code, detail in fails:
                print("        FAIL %-4s %s" % (code, detail))
            for code, detail in warns:
                print("        warn %-4s %s" % (code, detail))
    return n_fail, n_warn, n_unres, counts


def _preview(text, width=64):
    flat = " ".join(text.split())
    return flat[:width] + ("…" if len(flat) > width else "")


CONTROL_SPEC = (
    # surface, fixture stem, hook stem, provenance, codes the bad text must fail
    ("block", "known_bad", "transcript_read_guard",
     "verbatim deny text of git 7836b74^, the message two subagents\n"
     "               classified as prompt injection on 2026-08-29",
     {"P1", "P2", "R1"}),
    ("notice", "known_bad_notice", "shell_transport_guard",
     "a notice wearing the costume: rule-id authority, a read-elsewhere\n"
     "               pointer, no actor, no receipt (authored 2026-09-09 for F-8)",
     # every notice-side check is required to fire on it: a check with no
     # known-true positive is an assertion about new code, not a control
     {"P1", "P2", "R1", "R2n", "R3n"}),
)


def controls():
    """Two-sided calibration, per surface. Prints what each control proves.

    A surface with no controls is an unmeasured surface: the notice pair exists
    so that "the lint now covers notices" is a claim with a known-true positive
    and a known-true negative behind it, not an assertion about new code.
    """
    print("CONTROLS (rules/hook-deny-message.md; fixtures/ carries every text)")
    ok = True
    for surface, stem, hook, provenance, must_fail in CONTROL_SPEC:
        bad = (FIXTURES / (stem + ".txt")).read_text(encoding="utf-8").strip()
        good = (FIXTURES / (stem.replace("bad", "good") + ".txt")).read_text(
            encoding="utf-8").strip()
        bad_fails, _ = check(bad, hook, surface)
        good_fails, good_warns = check(good, hook, surface)
        codes = sorted({c for c, _ in bad_fails})
        print("  [%s] known-bad  = %s" % (surface, provenance))
        print("               -> %d FAIL: %s" % (len(bad_fails), ", ".join(codes) or "NONE"))
        for code, detail in bad_fails:
            print("                  %-4s %s" % (code, detail))
        print("  [%s] known-good = %s" % (surface, "current %s text" % hook))
        print("               -> %d FAIL, %d warn" % (len(good_fails), len(good_warns)))
        for code, detail in good_fails:
            print("                  %-4s %s" % (code, detail))
        if not must_fail <= set(codes):
            print("  INSTRUMENT BROKEN: %s known-bad must fail %s"
                  % (surface, ", ".join(sorted(must_fail))))
            ok = False
        if good_fails:
            print("  INSTRUMENT BROKEN: %s known-good must pass every FAIL check" % surface)
            ok = False
    print("  calibration: %s" % ("two-sided on both surfaces, all four controls "
                                 "behave" if ok else "FAILED"))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hook", help="one hook file (a draft path works)")
    ap.add_argument("--controls", action="store_true", help="calibration only")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--dump", action="store_true",
                    help="print each rendered message in full (authoring aid)")
    args = ap.parse_args()

    if args.dump:
        for path in ([Path(args.hook).resolve()] if args.hook
                     else sorted(HOOKS_DIR.glob("*.py"))):
            for lineno, text, resolved, surface in messages_of(path):
                print("=== %s L%d [%s] %s" % (path.name, lineno, surface,
                                              "" if resolved else "(UNRESOLVED)"))
                print(text)
                print()
        return 0

    ok = controls()
    if args.controls:
        return 0 if ok else 1
    print()

    if args.hook:
        paths = [Path(args.hook).resolve()]
    else:
        paths = sorted(p for p in HOOKS_DIR.glob("*.py"))

    total_f = total_w = total_u = 0
    checked = 0
    per_surface = {s: {"hooks": 0, "sites": 0} for s in SURFACES}
    for path in paths:
        sites = []
        try:
            sites = messages_of(path)
        except SyntaxError:
            pass
        if not sites:
            continue
        checked += 1
        counts = {}
        for _l, _t, _r, surface in sites:
            counts[surface] = counts.get(surface, 0) + 1
        print("%s  (%s)" % (path.name, ", ".join(
            "%d %s message(s)" % (counts[s], s) for s in SURFACES if counts.get(s))))
        f, w, u, _counts = lint_file(path, verbose=not args.quiet)
        if not (f or w or u):
            print("  conforms")
        for surface, n in counts.items():
            per_surface[surface]["hooks"] += 1
            per_surface[surface]["sites"] += n
        total_f += f
        total_w += w
        total_u += u

    print("\n%d hook(s) emit agent-facing text | FAIL %d | warn %d | unresolved %d"
          % (checked, total_f, total_w, total_u))
    print("surfaces ruled on: " + " | ".join(
        "%s %d site(s) in %d hook(s)" % (s, per_surface[s]["sites"], per_surface[s]["hooks"])
        for s in SURFACES))
    print("not ruled on: " + unruled_transport())
    print("ruler: static AST extraction; FAIL checks are structural only — the "
          "semantic question 'is this identity claim checkable' is not ruled on. "
          "A message composed from branches (`parts.append`) is checked as the "
          "union of its branches: sound for the prohibitions, an "
          "over-approximation for the requirements.")
    return 1 if (total_f or not ok) else 0


if __name__ == "__main__":
    sys.exit(main())
