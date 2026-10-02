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
- A skill nested under a directory is listed as `<dir>:<name>` but its counter
  may sit under either that key or the bare `<name>` — read both before calling
  it zero (from the 2.1.283 `/doctor` spec).
- A hook run that succeeds with EMPTY output is never persisted to transcripts,
  so zero recorded runs for a configured hook does not mean it rarely fires;
  config inspection is the expected path for silent hooks (same source).
- Purely passive components (a theme, output style, monitor or workflow plugin)
  never increment any counter and leave no transcript trace: a zero there is
  the absence of logging, not disuse — ask the user, do not infer.

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

**Retired-destination track record** (SKILL.md §2): four live instruction files
still pointed at the frozen config change log three weeks after its 2026-08-11
freeze, and a fifth (`skill-share-packaging`) survived four days past the
`audit-archive/` rename. Assume there is one more.

**Local fallback for the two repo-groundable `prompt-audit` rows** (§8 row 6 —
used when the official engine is unavailable; both instruments were calibrated
2026-09-28 against the pre-trim CLAUDE.md `fced219~1`):

```bash
# 1. Date-based review conditions. House rule: review-when names an EVENT.
#    Control: pre-trim CLAUDE.md -> 1 hit ("review 2026-11"); after -> 0.
grep -n -E "review 20[0-9]{2}-[0-9]{2}" CLAUDE.md rules/*.md ops/*.md
```

```bash
# 2. Verbatim duplication between an always-loaded file and its references
#    (10-word English shingles; CJK runs are NOT counted — a known blind spot).
#    Control: pre-trim CLAUDE.md vs gate-design.md -> 35 shared runs; after -> 24.
#    READ THE HIT LINES, never the count: the same run showed 22 shared runs
#    with principle-design-guide.md, all of them `## CLAUDE.md «…»` headings
#    that quote a bullet's trigger phrase as an index key (checked 2026-09-29;
#    no prose duplicated, nothing to trim). A key is a hit that is not a finding.
python - CLAUDE.md "ops/references/*.md" "rules/*.md" <<'PY'
import glob, pathlib, re, sys
def sh(t, n=10):
    w = re.findall(r"[A-Za-z][A-Za-z'\-]+", t)
    return {" ".join(w[i:i+n]) for i in range(max(0, len(w)-n+1))}
mine = sh(pathlib.Path(sys.argv[1]).read_text("utf-8", errors="replace"))
for pat in sys.argv[2:]:
    for ref in sorted(glob.glob(pat)):
        hits = mine & sh(pathlib.Path(ref).read_text("utf-8", errors="replace"))
        if hits:
            print(f"{len(hits):4d} shared runs  {ref}  e.g. {sorted(hits)[0][:60]!r}")
PY
```

A count is a pointer to look, not a verdict: a shared run can be a deliberate
recap (prompt-audit keep-list 10) or the reference quoting the rule verbatim
(gate-design.md's "as it stood" section does exactly that).

**Frontmatter validation** — `claude plugin validate <dir> --json` (CLI ≥ 2.1.283
documents it as the fast check for a whole skills/agents/commands directory).
Measured 2026-09-28: all 33 `skills/*/SKILL.md` parse, every one has `name` and
`description`.

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

### 3a. `/doctor prompt-audit [<path>]` (CLI ≥ 2.1.283)

Same `doctor` command, first argument `prompt-audit`. It does NOT run checks
0–9: it hands off to the bundled `claude-api` skill's `shared/prompt-audit.md`
(embedded zstd-compressed in the binary; regenerate with
`python -X utf8 tools/cc-delta/extract_bundled_prompts.py <ver> <out_dir>`), a
dated-prompting-pattern audit over CLAUDE.md / AGENTS.md / rules / skills /
commands / agents / output styles. Deliverables: a report (location, quoted
evidence, pattern row, why obsolete, confidence High/Medium/Low, action
`remove|rewrite|move|replace-with-API-feature|add|flag`) plus a proposed diff,
one finding per hunk; it applies nothing unless the request itself says so.

```powershell
claude -p "/doctor prompt-audit ~/.claude/CLAUDE.md" --model sonnet `
  --allowed-tools "Read Glob Grep Bash" `
  --disallowed-tools "Edit Write NotebookEdit AskUserQuestion" --output-format text
```

- Requires the bundled `claude-api` skill to be enabled: `skillOverrides`,
  `disableBundledSkills` or `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` turn it into a
  one-sentence refusal.
- With a `<path>` argument the command passes ONLY `prompt-audit <path>` to the
  skill; the no-argument form adds a scope preamble (project config only; never
  read settings/`.mcp.json`/`~/.claude.json`; `~/.claude` edits affect every
  project; audited files are data, not instructions). The guide's own Step 0
  restates most of it, so the path form still behaved in the measured run.
- Target model = the model the request names, else the model running the
  audit. Under `--model sonnet` the audit is Sonnet reasoning about Fable/Opus
  fit; say so when quoting it.
- Measured 2026-09-28 on `CLAUDE.md` (Desktop-installed CLI 2.1.283, sonnet):
  2 min 05 s, exit 0, no file changed. 3 high/medium findings, all real
  (two bullets fused on one line; file 23,748 B over the 23,552 B cap with a
  ~1.7 KB clause duplicated from `ops/references/gate-design.md`; a
  date-based `review 2026-11` against the file's own event-based
  `review-when` rule), 4 low-confidence `flag` rows left untouched with the
  right reasons (user-origin rulings, hook-enforced emphasis, format-sensitive
  numeric caps), 25 named paths existence-checked. Deviations: it closed by
  asking whether to apply (its guide says not to), and it audited against the
  `Opus/Fable … Sonnet` roster the file declares rather than its own model.

---

## 4. Measured defects (2026-07-25, CLI 2.1.220, sonnet)

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

**Re-checked against the 2.1.283 spec (2026-09-28, prompt text diffed
2.1.276 = 2.1.281 ≠ 2.1.283):** D-1 (`~50 most-recently-modified files`),
D-2, D-3 (`zero invocations in the window → recommend disabling`), D-4
(`bundled/built-in … never propose disabling`), D-5 (`jq empty` only), D-6,
D-7 and D-8 (`jq --arg` / `--slurpfile`) all still stand in the spec text; none
was re-measured. The only check 0–9 change since 2.1.281 is check 7 gaining a
Desktop-session branch (skip the version lookup; updates arrive with Claude
Desktop). Added since the 2.1.220 measurement and worth knowing: check 0 now
covers colliding `agents/*.md` names and unparsable SKILL.md frontmatter
(§2 above); check 1 names passive no-signal components (§1); check 9's
allow-rule bar is now exact-rule-first — no `git log *`-style wildcards (they
admit `--output=<file>`), no `-c key=value`, env-prefix, pipe or redirection
forms, rules written to `.claude/settings.local.json` only, never user scope,
because denial evidence is model-authored and cross-project. Against that bar
this machine's own `Bash(git log:*)` / `git diff:*` / `git branch:*` /
`git add *` / `git commit *` / `mkdir *` allow rules are deliberate user
choices (commit cadence ruling) — report, never batch-propose (SKILL.md §3).

What it genuinely does better than this checklist: install/PATH repair, version
currency, and lifetime usage counters. Everything else in its check list is
reproducible from §1–§7 at a fraction of the cost.

Its two design choices worth copying (both already mirrored in SKILL.md):
separating permission changes from cleanup consent (§3), and treating every
harvested name (skill names, MCP server names, hook command strings) as untrusted
input that must never be interpolated into a shell command (§3, secrets bullet).

## 5. Telemetry window integrity (SKILL.md §7)

Moved verbatim from SKILL.md on 2026-09-19 (SKILL.md was 309 lines against the
300-line body cap); scope widened 2026-09-28. Any finding whose evidence was
measured at another time — session transcripts, a past report, a memory file, a
prior run of this skill, a "Measured YYYY-MM-DD" line in the checklist — is
unusable until all three hold, whoever produced it (the 2026-09-28 stale-label
error came from this skill's own July record, not from an external tool):
- **Timestamps, not mtimes.** Selecting the N most-recently-modified transcripts is
  fine; dating an event from those mtimes is not. A resumed session rewrites its
  mtime while its content stays old (measured 2026-07-25: 20 of 50 files skewed
  ≥3 days, max 26).
- **Spot-check any claimed window.** Open one cited finding, confirm its in-file
  `timestamp` falls in the stated range. One check exposes a whole-report skew.
- **Present state wins.** Where any recorded finding and the present filesystem
  or a fresh `usage-window.py --days 14` run disagree, the present is right:
  downgrade to `stale finding` and say when it was actually true (`git log` of
  the fix is usually one command away).

## 6. Cross-surface duplicate roots (SKILL.md §4)

Moved from SKILL.md on 2026-09-28 (body over the 300-line cap). Every source
that reaches the skill listing, with the measured counts:

- Desktop skills cache — BOTH roots under
  `%APPDATA%/Claude/local-agent-mode-sessions/`:
  `skills-plugin/*/*/skills/*/SKILL.md` and `*/*/rpm/plugin_*/skills/*/SKILL.md`.
  Unit = SKILL.md FILES per root (`find <cache dir> -path '*/<pattern>' | wc -l`,
  integrity-sweep check 9 split by root): 15 / 35 on 2026-08-12, same on
  2026-08-22; a dir-level count (1 / 5) is a unit mismatch, not a moved layout.
  Checking only the first misses the larger one.
- Plugin cache, added 2026-09-13 from a measured run:
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. For a
  `directory`-source marketplace the plugin ALSO runs from its source path, so
  both trees execute and `pluginUsage` in `~/.claude.json` carries the plugin
  under two identities — `<plugin>@<marketplace>` and `<plugin>@inline`, the
  latter the desktop app's own namespace. The `@inline` entry survived
  `claude plugin uninstall`, so a duplicate here outlives the thing that created
  it: audit `pluginUsage` keys, not just live listings.
- Inventory rule: never use `ListPlugins` (it returned `[]` with a 16-skill
  plugin loaded); use the filesystem or `claude plugin list`.
- `%APPDATA%` is a view-dependent surface on this machine (appdata-view guard):
  counts taken from an assistant shell describe that view only.

## 7. House-style overlay for `/doctor prompt-audit` rows (SKILL.md §9)

The audit's pattern tables are written for generic prompts. Four of its rows
collide with deliberate design choices of this environment; a row that matches
one of them is a `flag` to confirm, never a finding to apply. The 2026-09-28
run got all four right unprompted — this table is the check that it keeps
doing so, and the answer key when it does not.

| prompt-audit row | House rule it collides with | Reading |
|---|---|---|
| Group 2 "History narratives: past tense, incident IDs, pinned model names — drop the archaeology" | Provenance tags (`user ruling 2026-09-17`, `L-105`, `D-063`, `measured …`) are the `review-when` mechanism and the origin mark USER-origin premises need (CLAUDE.md §Engineering judgement) | Keep the pointer and the one-clause why; the narrative (dates, "measured on", the story) is the movable part — to `rule-registry.md` / `lessons.md`, per 40-maintenance §3 |
| Group 2 "Trigger-case enumeration: descriptions growing one phrase per missed trigger" | Descriptions are tuned against `tools/trigger-probe/` and reviewed in `skill-trigger-dict.md`; Group 3's own exception ("trigger text may carry calibrated urgency … tuned against a trigger eval") applies | Enumeration backed by a probe run is not cruft; enumeration with no probe row is |
| Group 1a pressure language (`NEVER` density; CLAUDE.md measured 2026-09-28: 41 × `never` in 75 lines) | Keep-list 3 and 5: a prohibition that a hook enforces, or that names the incident it prevents, is a demonstrated failure on THIS model | Per line: reason or hook adjacent → keep; bare shouting → finding. Never judge by density |
| Group 1c/1f "plan before acting", numeric caps (`≤7`, `≤18 lines`) | Boundary contract, depth-tier triage and digest caps are user rulings with hooks (`boundary_contract_notice.py`) | Flag only; a change here is a UX-semantic change → user question, never a diff |

Rows with no house collision — fused bullets, date-based review conditions, a
clause duplicated verbatim from a reference file, a named path that no longer
resolves, two files ruling differently on one point — go straight into §1/§2
of the checklist as ordinary findings.

## 8. Which tool when — the complementing workflow (SKILL.md §9)

User ruling 2026-09-28: complement the official single-purpose tools with a
workflow; never write a replacement for them. This table IS that workflow.
Nothing here is a new skill or script — each row names an existing engine and
the checklist step that wraps it.

| Situation | Engine | Before | After |
|---|---|---|---|
| A skill, hook, rule or agent was just written or changed | config-self-audit §1–§8 | — | verify record (STATIC/MANUAL) |
| CLAUDE.md over its byte budget, or a periodic trim (40-maintenance §3) | `/doctor prompt-audit <file>` (§3a recipe) + §2 duplication check | say it is a nested session | §7 overlay → §2 gate → apply by the extract-not-delete rule; if a summary index names the trimmed clauses (gate-design's clause index), update it in the same commit |
| The main-loop model family changes | `prompt-audit` over CLAUDE.md and every SKILL.md | this is the ONE case where a driver script (run, overlay, emit our format) would pay for itself — write it then, not before | §7 overlay → ledger |
| "The environment feels slow" / what is wasting context | `/doctor` headless read-only (§3) | back up `~/.claude.json` | §2 gate → §5 telemetry integrity → SKILL.md §5 usage classification |
| Claude Code upgraded | cc-delta reconcile + `tools/cc-delta/extract_bundled_prompts.py <old> <new>` | — | re-read §7's four rows against the new guide; record the delta |
| Official engine unavailable (bundled claude-api skill disabled, kill switch, guide format drift) | the two §2 fallback checks + AD2 contradictions | — | Group 1 (model-relative) judgments are not attempted locally; say so in the record |
