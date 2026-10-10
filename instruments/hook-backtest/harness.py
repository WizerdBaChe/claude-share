r"""Shared corpus walk for hook backtests: recorded tool calls -> a predicate.

Every hook backtest in this tree used to carry its own copy of the same loop
(ps-errorpref-backtest, ps-pipeline-close-backtest, and the 2026-10-03
secret_file_guard property-2 run that stayed in a scratchpad). Three copies of
a corpus walk drift the way a copied detector drifts: a dedupe key or a record
filter changes in one and the reported rates stop being comparable. This module
is the one walk; a backtest names a predicate and keeps only its own reporting.

What it owns (and nothing else):
  * where the corpus is (`DEFAULT_ROOTS`) and how it is read (every *.jsonl,
    line by line, assistant `tool_use` blocks),
  * the dedupe policies -- sidechain/compaction rewrites repeat a call verbatim
    (up to 6x), so an undeduped rate is inflated,
  * corpus statistics (files, distinct days, calls per tool),
  * a locator per call (session, date, project/file:line, tool_use id) so a fire
    can be reopened without printing what the call carried,
  * redaction for the one place text may be printed (`excerpt`), fail-closed.

What it never owns: the detector. Predicates IMPORT the shipped hook (see
adapters.py); a backtest that re-implements its hook measures a detector
nobody runs (the ps-errorpref backtest diverged from its hook within a day).
"""
import importlib
import importlib.util
import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field

CLAUDE_HOME = os.path.join(os.path.expanduser("~"), ".claude")
# The LIVE hooks: a backtest measures what runs, so it imports from the
# canonical tree even when this tool is checked out in a worktree.
HOOKS_DIR = os.path.join(CLAUDE_HOME, "hooks")
# SHARE EDITION: the source also listed an offline session-archive directory on a
# non-system drive here; dropped. `--root` (repeatable) takes extra corpus roots.
DEFAULT_ROOTS = [
    os.path.join(CLAUDE_HOME, "projects"),
]
SHELL_TOOLS = ("Bash", "PowerShell")

# Measured 2026-08-21 for ps_errorpref_guard (median of 15 subprocess
# round-trips): 105 ms, essentially all of it Python start-up -- a payload that
# FIRES is no slower than one that exits on the first branch. Used only to
# price the PreToolUse tax in seconds/day.
MS_PER_CALL = 105


# ---------------------------------------------------------------- dedupe keys
def key_ts_head(ts, tool, inp):
    """(timestamp, tool, first 400 chars of command-or-file_path).

    The ps-* backtests' key. Two identical commands issued at different times
    are two calls; a compaction rewrite of the same call (same ts) is one.
    """
    fp = str(inp.get("file_path", "") or "")
    cmd = str(inp.get("command", "") or "")
    return (ts, tool, (cmd or fp)[:400])


def key_content(ts, tool, inp):
    """(tool, full command) for shell tools, (tool, canonical input) otherwise.

    The secret_file_guard backtest's key: it asks "how many DISTINCT forms
    would fire", so a command retyped later counts once.
    """
    if tool in SHELL_TOOLS:
        return (tool, str(inp.get("command") or ""))
    return (tool, json.dumps(inp, sort_keys=True))


DEDUPE = {"ts-head": key_ts_head, "content": key_content}


# --------------------------------------------------------------------- calls
@dataclass(frozen=True)
class Call:
    ts: str
    tool: str
    input: dict
    path: str
    line: int
    session: str
    project: str
    tool_use_id: str

    @property
    def date(self):
        return self.ts[:10] or "????-??-??"

    @property
    def locator(self):
        """project-dir/file:line -- reopens the call; carries no input text."""
        return "%s/%s:%d" % (self.project, os.path.basename(self.path), self.line)


@dataclass
class Corpus:
    """Statistics filled in by iter_calls as it walks."""
    files: int = 0
    calls: Counter = field(default_factory=Counter)
    days: set = field(default_factory=set)
    missing: list = field(default_factory=list)

    def window(self):
        return (min(self.days), max(self.days)) if self.days else ("-", "-")


def _say_missing(root):
    print("  (root not found, skipped: %s)" % root)


def iter_calls(roots=None, tools=None, dedupe=key_ts_head, assistant_only=True,
               corpus=None, on_missing=_say_missing):
    """Yield one Call per distinct recorded tool_use.

    tools          -- iterable of tool names to keep, None = every tool
    dedupe         -- key function (ts, tool, input) -> hashable, or None
    assistant_only -- only records whose type is "assistant" (tool_use blocks
                      live there; False reproduces a walk that did not check)
    corpus         -- a Corpus to fill with files / calls per tool / days
    """
    roots = roots or DEFAULT_ROOTS
    keep = set(tools) if tools else None
    corpus = corpus if corpus is not None else Corpus()
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            corpus.missing.append(root)
            if on_missing:
                on_missing(root)
            continue
        for dp, dn, fn in os.walk(root):
            for f in fn:
                if not f.endswith(".jsonl"):
                    continue
                corpus.files += 1
                path = os.path.join(dp, f)
                try:
                    fh = io.open(path, encoding="utf-8", errors="replace")
                except Exception:
                    continue
                project = os.path.basename(dp)
                stem = f[:-len(".jsonl")]
                with fh:
                    for lineno, line in enumerate(fh, 1):
                        # A tool_use block always spells its type literally;
                        # skipping json.loads on every other line is the speed.
                        if '"tool_use"' not in line:
                            continue
                        try:
                            d = json.loads(line)
                        except Exception:
                            continue
                        if not isinstance(d, dict):
                            continue
                        if assistant_only and d.get("type") != "assistant":
                            continue
                        msg = d.get("message")
                        c = msg.get("content") if isinstance(msg, dict) else None
                        if not isinstance(c, list):
                            continue
                        ts = d.get("timestamp", "") or ""
                        session = str(d.get("sessionId") or stem)
                        for b in c:
                            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                                continue
                            tool = b.get("name")
                            if keep is not None and tool not in keep:
                                continue
                            inp = b.get("input") or {}
                            if not isinstance(inp, dict):
                                continue
                            if dedupe is not None:
                                k = dedupe(ts, tool, inp)
                                if k in seen:
                                    continue
                                seen.add(k)
                            corpus.calls[tool] += 1
                            if ts:
                                corpus.days.add(ts[:10])
                            yield Call(ts, tool, inp, path, lineno, session,
                                       project, str(b.get("id") or ""))


def run(predicate, roots=None, tools=None, dedupe=key_ts_head, assistant_only=True,
        on_missing=_say_missing):
    """Feed every call to predicate(tool, input) -> (corpus, [(call, verdict)])."""
    corpus = Corpus()
    fires = []
    for call in iter_calls(roots, tools, dedupe, assistant_only, corpus, on_missing):
        v = predicate(call.tool, call.input)
        if v:
            fires.append((call, v))
    return corpus, fires


def verdict_kind(v):
    """A short label for a verdict: the string itself, a dict's 'kind', or 'fire'."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict) and isinstance(v.get("kind"), str):
        return v["kind"]
    return "fire"


# ------------------------------------------------------------ module loading
def load_hook(name):
    """Import a live hook module by name, exactly as the old backtests did."""
    if HOOKS_DIR not in sys.path:
        sys.path.insert(0, HOOKS_DIR)
    return importlib.import_module(name)


def load_predicate(spec):
    """'module:function' -> callable.

    module is a .py path, or a bare name looked up first in the live hooks/
    directory, then beside this file (adapters).
    """
    mod, _, fn = spec.rpartition(":")
    if not mod or not fn.isidentifier():
        raise SystemExit("predicate must be <module>:<function>, got %r" % spec)
    if mod.endswith(".py") or os.sep in mod or "/" in mod:
        path = os.path.abspath(mod)
        name = os.path.splitext(os.path.basename(path))[0]
        if name in sys.modules and getattr(sys.modules[name], "__file__", None) == path:
            m = sys.modules[name]
        else:
            s = importlib.util.spec_from_file_location(name, path)
            m = importlib.util.module_from_spec(s)
            sys.modules[name] = m
            s.loader.exec_module(m)
    elif os.path.isfile(os.path.join(HOOKS_DIR, mod + ".py")):
        m = load_hook(mod)
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        if here not in sys.path:
            sys.path.insert(0, here)
        m = importlib.import_module(mod)
    f = getattr(m, fn, None)
    if not callable(f):
        raise SystemExit("%s has no callable %r" % (getattr(m, "__file__", mod), fn))
    return f


# ------------------------------------------------------------- registration
def registered_tools(hook_name, fallback=(), missing_label="settings.json (NOT REGISTERED)"):
    """Which tools settings.json wires a hook to -> (set, source).

    DERIVED, never restated. A second mechanism holding its own copy of a value
    the owner also holds is integrity-sweep check 10's defect class. If the
    parse fails, say so and fall back to the declared baseline rather than
    silently reverting to it.
    """
    path = os.path.join(CLAUDE_HOME, "settings.json")
    try:
        d = json.load(io.open(path, encoding="utf-8"))
        for entry in d.get("hooks", {}).get("PreToolUse", []):
            for h in entry.get("hooks", []):
                if hook_name in h.get("command", ""):
                    m = str(entry.get("matcher", ""))
                    return set(t for t in m.split("|") if t), "settings.json"
        return set(), missing_label
    except Exception as e:
        return set(fallback), "declared fallback (settings.json unreadable: %s)" % e


# ---------------------------------------------------------------- redaction
_REDACTOR = None


def _patterns():
    """cred-sweep's credential patterns, imported (one list, not a copy)."""
    global _REDACTOR
    if _REDACTOR is None:
        here = os.path.dirname(os.path.abspath(__file__))
        p = os.path.join(os.path.dirname(here), "cred-sweep", "cred_sweep.py")
        s = importlib.util.spec_from_file_location("cred_sweep", p)
        m = importlib.util.module_from_spec(s)
        s.loader.exec_module(m)
        _REDACTOR = m.PATTERNS
    return _REDACTOR


def redact(text):
    """Replace every credential-shaped value with <redacted:category>.

    Stricter than cred-sweep's own verdicts on purpose: no plausibility filter,
    so a placeholder that merely LOOKS like a key is masked too. Raises if the
    pattern list cannot be loaded -- callers must not fall back to raw text.
    """
    for cat, rx in _patterns():
        def sub(m, cat=cat):
            a, b = m.span(1)
            s = m.group(0)
            o = m.start(0)
            return s[:a - o] + "<redacted:%s>" % cat + s[b - o:]
        text = rx.sub(sub, text)
    return text


def call_text(call):
    """The text a call is about: command, Grep pattern+target, or file path."""
    inp = call.input
    if "command" in inp:
        return str(inp.get("command") or "")
    if call.tool == "Grep":
        where = " ".join(str(inp.get(k) or "") for k in ("path", "glob", "type"))
        return "Grep %r in %s" % (inp.get("pattern"), where)
    return str(inp.get("file_path") or inp.get("path") or "")


def excerpt(call, width):
    """Redacted, whitespace-collapsed first `width` chars -- or a refusal."""
    try:
        t = redact(" ".join(call_text(call).split()))
    except Exception as e:  # fail closed: no redactor, no text
        return "<excerpt withheld: redactor unavailable (%s)>" % type(e).__name__
    return t[:width]
