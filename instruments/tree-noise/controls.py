"""Two-sided controls for tools/tree-noise/noise.py (rung 0-1: one case per class, each
noise class paired with the nearest REAL change it must not swallow).

Every case asserts the CLASS a path receives — the value a defect would change — and the
negative twin of each noise case differs from it by one content-bearing edit, so a
predicate that proves nothing (e.g. `--name-only` ignoring `--ignore-cr-at-eol`) turns a
pair of expected values into two identical ones and fails here.

Run:  python tools/tree-noise/controls.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import noise  # noqa: E402

HOOK = HERE.parent.parent / "hooks" / "tree_noise_gist.py"
results = []


def check(cid, ok, detail=""):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'}  {cid}" + ("" if ok else f"  <- {detail}"))


def sh(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0 and args[0] not in ("merge",):
        raise SystemExit(f"setup: git {' '.join(args)} failed: {r.stderr}")
    return r


def mkrepo(root: Path, files: dict[str, bytes], attrs: str = "") -> Path:
    root.mkdir(parents=True)
    sh(root, "init", "-q", "-b", "main")
    sh(root, "config", "core.autocrlf", "false")
    sh(root, "config", "user.email", "t@t")
    sh(root, "config", "user.name", "t")
    if attrs:
        files = {**files, ".gitattributes": attrs.encode()}
    for p, b in files.items():
        (root / p).parent.mkdir(parents=True, exist_ok=True)
        (root / p).write_bytes(b)
    sh(root, "add", "-A")
    sh(root, "commit", "-q", "-m", "base")
    return root


def cls_of(res, path):
    hits = [e["cls"] for e in res["entries"] if e["path"] == path]
    return hits[0] if len(hits) == 1 else f"<{len(hits)} entries>"


BASE = b'views:\n  - type: table\n    name: "All native notes"\n    order: [a, b]\n'
BASE_UNQUOTED = b"views:\n  - type: table\n    name: All native notes\n    order: [a, b]\n"
BASE_RENAMED = b"views:\n  - type: table\n    name: All notes\n    order: [a, b]\n"
MD = b'---\nxi: 1\nwhat: "x"\naliases: ["a", "b"]\n---\nbody\n'
MD_UNQUOTED = b"---\nxi: 1\nwhat: x\naliases: [a, b]\n---\nbody\n"

with tempfile.TemporaryDirectory(prefix="treenoise-") as td:
    td = Path(td)
    r = mkrepo(td / "r", {
        "a.base": BASE, "b.base": BASE, "n.md": MD,
        "eol.txt": b"one\ntwo\n", "eol2.txt": b"one\ntwo\n",
        "gen.md": b"v1\n", "other.md": b"v1\n",
        "cfg.json": b'{"a": 1, "b": [1, 2]}\n', "cfg2.json": b'{"a": 1}\n', "bad.json": b'{"a": 1}\n',
        "mv.txt": b"moved content\n", "mv2.txt": b"moved and edited\n",
    }, attrs="gen.md tool-appended\n")
    (r / "a.base").write_bytes(BASE_UNQUOTED)                    # quotes dropped
    (r / "b.base").write_bytes(BASE_RENAMED)                     # value changed
    (r / "n.md").write_bytes(MD_UNQUOTED)                        # front-matter re-serialised
    (r / "eol.txt").write_bytes(b"one\r\ntwo\r\n")               # CRLF only
    (r / "eol2.txt").write_bytes(b"one\r\ntwo!\r\n")             # CRLF + edit
    (r / "gen.md").write_bytes(b"v2\n")
    (r / "other.md").write_bytes(b"v2\n")
    (r / "cfg.json").write_bytes(b'{\n  "b": [1, 2],\n  "a": 1\n}\n')   # reordered, reformatted
    (r / "cfg2.json").write_bytes(b'{"a": 2}\n')
    (r / "bad.json").write_bytes(b'{"a": 1,,}\n')                # no longer parses
    os.rename(r / "mv.txt", r / "moved.txt")
    os.rename(r / "mv2.txt", r / "moved2.txt")
    (r / "moved2.txt").write_bytes(b"moved and edited!\n")
    (r / "fresh.txt").write_bytes(b"new\n")
    res = noise.classify(r)

    check("C1+ .base with quotes dropped -> format-only", cls_of(res, "a.base") == "format-only", cls_of(res, "a.base"))
    check("C1- .base with a value changed -> real", cls_of(res, "b.base") == "real", cls_of(res, "b.base"))
    check("C2  .md front-matter re-serialised -> real (known-excluded: never parsed)",
          cls_of(res, "n.md") == "real", cls_of(res, "n.md"))
    check("C3+ CRLF-only rewrite -> eol-only", cls_of(res, "eol.txt") == "eol-only", cls_of(res, "eol.txt"))
    check("C3- CRLF rewrite + one edit -> real", cls_of(res, "eol2.txt") == "real", cls_of(res, "eol2.txt"))
    check("C4+ edit of a tool-appended path -> generated", cls_of(res, "gen.md") == "generated", cls_of(res, "gen.md"))
    check("C4- identical edit of an unmarked path -> real", cls_of(res, "other.md") == "real", cls_of(res, "other.md"))
    check("C5+ .json reordered/reformatted -> format-only", cls_of(res, "cfg.json") == "format-only", cls_of(res, "cfg.json"))
    check("C5- .json value changed -> real", cls_of(res, "cfg2.json") == "real", cls_of(res, "cfg2.json"))
    check("C5b .json that no longer parses -> real", cls_of(res, "bad.json") == "real", cls_of(res, "bad.json"))
    check("C6+ moved, not edited -> rename-only pair", cls_of(res, "mv.txt -> moved.txt") == "rename-only",
          [e for e in res["entries"] if "mv" in e["path"] or "moved" in e["path"]])
    check("C6- moved AND edited -> deletion real + new path untracked",
          (cls_of(res, "mv2.txt"), cls_of(res, "moved2.txt")) == ("real", "untracked"),
          (cls_of(res, "mv2.txt"), cls_of(res, "moved2.txt")))
    check("C7  a brand-new file -> untracked (not noise)", cls_of(res, "fresh.txt") == "untracked", cls_of(res, "fresh.txt"))
    want = {"format-only": 2, "eol-only": 1, "generated": 1, "rename-only": 1, "real": 7, "untracked": 2, "undetermined": 0}
    check("C8  counts close over every path (none dropped, none double-counted)", res["counts"] == want, res["counts"])

    # undetermined: a merge conflict is a state the tool does not model
    c = mkrepo(td / "c", {"x.base": b"k: 1\n"})
    sh(c, "switch", "-q", "-c", "side")
    (c / "x.base").write_bytes(b"k: 2\n")
    sh(c, "commit", "-qam", "side")
    sh(c, "switch", "-q", "main")
    (c / "x.base").write_bytes(b"k: 3\n")
    sh(c, "commit", "-qam", "main")
    sh(c, "merge", "-q", "side")
    rc = noise.classify(c)
    check("C9  unmerged conflict -> undetermined, excluded from noise",
          cls_of(rc, "x.base") == "undetermined" and noise.noise_count(rc) == 0, rc["entries"])

    check("C10 not a git repo -> None", noise.classify(td) is None)

    # summary / hook surface
    check("C11 summary silent when there is no noise",
          noise.summary(noise.classify(mkrepo(td / "clean", {"a": b"1\n"}))) == "")
    s = noise.summary(res)
    check("C12 summary names counts and noise paths", "2 format-only" in s and "a.base (format-only)" in s
          and "7 real" in s and not re.search(r"(?<![\w.])n\.md", s), s)

    def hook(cwd):
        env = dict(os.environ, TREE_NOISE_TELEMETRY=str(td / "tel"))
        p = subprocess.run([sys.executable, "-X", "utf8", str(HOOK)], input=json.dumps({"cwd": str(cwd)}).encode(),
                           capture_output=True, env=env, timeout=60)
        return p.returncode, p.stdout.decode("utf-8", "replace")

    code, out = hook(r)
    check("H1 hook: noise present -> one notice naming itself first, exit 0",
          code == 0 and out.startswith("[tree-noise] tree_noise_gist, a local SessionStart hook") and "a.base" in out, out)
    check("H2 hook: notice says nothing needs doing and names its telemetry row",
          "Nothing needs doing" in out and "telemetry/tree-noise-gist.jsonl" in out, out)
    code, out = hook(td / "clean")
    check("H3 hook: clean tree -> silent", code == 0 and out.strip() == "", out)
    real_only = mkrepo(td / "ro", {"a.md": b"1\n"})
    (real_only / "a.md").write_bytes(b"2\n")
    code, out = hook(real_only)
    check("H4 hook: only real changes -> silent (the snapshot already shows them)", code == 0 and out.strip() == "", out)
    code, out = hook(td / "nowhere-at-all")
    check("H5 hook: cwd not a repo / missing -> silent, exit 0 (fail-open)", code == 0 and out.strip() == "", out)
    rows = (td / "tel" / "tree-noise-gist.jsonl").read_text(encoding="utf-8").splitlines()
    check("H6 hook: every run leaves a telemetry row, emitted flag matches output",
          len(rows) == 4 and [json.loads(x)["emitted"] for x in rows] == [True, False, False, False], rows)

print(f"\n{'ALL PASS' if all(results) else 'FAILED'} {sum(results)}/{len(results)}")
sys.exit(0 if all(results) else 1)
