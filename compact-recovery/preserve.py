#!/usr/bin/env python3
"""Memory pipeline — preservation stage.

Archives Claude Code session transcripts before the platform's rolling
cleanup deletes them, then generates one mechanical digest card per session.

Invariants implemented:
  INV-1  archive copies are never modified after creation
  INV-2  digest cards are a pure function of the raw record (rebuildable)
  INV-3  zero model calls, zero network — mechanical extraction only
  INV-7  output dirs live outside version control (keep them gitignored)
  INV-8  all paths live in CONFIG below; portable by editing one block

Usage:
  python preserve.py            # incremental archive + digest
  python preserve.py --rebuild  # force-regenerate all digest cards
"""

import json
import re
import shutil
import sys
from pathlib import Path

# --- CONFIG: the single portability block (INV-8) -------------------------
HOME = Path.home()
CONFIG = {
    # where the agent platform writes live transcripts
    "source_dir": HOME / ".claude" / "projects",
    # permanent raw-record archive (append-only)
    "archive_dir": HOME / ".claude" / "memory-archive" / "raw",
    # digest cards, one .md per session
    "digest_dir": HOME / ".claude" / "memory-archive" / "digests",
    # per-message truncation in digest cards (chars)
    "user_msg_max": 1200,
    "assistant_msg_max": 500,
    # skip sessions with fewer real user prompts than this (noise sessions)
    "min_user_messages": 1,
}
# --------------------------------------------------------------------------

NOISE_PREFIXES = ("<system-reminder>", "<local-command", "<command-name>",
                  "Caveat: the messages below")


def text_of(content):
    """Flatten a message content field to plain text, dropping tool blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def clean(text):
    """Strip embedded system-reminder blocks and collapse whitespace."""
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text,
                  flags=re.DOTALL)
    return text.strip()


def truncate(text, limit):
    return text if len(text) <= limit else text[:limit] + " …[truncated]"


def parse_session(jsonl_path):
    """Extract metadata and human-readable turns from one transcript.

    v2: keeps a per-turn timestamp, and drops exact-duplicate turns —
    compaction/resume replays the same messages verbatim into the transcript
    (observed up to 10x), which poisoned retrieval with duplicate hits.
    """
    meta = {"session": jsonl_path.stem, "project": jsonl_path.parent.name,
            "start": None, "end": None}
    turns = []  # list of (role, text, timestamp)
    seen = set()
    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = obj.get("timestamp")
            if ts:
                meta["start"] = meta["start"] or ts
                meta["end"] = ts
            kind = obj.get("type")
            if kind not in ("user", "assistant"):
                continue
            text = clean(text_of(obj.get("message", {}).get("content")))
            if not text or text.startswith(NOISE_PREFIXES):
                continue
            key = (kind, text)
            if key in seen:
                continue
            seen.add(key)
            turns.append((kind, text, ts or meta["start"] or ""))
    return meta, turns


def render_digest(meta, turns):
    user_count = sum(1 for r, _, _ in turns if r == "user")
    lines = [
        "---",
        f"session: {meta['session']}",
        f"project: {meta['project']}",
        f"start: {meta['start']}",
        f"end: {meta['end']}",
        f"user_messages: {user_count}",
        "generator: mechanical-v2",
        "---",
        "",
    ]
    for role, text, ts in turns:
        limit = (CONFIG["user_msg_max"] if role == "user"
                 else CONFIG["assistant_msg_max"])
        tag = "USER" if role == "user" else "AI"
        # per-turn timestamp so downstream consumers can align hits in time
        lines.append(f"## {tag} · {ts}" if ts else f"## {tag}")
        lines.append(truncate(text, limit))
        lines.append("")
    return "\n".join(lines)


def main():
    rebuild = "--rebuild" in sys.argv
    src, arc, dig = (CONFIG["source_dir"], CONFIG["archive_dir"],
                     CONFIG["digest_dir"])
    if not src.is_dir():
        sys.exit(f"source_dir not found: {src}")
    archived = digested = skipped = 0

    for jsonl in sorted(src.glob("*/*.jsonl")):
        rel = jsonl.relative_to(src)
        target = arc / rel
        # archive: copy when missing or the live file has grown/changed
        if (not target.exists()
                or jsonl.stat().st_mtime > target.stat().st_mtime):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(jsonl, target)
            archived += 1

    # digests are generated from the ARCHIVE, never the live dir (INV-2)
    for jsonl in sorted(arc.glob("*/*.jsonl")):
        card = dig / jsonl.parent.name / (jsonl.stem + ".md")
        if card.exists() and not rebuild \
                and card.stat().st_mtime >= jsonl.stat().st_mtime:
            continue
        meta, turns = parse_session(jsonl)
        if sum(1 for r, _, _ in turns if r == "user") < CONFIG["min_user_messages"]:
            skipped += 1
            continue
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text(render_digest(meta, turns), encoding="utf-8")
        digested += 1

    print(f"archived: {archived}  digested: {digested}  "
          f"skipped(noise): {skipped}")
    print(f"archive: {arc}\ndigests: {dig}")


if __name__ == "__main__":
    main()
