"""The 8 closed adapter classes (INV-2, INV-3): native, exit-code, tail-sentinel,
empty-output, line-scan, status-file, fs-link, manual.

Every adapt_* function returns a partial reading dict with at least
{"state", "quality", "evidence", "source"} and optionally {"remedy",
"stale_reason", "skip_reason"}. The collector fills in observed_at/since.

INV-3 (absence is not pass): every branch below that cannot positively confirm
a pass returns quality != "good" and/or state None -- never a bare default.
"""
import datetime
import json
import os
import re
import subprocess
import time
from pathlib import Path


def _run(argv, cwd, timeout_s):
    """(exit_code, stdout, stderr, error). error is a short reason string, or None."""
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout_s, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout, p.stderr, None
    except subprocess.TimeoutExpired:
        return None, "", "", "timeout"
    except FileNotFoundError as e:
        return None, "", "", f"spawn-error: {e}"
    except OSError as e:
        return None, "", "", f"spawn-error: {e}"


def _cwd_for(home, cfg):
    rel = cfg.get("cwd", ".")
    return str(Path(home) / rel) if rel != "." else str(home)


def fetch_source(source_cfg, home):
    """Run a native emitter once; cache-able result for R-5 (one invocation per run)."""
    argv = source_cfg["argv"]
    cwd = _cwd_for(home, source_cfg)
    code, out, err, error = _run(argv, cwd, source_cfg.get("timeout_s", 60))
    if error:
        return {"ok": False, "reason": error}
    if code != 0:
        return {"ok": False, "reason": f"exit {code}: {err.strip()[:200]}"}
    try:
        doc = json.loads(out)
    except Exception as e:
        return {"ok": False, "reason": f"parse-error: {e}"}
    if doc.get("protocol") != "hmi-report/1":
        return {"ok": False, "reason": f"protocol mismatch: {doc.get('protocol')!r}"}
    points_by_id = {p["id"]: p for p in doc.get("points", []) if "id" in p}
    return {"ok": True, "doc": doc, "points_by_id": points_by_id}


def adapt_native(cfg, source_cache):
    """Reader rules R-1..R-4 (PROTOCOL.md §3), verbatim."""
    src_id = cfg["source"]
    point_id = cfg["point"]
    entry = source_cache.get(src_id)
    if entry is None or not entry.get("ok"):
        reason = entry.get("reason") if entry else "source not fetched this run"
        # R-1
        return {"state": None, "quality": "probe_error",
                "evidence": f"native source {src_id!r} failed: {reason}", "source": src_id}
    doc_point = entry["points_by_id"].get(point_id)
    if doc_point is None:
        # R-2
        return {"state": None, "quality": "undetermined",
                "evidence": f"point {point_id!r} absent from {src_id} document (R-2)", "source": src_id}
    if not doc_point.get("ran", True):
        # R-4
        skip = doc_point.get("skip_reason")
        return {"state": None, "quality": "undetermined", "skip_reason": skip,
                "evidence": f"ran:false skip_reason={skip}", "source": src_id}
    state = doc_point.get("state")
    quality = doc_point.get("quality") or "good"
    findings = doc_point.get("findings") or []
    if findings:
        evidence = "; ".join(f"[{f.get('severity')}] {f.get('label')}: {f.get('text')}" for f in findings)
    else:
        evidence = "no findings"
    out = {"state": state, "quality": quality, "evidence": evidence,
           "remedy": doc_point.get("remedy"), "source": src_id}
    if doc_point.get("deferred") is not None:
        # R-6: the emitter's deferral CLAIM; the collector resolves it (hmi.deferral), never this adapter.
        out["deferral_spec"] = doc_point["deferred"]
    return out


def adapt_exit_code(cfg, home):
    argv = cfg["argv"]
    cwd = _cwd_for(home, cfg)
    code, out, err, error = _run(argv, cwd, cfg.get("timeout_s", 20))
    src = " ".join(argv)
    if error:
        return {"state": None, "quality": "probe_error", "evidence": error, "source": src}
    exit_map = cfg.get("exit_map", {})
    state = exit_map.get(str(code))
    if state is None:
        return {"state": None, "quality": "probe_error",
                "evidence": f"unmapped exit code {code}", "source": src}
    tail = out.strip().splitlines()[-1] if out.strip() else (err.strip().splitlines()[-1] if err.strip() else "")
    return {"state": state, "quality": "good", "evidence": tail, "source": src}


def adapt_tail_sentinel(cfg, home):
    argv = cfg["argv"]
    cwd = _cwd_for(home, cfg)
    code, out, err, error = _run(argv, cwd, cfg.get("timeout_s", 60))
    src = " ".join(argv)
    if error:
        return {"state": None, "quality": "probe_error", "evidence": error, "source": src}
    lines = [l for l in out.splitlines() if l.strip()]
    if not lines:
        return {"state": None, "quality": "probe_error", "evidence": "no output", "source": src}
    last = lines[-1]
    if re.search(cfg["pass_regex"], last):
        return {"state": "pass", "quality": "good", "evidence": last, "source": src}
    return {"state": "fail", "quality": "good", "evidence": last, "source": src}


def adapt_empty_output(cfg, home):
    argv = cfg["argv"]
    cwd = _cwd_for(home, cfg)
    code, out, err, error = _run(argv, cwd, cfg.get("timeout_s", 20))
    src = " ".join(argv)
    if error:
        return {"state": None, "quality": "probe_error", "evidence": error, "source": src}
    no_hit_exit = cfg.get("no_hit_exit", 1)
    stripped = out.strip()
    if not stripped and code == no_hit_exit:
        return {"state": "pass", "quality": "good", "evidence": "", "source": src}
    if stripped:
        return {"state": "fail", "quality": "good", "evidence": stripped.splitlines()[0], "source": src}
    return {"state": None, "quality": "probe_error",
            "evidence": f"exit {code}, empty output, not the declared no-hit code", "source": src}


def adapt_line_scan(cfg, home):
    argv = cfg["argv"]
    cwd = _cwd_for(home, cfg)
    code, out, err, error = _run(argv, cwd, cfg.get("timeout_s", 20))
    src = " ".join(argv)
    if error:
        return {"state": None, "quality": "probe_error", "evidence": error, "source": src}
    # INV-3: a command that crashed prints no fail/warn line either. Only an exit
    # code the registry DECLARES as a normal outcome may be scanned; anything else
    # is a probe error, never "no line matched -> pass".
    ok_exits = cfg.get("ok_exits", [0])
    if code not in ok_exits:
        return {"state": None, "quality": "probe_error",
                "evidence": f"exit {code} not in ok_exits {ok_exits}: {(err or out).strip()[:200]}", "source": src}
    fail_re = cfg.get("fail_regex")
    warn_re = cfg.get("warn_regex")
    fail_lines = [l for l in out.splitlines() if fail_re and re.search(fail_re, l)]
    if fail_lines:
        return {"state": "fail", "quality": "good", "evidence": "; ".join(fail_lines[:3]), "source": src}
    warn_lines = [l for l in out.splitlines() if warn_re and re.search(warn_re, l)]
    if warn_lines:
        return {"state": "warn", "quality": "good", "evidence": "; ".join(warn_lines[:3]), "source": src}
    # A declared pass_regex makes pass POSITIVE: silence (or a changed output
    # grammar) is then a probe error instead of a green light.
    pass_re = cfg.get("pass_regex")
    if pass_re:
        pass_lines = [l for l in out.splitlines() if re.search(pass_re, l)]
        if not pass_lines:
            return {"state": None, "quality": "probe_error",
                    "evidence": "no fail/warn line AND no pass_regex line: output grammar changed?", "source": src}
        return {"state": "pass", "quality": "good", "evidence": pass_lines[0], "source": src}
    return {"state": "pass", "quality": "good", "evidence": "no fail/warn line matched", "source": src}


def _parse_utc(ts):
    try:
        return datetime.datetime.strptime(ts.rstrip("Z"), "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def adapt_status_file(cfg, home):
    raw_path = cfg["path"]
    path = Path(raw_path) if os.path.isabs(raw_path) or ":" in raw_path[:3] else Path(home) / raw_path
    src = str(path)
    if not path.exists():
        return {"state": None, "quality": "probe_error", "evidence": f"missing: {src}", "source": src}
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as e:
        return {"state": None, "quality": "probe_error", "evidence": f"read error: {e}", "source": src}

    fmt = cfg.get("format", "text")
    ok_values = cfg.get("ok_values", [])
    warn_values = cfg.get("warn_values", [])
    ts = None
    if fmt == "json":
        try:
            data = json.loads(raw)
        except Exception as e:
            return {"state": None, "quality": "probe_error", "evidence": f"parse error: {e}", "source": src}
        field = cfg.get("field")
        value = data.get(field) if field else None
        ts_field = cfg.get("ts_field")
        if ts_field:
            ts = data.get(ts_field)
        evidence = f"{field}={value!r}"
    else:
        ok_regex = cfg.get("ok_regex")
        if ok_regex:
            value = "ok" if re.search(ok_regex, raw) else "not-ok"
            ok_values, warn_values = ["ok"], []
        else:
            value = raw.strip()
        evidence = f"content={value!r}"

    if value in ok_values:
        state = "pass"
    elif value in warn_values:
        state = "warn"
    else:
        state = "fail"

    max_age_s = cfg.get("max_age_s")
    if max_age_s:
        age = None
        if ts:
            dt = _parse_utc(ts)
            if dt:
                age = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds()
        if age is None:
            try:
                age = time.time() - path.stat().st_mtime
            except OSError:
                age = None
        if age is not None and age > max_age_s:
            return {"state": state, "quality": "stale", "stale_reason": "source-older-than-max-age",
                    "evidence": evidence + f" (age {age:.0f}s > max_age_s {max_age_s}s)", "source": src}
    return {"state": state, "quality": "good", "evidence": evidence, "source": src}


def adapt_fs_link(cfg, home):
    raw_path = cfg["path"]
    path = Path(raw_path) if os.path.isabs(raw_path) or ":" in raw_path[:3] else Path(home) / raw_path
    src = str(path)
    try:
        exists = path.exists()
    except OSError as e:
        return {"state": None, "quality": "probe_error", "evidence": str(e), "source": src}
    if not exists:
        return {"state": None, "quality": "probe_error", "evidence": f"not found: {src}", "source": src}
    expect = cfg.get("expect_target")
    if expect:
        try:
            resolved = str(path.resolve())
        except OSError as e:
            return {"state": None, "quality": "probe_error", "evidence": str(e), "source": src}
        if os.path.normcase(resolved) != os.path.normcase(str(Path(expect).resolve())):
            return {"state": "fail", "quality": "good",
                    "evidence": f"resolves to {resolved}, expected {expect}", "source": src}
    return {"state": "pass", "quality": "good", "evidence": f"exists: {src}", "source": src}


def adapt_manual(cfg):
    cmd = cfg.get("command_text", "")
    return {"state": None, "quality": "undetermined", "skip_reason": "manual-only",
            "evidence": cmd, "remedy": cmd, "source": "manual"}


ADAPTERS = {
    "exit-code": adapt_exit_code,
    "tail-sentinel": adapt_tail_sentinel,
    "empty-output": adapt_empty_output,
    "line-scan": adapt_line_scan,
    "status-file": adapt_status_file,
    "fs-link": adapt_fs_link,
}


def run_adapter(point, home, source_cache):
    """Dispatch by point['adapter']. `native` and `manual` use their own signatures."""
    adapter = point["adapter"]
    cfg = point.get("adapter_config", {})
    if adapter == "native":
        return adapt_native(cfg, source_cache)
    if adapter == "manual":
        return adapt_manual(cfg)
    fn = ADAPTERS.get(adapter)
    if fn is None:
        return {"state": None, "quality": "probe_error", "evidence": f"unknown adapter {adapter!r}", "source": None}
    return fn(cfg, home)
