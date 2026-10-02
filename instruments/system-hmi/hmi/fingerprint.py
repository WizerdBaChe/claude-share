"""Input fingerprints for `static` points (PIM v1.3, D-6 ruled 2026-09-19).

A slow point's verdict stays VALID while the things it judges have not changed -- the SCADA
shape: static data is not polled, it is re-read on a change event and on a slow integrity poll
(DNP3 class 0 + integrity poll; Ignition "driven" groups). The fingerprint is the change event.

fingerprint(home, inputs) hashes (relative path, size, mtime_ns) of every file under the declared
inputs, plus the interpreter version (a "major update" every static point depends on). It reads
metadata only -- never file contents -- so it is cheap enough to compute on every collect.

Known limit: it covers DECLARED inputs only. A suite that depends on something undeclared (an
environment variable, a module elsewhere) can change verdict with an unchanged fingerprint; the
integrity poll (registry/scan.json `integrity_poll_days`) is what bounds that blind spot, which is
why it may never be "never".
"""
import hashlib
import os
import sys
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".git", "node_modules", "out", ".pytest_cache"}


def _resolve(home, item):
    return Path(item) if (":" in item[:3] or item.startswith("/")) else Path(home) / item


def fingerprint(home, inputs):
    h = hashlib.sha256()
    h.update(("py:%d.%d" % sys.version_info[:2]).encode())
    for item in sorted(set(inputs)):
        root = _resolve(home, item)
        h.update(b"\x00" + item.encode("utf-8"))
        if root.is_file():
            files = [root]
        elif root.is_dir():
            files = []
            for d, dirs, names in os.walk(root):
                dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
                files += [Path(d) / n for n in sorted(names) if not n.endswith(".pyc")]
        else:
            h.update(b"<absent>")
            continue
        for f in files:
            try:
                st = f.stat()
            except OSError:
                continue
            rel = str(f.relative_to(root)) if f != root else f.name
            h.update(f"{rel}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8", "replace"))
    return h.hexdigest()[:16]
