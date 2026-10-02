"""Extract bundled prompt text from an installed Claude Code binary.

Read-only. Used to diff the /doctor prompt and the bundled claude-api
skill guides (for example ``shared/prompt-audit.md``) across CLI versions,
so a comparison record can quote the running build instead of memory.

Usage (from ~/.claude):
    python -X utf8 tools/cc-delta/extract_bundled_prompts.py 2.1.283 <out_dir>
    python -X utf8 tools/cc-delta/extract_bundled_prompts.py 2.1.281 2.1.283 <out_dir>

For each version it writes ``doctor-<ver>.md`` (the template literal that
starts with ``# Claude Code Doctor``, JS escapes decoded; ``${...}`` branches
are left visible because the 2.1.283 check 7 is a conditional) and, when the
``zstandard`` module is importable, ``bundled-<ver>-<slug>.md`` for every
zstd frame whose decompressed text starts with a Markdown heading listed in
HEADINGS. Given two versions it also prints a unified diff of the doctor
prompt. Frames are located by the zstd magic; a frame that fails to
decompress is skipped silently, so an empty result for a heading means
"not found in this build", not "absent from the product".

Binaries: ``~/.local/share/claude/versions/<ver>`` (native install layout).
"""
from __future__ import annotations

import difflib
import pathlib
import re
import sys

VERSIONS_DIR = pathlib.Path.home() / ".local/share/claude/versions"
DOCTOR_START = b"# Claude Code Doctor"
# The template literal ends right before the command registration that follows it.
DOCTOR_END_RE = re.compile(rb'\}function \w+\(\)\{\w+\(\{name:"doctor"')
ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"
HEADINGS = (
    b"# Prompt Audit",
    b"# Building LLM-Powered Applications with Claude",
    b"# Cost Optimization",
    b"# Building an Eval",
    b"# Prompt Caching",
    b"# Preserved Thinking",
)
BS = chr(92)


def decode_js_template(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")
    text = text.replace(BS + "n", "\n").replace(BS + "`", "`").replace(BS + BS, BS)
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)


def extract_doctor(data: bytes) -> str | None:
    i = data.find(DOCTOR_START)
    if i < 0:
        return None
    m = DOCTOR_END_RE.search(data, i)
    if not m:
        return None
    return decode_js_template(data[i:m.start()])


def extract_bundled(data: bytes):
    try:
        import zstandard as zstd  # type: ignore
    except ImportError:
        print("zstandard module not importable; skipping bundled guides", file=sys.stderr)
        return
    dctx = zstd.ZstdDecompressor()
    for m in re.finditer(re.escape(ZSTD_MAGIC), data):
        s = m.start()
        try:
            out = dctx.decompress(data[s:s + 2_000_000], max_output_size=8_000_000)
        except Exception:
            continue
        for h in HEADINGS:
            if out.startswith(h):
                slug = re.sub(rb"[^a-z0-9]+", b"-", h[2:].lower()).strip(b"-").decode()
                yield slug, out
                break


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    out_dir = pathlib.Path(argv[-1])
    versions = argv[:-1]
    out_dir.mkdir(parents=True, exist_ok=True)
    doctor_texts: dict[str, str] = {}
    for v in versions:
        path = VERSIONS_DIR / v
        if not path.exists():
            print(f"{v}: binary not found at {path}", file=sys.stderr)
            continue
        data = path.read_bytes()
        doc = extract_doctor(data)
        if doc is None:
            print(f"{v}: doctor prompt not found", file=sys.stderr)
        else:
            (out_dir / f"doctor-{v}.md").write_text(doc, encoding="utf-8")
            doctor_texts[v] = doc
            print(f"{v}: doctor prompt {len(doc)} chars -> doctor-{v}.md")
        seen: dict[str, int] = {}
        for slug, body in extract_bundled(data):
            # Two guides can share a heading (2.1.283 ships two "Preserved
            # Thinking" files); number the repeats instead of overwriting.
            n = seen.get(slug, 0)
            seen[slug] = n + 1
            name = f"bundled-{v}-{slug}{'' if n == 0 else f'-{n + 1}'}.md"
            (out_dir / name).write_bytes(body)
            print(f"{v}: bundled guide {slug} {len(body)} bytes -> {name}")
    if len(doctor_texts) == 2:
        a, b = versions[0], versions[1]
        diff = difflib.unified_diff(
            doctor_texts[a].splitlines(), doctor_texts[b].splitlines(),
            fromfile=f"doctor-{a}", tofile=f"doctor-{b}", lineterm="", n=1,
        )
        lines = list(diff)
        print(f"doctor prompt diff {a} -> {b}: {len(lines)} diff lines")
        for line in lines[:80]:
            print(line[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
