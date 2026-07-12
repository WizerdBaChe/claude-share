#!/usr/bin/env python3
"""Pre-scan for skill-share-packaging: mechanical first pass over a skill directory.

Mode B (import audit): flags likely-malicious patterns and prompt injection.
Mode A (export self-check): flags environment coupling and data leaks.

A clean scan is NOT a safety verdict — regex is bypassable. The manual
line-by-line review in SKILL.md remains mandatory. This script only makes the
cheap, tireless part of the audit run first, so the human pass can focus on
semantics.

Usage:
    python prescan.py <skill-dir> [--mode import|export|all] [--format text|json]

Exit codes: 0 = no findings, 1 = findings present, 2 = usage/path error.

Adapted from lifeos-memory skill-vetting scan.py (MIT-licensed upstream),
extended with the export-side coupling/leak checks from this skill's SKILL.md.
Findings inside this script itself are expected if you scan this skill.
"""

import json
import re
import sys
from pathlib import Path

# (pattern, description, severity); severity: CRITICAL > HIGH > MEDIUM > LOW
# Categories tagged 'import' run in import mode, 'export' in export mode.
PATTERNS = {
    # --- import-side: code execution & obfuscation ---
    ('import', 'code_execution'): [
        (r'\beval\s*\(', 'eval() execution', 'CRITICAL'),
        (r'\bexec\s*\(', 'exec() execution', 'CRITICAL'),
        (r'__import__\s*\(', 'dynamic import', 'HIGH'),
        (r'importlib\.import_module\s*\(', 'importlib dynamic import', 'HIGH'),
        (r'getattr\s*\(.*[\'"]system[\'"]', 'getattr obfuscation', 'CRITICAL'),
    ],
    ('import', 'subprocess'): [
        (r'subprocess\.(call|run|Popen).*shell\s*=\s*True', 'shell=True subprocess', 'CRITICAL'),
        (r'os\.system\s*\(', 'os.system()', 'CRITICAL'),
        (r'os\.popen\s*\(', 'os.popen()', 'HIGH'),
    ],
    ('import', 'obfuscation'): [
        (r'base64\.b64decode', 'base64 decoding', 'MEDIUM'),
        (r'codecs\.decode.*[\'"]hex[\'"]', 'hex decoding', 'MEDIUM'),
        (r'chr\s*\(\s*\d+\s*\)\s*(?:\+|for)', 'chr() string construction', 'MEDIUM'),
        ('[\u200b\u200c\u200d\u2060\ufeff]', 'invisible unicode character', 'HIGH'),
    ],
    ('import', 'network'): [
        (r'requests\.(get|post|put|delete)\s*\(', 'HTTP request', 'MEDIUM'),
        (r'urllib\.request\.urlopen', 'urllib request', 'MEDIUM'),
        (r'socket\.socket\s*\(', 'raw socket', 'HIGH'),
        (r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'URL with raw IP address', 'HIGH'),
        (r'curl\s+.*\|\s*(ba)?sh', 'curl piped to shell', 'CRITICAL'),
    ],
    ('import', 'file_operations'): [
        (r'os\.remove\s*\(', 'file deletion', 'HIGH'),
        (r'shutil\.rmtree', 'recursive tree deletion', 'HIGH'),
        (r'rm\s+-rf?\s+(?!\$?\{?TMP|/tmp|\.)', 'rm -rf outside temp', 'HIGH'),
        (r'>\s*~/\.(bashrc|zshrc|profile|ssh/)', 'writing to dotfiles/ssh', 'CRITICAL'),
    ],
    ('import', 'prompt_injection'): [
        (r'(?i)(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|above|prior|earlier|these)\s+(?:instruction|rule|guideline)', 'instruction override', 'CRITICAL'),
        (r'(?i)(?:pre-?approved|false.positiv|classify\s+(?:as\s+)?(?:safe|clean)|ignore\s+(?:this\s+)?(?:warning|finding|scanner))', 'reviewer-override phrasing', 'CRITICAL'),
        (r'(?i)(?:AI|LLM|assistant|agent|reviewer|Claude|GPT)\s+(?:must|should|is\s+(?:authorized|approved|required))', 'text addressing the AI reviewer', 'CRITICAL'),
        (r'(?i)always\s+(?:trigger|invoke|activate)\s+this\s+skill', 'always-trigger phrasing', 'HIGH'),
        (r'(?i)(?:fetch|download|read)\s+(?:and\s+)?(?:obey|follow|execute)\s+.{0,40}(?:url|remote|instruction)', 'obey-remote-content instruction', 'CRITICAL'),
        (r'<!--.*(?:instruction|system|assistant).*-->', 'hidden HTML-comment directive', 'HIGH'),
    ],
    # --- export-side: environment coupling & data leakage (SKILL.md A2/A3) ---
    ('export', 'env_coupling'): [
        (r'(?i)c:\\+users\\+\w+', 'Windows user-profile absolute path', 'HIGH'),
        (r'(?<![\w.])/(?:home|Users)/\w+', 'POSIX home absolute path', 'HIGH'),
        (r'~/\.claude/(?:ops|skills|hooks)/', 'reference into private ~/.claude tree', 'MEDIUM'),
        (r'skill-trigger-dict', 'private routing-dict reference', 'MEDIUM'),
        (r'(?i)mcp__\w+__\w+', 'named MCP tool (needs "if available" + fallback)', 'LOW'),
    ],
    ('export', 'data_leak'): [
        (r'sk-[a-zA-Z0-9]{16,}', 'API-key-shaped string', 'CRITICAL'),
        (r'(?i)(?:api[_-]?key|token|secret)\s*[:=]\s*[\'"][^\'"]{8,}', 'hardcoded credential assignment', 'CRITICAL'),
        (r'[a-zA-Z0-9._%+-]+@(?!example\.)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email address', 'HIGH'),
        (r'(?i)key:\s*\w{4,}\.{2,}\w{4,}', 'partial-key trace in notes/logs', 'HIGH'),
    ],
}

BINARY_EXTS = {
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
    '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.wav',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.ttf', '.otf', '.woff', '.woff2', '.pyc',
}

SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']


def is_text_file(path):
    if path.suffix.lower() in BINARY_EXTS:
        return False
    try:
        with open(path, 'rb') as f:
            return b'\x00' not in f.read(8192)
    except OSError:
        return False


def scan(root, modes):
    findings = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or not is_text_file(path):
            continue
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            print(f"warning: could not read {path}: {e}", file=sys.stderr)
            continue
        rel = path.relative_to(root)
        for (mode, category), patterns in PATTERNS.items():
            if mode not in modes:
                continue
            for pattern, description, severity in patterns:
                for match in re.finditer(pattern, content, re.MULTILINE):
                    findings.append({
                        'file': str(rel),
                        'line': content[: match.start()].count('\n') + 1,
                        'mode': mode,
                        'category': category,
                        'severity': severity,
                        'description': description,
                        'match': match.group(0)[:60],
                    })
    return findings


def print_text(findings):
    if not findings:
        print("CLEAN: no findings (regex pass only -- manual review still required)")
        return
    counts = {}
    for f in findings:
        counts[f['severity']] = counts.get(f['severity'], 0) + 1
    summary = ', '.join(f"{s}: {counts[s]}" for s in SEVERITY_ORDER if s in counts)
    print(f"FINDINGS: {len(findings)} ({summary})\n")
    for sev in SEVERITY_ORDER:
        for f in findings:
            if f['severity'] != sev:
                continue
            print(f"[{sev}] {f['file']}:{f['line']} ({f['mode']}/{f['category']}) {f['description']}")
            print(f"         match: {f['match']}")
    print("\nNote: a finding is a review pointer, not a verdict; a clean scan is not a safety guarantee.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Mechanical pre-scan for skill packaging/audit')
    parser.add_argument('path', help='skill directory to scan')
    parser.add_argument('--mode', choices=['import', 'export', 'all'], default='all')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    args = parser.parse_args()

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    modes = {'import', 'export'} if args.mode == 'all' else {args.mode}
    findings = scan(root, modes)

    if args.format == 'json':
        print(json.dumps({'total': len(findings), 'clean': not findings,
                          'findings': findings}, indent=2))
    else:
        print_text(findings)
    sys.exit(1 if findings else 0)


if __name__ == '__main__':
    main()
