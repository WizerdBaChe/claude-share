# Telemetry, integrity commands, and external health-check tools

Loaded on demand by `config-self-audit`. Everything here is a concrete command or
a measured fact — no policy. Policy lives in SKILL.md §2, §5, §7, §8.

---

## 1. Usage measurement — `tools/usage-window.py`

```bash
python ~/.claude/tools/usage-window.py --days 30
```

Stdlib only, read-only, no network. Scans `~/.claude/projects/**/*.jsonl` and
reports, **keyed on each event's in-file `timestamp`** (not file mtime):

- skill dispatches (`Skill` tool_use, `input.skill`) and `<command-name>` slash uses
- MCP invocations per server (`mcp__<server>__<tool>`)
- hook runs per command string: count, median/max `durationMs`, timeout count
- tool denials by `toolDenialKind` (`interrupted`/`cancelled` excluded — not denials)
- **an mtime-skew list**: files whose content starts well before their mtime

Options: `--days N` (default 30), `--json`, `--projects <dir>`.

Reading the output:

- The skew list is the integrity check for SKILL.md §7. A long list means any
  mtime-windowed report about this machine — including `/doctor`'s — is suspect.
- Hook rows are keyed by command string, so a hook whose script was removed still
  appears with its historical rows. Cross-check with `Test-Path` (§2 gate) before
  treating any hook row as a live problem.
- Lifetime counters live elsewhere (`~/.claude.json` → `skillUsage`,
  `pluginUsage`); this tool reports the window only. `pluginUsage.lastUsedAt` is
  seeded on install/enable, so for a zero-count plugin it is not usage evidence.

---

## 2. Integrity one-liners (SKILL.md §2)

**Duplicate and variant-collision keys** — two different failures; check both.
An EXACT duplicate is silently accepted by `jq empty` and by Python (last wins).
A VARIANT collision is a set of keys that differ only by case or path separator:
JSON and Python treat them as distinct, so a plain duplicate check finds nothing,
but case-insensitive consumers reject the file outright (PowerShell's
`ConvertFrom-Json` errors with "duplicated keys"), and the product itself keys
per-project state by the literal cwd string — so `D:\x`, `D:/x` and `d:/x` become
three projects with three sets of MCP approvals, trust flags and permission
history. That is what "why is it asking me again?" looks like.

```bash
python - ~/.claude.json <<'PY'
import json, collections, sys
path = sys.argv[1]
norm = lambda k: k.replace("\\", "/").rstrip("/").casefold()
def hook(pairs):
    keys = [k for k, _ in pairs]
    for k, n in collections.Counter(keys).items():
        if n > 1:
            print("EXACT-DUP:", k)
    groups = collections.defaultdict(list)
    for k in keys:
        groups[norm(k)].append(k)
    for g in groups.values():
        if len(g) > 1:
            print("VARIANT-COLLISION:", " | ".join(g))
    return dict(pairs)
json.loads(open(path, encoding="utf-8").read(), object_pairs_hook=hook)
print("checked", path)
PY
```

Measured 2026-07-25 on this machine: 0 exact duplicates, **6 variant-collision
groups** (14 `projects` entries that are really 6 projects). A duplicate-only
check would have reported the file clean.

**CLI self-validation warnings** — Claude Code checks permission rules at startup
and writes problems to stderr:

```bash
claude -p "ok" --model haiku --disallowed-tools "Edit Write NotebookEdit" 2>&1 >/dev/null
```

Known class (confirmed 2026-07-25): `Write(<path>)` permission rules are never
matched by file permission checks — only `Edit(<path>)` rules are, and `Edit`
rules cover every file-editing tool including Write. A settings file carrying a
lone `Write(...)` ask/deny rule has no protection at all on that path.

---

## 3. Invoking `/doctor` (SKILL.md §8)

`/doctor` is an interactive slash command; the model cannot call it directly.
Three ways to obtain its output, cheapest first:

| Method | Cost | Use when |
|---|---|---|
| Ask the user to run `/doctor` and paste the output | 0 | default |
| `claude doctor` (CLI subcommand) | very low | install-layer health only: PATH, duplicate installs, settings parse, ripgrep |
| Headless full checkup (below) | **high** — a full nested session, 61 tool calls measured | user explicitly asks for an official checkup in the same turn |

Headless invocation — **must run from PowerShell**:

```powershell
claude -p "/doctor" --model sonnet `
  --allowed-tools "Read Glob Grep Bash" `
  --disallowed-tools "Edit Write NotebookEdit AskUserQuestion"
```

- **Git-Bash trap:** under MSYS, `"/doctor"` is rewritten to
  `C:/Program Files/Git/doctor` and the command silently does not run. Use
  PowerShell, or `MSYS_NO_PATHCONV=1`.
- Disallowing the write tools keeps the run read-only; disallowing
  `AskUserQuestion` makes it emit its report and stop instead of blocking on a
  confirmation gate it cannot receive.
- `--model` matters: the prompt is ~46 KB and the scan touches ~50 transcripts.
- Back up `~/.claude.json` before any run that is allowed to write — it is
  usually outside git.
- Observed behaviour worth knowing: the run escalated out of the PowerShell
  sandbox on its own to finish its scan, and spent a large share of its calls on
  Windows path conversion.

---

## 4. Measured defects (2026-07-25, CLI 2.1.220, sonnet)

Full analysis: `~/.claude/reports/2026-07-25-doctor-vs-config-self-audit.md`.

| ID | Defect | Consequence |
|---|---|---|
| D-1 | Scan window is decided by transcript **mtime**, not event timestamp | Headline finding was a hook timing out 217/220 times; the events were 07-03/04, the script was archived 07-07, the claimed window was 07-20..07-25 |
| D-2 | Telemetry findings never existence-check what they reference | 61 tool calls, zero `Test-Path` on the reported hook path |
| D-3 | "Zero lifetime uses → remove" | Recommended deleting 5 user skills including two research tools; the same report kept 1-use skills with "rare by design" reasoning |
| D-4 | "Never propose disabling bundled/built-in" | Left ~1.7k tokens/session of never-used bundled plugins untouched while proposing to cut ~0.7k of the user's own skills |
| D-5 | Settings check is parse-only | Missed 30 `projects` entries with case/separator duplicate keys |
| D-6 | Does not collect the CLI's own startup warnings | Missed 4 dead `Write(...)` permission rules |
| D-7 | No cross-surface duplicate detection | Missed a byte-identical duplicate of a user skill in the desktop skills cache |
| D-8 | Spec assumes `jq`; absent here | Fell back to PowerShell then Python, losing the spec's `--arg` / `--slurpfile` injection defences |

What it genuinely does better than this checklist: install/PATH repair, version
currency, and lifetime usage counters. Everything else in its check list is
reproducible from §1–§7 at a fraction of the cost.

Its two design choices worth copying (both already mirrored in SKILL.md):
separating permission changes from cleanup consent (§3), and treating every
harvested name (skill names, MCP server names, hook command strings) as untrusted
input that must never be interpolated into a shell command (§3, secrets bullet).
