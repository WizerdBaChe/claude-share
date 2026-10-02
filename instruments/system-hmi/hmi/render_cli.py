"""table / --json / --summary renderers; exit codes 0/1/2/3 (Nagios-style)."""
import json

from .deferral import holding

MARKER = {"pass": "  ", "warn": "! ", "fail": "!!", None: "??"}
QUALITY_WORD = {"good": "good", "stale": "STALE", "probe_error": "PROBE-ERROR",
                "undetermined": "UNDETERMINED", "no_probe": "NO-PROBE"}


def exit_code(snap):
    if snap is None:
        return 3
    points = snap.get("points", [])
    if not points:
        return 0
    has_fail = any(p["reading"]["state"] == "fail" and p["reading"]["quality"] == "good" for p in points)
    if has_fail:
        return 2
    has_warn_or_degraded = any(
        (p["reading"]["state"] == "warn" and p["reading"]["quality"] == "good")
        or p["reading"]["quality"] != "good"
        for p in points)
    if has_warn_or_degraded:
        return 1
    return 0


def _point_label(pt):
    r = pt["reading"]
    if r.get("shelved_display"):
        return "SHELVED"
    if holding(r):
        return "DEFERRED"
    if r["quality"] == "good":
        return r["state"] or "—"
    return QUALITY_WORD.get(r["quality"], r["quality"])


def render_table(snap, subsystem_filter=None):
    lines = []
    if snap is None:
        return ["[system-hmi] no snapshot -- run: python tools/system-hmi/hmi.py collect"]
    run = snap.get("run", {})
    lines.append(f"[system-hmi] snapshot age: finished_at={run.get('finished_at')} "
                 f"status={run.get('status')} tiers={run.get('tiers_run')}")
    comp_map = {c["id"]: c for c in snap.get("components", [])}
    no_probe_by_sub = {}
    for c in snap.get("components", []):
        if c.get("probe_quality") == "no_probe":
            no_probe_by_sub.setdefault(c["subsystem"], []).append(c["id"])

    if not subsystem_filter:
        for grp in snap.get("groups", []):
            lines.append(f"== {grp['id']} ({grp.get('title_zh')}) -- capability faces, R and I never fold")
            for fid, f in sorted(grp.get("faces", {}).items()):
                empty = "  (no probe reads this face yet -- not PASS)" if not f["points"] else ""
                lines.append(f"   {fid} {f['title']:<34} R={f['r_state'] or '-':<5}I={f['i_state'] or '-':<5} "
                             f"points={f['points']:<3} degraded={f['degraded']}{empty}")
    subs = sorted(snap.get("subsystems", []), key=lambda s: (s["state"] != "fail", s["state"] != "warn", s["id"]))
    for sub in subs:
        if subsystem_filter and sub["id"] != subsystem_filter:
            continue
        marker = MARKER.get(sub["state"], "??")
        hist = sub.get("completeness_histogram", {})
        hist_s = " ".join(f"{k}:{v}" for k, v in sorted(hist.items()))
        no_probe_ids = no_probe_by_sub.get(sub["id"], [])
        no_probe_tag = f" no_probe:{len(no_probe_ids)}" if no_probe_ids else ""
        if sub.get("deferred_count"):
            no_probe_tag += f" deferred:{sub['deferred_count']}"
        line = (f"{marker} {sub['id']:<24} R={sub.get('r_state') or '-':<5}I={sub.get('i_state') or '-':<5} "
                f"degraded={sub['quality_degraded_count']:<3} standing={sub['standing_count']:<3} "
                f"[{hist_s}]{no_probe_tag}")
        if sub.get("last_known_state"):
            line += (f" last_known={sub['last_known_state']}"
                     f"@{sub.get('last_known_oldest_observed_at')} (stale: tier not run)")
        if sub["state"] not in ("warn", "fail") and not subsystem_filter:
            lines.append(line)
            continue
        lines.append(line)
        if subsystem_filter:
            for comp_id in no_probe_ids:
                lines.append(f"    no_probe     {comp_id:<40} (沒有探針 -- 不是 PASS)")
            for pt in snap.get("points", []):
                comp = comp_map.get(pt["component"])
                if (pt.get("subsystem") or (comp or {}).get("subsystem")) != sub["id"]:
                    continue
                cls = "R" if pt.get("class") == "reconcile" else "I"
                ev = ((pt["reading"].get("evidence") or "")
                      if pt["reading"].get("state") in ("warn", "fail") or holding(pt["reading"]) else "")
                # a holding deferral shows its trigger, never the remedy it is deferring
                tail = ev if holding(pt["reading"]) else (ev or pt.get("remedy") or "")
                lines.append(f"    {cls} {_point_label(pt):<12} {pt['id']:<40} {tail[:160]}")
    return lines


def render_summary(snap):
    if snap is None:
        return ["[system-hmi] no snapshot -- run: python tools/system-hmi/hmi.py collect"]
    run = snap.get("run", {})
    points = snap.get("points", [])
    n_fail = sum(1 for p in points if p["reading"]["quality"] == "good" and p["reading"]["state"] == "fail")
    n_warn = sum(1 for p in points if p["reading"]["quality"] == "good" and p["reading"]["state"] == "warn")
    n_unwatched = sum(1 for p in points if p["reading"]["quality"] != "good")
    n_deferred = sum(1 for p in points if p["reading"]["quality"] == "good" and holding(p["reading"]))
    lines = [f"[system-hmi] snapshot age: finished_at={run.get('finished_at')}",
             f"[system-hmi] {n_fail} fail, {n_warn} warn, {n_unwatched} unwatched"
             + (f", {n_deferred} deferred (trigger not fired)" if n_deferred else "")]
    bad = [s for s in snap.get("subsystems", []) if s["state"] in ("warn", "fail")]
    if not bad:
        return lines
    bad.sort(key=lambda s: (s["state"] != "fail", s["id"]))
    for sub in bad[:10]:
        points_for = [pt for pt in points
                      if _component_subsystem(snap, pt["component"]) == sub["id"]
                      and pt["reading"]["quality"] == "good" and pt["reading"]["state"] in ("warn", "fail")]
        remedy = points_for[0].get("remedy") if points_for else None
        lines.append(f"  {MARKER.get(sub['state'])} {sub['id']}: {sub['state']} -- {remedy or 'see: hmi.py show --subsystem ' + sub['id']}")
    if len(bad) > 10:
        lines.append(f"  ...and {len(bad) - 10} more (hmi.py show)")
    return lines[:12]


def _component_subsystem(snap, component_id):
    for c in snap.get("components", []):
        if c["id"] == component_id:
            return c["subsystem"]
    return None


def render_json(snap):
    return json.dumps(snap, indent=1, ensure_ascii=False)
