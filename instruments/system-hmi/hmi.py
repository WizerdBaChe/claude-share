#!/usr/bin/env python3
"""system-hmi CLI: validate | scan | collect | show | conform | verdict | static | serve.

Read-only intermediary layer over the existing ~/.claude checks. stdlib only.
Invoke as `python tools/system-hmi/hmi.py <command>` from the repo root, or
from anywhere -- HOME is resolved from this file's location, never from cwd.

Proof-of-life: `python tools/system-hmi/controls.py`
"""
import argparse
import json
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
TOOL_DIR = Path(__file__).resolve().parent
REGISTRY_DIR = TOOL_DIR / "registry"
OUT_DIR = TOOL_DIR / "out"

sys.path.insert(0, str(TOOL_DIR))
from hmi import registry as registry_mod  # noqa: E402
from hmi import scan as scan_mod  # noqa: E402
from hmi import collector as collector_mod  # noqa: E402
from hmi import snapshot as snapshot_mod  # noqa: E402
from hmi import render_cli  # noqa: E402
from hmi import adapters  # noqa: E402


def cmd_validate(args):
    reg = registry_mod.load_registry(REGISTRY_DIR)
    errors = registry_mod.validate(reg, home=str(HOME))
    if errors:
        for e in errors:
            print("VALIDATE FAIL:", e)
        return 1
    print(f"validate: ok ({len(reg['subsystems'])} subsystems, {len(reg['points'])} points, "
          f"{len(reg['sources'])} sources)")
    return 0


def cmd_scan(args):
    reg = registry_mod.load_registry(REGISTRY_DIR)
    result = scan_mod.scan(str(HOME), reg)
    print(f"registered: {len(result['registered'])}  retired: {len(result['retired'])}  "
          f"ignored: {result['ignored_count']}  external: {len(result['external'])}")
    print(f"UNREGISTERED: {len(result['unregistered'])}")
    for u in result["unregistered"]:
        print("  UNREGISTERED:", u["path"])
    print(f"MISSING: {len(result['missing'])}")
    for m in result["missing"]:
        print("  MISSING:", m["path"], "(subsystem", m["subsystem"] + ")")
    print(f"overlaps: {len(result['overlaps'])}")
    for o in result["overlaps"]:
        print("  OVERLAP:", o["path"], o["subsystems"])
    ext_missing = [e for e in result["external"] if e.get("exists") is False]
    if ext_missing:
        print(f"external paths not found: {len(ext_missing)}")
        for e in ext_missing:
            print("  MISSING(external):", e["path"])
    return 1 if (result["unregistered"] or result["missing"] or result["overlaps"]) else 0


def cmd_collect(args):
    reg = registry_mod.load_registry(REGISTRY_DIR)
    errors = registry_mod.validate(reg, home=str(HOME))
    if errors:
        for e in errors:
            print("collect refused, registry invalid:", e)
        return 5
    result = collector_mod.collect(str(HOME), reg, str(OUT_DIR), full=args.full, due=getattr(args, 'due', False),
                                    point_id=args.point, subsystem_id=args.subsystem)
    if not result["ok"]:
        if result["reason"] == "locked":
            holder = result.get("holder", {})
            print(f"collect refused: lock held by pid={holder.get('pid')} since {holder.get('started_at')}")
            return 4
        print("collect: exception during run,", result.get("detail"), "-- partial snapshot written")
        return 1
    run = result["snapshot"]["run"]
    print(f"collect: ok, status={run['status']}, duration={run.get('duration_s')}s, "
          f"tiers={run.get('tiers_run')}, scope={run.get('scope')}")
    _render_pages()
    return 0


def _render_pages():
    """Re-render the static pages that INLINE the snapshot (2026-09-22).

    mimic.html and structure.html embed snapshot.json at render time, so a
    collect that did not re-render them left the pages showing the last hand
    render: the daily carrier kept the snapshot fresh while the page a human
    opens stayed on 2026-09-19. A render failure is printed, never swallowed,
    and does not turn a good collect into a failed one -- the snapshot is the
    record, the page is a view of it.
    """
    import mimic_view
    import structure_view
    for name, mod in (("mimic", mimic_view), ("structure", structure_view)):
        try:
            rc = mod.main()
        except Exception as exc:  # noqa: BLE001 -- a view must not sink the collect
            print(f"render {name}: FAILED ({type(exc).__name__}: {exc}); "
                  f"run python tools/system-hmi/{name}_view.py to see it", file=sys.stderr)
            continue
        if rc:
            print(f"render {name}: exit {rc}", file=sys.stderr)


def cmd_show(args):
    snap = snapshot_mod.load(str(OUT_DIR))
    if args.json:
        print(render_cli.render_json(snap))
    elif args.summary:
        for line in render_cli.render_summary(snap):
            print(line)
    else:
        for line in render_cli.render_table(snap, subsystem_filter=args.subsystem):
            print(line)
    return render_cli.exit_code(snap)


def cmd_conform(args):
    reg = registry_mod.load_registry(REGISTRY_DIR)
    sources_by_id = {s["id"]: s for s in reg["sources"]}
    src_cfg = sources_by_id.get(args.source)
    if not src_cfg:
        print(f"conform: unknown source {args.source!r}; known: {sorted(sources_by_id)}")
        return 1
    entry = adapters.fetch_source(src_cfg, str(HOME))
    if not entry.get("ok"):
        print(f"conform FAIL: {args.source}: {entry.get('reason')}")
        return 1
    doc = entry["doc"]
    errs = []
    if doc.get("protocol") != "hmi-report/1":
        errs.append("protocol field is not exactly 'hmi-report/1'")
    if doc.get("source") != args.source:
        errs.append(f"document 'source' {doc.get('source')!r} != requested {args.source!r}")
    if "generated_at" not in doc:
        errs.append("missing generated_at")
    points = doc.get("points")
    if not isinstance(points, list) or not points:
        errs.append("points[] missing or empty")
    else:
        for p in points:
            if "id" not in p or not p["id"].startswith(args.source.split("-")[0]) and not p["id"].startswith(args.source):
                pass  # id prefix is <source>.<slug> per PROTOCOL.md; source-specific prefixing varies, not fatal here
            if "ran" not in p:
                errs.append(f"point {p.get('id')} missing 'ran'")
            elif p["ran"] is False and p.get("state") is not None:
                errs.append(f"point {p.get('id')} ran:false but state is not null")
            if "state" not in p:
                errs.append(f"point {p.get('id')} missing 'state'")
    if errs:
        for e in errs:
            print("conform FAIL:", e)
        return 1
    print(f"conform: ok ({args.source}, {len(points)} points, protocol {doc.get('protocol')})")
    return 0


def cmd_verdict(args):
    """Known-good verdict of HEAD (design 17 R-1). Exit 0 GOOD+marked, 1 BAD,
    2 PARTIAL or not markable (dirty code / not a full collect), 3 collect failed."""
    from hmi import release

    def _collect(mode):
        ns = argparse.Namespace(full=(mode == "full"), due=(mode == "due"),
                                point=None, subsystem=None)
        return cmd_collect(ns)

    mode = "none" if args.no_collect else ("due" if args.due else "full")
    declared = release.gate_ids(registry_mod.load_registry(REGISTRY_DIR)["points"])
    code, doc = release.run(str(HOME), str(OUT_DIR), _collect, mode=mode, declared=declared)
    print(f"verdict: {doc['verdict']} at {doc['sha'][:7]} -- gate points "
          f"{doc['gate_pass']}/{doc['gate_total']} pass, scope={doc['scope'] or '-'}, "
          f"marked known-good: {'yes' if doc['marked'] else 'no'}")
    for pid in doc["failing"]:
        print("  FAIL:", pid)
    for pid in doc["non_good"]:
        print("  not determined:", pid)
    if doc["dirty"]:
        print("  not markable, modified tracked code:", ", ".join(doc["dirty"][:8]))
    return code


def cmd_static(args):
    import mimic_view
    return mimic_view.main()


def _exit_when_idle(srv, idle_s):
    """Stop the service once no request arrived for idle_s (2026-09-22). The windowless launcher
    (open_hmi.pyw) starts this service with no console to close, so without this it would outlive
    the page indefinitely. An open page polls /api/meta every 20 s, so idle means the page is gone.
    Counted from request ARRIVAL: a refresh collect (up to ~8 min) must stay under idle_s."""
    import threading
    import time
    last = [time.monotonic()]
    orig = srv.verify_request

    def verify(request, client_address):
        last[0] = time.monotonic()
        return orig(request, client_address)
    srv.verify_request = verify

    def watch():
        while True:
            time.sleep(min(30, idle_s))
            if time.monotonic() - last[0] >= idle_s:
                print(f"serve: idle {idle_s // 60} min, stopping", flush=True)
                srv.shutdown()
                return
    threading.Thread(target=watch, daemon=True).start()


def cmd_serve(args):
    """Local page + re-run of read-only probes. Binds 127.0.0.1 only (INV-8)."""
    import mimic_view
    from hmi import server as server_mod
    try:
        srv = server_mod.make_server(TOOL_DIR, mimic_view.render, port=args.port)
    except OSError as exc:
        print(f"serve: cannot bind 127.0.0.1:{args.port} ({exc}) - is it already running?")
        return 1
    host, port = srv.server_address[:2]
    print(f"serve: http://{host}:{port}/  (Ctrl+C to stop)", flush=True)
    if args.idle_exit:
        _exit_when_idle(srv, args.idle_exit * 60)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


def main():
    ap = argparse.ArgumentParser(prog="hmi.py")
    sub = ap.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    sub.add_parser("scan")

    p_collect = sub.add_parser("collect")
    p_collect.add_argument("--full", action="store_true")
    p_collect.add_argument("--due", action="store_true",
                           help="run only the static (slow) points whose inputs changed or whose "
                                "integrity poll is due; everything else as a plain collect")
    p_collect.add_argument("--point", default=None)
    p_collect.add_argument("--subsystem", default=None)

    p_show = sub.add_parser("show")
    p_show.add_argument("--json", action="store_true")
    p_show.add_argument("--summary", action="store_true")
    p_show.add_argument("--subsystem", default=None)

    p_conform = sub.add_parser("conform")
    p_conform.add_argument("source")

    p_verdict = sub.add_parser("verdict")
    p_verdict.add_argument("--due", action="store_true",
                           help="collect --due first (fast; can never mark known-good)")
    p_verdict.add_argument("--no-collect", action="store_true",
                           help="judge the existing snapshot (never marks: it may predate HEAD)")

    sub.add_parser("static")

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=8787)
    p_serve.add_argument("--idle-exit", type=int, default=0, metavar="MIN",
                         help="stop after MIN minutes with no request (0 = never); an open page polls every 20 s")

    args = ap.parse_args()
    fn = {"validate": cmd_validate, "scan": cmd_scan, "collect": cmd_collect,
          "show": cmd_show, "conform": cmd_conform, "verdict": cmd_verdict,
          "static": cmd_static, "serve": cmd_serve}[args.command]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
