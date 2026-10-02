"""Coverage rubric (INV-7, PIM v1.3): how much of a component the HMI can JUDGE, independent of
what it judged. C1 registered, C2 R-covered (a reconcile point reaches it), C3 I-covered (an
integrity point reaches it), C4 self-tested, C5 watched by a mechanism outside the HMI.

A point REACHES a component when it is bound to it, when one of its `covers` globs matches the
component id (fleet-level checks: one probe, many components), or when it declares
`covers_subsystem` and sits in the component's subsystem (the per-subsystem git reconcile points).
"Documented" left the rubric on 2026-09-19 (user ruling Q4): a missing README is a reconcile
FINDING that should light up, not a completeness item."""
import fnmatch
from pathlib import Path

EVIDENCE_IDS = ["C1", "C2", "C3", "C4", "C5"]


def _applicable(kind, role, rubric):
    key = "tool-utility" if (kind == "tool" and role == "utility") else kind
    return set(rubric["applicable_by_kind"].get(key, []))


def _detect_e1(component, home, registered_hook_targets):
    kind = component["kind"]
    if kind == "hook":
        name = Path(component["path"]).name
        return name in registered_hook_targets
    # everything else reaching this detector is, by construction, matched by a
    # subsystem component_rule (that IS the registration surface for non-hook kinds).
    return True


def _detect_e2(component, home):
    kind = component["kind"]
    path = component.get("path", "")
    if kind == "hook" or kind == "hook-library":
        p = Path(home) / path
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        head = text[:4000]
        return "STATUS:" in head or '"""' in head[:10] and "STATUS" in head
    if kind == "skill":
        return (Path(home) / path / "SKILL.md").exists()
    if kind in ("tool", "test-suite"):
        return (Path(home) / path / "README.md").exists()
    if kind in ("link", "shared-edition", "store", "index"):
        p = Path(path) if (":" in path[:3] or path.startswith("/")) else Path(home) / path
        return p.exists()  # existence of the target is the closest cheap "documented" proxy
    return False


def _detect_e3(component, home, pol_points_by_hook):
    kind = component["kind"]
    if kind == "hook":
        name = Path(component["path"]).stem
        pt = pol_points_by_hook.get(name)
        return bool(pt and pt.get("ran") and pt.get("state") in ("pass", "fail"))
    if kind in ("tool", "test-suite"):
        d = Path(home) / component.get("path", "")
        if not d.is_dir():
            return False
        if (d / "controls.py").exists():
            return True
        return any(d.glob("test_*.py")) or any(d.glob("*_test.py"))
    return False


def reaches(point, component):
    if point.get("component") == component["id"]:
        return True
    if any(fnmatch.fnmatch(component["id"], g) for g in point.get("covers", [])):
        return True
    return bool(point.get("covers_subsystem")) and point.get("subsystem") == component.get("subsystem")         and ":" not in component["id"][:3]


def _covered(component, all_points, cls):
    return any(p["adapter"] != "manual" and (p.get("class") or "integrity") == cls and reaches(p, component)
               for p in all_points)


def _detect_e5(component_id, points_for_component, scheduled_task_names):
    """PIM §7: declared and verifiable -> True; declared but not verifiable -> None
    ("?"); nothing declared -> False. The registry is the HMI's declared knowledge,
    so an absent `watched_by` is a determinable "not watched", never a "?"."""
    declared = False
    for p in points_for_component:
        wb = p.get("watched_by")
        if not wb:
            continue
        declared = True
        if wb.startswith("ops-health"):
            return True
        if any(t in wb for t in scheduled_task_names):
            return True
    # A native ops-health point on this component is itself E5 evidence (checked
    # every SessionStart, per PIM §7 E5(b)) even without an explicit watched_by.
    for p in points_for_component:
        if p["adapter"] == "native" and p.get("adapter_config", {}).get("source") == "ops-health":
            return True
    return None if declared else False


def label(applicable, satisfied_count, has_undetermined):
    if not applicable:
        return "N/A"
    if has_undetermined:
        return "UNDETERMINED"
    if satisfied_count <= 1:
        return "BARE"
    if satisfied_count == len(applicable):
        return "COMPLETE"
    return "PARTIAL"


def evaluate(component, home, rubric, registered_hook_targets, pol_points_by_hook,
             points_for_component, scheduled_task_names, all_points=None):
    applicable = _applicable(component["kind"], component.get("role"), rubric)
    all_points = all_points if all_points is not None else points_for_component
    watchers = [p for p in all_points if reaches(p, component)]
    values = {}
    if "C1" in applicable:
        values["C1"] = _detect_e1(component, home, registered_hook_targets)
    if "C2" in applicable:
        values["C2"] = _covered(component, all_points, "reconcile")
    if "C3" in applicable:
        values["C3"] = _covered(component, all_points, "integrity")
    if "C4" in applicable:
        values["C4"] = _detect_e3(component, home, pol_points_by_hook)
    if "C5" in applicable:
        values["C5"] = _detect_e5(component["id"], watchers, scheduled_task_names)

    satisfied = sum(1 for v in values.values() if v is True)
    undetermined = any(v is None for v in values.values())
    missing = [k for k, v in values.items() if v is False]
    lbl = label(applicable, satisfied, undetermined)
    score = f"{satisfied}/{len(applicable)}" if applicable else "n/a"
    out = {k: values.get(k, "n/a") for k in EVIDENCE_IDS}
    out.update({"score": score, "label": lbl, "missing": missing})
    return out
