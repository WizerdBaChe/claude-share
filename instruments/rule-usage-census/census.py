"""rule-usage-census — which rule surfaces are actually used, by which main-loop model.

Reads two existing instruments and crosses them; it writes no telemetry of its own:
  (1) main-session transcripts  <archive>/<project>/<session>.jsonl  (default archive: ~/.claude/projects;
      a mirror directory of the same layout also works; subagent transcripts are skipped)
  (2) telemetry/rule-loads.jsonl        InstructionsLoaded events (tools/context-budget/rule_loads.py
      already reports these alone; this tool only joins them to the transcript set)

Per session it records: main-loop model (majority of assistant `message.model`), user turns,
assistant output chars, Read/Grep/Glob/shell touches of ~/.claude rule surfaces (ops/*, rules/*,
skills/*/SKILL.md, references), Skill-tool invocations, Agent dispatches (+ model), and one PROBE
hit per global-CLAUDE.md bullet: a regex over assistant TEXT that only that rule's vocabulary
produces ("Boundary Contract", "A 必驗", "[deviated]", ...). The probe table is PROBES below —
add a row when a bullet is added, retire it when the bullet leaves.

Severity: ADVISORY (WARN-only). An LLM or the user reads the tables; nothing downstream consumes
them. A probe measures "the rule's vocabulary appeared", NOT "the rule was obeyed", and a low
rate is only a trim CANDIDATE — a rule whose trigger is rare fires rarely by design (40-maintenance
§3: absence of evidence is not proof of no effect). Promotion trigger: none foreseen; if a trim
pass ever cites a rate here as its sole ground for deleting a rule, that pass must first show the
rule's trigger frequency from the same corpus.

Calibration (gate rule, global CLAUDE.md): `--selftest` builds two synthetic transcripts — one
carrying a known model, one probe token and one ops/ read (must be counted), one carrying none
(must count zero) — and fails loudly if either side is wrong. Run it before trusting a table.

Usage:
  python tools/rule-usage-census/census.py                       # tables to stdout, JSON beside
  python tools/rule-usage-census/census.py --since 2026-09-01    # window
  python tools/rule-usage-census/census.py --selftest
First report: reports/2026-09-10-rules-debt-audit.md.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import tempfile
import time

HOME = os.path.expanduser('~/.claude')
ARCHIVE = os.path.join(HOME, 'projects')

# probe key -> regex over assistant text. Key = "<bullet family>:<distinctive token>".
PROBES = {
    'git:conventional': r'Conventional Commits|type\(scope\)',
    'shell:bash-limits(L-024)': r'L-024',
    'shell:fence-label': r'```(powershell|git bash)',
    'shell:gitattributes': r'\.gitattributes',
    'shell:ps-native-quote': r'\$LASTEXITCODE|-F <file>',
    'shell:py-rawstring': r'r"[A-Z]:\\',
    'lint:pre-existing': r'pre-existing|既有(的)?(技術)?債',
    'visual:gate': r'visual gate|視覺閘門',
    'html:page-class': r'data-page-class|fill_gate\.py',
    'browser:senduserfile': r'SendUserFile',
    'volatile:websearch-mention': r'WebSearch|web search|官方文件',
    'gate:positive-control': r'positive control|正對照|calibrat',
    'invariant:asset-property': r'asset propert|property of the ASSET|資產屬性',
    'placement:level-consumer': r'naming-and-placement|LEVEL.{0,40}CONSUMER',
    'BC:uat-list': r'A 必驗',
    'accepted:regression': r'regression case|回歸案例',
    'ext:core-need': r'core need|不要為了做而做|核心需求已',
    'priorart:check': r'prior-art|xi\.py query|gsnap\.py query|session-find',
    'runtime:fps': r'FPS',
    'diagram:representation': r'representation-models',
    'charter:ledger': r'ledger\.py add|process ledger|process-ledger',
    'BC:contract': r'Boundary Contract|邊界契約',
    'premises:refutability': r'refutab|holds-when|overturned-by|Premises',
    'depth:tier': r'\bR8\b|深想|快答|Tier-2|\bT2\b',
    'skill:dict': r'skill-trigger-dict',
    'relax:level': r'ops-relaxation|L2 \(fully|L1 \(core|fully relaxed',
    'unattended': r'\[unattended-run\]',
    'closeout:digest': r'session-digest',
    'hygiene:archive': r'archive/',
    'deviated': r'\[deviated\]',
    'lang:inline-en': r'[\u4e00-\u9fff]+ \([A-Za-z][^)]{2,40}\)',
}
PROBES_RX = {k: re.compile(v) for k, v in PROBES.items()}
SURFACE_RX = re.compile(r'(ops/[\w\-/]+\.md|rules/[\w\-]+\.md|skills/[\w\-]+/SKILL\.md|CLAUDE\.md|PHILOSOPHY\.md|'
                        r'skill-trigger-dict\.md|LABEL-REGISTRY\.md|OPERATOR-GUIDE\.md)$')
SHELL_RX = re.compile(r'(ops/[\w\-/]+\.md|rules/[\w\-]+\.md|skills/[\w\-]+/SKILL\.md)')


def norm(p: str | None) -> str:
    p = (p or '').replace('\\', '/')
    return re.sub(r'^[A-Za-z]:/Users/[^/]+/\.claude/', '~/', p)


def fam(model: str | None) -> str:
    if not model:
        return 'none'
    for k in ('fable', 'opus', 'sonnet', 'haiku'):
        if k in model:
            return k
    return 'other'


def scan_file(path: str) -> dict:
    proj = os.path.basename(os.path.dirname(path))
    sid = os.path.basename(path)[:-6]
    models = collections.Counter(); reads = collections.Counter(); skills = collections.Counter()
    tools = collections.Counter(); probes = collections.Counter(); agent_models = collections.Counter()
    user_turns = asst_chars = agents = 0
    first = last = cwd = None
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = d.get('timestamp')
            if ts:
                first = first or ts; last = ts
            cwd = cwd or d.get('cwd')
            t = d.get('type')
            m = d.get('message') if isinstance(d.get('message'), dict) else {}
            if t == 'user':
                c = m.get('content')
                if isinstance(c, str) or (isinstance(c, list) and c and isinstance(c[0], dict) and c[0].get('type') == 'text'):
                    user_turns += 1
            elif t == 'assistant':
                if m.get('model'):
                    models[m['model']] += 1
                for blk in m.get('content') or []:
                    if not isinstance(blk, dict):
                        continue
                    if blk.get('type') == 'text':
                        txt = blk.get('text', ''); asst_chars += len(txt)
                        for k, rx in PROBES_RX.items():
                            if rx.search(txt):
                                probes[k] += 1
                    elif blk.get('type') == 'tool_use':
                        name = blk.get('name', '?'); inp = blk.get('input') or {}
                        tools[name] += 1
                        if name in ('Read', 'Grep', 'Glob'):
                            p = norm(inp.get('file_path') or inp.get('path'))
                            if p.startswith('~/'):
                                reads[p if name == 'Read' else name + ':' + p] += 1
                        elif name == 'Skill':
                            skills[inp.get('skill', '?')] += 1
                        elif name in ('Agent', 'Task'):
                            agents += 1; agent_models[inp.get('model') or 'inherit'] += 1
                        elif name in ('Bash', 'PowerShell'):
                            for mm in SHELL_RX.finditer(inp.get('command', '')):
                                reads['sh:~/' + mm.group(1)] += 1
    return dict(project=proj, sid=sid, cwd=cwd, first=first, last=last, models=dict(models),
                main_model=(models.most_common(1)[0][0] if models else None), user_turns=user_turns,
                asst_chars=asst_chars, reads=dict(reads), skills=dict(skills), tools=dict(tools),
                agents=agents, agent_models=dict(agent_models), probes=dict(probes))


def scan(archive: str, since: str | None) -> list[dict]:
    out = []
    for f in glob.glob(archive + '/*/*.jsonl'):
        s = scan_file(f)
        if since and (s['first'] or '') < since:
            continue
        out.append(s)
    return out


def report(S: list[dict], out=sys.stdout) -> None:
    P = lambda *a: print(*a, file=out)
    real = [s for s in S if s['main_model'] and s['user_turns'] >= 1]
    bench = [s for s in real if s['project'].startswith('D--BenchRuns')]
    live = [s for s in real if s not in bench]
    P(f'sessions scanned {len(S)}  with a model {len(real)}  live {len(live)}  bench (excluded below) {len(bench)}')
    P('\n== main-loop model family per month (live sessions) ==')
    tab = collections.defaultdict(collections.Counter)
    for s in live:
        tab[(s['first'] or '')[:7]][fam(s['main_model'])] += 1
    for m in sorted(tab):
        P(m, dict(tab[m]))
    w = collections.Counter()
    for s in live:
        w[fam(s['main_model'])] += s['asst_chars']
    tot = sum(w.values()) or 1
    P('share of assistant output chars:', {k: f'{v / tot:.0%}' for k, v in w.most_common()})
    fams = ['fable', 'opus', 'sonnet', 'haiku']
    n = {f: sum(1 for s in live if fam(s['main_model']) == f) for f in fams}
    big = {f: sum(1 for s in live if fam(s['main_model']) == f and s['user_turns'] >= 5) for f in fams}
    P('\n== probe fires: sessions where the token appears >=1 (in parentheses: sessions with >=5 user turns) ==')
    P('n', n, ' n>=5 turns', big)
    P(f"{'probe':30s} " + ' '.join(f'{f:>20s}' for f in fams))
    for k in PROBES:
        cells = []
        for f in fams:
            hit = sum(1 for s in live if fam(s['main_model']) == f and s['probes'].get(k))
            hb = sum(1 for s in live if fam(s['main_model']) == f and s['user_turns'] >= 5 and s['probes'].get(k))
            cells.append(f'{hit:3d}/{n[f]:3d} ({hb:3d}/{big[f]:3d})')
        P(f'{k:30s} ' + ' '.join(f'{c:>20s}' for c in cells))
    P('\n== rule-surface reads (Read tool or shell): sessions touching, by family ==')
    rd = collections.defaultdict(collections.Counter)
    for s in live:
        seen = set()
        for p in s['reads']:
            q = p.replace('sh:', '')
            if q.startswith(('Grep:', 'Glob:')):
                continue
            mm = SURFACE_RX.search(q)
            if mm:
                seen.add(mm.group(1))
        for q in seen:
            rd[q][fam(s['main_model'])] += 1
    for q, c in sorted(rd.items(), key=lambda kv: -sum(kv[1].values())):
        P(f'{sum(c.values()):4d}  {dict(c)}  {q}')
    P('\n== Skill invocations: sessions using each skill ==')
    sk = collections.Counter(); skf = collections.defaultdict(collections.Counter)
    for s in live:
        for k in s['skills']:
            sk[k] += 1; skf[k][fam(s['main_model'])] += 1
    for k, v in sk.most_common():
        P(f'{v:4d} {dict(skf[k])} {k}')
    am = collections.Counter(); ns = 0
    for s in live:
        ns += bool(s['agents'])
        for k, v in s['agent_models'].items():
            am[k] += v
    P('\n== Agent dispatches ==', 'sessions with a dispatch', ns, 'by model param', dict(am))


def selftest() -> int:
    """Positive control: a synthetic session with a known model, one probe token and one ops/ read
    must be counted; negative control: a session with none must count zero. Prints both."""
    d = tempfile.mkdtemp(prefix='ruc-')
    os.makedirs(os.path.join(d, 'P'))
    pos = [
        {'type': 'user', 'timestamp': '2026-09-10T00:00:00Z', 'cwd': '/work/x', 'message': {'content': 'hi'}},
        {'type': 'assistant', 'timestamp': '2026-09-10T00:00:01Z', 'message': {'model': 'claude-opus-5', 'content': [
            {'type': 'text', 'text': 'Emitting the Boundary Contract now.'},
            {'type': 'tool_use', 'name': 'Read', 'input': {'file_path': 'C:\\Users\\me\\.claude\\ops\\OPS.md'}},
            {'type': 'tool_use', 'name': 'Skill', 'input': {'skill': 'config-self-audit'}}]}},
    ]
    neg = [
        {'type': 'user', 'timestamp': '2026-09-10T00:00:00Z', 'message': {'content': 'hi'}},
        {'type': 'assistant', 'timestamp': '2026-09-10T00:00:01Z', 'message': {'model': 'claude-sonnet-5', 'content': [
            {'type': 'text', 'text': 'plain answer, no rule vocabulary'}]}},
    ]
    for name, rows in (('pos', pos), ('neg', neg)):
        with open(os.path.join(d, 'P', name + '.jsonl'), 'w', encoding='utf-8') as fh:
            for r in rows:
                fh.write(json.dumps(r) + '\n')
    S = {s['sid']: s for s in scan(d, None)}
    ok = True
    p, q = S['pos'], S['neg']
    checks = [
        ('pos model=opus', fam(p['main_model']) == 'opus'),
        ('pos probe BC:contract counted', p['probes'].get('BC:contract') == 1),
        ('pos ops/OPS.md read counted', any(k.endswith('ops/OPS.md') for k in p['reads'])),
        ('pos skill counted', p['skills'].get('config-self-audit') == 1),
        ('neg model=sonnet', fam(q['main_model']) == 'sonnet'),
        ('neg zero probes', not q['probes']),
        ('neg zero reads', not q['reads']),
    ]
    for label, res in checks:
        print(('PASS ' if res else 'FAIL ') + label); ok &= res
    print('selftest', 'PASS' if ok else 'FAIL', f'({len(checks)} checks, {sum(1 for _, r in checks if r)} passed)')
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--archive', default=ARCHIVE)
    ap.add_argument('--since', default=None, help='ISO date; sessions starting earlier are dropped')
    ap.add_argument('--json', default=None, help='write per-session JSON here (default: beside this script)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    t0 = time.time()
    S = scan(a.archive, a.since)
    out = a.json or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions.json')
    json.dump(S, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    report(S)
    print(f'\nscanned {len(S)} sessions in {time.time() - t0:.0f}s -> {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
