---
xi: 1
what: hmi-report/1 — the one reporting protocol every system-level check speaks to the system-hmi intermediary layer (emitter contract, reader contract, versioning, conformance)
tags: [system-hmi, protocol, monitoring, contract]
aliases: [hmi-report, 回報協定, 監控共用協定, reporting protocol, emitter contract]
layer: rule-tier-adjacent instrument
audience: builder
date: 2026-09-19
status: live
status_note: live v1 — two native emitters (hooks/ops_health_nudge.py --json, tools/hook-proof-of-life/pol.py --json)
---

# hmi-report/1

One document shape for "here is what I checked and what I found". A subsystem that speaks it
needs NO per-source logic inside system-hmi; a subsystem that does not is reached through a
legacy adapter (exit code, sentinel line, status file) that converts to the same point record.
**Native emitters are the target state; adapters are the migration path.**

## 1. Document

```json
{ "protocol": "hmi-report/1",
  "source": "ops-health",
  "generated_at": "2026-09-19T12:00:00Z",
  "points": [ { "id": "ops-health.graph-watchdog",
                "alias": "ops-health 15",
                "ran": true,
                "skip_reason": null,
                "state": "fail",
                "quality": "good",
                "findings": [ { "severity": "alarm", "label": "graph MOC lag",
                                "text": "…remedy text the source already prints…" } ],
                "remedy": "python -X utf8 tools/graph-snapshot/gsnap.py emit-moc" } ] }
```

| field | req | rule |
|---|---|---|
| `protocol` | yes | exactly `hmi-report/1`. A reader that sees another major version reports every point of that source as `probe_error` — it never guesses |
| `source` | yes | stable slug of the emitter |
| `generated_at` | yes | UTC, `YYYY-MM-DDTHH:MM:SSZ` — when the CHECK ran, not when the file was read |
| `points[].id` | yes | `<source>.<slug>`; stable forever; never a check NUMBER (numbers are `alias`) |
| `points[].ran` | yes | `false` = skipped BY DESIGN or never reached. A point with `ran:false` has `state:null` — no exception |
| `points[].skip_reason` | when `ran:false` | short slug (`cwd-not-home`, `not-reached`, `manual-only`, …) |
| `points[].state` | yes | `pass` \| `warn` \| `fail` \| `null`. The EMITTER maps its native severity to a state, once, in one table beside its checks |
| `points[].quality` | no | `good` (default) \| `undetermined` — the emitter's own statement that this run determined nothing (timeout, scenario did not occur). Readers may only DOWNGRADE it (to `stale`, `probe_error`) |
| `points[].findings[]` | no | native detail: `severity` (emitter vocabulary, free), `label`, `text` |
| `points[].remedy` | no | ONE command or sentence |
| `points[].class` | no | verdict class, added 2026-09-19 (additive, E-3): `reconcile` = does the disk agree with the RECORD (git, registry, routing/index, manifest) · `integrity` = does it WORK (tests, calls, links). Absent = `integrity`. The REGISTRY's `class` on the bound point wins over the document's, so an emitter that predates the field needs no change. Readers roll the two classes up SEPARATELY and never fold one into the other |
| `points[].deferred` | no | added 2026-09-23 (additive): the emitter's CLAIM that this point's findings are ALL deliberate deferrals, each waiting on a named trigger. Shape = `tools/system-hmi/hmi/deferral.py` docstring: `kind` (`manual` \| `probe`), `trigger` (non-empty words), `ruling` (required for `manual`), optional `items[]` (`item`, `trigger`), optional `fired`. The `state` stays what the native severity maps to — the claim never changes it (E-7) |
| unknown fields | — | ignored by readers; never an error (forward compatibility) |

## 2. Emitter rules

- **E-1 Declare, then report.** The emitter holds a declared list of every point it CAN report
  and emits all of them on every run. A declared point that never executed is
  `ran:false, skip_reason:"not-reached"`. This is the whole reason the protocol exists: in a
  findings-only output a pass prints nothing, so "clean" and "skipped" are the same silence.
- **E-2 A finding with no declared owner must not vanish**: emit it under its own id with
  `"undeclared": true` and `state:"fail"`.
- **E-3 Additive only.** `--json` (or an equivalent) is a NEW transport. It may not change any
  existing output, condition, ordering or exit code; the emitter's own regression suite proves it.
- **E-4 No thresholds in the document.** Numbers live in the finding text the source already
  prints; system-hmi never restates or re-judges them.
- **E-5 stdout is the document and nothing else.** Diagnostics go to stderr. Exit 0 whenever a
  well-formed document was produced, whatever the states in it; non-zero means "no document".
- **E-6 Known limit to state, not hide**: `ran:true` means the check's block was entered. An
  emitter whose checks fail open inside a swallowed exception says so in its docstring.
- **E-7 A deferral is a claim beside the state, never a state.** Attach `deferred` only when EVERY
  finding of the point is a deliberate deferral with a named trigger; one other finding and the
  point carries no claim. Keep emitting the native state (usually `warn`).

## 3. Reader rules (system-hmi `native` adapter)

- **R-1** Parse failure, wrong `protocol`, non-zero exit, timeout → every registry point bound to
  that source reads `quality: probe_error`, `state: null`.
- **R-2** A registry point whose `id` is absent from a well-formed document → `undetermined`
  (the emitter dropped it), never `pass`.
- **R-3** A document point with no registry entry → surfaced as `UNREGISTERED point` (warn).
  New checks added to an emitter therefore appear on the board by themselves.
- **R-4** `ran:false` → `quality: undetermined` with the `skip_reason` shown.
- **R-5** One invocation per source per collector run; the document is cached for all its points.
- **R-6** A `deferred` claim (or the registry point's own `deferral`, which wins) is resolved by
  `hmi/deferral.py`, only over quality `good` + state `warn`: trigger not fired → the reading is
  `state: pass` with `deferral.status: "holding"` (raw state and evidence kept in the annotation —
  "no operator action is due", ISA-18.2 suppression by design); trigger fired → `warn`, status
  `fired`; no trigger, a manual trigger with no ruling, or a trigger the machine cannot read →
  `warn`, status `rejected`. A fail, and any non-`good` quality, are never deferred (INV-3).
  Every reader that DRAWS a reading shows a holding deferral apart from a plain pass.

## 4. Versioning

Minor additions = new optional fields, same `hmi-report/1`. Anything that changes the meaning of
an existing field = `hmi-report/2`; readers keep a `/1` parser until no emitter speaks it.

## 5. Conformance

`python tools/system-hmi/hmi.py conform <source>` runs an emitter and checks §1–§2 mechanically
(required fields, id prefix, `ran:false ⇒ state:null`, UTC stamp, exit 0, stdout parses as ONE
JSON document). Every native emitter is listed in `registry/sources.json` and is conformance-
checked by `controls.py`.

## 6. Migration ladder for a legacy check

`manual` (a human reads it) → legacy adapter (`exit-code` / `tail-sentinel` / `empty-output` /
`status-file`) → **native emitter**. Promote when the adapter has to pattern-match text, when
"skipped" and "clean" cannot be told apart, or when the check list of a source changes more
than once a quarter. Current natives: `ops-health` (18 points), `hook-proof-of-life` (one point
per registered hook).

## review-when

A third agent adds an emitter (check §2 held without this file being read) · a reader needs a
field that is not here (extend §1, do not smuggle it into `findings`) · the harness changes how
hooks are registered (hook-proof-of-life's point list derives from it).
