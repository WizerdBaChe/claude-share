"""Helpers shared by the task modules. Not a task (the loader only picks tNN_*.py)."""
from __future__ import annotations
import json
import re
from pathlib import Path

_FENCE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n(.*?)\n\s*```\s*$", re.S)


def strip_fences(text: str) -> str:
    m = _FENCE.match(text.strip())
    return m.group(1) if m else text.strip()


def parse_json(text: str):
    """json.loads after fence stripping; falls back to the outermost [..] or {..} span."""
    t = strip_fences(text)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    for open_, close in (("[", "]"), ("{", "}")):
        i, j = t.find(open_), t.rfind(close)
        if i != -1 and j > i:
            try:
                return json.loads(t[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON payload")


def verdict(ok: bool, details: str, score: float | None = None) -> dict:
    return {"pass": bool(ok), "score": (1.0 if ok else 0.0) if score is None else score,
            "details": details}


def write(workdir: Path, rel: str, content: str) -> None:
    p = workdir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def gold_path(workdir: Path) -> Path:
    """Answer key as a SIBLING of workdir: the model under test works inside workdir and must
    never be able to read the gate's gold (rounds 1-4 planted it inside; see round5-report)."""
    w = Path(workdir)
    return w.parent / (w.name + ".gold.json")


CJK = re.compile(r"[㐀-鿿豈-﫿　-〿＀-￯]")
