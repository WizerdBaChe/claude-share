"""Load + schema-validate registry/*.json (INV-4, INV-12)."""
import ast
import json
import re
from pathlib import Path

from . import scan as scan_mod
from .deferral import spec_problems

CLOSED_KINDS = {
    "hook", "hook-library", "tool", "test-suite", "skill", "rule", "agent-def",
    "scheduled-task", "link", "shared-edition", "index", "store",
}
CLOSED_ADAPTERS = {
    "native", "exit-code", "tail-sentinel", "empty-output", "line-scan",
    "status-file", "fs-link", "manual",
}
CLOSED_DISPOSITIONS = {"active", "shelved", "out_of_service", "retired"}
CLOSED_TIERS = {"cheap", "slow"}
# INV-4: no restated numeric thresholds except timeout_s (all adapters) and
# max_age_s (status-file only).
ALLOWED_NUMERIC_FIELDS = {"timeout_s", "max_age_s", "no_hit_exit"}


class RegistryError(Exception):
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_registry(registry_dir):
    registry_dir = Path(registry_dir)
    return {
        "scan": _load(registry_dir / "scan.json") if (Path(registry_dir) / "scan.json").exists() else {},
        "groups": (_load(registry_dir / "groups.json").get("groups", [])
                   if (Path(registry_dir) / "groups.json").exists() else []),
        "subsystems": _load(registry_dir / "subsystems.json"),
        "points": _load(registry_dir / "points.json"),
        "rubric": _load(registry_dir / "rubric.json"),
        "ignore": _load(registry_dir / "ignore.json"),
        "sources": _load(registry_dir / "sources.json"),
        # optional (WC-05b): hooks' telemetry files and how to read their timestamps; absent = no check
        "telemetry": (_load(registry_dir / "telemetry.json")
                      if (registry_dir / "telemetry.json").exists() else None),
    }


# ---------------------------------------------------------------------------
# telemetry registry (WC-05b, snapshot-unification 02 section 9.2, V-33, V-41)
# ---------------------------------------------------------------------------
# registry/telemetry.json = {"rows": [{file, hook, ts_field, ts_format[, path_built][, not_yet_fired]}],
# "unowned": [{file, reason}]}. validate rules (errors only on what it can DETERMINE):
#   ERROR   a (hook, file) producer pair with no row and file not unowned
#             (a) hooks/*.py holding a literal `telemetry/<name>.jsonl`
#             (b) hooks/*.py CALLING deny_receipt clause()/receipt() (alias-aware); file =
#                 telemetry/<first argument with _ -> ->.jsonl> (hooks/deny_receipt.py log_path).
#                 Importing alone, or only notice_clause()/fp_clause()/log_path(), writes no row.
#   ERROR   an existing telemetry/*.jsonl that is neither a row's file nor unowned
#   ERROR   a row whose file does not exist (unless the row says "not_yet_fired": true, which is
#           itself reported as a warning once the file exists)
#   WARNING a row whose (hook, file) pair no longer qualifies by (a)/(b) and is not "path_built": true
# Own stdlib scan; nothing is imported from the workbench (INV-10).

TS_FORMATS = ("epoch", "iso", "date")
TELEMETRY_WRITERS = ("clause", "receipt")
LITERAL_TELEMETRY_RE = re.compile(r"telemetry/([A-Za-z0-9_][A-Za-z0-9_.-]*\.jsonl)")


def _caller_files(src, stem):
    """(b): files written by deny_receipt.clause()/receipt() calls in one hook source.
    -> (set of file names, or None when the source does not parse)."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    fn_alias, mod_alias, consts = set(), set(), {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "deny_receipt":
            fn_alias.update(a.asname or a.name for a in node.names if a.name in TELEMETRY_WRITERS)
        elif isinstance(node, ast.Import):
            mod_alias.update(a.asname or a.name for a in node.names if a.name == "deny_receipt")
    for node in tree.body:  # module-level `HOOK = "name"` constants
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            consts[node.targets[0].id] = node.value.value
    files = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        is_writer = ((isinstance(f, ast.Name) and f.id in fn_alias)
                     or (isinstance(f, ast.Attribute) and f.attr in TELEMETRY_WRITERS
                         and isinstance(f.value, ast.Name) and f.value.id in mod_alias))
        if not is_writer:
            continue
        arg = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "hook"), None)
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            name = arg.value
        elif isinstance(arg, ast.Name) and arg.id in consts:
            name = consts[arg.id]
        else:
            name = stem  # argument not statically known: deny_receipt's own convention is hook = stem
        files.add(name.replace("_", "-") + ".jsonl")
    return files


def telemetry_producers(hooks_dir):
    """-> {"a": {(stem, file)}, "b": {(stem, file)}, "unparsed": [stem]} over hooks_dir/*.py (top level)."""
    out = {"a": set(), "b": set(), "unparsed": []}
    for p in sorted(Path(hooks_dir).glob("*.py")):
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in LITERAL_TELEMETRY_RE.finditer(src):
            out["a"].add((p.stem, m.group(1)))
        if "deny_receipt" in src:
            files = _caller_files(src, p.stem)
            if files is None:
                out["unparsed"].append(p.stem)
            else:
                out["b"].update((p.stem, f) for f in files)
    return out


def _unowned_files(treg):
    out = set()
    for u in treg.get("unowned", []):
        out.add(u.get("file") if isinstance(u, dict) else u)
    return out


def telemetry_check(treg, home, telemetry_dir=None, hooks_dir=None):
    """-> (errors, warnings) for registry/telemetry.json against hooks/*.py and the telemetry dir."""
    home = Path(home)
    tdir = Path(telemetry_dir) if telemetry_dir else home / "telemetry"
    hdir = Path(hooks_dir) if hooks_dir else home / "hooks"
    errors, warnings = [], []
    if not isinstance(treg, dict) or not isinstance(treg.get("rows"), list):
        return ["telemetry.json: needs an object with a 'rows' list"], warnings
    rows, row_files = [], set()
    for r in treg["rows"]:
        bad = [k for k in ("file", "hook", "ts_field", "ts_format") if not isinstance(r.get(k), str) or not r.get(k)]
        if bad:
            errors.append(f"telemetry row missing field(s) {bad}: {r.get('file', r)}")
            continue
        if r["ts_format"] not in TS_FORMATS:
            errors.append(f"telemetry row {r['file']!r} ts_format {r['ts_format']!r} not in {TS_FORMATS}")
        if r["file"] in row_files:
            errors.append(f"telemetry row duplicated for file {r['file']!r}")
        row_files.add(r["file"])
        rows.append(r)
    unowned = _unowned_files(treg)
    for f in sorted(unowned & row_files):
        errors.append(f"telemetry file {f!r} is both a trend row and unowned")
    covered = row_files | unowned
    prod = telemetry_producers(hdir)
    pairs = prod["a"] | prod["b"]
    for hook, f in sorted(pairs):
        if f not in covered:
            errors.append(f"telemetry file without a trend row: {hook} -> {f}")
    existing = {p.name for p in tdir.glob("*.jsonl")} if tdir.is_dir() else set()
    for f in sorted(existing - covered):
        errors.append(f"telemetry file not registered: {f} (add a row, or list it under 'unowned')")
    for r in rows:
        exists = r["file"] in existing
        if not exists and not r.get("not_yet_fired"):
            errors.append(f"telemetry row's file does not exist: {r['file']} (hook {r['hook']})")
        if exists and r.get("not_yet_fired"):
            warnings.append(f"telemetry row {r['file']}: 'not_yet_fired' is set but the file exists (stale flag)")
        if (r["hook"], r["file"]) not in pairs and not r.get("path_built"):
            warnings.append(f"telemetry row {r['file']}: hook {r['hook']} no longer qualifies by literal path or "
                            f"deny_receipt call, and the row is not marked path_built (stale row)")
    return errors, warnings


def _find_numeric_leaks(config):
    bad = []
    for k, v in config.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ALLOWED_NUMERIC_FIELDS:
            bad.append(k)
    return bad


def validate(registry, home=None, warnings=None):
    """Returns list of error strings; empty = valid. If `warnings` is a list, non-fatal findings
    (stale telemetry rows) are appended to it; the return value stays errors-only.

    Checks: subsystem/point schema shape, closed-set membership, id uniqueness,
    disk/registry rule-overlap (needs `home` for a live disk walk; skipped,
    not failed, when home is None), INV-4 numeric-threshold lint, SG-2 mirror
    check (a point whose adapter_config declares "mirrors": "<path>" must have
    its argv/command_text occur verbatim in that file, else it is flagged here
    so `collect` can read it `undetermined` -- forward-compatible, currently
    vacuous since no shipped point uses it).
    """
    errors = []
    subsystems = registry.get("subsystems", [])
    seen_sub_ids = set()
    for sub in subsystems:
        for field in ("id", "title_zh", "title_en", "order", "component_rules"):
            if field not in sub:
                errors.append(f"subsystem missing field {field!r}: {sub.get('id', '?')}")
        sid = sub.get("id")
        if sid in seen_sub_ids:
            errors.append(f"duplicate subsystem id {sid!r}")
        seen_sub_ids.add(sid)
        for rule in sub.get("component_rules", []):
            if "glob" not in rule or "kind" not in rule:
                errors.append(f"component_rule missing glob/kind in subsystem {sid!r}: {rule}")
                continue
            if rule["kind"] not in CLOSED_KINDS:
                errors.append(f"component_rule kind {rule['kind']!r} not in closed set ({sid})")
            disp = rule.get("disposition")
            if disp is not None and disp not in CLOSED_DISPOSITIONS:
                errors.append(f"component_rule disposition {disp!r} not in closed set ({sid}, {rule['glob']})")
            if disp in ("shelved",) and "until" not in rule:
                errors.append(f"shelved component_rule missing 'until' ({sid}, {rule['glob']})")
            if disp in ("shelved", "out_of_service", "retired") and "reason" not in rule:
                errors.append(f"disposition {disp!r} requires 'reason' ({sid}, {rule['glob']})")

    points = registry.get("points", [])
    seen_point_ids = set()
    for pt in points:
        for field in ("id", "component", "adapter", "adapter_config", "disposition", "tier"):
            if field not in pt:
                errors.append(f"point missing field {field!r}: {pt.get('id', '?')}")
        pid = pt.get("id")
        if pid in seen_point_ids:
            errors.append(f"duplicate point id {pid!r}")
        seen_point_ids.add(pid)
        if pt.get("adapter") not in CLOSED_ADAPTERS:
            errors.append(f"point {pid!r} adapter {pt.get('adapter')!r} not in closed set")
        if pt.get("tier") not in CLOSED_TIERS:
            errors.append(f"point {pid!r} tier {pt.get('tier')!r} not in closed set")
        if pt.get("subsystem") is not None and pt["subsystem"] not in {x.get("id") for x in registry.get("subsystems", [])}:
            errors.append(f"point {pid!r} names unknown subsystem {pt['subsystem']!r}")
        disp = pt.get("disposition", {})
        if not isinstance(disp, dict) or disp.get("value") not in CLOSED_DISPOSITIONS:
            errors.append(f"point {pid!r} disposition.value not in closed set: {disp}")
        else:
            if disp["value"] == "shelved" and "until" not in disp:
                errors.append(f"point {pid!r} disposition=shelved missing 'until'")
            if disp["value"] in ("shelved", "out_of_service", "retired") and "reason" not in disp:
                errors.append(f"point {pid!r} disposition={disp['value']!r} missing 'reason'")
        if "deferral" in pt:
            # a deferral that cannot name its trigger would hold a warn off forever (hmi.deferral)
            for prob in spec_problems(pt["deferral"]):
                errors.append(f"point {pid!r} deferral: {prob}")
        cfg = pt.get("adapter_config", {})
        if isinstance(cfg, dict):
            leaks = _find_numeric_leaks(cfg)
            if leaks:
                errors.append(f"point {pid!r} adapter_config carries a restated threshold {leaks} (INV-4)")
            mirrors = cfg.get("mirrors")
            if mirrors:
                mirror_path = Path(home or ".") / mirrors
                needle = cfg.get("argv") and " ".join(cfg["argv"]) or cfg.get("command_text", "")
                if mirror_path.exists():
                    text = mirror_path.read_text(encoding="utf-8", errors="replace")
                    if needle and needle not in text:
                        errors.append(f"point {pid!r} SG-2 drift: {needle!r} not found verbatim in {mirrors}")
                else:
                    errors.append(f"point {pid!r} SG-2 mirror file missing: {mirrors}")

    ignore = registry.get("ignore", [])
    for ig in ignore:
        for field in ("path_glob", "reason", "added"):
            if field not in ig:
                errors.append(f"ignore entry missing {field!r}: {ig}")

    sub_ids = {x.get("id") for x in registry.get("subsystems", [])}
    for grp in registry.get("groups", []):
        gid = grp.get("id", "?")
        faces = grp.get("faces", {})
        for sid, face in grp.get("subsystems", {}).items():
            if sid not in sub_ids:
                errors.append(f"group {gid!r} names unknown subsystem {sid!r}")
            if face not in faces:
                errors.append(f"group {gid!r} maps {sid!r} to undeclared face {face!r}")
        for pid, face in grp.get("points", {}).items():
            if face not in faces:
                errors.append(f"group {gid!r} maps point {pid!r} to undeclared face {face!r}")

    sources = registry.get("sources", [])
    for src in sources:
        for field in ("id", "argv", "cwd", "tier", "timeout_s"):
            if field not in src:
                errors.append(f"source missing field {field!r}: {src.get('id', '?')}")

    # Telemetry registry (WC-05b): needs the hooks dir and telemetry dir under `home`; absent = unchecked.
    if home is not None and registry.get("telemetry") is not None:
        t_err, t_warn = telemetry_check(registry["telemetry"], home)
        errors.extend(t_err)
        if warnings is not None:
            warnings.extend(t_warn)

    # Rule overlap (needs a live disk walk).
    if home is not None:
        try:
            result = scan_mod.scan(home, registry)
            for ov in result["overlaps"]:
                errors.append(f"overlapping component_rules on {ov['path']!r}: {ov['subsystems']}")
        except Exception as e:
            errors.append(f"scan failed during validate: {e}")

    return errors
