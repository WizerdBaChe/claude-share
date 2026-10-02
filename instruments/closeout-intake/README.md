# closeout-intake — lossless lesson intake (`ops/lessons/`)

> status: LIVE since 2026-09-07 (claude-config Phase 23). Owner of the record format
> registered in `ops/rules-usage-dict.md` §7 ("lessons entry"). Severity: `add`/`event`
> are FAIL-CLOSED writer gates; `check`/`report` are WARN-grade (read by a model/human;
> exit 4 so a sweep sees it); `hooks/intake_guard.py` is DENY.

Sole build basis: `references/closeout-capture-r3-psm-2026-09-07.md`. Semantics owner:
`references/closeout-capture-r3-design-2026-09-07.md` §4 (BR / INV / S / D ids cited below).

## What it is

One Markdown file per lesson under `ops/lessons/L-nnn.md` — the **intake record**: the
authoritative, lossless text, born only through `intake.py add` after validation (INV-1),
never rewritten afterwards (INV-2; the guard hook denies Write/Edit/shell writes). Every
later step — a recurrence, a fold into a rule, a supersession, a retraction — is one
appended line under `## Events`. `hits` and lifecycle state are DERIVED from those events
(INV-4). `ops/lessons.md` is a GENERATED index of capped cards (INV-5) — the path is kept
so `L-nnn` citations keep resolving.

Why: the hand-written two-file ledger needed 11 manual steps at ~190k context; 77 % of
writing sessions skipped the second file, ids collided twice, and every few weeks a
several-hundred-line "trim pass" rewrote what had been captured (R2 evaluation RC1–RC5).
The user's premise: capture with a fixed format so later consolidation loses less —
every processing step loses or changes something, so processing appends, never rewrites.

## Write a lesson (Step 8.2 of the command loop)

1. Write a draft with the Write tool (scratchpad), shape:
   ```
   ---
   what: 一句中文 (one English clause)        # bilingual, xi grammar
   tags: [verify, silent-failure]             # ≥1 word from tags.txt (D3)
   ---
   ## Record
   locator: turn 14 / tool_use_id toolu_…     # required; literal `unrecorded` allowed
   project: SSLD                              # optional (default: registry lookup of cwd)

   ## Context      (≤400 B)
   ## Pitfall      (≤700 B — the MECHANISM)
   ## Fix          (≤700 B — and where it lives if folded)
   ## Detection    (≤300 B, optional)
   ## Narrative    (unbounded, verbatim — the "lose less" home)
   ```
2. `python tools/closeout-intake/intake.py add --from <draft.md>` → prints the card and
   `ops/lessons/L-nnn.md`. A reject (exit 2) names the rule (D1–D9) and the repair,
   e.g. `D5 Pitfall over cap by 112 B — move at least 112 B to ## Narrative`. Nothing is
   written on a reject; edit the draft and rerun.

Never add `xi:`, `aliases:`, `date:`, `status:`, `id:`, `created:`, `session:`, `hits:`
or `## Events` to a draft — the tool owns them (D7–D9).

**`session:` resolves from this process, not from the shared pointer** (2026-09-07, ported
from `ledger.py`; cases C-97..C-99): explicit `--session` → `CLAUDE_CODE_SESSION_ID` →
`cache/handoff/current-session.json` → `unrecorded`. That pointer is one global file every
session's every prompt overwrites, so under concurrency it names whichever session prompted
last; a record is never rewritten (INV-2), which makes a wrong `session:` permanent. A
disagreement prints one stderr warning and records under this process.

## Later events (`intake.py event L-nnn --kind …`)

| kind | args | effect |
|---|---|---|
| `recurrence` | `--held yes\|no --note "…"` (`--held` REQUIRED) | hits+1. `held=yes` = an existing rule or detection caught it BEFORE the output reached its consumer; `held=no` = it escaped. On a folded record: `no` → "folded but recurring" (report (b)); `yes` → "the fold held" (report (b′)) |
| `fold` | `--target "ops/40-maintenance.md §2a"` | state folded, `status: spent`; target file must exist |
| `fold` on a folded record (re-fold) | `--target … --cause trigger-gap\|inert-text\|wrong-layer\|different-pitfall\|misattributed --note "…"` | admitted ONLY after a `held=no` recurrence since the last fold; the line records `cause=` + reason; clears (b). Routing: `ops/40-maintenance.md` §2a re-fold loop |
| `supersede` | `--successor L-mmm --note "…"` | state superseded, `status: superseded: L-mmm` |
| `retract` | `--note "…"` | state retracted, `status: spent` |

Illegal transitions (design §4.4 table) are refused with `ILLEGAL-EVENT state×kind`. The
front-matter `status:` line is the ONE line the tool rewrites outside `## Events` (S-9).

## Read side

- `intake.py match --text "…" [--project X]` — ≤3 cards / ≤1500 B by tag overlap (INV-7);
  `hooks/intake_match_shadow.py` (UserPromptSubmit, SHADOW) calls it on every prompt and
  only logs `telemetry/intake-match.jsonl` `{ts, session, n_cards, bytes, ids, top_score,
  ms, prompt_len}` — it prints nothing. Measured at M3 (2026-09-07, five direct probes on
  the 54-record store): `ms` median 108 (93–125), under the PSM's 200 ms target; each
  probe returned ONE card of 1,448 B — an imported legacy card fills most of the 1,500 B
  budget by itself, so until records are born capped the budget effectively means "one
  card" (a fact for the `INTAKE_INJECT_BUDGET` review, not a defect). Graduation to real
  injection is a user gate; its criterion (precision on ~20 real prompts read from the
  log) is pending.
- `intake.py report` — (a) hits≥2 never folded → route through `40-maintenance.md` §2a;
  (b) folded but recurring; (c) dormant (90 d without an event, hits 1); (d) status
  inconsistent. `--nudge` prints ≤2 lines for `ops_health_nudge.py`.
- `intake.py check [--against HEAD] [--index]` — INV-1/2/4/5/6 over the store; exit 4 on
  any violation. Runs in `ops/references/integrity-sweep.md`.
- grep / Obsidian / cross-index: records are valid xi cards (`what`, `tags`, `aliases`).

## Controls

`python tools/closeout-intake/controls.py` — two-sided cases C-01…C-96 on a temp store
(never `ops/lessons/`): every D-rule positive+negative, INV-2 mutations against a git
HEAD, a 20-process id race (INV-3), render idempotence, a Hypothesis property for the
match budget, the real legacy import with `--verify` plus a tampered source, stale/fresh
lock, and the guard hook payloads. Last line `ALL PASS n/n` (`ALL PASS 47/47` at M2,
2026-09-07); a `PASS … (skipped C-90…)` line means `hooks/intake_guard.py` is missing —
read it as the guard being DOWN. The sweep (`ops/references/integrity-sweep.md` check 5/5b)
runs `intake.py check --against HEAD --index` and this harness's last line.

## Registration set (M2, one commit — where the mechanism is wired)

| surface | what |
|---|---|
| `settings.json` PreToolUse `Write\|Edit\|Bash\|PowerShell` | `hooks/intake_guard.py` (DENY; fail-open; telemetry `telemetry/intake-guard.jsonl`, deny/error rows only) |
| `hooks/ops_health_nudge.py` check 1 | `intake.py report --nudge` (SEV_QUEUE, 1.5 s budget, every cwd) — replaced `LESSON_CAP` |
| `ops/references/integrity-sweep.md` 5 / 5b | `check --against HEAD --index` + `controls.py \| tail -1` — replaced 5/5b/5c/5d |
| `ops/rule-registry.md` `INTAKE` | semantics + sub-keys `INTAKE_FIELD_CAPS` / `INTAKE_INJECT_BUDGET` / `INTAKE_LOCK_STALE_S` (PROVISIONAL, review-when); `LESSON_CAP` retired, `lessons ledger shape` superseded |
| `ops/40-maintenance.md` §2 | destination row = `intake.py add` / `event`; §3 count-cap row deleted |
| `ops/rules-usage-dict.md` §7 | "lessons entry" minimum fields → this README is the owner |
| `ops/10-command-loop.md` Step 1(b) / 8.2, `ops/60-bootstrap.md` §A.1 | `intake.py match` before acting; `intake.py add` at close-out |
| `LABEL-REGISTRY.md` `L-NNN` | owner `ops/lessons/`, index generated |
| `tools/ops-health-test/check_cap_binding.py`, `test_ops_health_nudge.py` | `LESSON_CAP` binding removed; the budget fixture seeds check 1 with a stub tool |
| memory `pitfall-card-convention.md` | one line: written via `intake.py` since 2026-09 |

## Cutover record (2026-09-07)

`intake.py import` moved 35 live cards + 19 Archived bullets (54 ids, = the 54 detail
sections) into records with the legacy card/bullet AND the full detail section verbatim
inside `## Narrative` (fenced), `imported hits=N` events, and `fold →` events for the
bullets. `ops/references/lessons-detail.md` is FROZEN in place; the pre-cutover index is
in git history (`git show 483435f:archive/lessons-cutover-2026-09/NOTE.md`; the ledger itself `git show fa08fa3:ops/lessons.md`). Retired: `LESSON_CAP`, integrity-sweep checks
5/5b/5c/5d, rule-registry `LESSONS-SPLIT`.

Caps and budgets: `ops/rule-registry.md` keys `INTAKE_FIELD_CAPS`, `INTAKE_INJECT_BUDGET`,
`INTAKE_LOCK_STALE_S` (values are PROVISIONAL; the constants live in `intake_core.py` /
`intake.py` — the registry names them, never restates them).
