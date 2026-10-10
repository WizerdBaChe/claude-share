#!/usr/bin/env python
"""make_fixture.py — render a slice of a Claude Code transcript into the observer's window format.

    python make_fixture.py <transcript.jsonl> <first-record> <last-record> <name> [--limit 40000]

Writes <name>.window.txt beside this script in exactly the text `hooks/window.ts renderMessage`
produces (`### role #i`, the text, one `[tool NAME] <input> -> <result>` line per tool use, 200-char
clips), so a calibration run exercises the same prompt the live check sends. The pairing
<name>.expect.json is written by hand: {"expect_target": "hook:x"} for a known-TRUE window,
{"expect_empty": true} for a known-FALSE one. Record numbers are 0-based line indices of the
transcript (blank lines skipped); the provenance header is written as the first user message.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLIP = 200


def clip(v, n: int = CLIP) -> str:
    t = v if isinstance(v, str) else ('' if v is None else json.dumps(v, ensure_ascii=False))
    one = ' '.join(t.split())
    return one if len(one) <= n else one[: n - 1] + '…'


def messages(recs: list[dict], first: int, last: int) -> list[dict]:
    out: list[dict] = []
    pending: dict[str, dict] = {}
    for r in recs[first:last + 1]:
        kind = r.get('type')
        m = r.get('message') or {}
        content = m.get('content')
        if kind == 'assistant':
            msg = {'role': 'assistant', 'text': '', 'toolUses': []}
            if isinstance(content, str):
                msg['text'] = content
            else:
                for b in content or []:
                    if b.get('type') == 'text':
                        msg['text'] += b.get('text', '')
                    elif b.get('type') == 'tool_use':
                        u = {'tool': b.get('name', '?'), 'input': b.get('input'), 'text': ''}
                        msg['toolUses'].append(u)
                        pending[b.get('id', '')] = u
            if msg['text'].strip() or msg['toolUses']:
                out.append(msg)
        elif kind == 'user':
            if isinstance(content, str):
                if content.strip():
                    out.append({'role': 'user', 'text': content, 'toolUses': []})
                continue
            text = ''
            for b in content or []:
                if b.get('type') == 'tool_result':
                    cc = b.get('content')
                    s = cc if isinstance(cc, str) else ' '.join(x.get('text', '') for x in (cc or []) if isinstance(x, dict))
                    u = pending.get(b.get('tool_use_id', ''))
                    if u is not None:
                        u['text'] = s
                        if b.get('is_error'):
                            u['isError'] = True
                elif b.get('type') == 'text':
                    text += b.get('text', '')
            if text.strip():
                out.append({'role': 'user', 'text': text, 'toolUses': []})
    return out


def render(msgs: list[dict]) -> list[str]:
    blocks = []
    for i, m in enumerate(msgs):
        lines = [f"### {m['role']} #{i}"]
        if m['text'].strip():
            lines.append(m['text'].strip())
        for u in m['toolUses']:
            lines.append(f"[tool {u['tool']}{' ERROR' if u.get('isError') else ''}] {clip(u.get('input'))} -> {clip(u.get('text', ''))}")
        blocks.append('\n'.join(lines))
    return blocks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('transcript', type=Path)
    ap.add_argument('first', type=int)
    ap.add_argument('last', type=int)
    ap.add_argument('name')
    ap.add_argument('--limit', type=int, default=40_000)
    a = ap.parse_args(argv)
    recs = [json.loads(l) for l in a.transcript.read_text(encoding='utf-8', errors='replace').splitlines() if l.strip()]
    header = {'role': 'user', 'text': f"[fixture {a.name}: {a.transcript.name} records {a.first}-{a.last}]", 'toolUses': []}
    blocks = render([header] + messages(recs, a.first, a.last))
    text = '\n\n'.join(blocks)
    while len(text) > a.limit and len(blocks) > 1:
        blocks.pop(1)                       # tail-biased, like buildWindow; keep the provenance header
        text = '\n\n'.join(blocks)
    out = HERE / f"{a.name}.window.txt"
    out.write_text(text, encoding='utf-8', newline='\n')
    print(f"{out} {len(text)} chars, {len(blocks)} messages")
    return 0


if __name__ == '__main__':
    sys.exit(main())
