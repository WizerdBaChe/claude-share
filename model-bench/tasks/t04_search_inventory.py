"""T04 — find every definition of handle_* across a 30-file tree; exact set gate. Dispatch row: 'Search / inventory' (cheap–mid)."""
import random
from _common import strip_fences, verdict, write

ID = "t04_search_inventory"
CATEGORY = "search-inventory"
DISPATCH_ROW = "Search / inventory / read-many-files"
EXPECTED_TIER = "cheap"
TOOLS = "default"
MAX_TURNS = 12
TIMEOUT_S = 420

PROMPT = """In the current directory tree (`src/`), find every Python FUNCTION DEFINITION whose
name starts with `handle_`. Count only real `def` statements — not mentions in comments,
docstrings, strings, or calls. Methods inside classes count. Output ONLY lines of the form
`relative/path.py:LINE:function_name` — the path relative to the CURRENT directory, so it begins
with `src/` — one per definition, sorted lexicographically. No prose."""

DIRS = ["src/api", "src/api/v2", "src/core", "src/core/jobs", "src/util", "src/cli"]
NAMES = ["load", "parse", "render", "flush", "rotate", "merge", "split", "index", "notify", "seed"]


def _tree():
    rng = random.Random(777)
    files, gold = {}, set()
    for i in range(30):
        d = DIRS[i % len(DIRS)]
        rel = f"{d}/{rng.choice(NAMES)}_{i:02d}.py"
        lines = ['"""Module docstring. Mentions handle_request only as text."""', "import os", ""]
        n_defs = rng.randint(1, 4)
        for k in range(n_defs):
            roll = rng.random()
            if roll < 0.22:
                fn = f"handle_{rng.choice(NAMES)}_{i}{k}"
                if rng.random() < 0.3:  # method inside a class
                    lines += [f"class Worker{k}:", f"    def {fn}(self, x):", "        return x", ""]
                    gold.add(f"{rel}:{len(lines) - 2}:{fn}")
                else:
                    lines += [f"def {fn}(x):", "    return x", ""]
                    gold.add(f"{rel}:{len(lines) - 2}:{fn}")
            elif roll < 0.35:  # decoys
                lines += [f"# TODO: def handle_{rng.choice(NAMES)} later", f"result = handle_{rng.choice(NAMES)}_call(1)",
                          f'label = "def handle_{rng.choice(NAMES)}"', ""]
            else:
                lines += [f"def {rng.choice(NAMES)}_{k}(x):", "    return x", ""]
        files[rel] = "\n".join(lines) + "\n"
    return files, gold


FILES, GOLD = _tree()


def setup(workdir):
    for rel, content in FILES.items():
        write(workdir, rel, content)


def check(result, workdir):
    got = [l.strip().strip("`") for l in strip_fences(result).splitlines() if l.strip()]
    prose = [l for l in got if l.count(":") < 2 or not l.split(":")[0].endswith(".py")]
    if prose:
        return verdict(False, f"non-conforming line: {prose[0][:60]!r}")
    norm = {l.lstrip("./") for l in got}
    if norm == GOLD and got == sorted(got):
        return verdict(True, f"{len(GOLD)}/{len(GOLD)} definitions, exact set, sorted")
    missing, extra = GOLD - norm, norm - GOLD
    if not missing and not extra:
        return verdict(False, "set correct but not sorted", score=0.9)
    return verdict(False, f"missing={len(missing)} extra={len(extra)} of {len(GOLD)} (e.g. {sorted(missing | extra)[0]})",
                   score=max(0.0, 1 - (len(missing) + len(extra)) / len(GOLD)))


CONTROLS = [
    {"result": "\n".join(sorted(GOLD)), "expect": True},
    {"result": "\n".join(sorted(GOLD)[1:]), "expect": False},
    {"result": "\n".join(sorted(GOLD) + ["src/api/load_00.py:1:handle_request"]), "expect": False},
    {"result": "Found these:\n" + "\n".join(sorted(GOLD)), "expect": False},
]
