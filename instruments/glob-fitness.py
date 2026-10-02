r"""Measure whether a path-scoped rule's globs can actually REACH the code it is about.

A rule under `~/.claude/rules/` loads only on `path_glob_match`. If its globs
match no file that contains the thing the rule describes, the rule is a ghost:
it exists, it reads correctly, and it never fires. `shader-failure-modes.md`
sat in exactly that state for months — 1 fire in 1,094 sessions, because every
line of GLSL in its own source project lives in a `.ts` template string.

A low fire rate reads as ACCURACY only after this check comes back positive.

    python glob-fitness.py --rule ~/.claude/rules/shader-failure-modes.md \
                           --root <projects-root> --content "gl_FragColor|gl_Position|uniform sampler2D"

    python glob-fitness.py --rule <file> --root <dir> --content <regex> --list

`--content` is the ground truth: the regex that identifies a file the rule is
genuinely ABOUT. Recall is what matters (a rule that cannot reach its subject is
worthless); precision matters far less, because a path-scoped rule costs nothing
until a matching file is READ — so a false positive in a vendored tree that is
never opened is not a real cost. The report splits the two for that reason.
"""
import argparse
import fnmatch
import io
import os
import re
import sys

SKIP_PARTS = ("node_modules", ".git", "dist", "build", "bin", "obj", "publish",
              "venv", ".venv", "__pycache__", "coverage", "site-packages",
              "python_embeded", "archive", ".next", "target")
# Present on disk but effectively never opened, so a match here is not a real cost.
VENDORED_HINTS = ("toolchains", "vendor", "third_party", "tcl", "Lib")
TEXT_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".svelte", ".vue",
            ".glsl", ".frag", ".vert", ".vs", ".fs", ".py", ".cs", ".java",
            ".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".html", ".css")


def read_globs(rule_path):
    txt = io.open(rule_path, encoding="utf-8", errors="replace").read()
    if not txt.startswith("---"):
        return []
    fm = txt.split("---")[1]
    return re.findall(r'-\s*"([^"]+)"', fm) + re.findall(r"-\s*'([^']+)'", fm)


def expand(g):
    """Expand one brace group, which is all the `paths:` syntax uses in practice."""
    m = re.search(r"\{([^}]+)\}", g)
    if not m:
        return [g]
    return [g[:m.start()] + alt.strip() + g[m.end():] for alt in m.group(1).split(",")]


def matches(path, flat):
    base = path.split("/")[-1]
    for g in flat:
        if fnmatch.fnmatch(path, g):
            return g
        if g.startswith("**/") and fnmatch.fnmatch(base, g[3:]):
            return g
        if g.endswith("/**") and ("/" + g[3:-3] + "/") in ("/" + path):
            return g
    return None


def skipped(path):
    return any(p in SKIP_PARTS for p in path.replace("\\", "/").split("/"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--content", required=True, help="regex identifying a file the rule is ABOUT")
    ap.add_argument("--list", action="store_true", help="print every matched file")
    a = ap.parse_args()

    rule = os.path.expanduser(a.rule)
    globs = read_globs(rule)
    if not globs:
        print("no `paths:` frontmatter in %s — nothing to measure" % rule)
        return 2
    flat = [x for g in globs for x in expand(g)]
    content = re.compile(a.content)

    files, truth, hits = [], set(), []
    for dp, dn, fn in os.walk(a.root):
        if skipped(dp):
            dn[:] = []
            continue
        for f in fn:
            if not f.endswith(TEXT_EXT):
                continue
            p = os.path.join(dp, f).replace("\\", "/")
            files.append(p)
            is_truth = False
            try:
                if os.path.getsize(p) <= 2_000_000:
                    is_truth = bool(content.search(
                        io.open(p, encoding="utf-8", errors="replace").read()))
            except Exception:
                pass
            if is_truth:
                truth.add(p)
            g = matches(p, flat)
            if g:
                hits.append((is_truth, g, p))

    live = [h for h in hits if not any(v in h[2] for v in VENDORED_HINTS)]
    tp = [h for h in hits if h[0]]
    miss = sorted(p for p in truth if p not in {h[2] for h in hits})

    print("rule   : %s   (%d globs -> %d after brace expansion)" % (rule, len(globs), len(flat)))
    print("root   : %s   (%d source files scanned)" % (a.root, len(files)))
    print("truth  : %d file(s) match --content" % len(truth))
    print()
    print("  RECALL     %5.1f%%  (%d of %d) %s"
          % (100.0 * len(tp) / len(truth) if truth else 0.0, len(tp), len(truth),
             "<-- THE NUMBER THAT MATTERS" if truth else ""))
    print("  precision  %5.1f%%  (%d of %d matched)"
          % (100.0 * len(tp) / len(hits) if hits else 0.0, len(tp), len(hits)))
    print("  precision on files that are actually OPENED (vendored trees dropped): "
          "%5.1f%%  (%d of %d)"
          % (100.0 * len(tp) / len(live) if live else 0.0, len(tp), len(live)))
    if miss:
        print()
        print("  UNREACHED — the rule is about these and cannot load on them:")
        for p in miss[:20]:
            print("    %s" % p.replace(a.root.replace("\\", "/") + "/", ""))
    if a.list:
        print()
        print("  matched:")
        for has, g, p in sorted(hits, key=lambda r: not r[0]):
            print("    %s %-30s %s" % ("HIT " if has else "    ", g,
                                       p.replace(a.root.replace("\\", "/") + "/", "")))
    print()
    if truth and not tp:
        print("  VERDICT: ghost rule. It cannot fire on its own subject.")
    elif miss:
        print("  VERDICT: partial. %d subject file(s) unreachable." % len(miss))
    else:
        print("  VERDICT: reaches every file it is about (within this root).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
