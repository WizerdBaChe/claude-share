"""Local HMI service (HMI-06, INV-8): serves the overview and re-runs READ-ONLY probes on request.

Boundaries, each one asserted in controls.py:
  * binds 127.0.0.1 only;
  * a request whose Host (or Origin, when present) is not this loopback address and port is refused (403)
    - a web page on another origin cannot drive the service through the user's browser;
  * POST /refresh needs the per-start token that only the served page carries (403 otherwise);
  * the only thing a request can start is `hmi.py collect` with ONE id taken from the registry or one of
    two tier names; an unknown id is 404 and nothing is started; the request never supplies a command,
    a path or an argument string;
  * every child process goes through `spawn`, so a test can count them.
stdlib only. No state is kept here: the page is rendered from out/snapshot.json on every GET.

Code drift (2026-09-23): the page TEMPLATE is imported once at start, so a long-lived service keeps serving
the code it started with - the desktop shortcut reused one and showed the pre-change page. /api/meta
therefore reports `code` (fingerprint of the code this process loaded), `disk` (the same fingerprint of the
files now on disk) and `pid`; open_hmi.pyw restarts a service whose code != disk, and the page says so.
"""
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import registry as registry_mod
from . import snapshot as snapshot_mod

BIND = "127.0.0.1"
DEFAULT_PORT = 8787
MAX_BODY = 4096
COLLECT_TIMEOUT_S = 900
TIERS = {"cheap": [], "full": ["--full"]}


def code_fingerprint(tool_dir):
    """sha256 over the code that builds the served page: hmi.py, mimic_view.py and hmi/*.py (path + bytes).
    Data (registry/*.json, out/) is read per request and is deliberately NOT part of it."""
    tool_dir = Path(tool_dir)
    files = [tool_dir / "hmi.py", tool_dir / "mimic_view.py"] + sorted((tool_dir / "hmi").glob("*.py"))
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(tool_dir).as_posix().encode("utf-8") + b"\0")
        try:
            h.update(f.read_bytes())
        except OSError:
            h.update(b"<missing>")
        h.update(b"\0")
    return h.hexdigest()[:16]


def default_spawn(argv):
    """Run one collect and return (returncode, combined output). The single place a child is started."""
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=COLLECT_TIMEOUT_S)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def resolve_request(body, reg):
    """Map a /refresh body to collect arguments. Returns (args, None) or (None, (status, message)).
    Exactly one selector; ids must exist in the registry; extra keys are ignored."""
    chosen = [(k, body.get(k)) for k in ("point_id", "subsystem_id", "tier") if body.get(k) is not None]
    if len(chosen) != 1 or not isinstance(chosen[0][1], str):
        return None, (400, "exactly one of point_id / subsystem_id / tier, as a string")
    key, value = chosen[0]
    if key == "tier":
        if value not in TIERS:
            return None, (404, "unknown tier")
        return list(TIERS[value]), None
    known = {x["id"] for x in reg["points" if key == "point_id" else "subsystems"]}
    if value not in known:
        return None, (404, "unknown id")
    return ["--point" if key == "point_id" else "--subsystem", value], None


def make_server(tool_dir, render_page, port=DEFAULT_PORT, spawn=default_spawn, token=None):
    """render_page(snap, groups, live) -> html. Returns a ThreadingHTTPServer (not yet serving)."""
    tool_dir = Path(tool_dir)
    token = token or secrets.token_urlsafe(24)
    code = code_fingerprint(tool_dir)

    class Handler(BaseHTTPRequestHandler):
        server_version = "system-hmi"

        def log_message(self, fmt, *args):   # quiet: one line per refresh is printed by _refresh itself
            pass

        def _allowed(self):
            port_now = self.server.server_address[1]
            ok_hosts = {f"127.0.0.1:{port_now}", f"localhost:{port_now}"}
            if (self.headers.get("Host") or "") not in ok_hosts:
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin in {"http://" + h for h in ok_hosts}

        def _send(self, status, payload, ctype="application/json; charset=utf-8"):
            data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self._allowed():
                return self._send(403, {"error": "host not allowed"})
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                snap = snapshot_mod.load(str(tool_dir / "out"))
                try:
                    groups = json.loads((tool_dir / "registry" / "groups.json").read_text(encoding="utf-8"))
                    groups = groups if isinstance(groups, list) else groups.get("groups", [])
                except (OSError, ValueError):
                    groups = []
                return self._send(200, render_page(snap, groups, {"token": token, "code": code}).encode("utf-8"),
                                  "text/html; charset=utf-8")
            if path == "/api/meta":
                snap = snapshot_mod.load(str(tool_dir / "out")) or {}
                return self._send(200, {"finished_at": (snap.get("run") or {}).get("finished_at"),
                                        "code": code, "disk": code_fingerprint(tool_dir), "pid": os.getpid()})
            if path == "/refresh":
                return self._send(405, {"error": "POST only"})
            if path == "/favicon.ico":   # no icon: answer quietly instead of a console error on every load
                return self._send(204, b"", "image/x-icon")
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            if not self._allowed():
                return self._send(403, {"error": "host not allowed"})
            if self.path.split("?", 1)[0] != "/refresh":
                return self._send(404, {"error": "not found"})
            try:
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0 or length > MAX_BODY:
                    return self._send(400, {"error": "body size"})
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError
            except (ValueError, UnicodeDecodeError):
                return self._send(400, {"error": "body is not a JSON object"})
            if not hmac.compare_digest(str(body.get("token") or ""), token):
                return self._send(403, {"error": "token"})
            reg = registry_mod.load_registry(tool_dir / "registry")
            args, err = resolve_request(body, reg)
            if err:
                return self._send(err[0], {"error": err[1]})
            argv = [sys.executable, "-X", "utf8", str(tool_dir / "hmi.py"), "collect"] + args
            try:
                rc, out = spawn(argv)
            except subprocess.TimeoutExpired:
                return self._send(504, {"error": f"collect did not finish in {COLLECT_TIMEOUT_S}s"})
            print(f"refresh {args or ['cheap']} -> rc={rc}", flush=True)
            if rc == 0:
                return self._send(200, {"ok": True, "detail": out[-300:]})
            if rc == 4:
                return self._send(409, {"error": "locked", "detail": out[-300:]})
            return self._send(500, {"error": "collect failed", "rc": rc, "detail": out[-600:]})

    srv = ThreadingHTTPServer((BIND, port), Handler)
    srv.token = token
    srv.code = code
    return srv
