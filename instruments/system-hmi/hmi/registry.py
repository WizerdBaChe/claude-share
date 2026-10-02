"""Load + schema-validate registry/*.json (INV-4, INV-12)."""
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
    }


def _find_numeric_leaks(config):
    bad = []
    for k, v in config.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and k not in ALLOWED_NUMERIC_FIELDS:
            bad.append(k)
    return bad


def validate(registry, home=None):
    """Returns list of error strings; empty = valid.

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

    # Rule overlap (needs a live disk walk).
    if home is not None:
        try:
            result = scan_mod.scan(home, registry)
            for ov in result["overlaps"]:
                errors.append(f"overlapping component_rules on {ov['path']!r}: {ov['subsystems']}")
        except Exception as e:
            errors.append(f"scan failed during validate: {e}")

    return errors
