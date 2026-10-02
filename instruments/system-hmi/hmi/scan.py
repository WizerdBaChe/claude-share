"""Disk <-> Registry scan closure (INV-5).

Scan roots (PSM 04 §2.2, verbatim): hooks/*.py, tools/* (depth 1), skills/*
(depth 1), rules/*.md, agents/*.md. settings.json is parsed as JSON (never by
regex) to answer "is this hooks/x.py a command target" for rubric E1 -- it is
NOT itself a scanned component.

Two independent directions (INV-5):
  (a) disk -> registry: every scanned disk path is registered / ignored / UNREGISTERED
  (b) registry -> disk: every LITERAL (non-wildcard) component_rules path either
      exists on disk or is MISSING (disposition retired excepted)

External components (component_rules entries with "external": true) are not
discovered by the disk walk; their existence is checked directly by path.
"""
import fnmatch
import json
import os
from pathlib import Path

WILDCARD_CHARS = set("*?[]")


def posix(p):
    return str(p).replace(os.sep, "/")


def list_disk_paths(home):
    """[(relpath, exists_kind_hint)] for every item under the declared scan roots."""
    home = Path(home)
    paths = []
    hooks_dir = home / "hooks"
    if hooks_dir.is_dir():
        for f in sorted(hooks_dir.glob("*.py")):
            paths.append("hooks/" + f.name)
    tools_dir = home / "tools"
    if tools_dir.is_dir():
        for entry in sorted(tools_dir.iterdir()):
            paths.append("tools/" + entry.name)
    skills_dir = home / "skills"
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            paths.append("skills/" + entry.name)
    rules_dir = home / "rules"
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("*.md")):
            paths.append("rules/" + f.name)
    agents_dir = home / "agents"
    if agents_dir.is_dir():
        for f in sorted(agents_dir.glob("*.md")):
            paths.append("agents/" + f.name)
    return paths


def registered_hook_targets(home):
    """Set of hooks/*.py basenames that are command targets in settings.json.

    Parsed as JSON (never regex over the text), per PSM 04 §2.2.
    """
    settings_path = Path(home) / "settings.json"
    targets = set()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return targets
    hooks = data.get("hooks", {})
    for _event, entries in hooks.items():
        for entry in entries:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                # command is a quoted python.exe path followed by a quoted script path
                # (+ optional bare args); pull every "...hooks\X.py"/"...hooks/X.py" token.
                for tok in cmd.replace("'", '"').split('"'):
                    tok_p = tok.replace("\\", "/")
                    if "/hooks/" in tok_p and tok_p.endswith(".py"):
                        targets.add(tok_p.rsplit("/", 1)[-1])
    return targets


def _rules(subsystems):
    for sub in subsystems:
        for rule in sub.get("component_rules", []):
            yield sub["id"], rule


def match_internal_rules(path, subsystems):
    """[(subsystem_id, rule)] among non-external rules whose glob matches path."""
    hits = []
    for sub_id, rule in _rules(subsystems):
        if rule.get("external"):
            continue
        if fnmatch.fnmatch(path, rule["glob"]):
            hits.append((sub_id, rule))
    return hits


def match_ignore(path, ignore_list):
    for ig in ignore_list:
        if fnmatch.fnmatch(path, ig["path_glob"]):
            return ig
    return None


def scan(home, registry):
    """Run the full scan. Returns a dict; never raises on a clean registry."""
    subsystems = registry["subsystems"]
    ignore_list = registry.get("ignore", [])
    disk_paths = list_disk_paths(home)
    registered, ignored, unregistered, retired, overlaps = [], [], [], [], []

    for path in disk_paths:
        hits = match_internal_rules(path, subsystems)
        if len(hits) > 1:
            overlaps.append({"path": path, "subsystems": sorted({h[0] for h in hits})})
            continue
        if hits:
            sub_id, rule = hits[0]
            entry = {"id": path, "path": path, "subsystem": sub_id, "kind": rule["kind"],
                      "role": rule.get("role"), "disposition": rule.get("disposition", "active")}
            if rule.get("disposition") == "retired":
                retired.append(entry)
            elif rule.get("disposition") == "out_of_service":
                entry_oos = dict(entry)
                registered.append(entry_oos)
            else:
                registered.append(entry)
            continue
        ig = match_ignore(path, ignore_list)
        if ig:
            ignored.append({"path": path, "reason": ig["reason"]})
        else:
            unregistered.append({"path": path})

    # (b) registry -> disk: literal (non-wildcard) internal rules only.
    disk_set = set(disk_paths)
    missing = []
    seen_literal = set()
    for sub_id, rule in _rules(subsystems):
        if rule.get("external"):
            continue
        glob = rule["glob"]
        if any(c in glob for c in WILDCARD_CHARS):
            continue
        if glob in seen_literal:
            continue
        seen_literal.add(glob)
        if glob not in disk_set:
            if rule.get("disposition") == "retired":
                continue
            missing.append({"path": glob, "subsystem": sub_id,
                             "disposition": rule.get("disposition", "active")})

    # External declared components: existence checked directly.
    external = []
    for sub_id, rule in _rules(subsystems):
        if not rule.get("external"):
            continue
        p = rule["glob"]
        no_check = rule.get("no_fs_check", False)
        exists = None
        if not no_check:
            path_obj = Path(p) if os.path.isabs(p) or ":" in p[:3] else Path(home) / p
            try:
                exists = path_obj.exists()
            except OSError:
                exists = False
        external.append({"id": p, "path": p, "subsystem": sub_id, "kind": rule["kind"],
                          "role": rule.get("role"), "disposition": rule.get("disposition", "active"),
                          "exists": exists})

    return {
        "registered": registered, "ignored": ignored, "unregistered": unregistered,
        "retired": retired, "overlaps": overlaps, "missing": missing, "external": external,
        "ignored_count": len(ignored),
    }


def component_index(scan_result):
    """id -> component dict, over registered + retired + external (not unregistered/missing)."""
    idx = {}
    for bucket in ("registered", "retired", "external"):
        for c in scan_result[bucket]:
            idx[c["id"]] = c
    return idx
