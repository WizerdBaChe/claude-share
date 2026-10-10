# entry-schema-lint

Status: live 2026-09-08 | severity: FAIL for ES-1..ES-6 (ES-1..ES-5 promoted 2026-09-08 when the
legacy count reached 0), WARN for the two heuristic checks (consumer = the human/LLM reading the
sweep), exit 2 on a lost anchor | controls: `controls.py` (two-sided, `ALL PASS n/n`) |
wired: `ops/references/integrity-sweep.md` check 29; `config-self-audit` §4 (`--path`).

Enumerates artifacts under `~/.claude` (and, on request, one project tree) that do not carry the
core fields of `ops/references/entry-schema.md`, and the asset properties of
`ops/references/principle-design-guide.md` that have a mechanical detection. Grep-grade: stdlib
only, seconds, no judgement — each line is a defect or nothing.

## Run

```powershell
python -X utf8 tools/entry-schema-lint/lint.py                       # the whole ~/.claude tree
python -X utf8 tools/entry-schema-lint/lint.py --path hooks/x.py      # one artifact (config-self-audit §4)
python -X utf8 tools/entry-schema-lint/lint.py --project-root path\to\repo   # + ES-7 page builders, ES-8 on CLAUDE.md
python -X utf8 tools/entry-schema-lint/controls.py                    # calibration; last line ALL PASS n/n
```

## Checks

| id | reads | rules on | severity |
|---|---|---|---|
| ES-1 | registered `hooks/*.py` docstrings | `STATUS: LIVE\|SHADOW\|RETIRED since <date>`; SHADOW names a graduation criterion | FAIL (ES-1 promoted 2026-09-08; was FAIL born-after / WARN legacy) |
| ES-2 | settings.json × the hook's own docstring | every registered hook DECLARES a runnable proof-of-life (`Proof-of-life: \`python <suite>\``), which sweep check 31 executes; the grammar is `tools/hook-proof-of-life/pol.py`'s, imported not copied | FAIL (promoted) / UNDET unclassifiable |
| ES-3 | `rules/*.md` × CLAUDE.md index line | frontmatter, `paths:`, stem in the `**Path-scoped rules**` line; a review-when in any of its three carriers (frontmatter key, `## review-when` section, inline `review-when: <event>`) — a review DATE is not a trigger, and naming the concept is not declaring one | FAIL (promoted; the review-when case was WARN legacy) |
| ES-4 | `skill-trigger-classes.md` | skill exists; class/source/on-fire in the value sets; zero-means present | FAIL (promoted; the zero-means case was WARN legacy) |
| ES-5 | rules-usage-dict §7, LABEL-REGISTRY §2, rules/*.md, every top-level *.md, rule-registry | owner and mechanism paths resolve; in top-level docs every backticked capability path exists (a glob must match, a `<placeholder>` is skipped, a skill-relative path resolves under `skills/<x>/` — 2026-10-03, when OPERATOR-GUIDE/PHILOSOPHY counts became pointers; whether the target is in git is tracking-refs' half); registry entries carry current/why/evidence | FAIL (promoted; the registry-entry case was WARN legacy) |
| ES-6 | principle-design-guide.md | `CLAUDE.md «phrase»` verbatim; `PHILOSOPHY §一.n` heading exists | FAIL |
| ES-7 | `--project-root` `*.py` with `<html` | data-page-class, data-audience, a shared shell module | WARN (heuristic) |
| ES-8 | rules/, skills/*/SKILL.md, ops/*.md | ruling sentences bound to a tool or moment (RD-1) | WARN (heuristic) |

Legacy = first git commit on or before `SCHEMA_BORN` (2026-09-08). A class in `SEVERITY_PROMOTED`
reports FAIL regardless of birth date; two named triggers put it there — the class rose above its
baseline in two consecutive sweeps, or the class's legacy count reached **0**, at which point WARN
no longer describes anything ("legacy debt") and the next WARN could only be a regression printed
quietly. ES-1..ES-5 were promoted 2026-09-08 under the second trigger, the day the born-RED
baseline closed (0 FAIL / 59 WARN → 0 / 0). ES-7/ES-8 are NOT eligible: a heuristic prompts a
review and may never rule FAIL. Rollback: remove the class from the set.

Until that same day four findings hardcoded `"WARN"` instead of calling `severity_for`, so the
promotion this README describes would have been inert for ES-1's graduation case, ES-3, ES-4 and
ES-5 — documented, trusted, and unable to fire. C-05/C-05b/C-05c are the control pair that now
proves the lever moves (and that the heuristics stay out of it).

## Calibration

`controls.py` builds a temp `~/.claude`-shaped fixture with a known-bad and a known-good per check
(C-01..C-31, plus C-05b/C-05c, C-08b..C-08e and C-11b..C-11d) plus C-00, which runs the live tree read-only and
asserts only that no anchor is lost. Two of those are REGRESSION cases for gates that were loosened
on 2026-09-08 and are named as such in the file: C-08 (a hook absent from `integrity-sweep.md` with
no declaration is still caught, which is what the replaced position-based ES-2 predicate caught) and
C-11c/C-11d (a rule that only MENTIONS `review-when`, or writes the key with nothing after it, is
still caught by the widened ES-3 detector).
ES-7's shell predicate is per builder: when 2+ emitters of `<html` import no other emitter (roots),
every root that is not imported by 2+ distinct non-test modules is an independent shell (a helper
imported by many builders is not a shell -- the SSLD `selfdecl` case that silenced the first cut;
one wrapper importing one viewer is a builder split in two files, not sharing). A compliant
delegating builder has no `<html` literal at all, so it is never judged; the known-good fixtures
carry no placebo comments (red-team finding 2026-09-08).
Born-RED baseline 2026-09-08 on the live tree: see `ops/references/integrity-sweep.md` check 29.

## Not covered

SKILL.md frontmatter beyond `name`/`description` (loader-fixed; the trigger-class block is the
carrier); `skill-trigger-dict.md` bullets (`tools/skill-routing-audit.py`); intake records and xi
cards (their own parsers); OPS.md / inbound-routing / 40-maintenance §2a rows (documented-only in
the adapter table); the verdict KIND of a hook (deny/warn/annotate) versus its docstring
(`config-self-audit` §1 reads the code). ES-7/ES-8 are heuristics: a hit is a review prompt.

## review-when

- `settings.json` hook command shape changes (the `hooks/<name>.py` regex stops matching) → ES-1/ES-2 go blind; C-00 does NOT catch this — re-check `registered_hooks()` after a harness upgrade.
- `skill-trigger-classes.md` gains a key → extend ES-4 and the parser together (`tools/skill-routing-audit.py load_classes()`).
- the CLAUDE.md index line is renamed → ES-3 exits 2 (that is the alarm, not a bug).
- `tools/hook-proof-of-life/pol.py` moves or its declaration grammar gains a class → ES-2 emits a
  LOST anchor (it imports that module rather than copying the regex, so the two cannot drift apart
  silently); fix `load_pol()`'s two named search sites, never re-implement the grammar here.
