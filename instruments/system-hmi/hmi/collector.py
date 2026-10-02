"""Run order, tiers, timeouts, partial snapshot (INV-1, INV-10); the point
state machine (PIM 02 §6.1, incl. v1.2 W-1/W-2/W-3), subsystem rollup (INV-6),
completeness (INV-7, via hmi.completeness), snapshot write (SG-3 `since`).
"""
import ast
import datetime
import re
import time
from pathlib import Path

from . import adapters, completeness, deferral, fingerprint as fp_mod, lock, scan as scan_mod, snapshot as snap_mod
from . import COLLECTOR_VERSION

STATE_RANK = {"pass": 0, "warn": 1, "fail": 2}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_LIVE_READS = re.compile(r"^Live-reads:(.*)$", re.M)
_LIVE_PATH = re.compile(r"`([^`\s]+)`")


def _live_reads(hook_path):
    """Paths a hook declares on its `Live-reads:` docstring line(s) -- the same
    declaration hooks/golive_check.py reads at save time (L-121). Backticked
    paths only. Mirrored here rather than imported so the collector never
    executes a hook module."""
    try:
        text = Path(hook_path).read_text(encoding="utf-8")
        if "Live-reads:" not in text:
            return []
        doc = ast.get_docstring(ast.parse(text)) or ""
    except Exception:
        return []
    return [p for m in _LIVE_READS.finditer(doc) for p in _LIVE_PATH.findall(m.group(1))]


def _hook_suite_points(scan_result, home=None):
    """HMI-04 (redefined): one `native` point per REGISTERED hook, generated from
    the scan -- never hand-listed. tier=slow, source=hook-proof-of-life.

    Inputs include the hook's `Live-reads:` files (2026-09-29, L-121 hit 3): a
    suite that checks a live data register was carried as `inputs-unchanged`
    after the register was fixed, because only code paths were fingerprinted,
    so the HMI kept showing the OLD fail for a day."""
    pts = []
    suite_dirs = sorted(c["path"] for c in scan_result["registered"] if c["kind"] == "test-suite")
    for c in scan_result["registered"]:
        if c["kind"] != "hook":
            continue
        name = Path(c["path"]).stem
        live = _live_reads(Path(home) / c["path"]) if home else []
        pts.append({
            "id": f"hook-suite.{name}", "component": c["path"], "alias": name,
            "tier": "slow", "adapter": "native",
            "adapter_config": {"source": "hook-proof-of-life", "point": f"hook-suite.{name}"},
            "disposition": {"value": "active"}, "remedy": None,
            "why": "generated from scan: this hook is a registered command target",
            "watched_by": None,
            # static inputs: pol.py runs every suite in one sweep, so the honest unit of change
            # is "any hook, any suite, pol itself, or the registration file".
            "inputs": ["hooks", "tools/hook-proof-of-life", "settings.json"] + suite_dirs + live,
        })
    return pts


def _static_plan(point, prev_reading, home, poll_days, now_ts):
    """-> (fingerprint, valid). A slow point's previous verdict is VALID when its declared inputs
    are unchanged AND it was actually run within the integrity-poll period (PIM v1.3 / D-6)."""
    if point["adapter"] == "manual" or point["tier"] != "slow" or poll_days is None:
        return None, False
    fp = fp_mod.fingerprint(home, point.get("inputs") or [point["component"]])
    if not prev_reading or prev_reading.get("state") is None or prev_reading.get("fingerprint") != fp:
        return fp, False
    ran = prev_reading.get("last_ran_at")
    try:
        ran_ts = datetime.datetime.strptime(ran, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except (TypeError, ValueError):
        return fp, False
    return fp, (now_ts - ran_ts) < poll_days * 86400


def _classify_and_probe(point, missing_components, previous_by_id, run_tiers, home, source_cache,
                        plan=None):
    pid = point["id"]
    now = _now()
    component = point["component"]

    # W-3: component scan class MISSING short-circuits everything else.
    if component in missing_components:
        return {"state": None, "quality": "probe_error", "evidence": "component missing",
                "remedy": None, "source": None, "stale_reason": None, "observed_at": now, "since": now}

    disp = point["disposition"]["value"]
    if disp == "retired":
        return {"state": None, "quality": "no_probe", "evidence": "disposition: retired",
                "remedy": None, "source": None, "stale_reason": None, "observed_at": now, "since": now}
    if disp == "out_of_service":
        reason = point["disposition"].get("reason", "")
        return {"state": None, "quality": "no_probe", "evidence": f"disposition: out_of_service — {reason}",
                "remedy": None, "source": None, "stale_reason": None, "observed_at": now, "since": now}

    prev = previous_by_id.get(pid)
    prev_reading = (prev or {}).get("reading")

    fp, valid, run_now = (plan or {}).get(pid, (None, False, False))
    if valid and not run_now:
        carried = dict(prev_reading)
        carried.update({"quality": "good", "stale_reason": None, "carried": "inputs-unchanged", "due": False})
        return carried
    if point["adapter"] != "manual" and point["tier"] not in run_tiers and not run_now:
        if prev_reading and prev_reading.get("state") is not None:
            return {"state": prev_reading["state"], "quality": "stale", "stale_reason": "tier-not-run",
                     "evidence": prev_reading.get("evidence"), "remedy": prev_reading.get("remedy"),
                     "source": prev_reading.get("source"),
                     # a carried reading keeps the time it was OBSERVED; stamping it
                     # `now` would make an old verdict look fresh.
                     "observed_at": prev_reading.get("observed_at") or now,
                     "fingerprint": prev_reading.get("fingerprint"),
                     "deferral": prev_reading.get("deferral"),
                     "last_ran_at": prev_reading.get("last_ran_at"), "due": True,
                     "since": prev_reading.get("since") or now}
        return {"state": None, "quality": "undetermined", "evidence": "tier not run this pass, no previous reading",
                "remedy": None, "source": None, "stale_reason": None, "observed_at": now, "since": now}

    result = dict(adapters.run_adapter(point, home, source_cache))
    # A deferral with a named trigger holds a warn off (hmi.deferral). The registry's spec wins over
    # a native document's, the way the registry's `class` does (PROTOCOL.md §1, R-6).
    doc_spec = result.pop("deferral_spec", None)
    reading = deferral.resolve(result, point.get("deferral") or doc_spec, home)
    reading = dict(reading)
    reading.setdefault("stale_reason", None)
    reading.setdefault("remedy", point.get("remedy"))
    reading["observed_at"] = now
    if fp is not None:
        reading.update({"fingerprint": fp, "last_ran_at": now, "due": False})
    if (prev_reading and prev_reading.get("state") == reading.get("state")
            and prev_reading.get("quality") == reading.get("quality")):
        reading["since"] = prev_reading.get("since") or now
    else:
        reading["since"] = now
    return reading


def _presentation_shelved(point, reading):
    """W-1: shelved only takes effect when quality=good AND state in {warn,fail}."""
    disp = point["disposition"]
    if disp.get("value") != "shelved":
        return False
    if reading.get("quality") != "good":
        return False
    if reading.get("state") not in ("warn", "fail"):
        return False
    until = disp.get("until")
    if until:
        try:
            until_dt = datetime.datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
            if datetime.datetime.now(datetime.timezone.utc) > until_dt:
                return False  # expired -> shown as active + an extra warn, not this function's job
        except ValueError:
            pass
    return True


def _point_subsystem(point, component_idx):
    """A point rolls up under its own `subsystem` when it declares one, else under
    its component's. Cross-cutting checks (one emitter judging many subsystems, e.g.
    ops-health's budget checks) need this: their COMPONENT is the emitter, but the
    fact they judge belongs elsewhere."""
    return point.get("subsystem") or component_idx.get(point["component"], {}).get("subsystem")


def _group_rollup(groups, points_out, component_idx):
    """A group is a VIEW over existing subsystems, split into capability faces; each face rolls
    R and I separately, from good-quality readings only (INV-6). A face nobody reads shows None
    for both -- absence is not pass (INV-3). Nothing here feeds back into a subsystem's state."""
    out = []
    for grp in groups:
        faces = {f: {"title": t, "r_state": None, "i_state": None, "points": 0, "degraded": 0}
                 for f, t in grp.get("faces", {}).items()}
        for pt in points_out:
            face = grp.get("points", {}).get(pt["id"]) or \
                grp.get("subsystems", {}).get(_point_subsystem(pt, component_idx))
            if face not in faces:
                continue
            f = faces[face]
            f["points"] += 1
            rd = pt["reading"]
            if rd["quality"] != "good":
                f["degraded"] += 1
                continue
            if rd["state"] in STATE_RANK:
                key = "r_state" if pt.get("class", "integrity") == "reconcile" else "i_state"
                if f[key] is None or STATE_RANK[rd["state"]] > STATE_RANK[f[key]]:
                    f[key] = rd["state"]
        out.append({"id": grp["id"], "title_zh": grp.get("title_zh"), "title_en": grp.get("title_en"),
                    "faces": faces})
    return out


def _subsystem_rollup(sub, points, component_idx, hist):
    """One subsystem's rollup from its points (INV-6: good-quality readings only). Shared by the
    full run and the scoped merge so the derived summary can never drift from its detail.
    `hist` (the completeness histogram) is passed in: the full run derives it from components[],
    a scoped run carries it."""
    sid = sub["id"]
    sub_points = [pt for pt in points if _point_subsystem(pt, component_idx) == sid]
    good_states = [pt["reading"]["state"] for pt in sub_points
                    if pt["reading"]["quality"] == "good" and pt["reading"]["state"] in STATE_RANK]
    state = max(good_states, key=lambda s: STATE_RANK[s]) if good_states else None
    by_class = {}
    for cls in ("reconcile", "integrity"):
        cs = [pt["reading"]["state"] for pt in sub_points
              if pt.get("class", "integrity") == cls and pt["reading"]["quality"] == "good"
              and pt["reading"]["state"] in STATE_RANK]
        by_class[cls] = max(cs, key=lambda s: STATE_RANK[s]) if cs else None
    # Additive: the worst CARRIED state, shown beside `state`, never folded into
    # it (INV-6 keeps the rollup to good-quality readings only).
    carried = [pt["reading"] for pt in sub_points
               if pt["reading"]["quality"] == "stale" and pt["reading"]["state"] in STATE_RANK]
    last_known_state = (max((r["state"] for r in carried), key=lambda s: STATE_RANK[s])
                        if carried else None)
    last_known_oldest = min((r["observed_at"] for r in carried), default=None)
    quality_degraded_count = sum(1 for pt in sub_points if pt["reading"]["quality"] != "good")
    standing_count = sum(1 for pt in sub_points if pt["reading"]["quality"] != "good"
                          or pt["reading"]["state"] in ("warn", "fail"))
    # Additive: deferrals holding a warn off. They read pass in `state` (no action due),
    # so this count is what keeps them visible on the subsystem.
    deferred_count = sum(1 for pt in sub_points if pt["reading"]["quality"] == "good"
                          and deferral.holding(pt["reading"]))
    return {"id": sid, "title_zh": sub["title_zh"], "title_en": sub["title_en"],
            "state": state, "quality_degraded_count": quality_degraded_count,
            "completeness_histogram": hist, "standing_count": standing_count,
            "deferred_count": deferred_count,
            # R and I never fold into each other; `state` stays max(R, I)
            # for sorting and for readers that predate the split.
            "r_state": by_class["reconcile"], "i_state": by_class["integrity"],
            "last_known_state": last_known_state,
            "last_known_oldest_observed_at": last_known_oldest}


def collect(home, registry, out_dir, full=False, point_id=None, subsystem_id=None, due=False):
    home = Path(home)
    out_dir = Path(out_dir)
    lock_path = out_dir / "collector.lock"
    ok, holder = lock.acquire(lock_path)
    if not ok:
        return {"ok": False, "reason": "locked", "holder": holder}

    started = time.time()
    started_at = _now()
    status = "ok"
    exception_note = None
    try:
        scan_result = scan_mod.scan(str(home), registry)
        component_idx = scan_mod.component_index(scan_result)
        missing_components = {m["path"] for m in scan_result["missing"]}

        run_tiers = {"cheap"}
        if full:
            run_tiers.add("slow")

        # R-5: one invocation per source per run. Only fetch sources that some
        # point actually needs this run (cheap-tier sources always; slow-tier
        # sources only on --full).
        sources_by_id = {s["id"]: s for s in registry["sources"]}
        source_cache = {}
        needed_sources = set()
        registry_points = list(registry["points"])
        hook_points = _hook_suite_points(scan_result, home)
        effective_points = registry_points + hook_points
        previous_by_id = snap_mod.previous_points_by_id(str(out_dir))
        poll_days = (registry.get("scan") or {}).get("integrity_poll_days")
        now_ts = time.time()
        plan = {}
        for p in effective_points:
            prev_r = (previous_by_id.get(p["id"]) or {}).get("reading")
            fp, valid = _static_plan(p, prev_r, str(home), poll_days, now_ts)
            # --full re-runs everything; --due re-runs exactly the static points whose verdict
            # is no longer valid; a plain collect runs no slow point at all.
            run_now = fp is not None and ((full) or (due and not valid))
            plan[p["id"]] = (fp, valid and not full, run_now)
        for p in effective_points:
            if p["adapter"] == "native" and (p["tier"] in run_tiers or plan[p["id"]][2]):
                needed_sources.add(p["adapter_config"]["source"])
        for src_id in needed_sources:
            src_cfg = sources_by_id.get(src_id)
            if src_cfg:
                source_cache[src_id] = adapters.fetch_source(src_cfg, str(home))

        if point_id or subsystem_id:
            effective_points = [p for p in effective_points if
                                 (point_id and p["id"] == point_id) or
                                 (subsystem_id and _point_subsystem(p, component_idx) == subsystem_id)]

        points_out = []
        for p in effective_points:
            reading = _classify_and_probe(p, missing_components, previous_by_id, run_tiers, str(home), source_cache,
                                          plan=plan)
            reading["shelved_display"] = _presentation_shelved(p, reading)
            points_out.append({
                "id": p["id"], "component": p["component"],
                "subsystem": _point_subsystem(p, component_idx), "alias": p.get("alias"),
                # verdict class (PIM v1.3): "reconcile" = disk vs record, "integrity" = does it
                # work. The registry decides; an undeclared point is an integrity point.
                "class": p.get("class") or "integrity",
                "adapter": p["adapter"], "tier": p["tier"], "disposition": p["disposition"],
                "remedy": p.get("remedy"), "why": p.get("why"), "watched_by": p.get("watched_by"),
                "reading": reading,
            })

        # R-3: document points with no registry entry, per fetched source.
        unregistered_points = []
        for src_id, entry in source_cache.items():
            if not entry.get("ok"):
                continue
            bound_ids = {p["id"] for p in effective_points
                         if p["adapter"] == "native" and p["adapter_config"]["source"] == src_id}
            for doc_id in entry["points_by_id"]:
                if doc_id not in bound_ids:
                    unregistered_points.append({"source": src_id, "id": doc_id})

        if point_id or subsystem_id:
            # Merge into the current snapshot. The point-derived rollups are recomputed from the
            # merged points -- subsystems[] for every subsystem a fresh point belongs to (via the
            # same _subsystem_rollup the full run uses) and groups[] whole -- so the summary
            # cannot keep a verdict its detail no longer holds. Still CARRIED, not recomputed:
            # components[], each subsystem's completeness_histogram, and scan{} (the scan and
            # completeness evaluation only run on a full pass).
            prev_snapshot = snap_mod.load(str(out_dir)) or {"subsystems": [], "components": [], "points": [],
                                                              "scan": {}}
            merged_by_id = {pt["id"]: pt for pt in prev_snapshot.get("points", [])}
            for pt in points_out:
                merged_by_id[pt["id"]] = pt
            merged_points = list(merged_by_id.values())
            affected = {_point_subsystem(pt, component_idx) for pt in points_out}
            subs_out = list(prev_snapshot.get("subsystems", []))
            index_by_id = {s.get("id"): i for i, s in enumerate(subs_out)}
            for sub in registry["subsystems"]:
                if sub["id"] not in affected:
                    continue
                i = index_by_id.get(sub["id"])
                hist = (subs_out[i].get("completeness_histogram") if i is not None else None) or {}
                rolled = _subsystem_rollup(sub, merged_points, component_idx, hist)
                if i is None:
                    subs_out.append(rolled)
                else:
                    subs_out[i] = rolled
            snap = dict(prev_snapshot)
            snap["points"] = merged_points
            snap["subsystems"] = subs_out
            snap["groups"] = _group_rollup(registry.get("groups", []), merged_points, component_idx)
            snap["run"] = {
                "started_at": started_at, "finished_at": _now(),
                "duration_s": round(time.time() - started, 3), "status": status,
                "collector_version": COLLECTOR_VERSION,
                "registry_sha256": snap_mod.registry_sha256(str(home / "tools" / "system-hmi" / "registry")),
                "tiers_run": sorted(run_tiers),
                "scope": "point" if point_id else "subsystem",
            }
            snap_mod.write(str(out_dir), snap)
            return {"ok": True, "snapshot": snap}

        # Full run: rebuild subsystems[] and components[] from the scan + points.
        registered_hook_targets = scan_mod.registered_hook_targets(str(home))
        pol_points_by_hook = {}
        pol_entry = source_cache.get("hook-proof-of-life")
        if pol_entry and pol_entry.get("ok"):
            for doc_id, doc_pt in pol_entry["points_by_id"].items():
                if doc_id.startswith("hook-suite."):
                    pol_points_by_hook[doc_id[len("hook-suite."):]] = doc_pt

        scheduled_task_names = set()
        for p in registry_points:
            cfg = p.get("adapter_config", {})
            argv = cfg.get("argv") or []
            if argv[:1] == ["schtasks"] and "/TN" in argv:
                scheduled_task_names.add(argv[argv.index("/TN") + 1])

        points_by_component = {}
        for pt in points_out:
            points_by_component.setdefault(pt["component"], []).append(pt)
        raw_points_by_component = {}
        for p in effective_points:
            raw_points_by_component.setdefault(p["component"], []).append(p)

        components_out = []
        for bucket in ("registered", "retired", "external"):
            for c in scan_result[bucket]:
                comp_points = raw_points_by_component.get(c["id"], [])
                comp = completeness.evaluate(c, str(home), registry["rubric"], registered_hook_targets,
                                              pol_points_by_hook, comp_points, scheduled_task_names,
                                              all_points=[dict(p, subsystem=_point_subsystem(p, component_idx)) for p in effective_points])
                # Honest-blank marker (PIM §3 "no_probe"): a registered component that
                # NO non-manual point targets is not PASS and not merely UNDETERMINED --
                # additive field, ignored by readers that don't know it yet (PROTOCOL §1).
                probe_quality = "no_probe" if (comp.get("C3") is False and comp.get("C2") is not True) else None
                components_out.append({"id": c["id"], "kind": c["kind"], "subsystem": c["subsystem"],
                                        "scan_class": ("retired" if bucket == "retired" else
                                                        ("external-missing" if bucket == "external" and c.get("exists") is False
                                                         else bucket)),
                                        "completeness": comp, "probe_quality": probe_quality})

        subsystems_out = []
        for sub in registry["subsystems"]:
            hist = {}
            for c in components_out:
                if c["subsystem"] != sub["id"]:
                    continue
                lbl = c["completeness"]["label"]
                hist[lbl] = hist.get(lbl, 0) + 1
            subsystems_out.append(_subsystem_rollup(sub, points_out, component_idx, hist))

        snap = {
            "run": {"started_at": started_at, "finished_at": _now(),
                     "duration_s": round(time.time() - started, 3), "status": status,
                     "collector_version": COLLECTOR_VERSION,
                     "registry_sha256": snap_mod.registry_sha256(str(home / "tools" / "system-hmi" / "registry")),
                     "tiers_run": sorted(run_tiers),
                     "scope": "full-all" if full else ("due" if due else "full-cheap"),
                     "due_points": sorted(pt["id"] for pt in points_out if pt["reading"].get("due"))},
            "subsystems": subsystems_out,
            "groups": _group_rollup(registry.get("groups", []), points_out, component_idx),
            "components": components_out,
            "points": points_out,
            "scan": {"unregistered": scan_result["unregistered"], "missing": scan_result["missing"],
                     "ignored_count": scan_result["ignored_count"], "overlaps": scan_result["overlaps"],
                     "unregistered_points": unregistered_points},
        }
        snap_mod.write(str(out_dir), snap)
        return {"ok": True, "snapshot": snap}
    except Exception as e:
        status = "partial"
        exception_note = f"{type(e).__name__}: {e}"
        try:
            snap = {"run": {"started_at": started_at, "finished_at": _now(),
                              "duration_s": round(time.time() - started, 3), "status": status,
                              "exception": exception_note, "collector_version": COLLECTOR_VERSION,
                              "tiers_run": sorted(locals().get("run_tiers", set()))},
                    "subsystems": [], "components": [], "points": locals().get("points_out", []),
                    "scan": {}}
            snap_mod.write(str(out_dir), snap)
        except Exception:
            pass
        return {"ok": False, "reason": "exception", "detail": exception_note}
    finally:
        lock.release(lock_path)
