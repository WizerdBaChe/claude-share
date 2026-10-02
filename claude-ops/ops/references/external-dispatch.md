# External dispatch — reference

Owner: `20-dispatch.md` §4a decides the PATH and states the redlines; this file
carries the detail that would otherwise saturate it. Environment facts (entry
point, providers, gates, cost) live in `environment.md` "External dispatch tier".
Read this when you have already decided to dispatch externally.

## 1. Profile → task shape

`extdispatch.py status` prints the live chains and each model's health; treat
that output as authoritative over this table, which can go stale.

| Profile | Use for | Leads with | Agent |
|---|---|---|---|
| `code` | code against a stated spec | Zen deepseek (200K) | `card-worker` |
| `review` | read-only adversarial review, findings only | Zen deepseek | `red-team` |
| `agentic` | multi-step work that uses tools | Zen ultra (1M) | `card-worker` |
| `longctx` | multi-file / large reading surface | Zen ultra | `card-worker` |
| `mechanical` | rename / reformat / extract | Zen lightning (262K) | `card-worker` |
| `query` | data lookup / web-grounded fact finding, every claim with a source URL | `agy-flash` (`gemini-3.8-flash-low`) → `agy-flash-37` (`gemini-3.7-flash-low`); Antigravity CLI, Google subscription login; fallback stays inside agy | agy's own |

`query` is the one profile NOT on `opencode serve`: `extdispatch` spawns
`agy -p --output-format json` in the `_agy-worker\cwd` tree under the source's work root with
`USERPROFILE` redirected to its sibling `home` tree (its own
settings.json: shell/write/MCP denied, `read_url` allowed). Login is a one-time
user action: `tools/extdispatch/agy_login.ps1` in the user's own PowerShell.
Acceptance for a query answer is the source URL per claim, spot-checked by the
dispatcher; an answer without sources is not accepted.

Volume: `query` counts in its own class (`PROVIDER_VOLUME["agy"]` — 300/day, 3
concurrent slots, 50 uses per grant), so it neither spends nor waits on the
free tiers' 40/day and single lock. Live 2026-09-15: four simultaneous
dispatches → three answered (8–53 s), the fourth refused `LOCK` exit 7 as
designed. Measured cost: ~60 K input tokens per call (agy's own preamble).
Exit path (credentials, data folders, PATH): the `_agy-worker\uninstall\` tree (same root).

Every chain leads with a keyless Zen id and ENDS on a NIM id, so a Zen-wide
outage degrades rather than stops. Pin one model with `--model <key>` only for
experiment arms: it disables fallback, which is the point — a chain that
silently substitutes a model invalidates the comparison it was run to produce.

Both Zen ids are confirmed to run real multi-step tool loops (zen-deepseek: 4
tool-call rounds / 9 invocations in a review; zen-ultra: grep → glob to a
correct answer in 16.6 s). The catalogue's `tool_call: null` means UNREPORTED,
not unsupported — reading it as "cannot" put NIM at the head of the `agentic`
chain for half a day on no evidence.

## 2. Prompt shape — measured, not stylistic

1. **Output format on the FIRST line.** Peer-measured: 12/12 accepted with the
   format instruction leading, 8/8 rejected with it trailing.
2. **Evidence anchor.** Every claim carries a verbatim quote plus `file:line`,
   or the literal `SOURCE-NOT-FOUND`. State in the prompt that ONE bad anchor
   rejects the whole report — that is what makes fabrication expensive instead
   of free. Verify with `tools/extdispatch/score_redteam.py`, never by reading.
3. **Name the scope explicitly — list the files.** The anchor verifies the
   QUOTE, not the SUBJECT. Measured: given "review commit X", an arm anchored
   character-perfectly on a file that is untracked by git and in no commit, and
   spent 438 s doing it. The same model, same task, with four filenames listed:
   3/3 anchored findings, ACCEPTED, 110 s. Scope drift is the failure the
   anchor layer cannot catch, so the prompt has to.
4. **License the empty answer.** "Returning `[]` is correct and costs nothing."
   The one fabrication on record was produced under visible output pressure —
   its trace reads "need to output findings. Provide none. But perhaps there's
   a defect:". The anchor raises the cost of inventing; this lowers the cost of
   not inventing. Weaker apart than together.
5. **Trade-off to expect.** The anchored prompt suppresses unanchorable
   findings, including true ones: the same sonnet reviewer returned 7 findings
   unanchored and 2 anchored on the same commit. Treat the two prompt shapes as
   different instruments, not as v1 superseded by v2.

## 3. Acceptance

`score_redteam.py --repo <path> --report <file> --commit <sha>` implements the
peer's mechanical layers:

- **structure** — it parses and every required key is present, or it is not a
  report at all;
- **anchor** — the quote matches that file at that line (`OK`), is real but
  elsewhere (`MISMATCH`, sloppy not invented), or was declared unanchorable
  (`NOT-FOUND-DECLARED`, which is an honest answer and not a failure);
- **scope** — the file is in the reviewed commit's change set, else
  `OUT-OF-SCOPE`;
- **spot-check** — any bad anchor sets the whole report to `REJECTED`.

A 100% pass rate is itself a red flag: suspect the gate before believing the
result.

Layer 5 (adversarial) is §7 below. Layer 6 (ledger chain) is already satisfied
by construction: `telemetry.jsonl` and the audit records are written by the
dispatcher, never by the worker, so a worker cannot author its own accounting.
The interop view of that ledger is §8.

## 4. Failure signatures worth recognising

| What you see | What it is |
|---|---|
| `finish:"error"` with `HTTP 429` in `error.message` | quota refusal, surfaced verbatim in ~4 s over HTTP |
| `finish:"tool-calls"` | INTERMEDIATE — the run continues. Treating it as terminal killed three healthy runs |
| no finish, no error, silence past `FIRST_SIGNAL_S` | a wall, not a slow model — the discriminator fires |
| `permission-blocked` | a rule resolved to `ask`, which nobody can answer headless. `ask` is a banned value in this path |
| HTTP 401 whose body says `ModelError: not supported` | wrong provider for that id — read the body, not the status |
| perfect anchors on an unexpected file | scope drift; the prompt did not pin the files |
| `permission-blocked` naming a tool you never configured | that tool matched NO rule and fell through to `ask`. The custom agents carry a leading `"*": "deny"` floor for exactly this; if you still see it, the SERVER IS RUNNING OLD CONFIG |
| a config edit that changes nothing | `opencode serve` reads config at STARTUP and does not hot-reload. Restart it, then re-read `GET /api/agent` and confirm the resolved rules before believing the edit landed |
| every `nvidia`-provider call fails auth while Zen works | the SERVER was started from a shell without `NVIDIA_API_KEY` and inherited that env. `ensure_server()` now recovers the key from `HKCU\Environment`, but a server started before that fix, or by hand, still carries the gap. `status` prints the key state of the CALLER, not of the server |
| `STRUCTURE-FAIL` on a report whose JSON is visibly fine | a UTF-8 BOM. PowerShell's `Out-File -Encoding utf8` writes `EF BB BF`, which `.strip()` does not remove. Fixed in `extract_findings`; expect the same shape wherever a PowerShell redirect feeds a parser |
| `query` fails with `upstream: auth` | the worker home has no live agy login. Run `agy_login.ps1` in the user's own shell; retrying cannot fix it |
| `query` fails with `upstream: stall` after budget + 30 s | `agy -p` waited on a tool approval nobody can answer (agy issue #548); the tree was killed. Check which tool in the audit JSON and adjust the worker settings.json |
| `query` trail shows `upstream: capacity` | agy's server had no room for that slug (503 "No capacity available for model"); the slug is quarantined 300 s and the chain moves to the next agy slug. Both slugs capacity → retry the spool later |
| `query` trail shows `upstream: model` | agy could not resolve the pinned slug ("invalid model selection"). Seen once right after a 503 (2026-09-15), so check the neighbouring rows first; if it persists without a 503, the slug left the catalogue — re-pick from `agy models` and re-verify live |
| `query` trail row with `stage: preflight` | the pinned slug is not in `agy models` (cached 1 h in `tools/extdispatch/agy-catalog.json`); the detail names same-family candidates. Nothing is swapped automatically: pick one, live-verify it, then change `MODELS`. An unreadable catalogue reads `undet` and never blocks. Manual check: `extdispatch.py probe --model agy-flash` (refreshes, spends no completion) or `status` |
| capturing a grant token in a shell | use `grant ... --token-only`; the default output is multi-line JSON and `tail -1` yields `}` |
| `query` fails `empty-answer` with `upstream: permission` | agy soft-denied a tool and produced no text; `denied_actions` in the trail names it |
| `query` fails `context-reset` (before 2026-09-23: `ok:true` with a greeting, "I am ready to help…") | agy lost the task to its own error recovery. Root cause read from agy's transcript (`brain/<conversation_id>/.system_generated/logs/transcript_full.jsonl`) and reproduced on demand: `read_url_content` on a very large page (the full npm packument `registry.npmjs.org/next`, saved as 31 MB; `pypi.org/pypi/pandas/json`) → step CLEARED → empty model output → ERROR_MESSAGE → compaction whose summary is written from the error, not the request → greeting, status SUCCESS. 7 of 85 worker conversations, all publish-DATE checks; wording variants were never the cause. `attempt_agy` now flags the CHECKPOINT-after-ERROR signature (`agy_context_reset`). Fix in the prompt: name a small endpoint (`registry.npmjs.org/<pkg>/latest` for versions; `pypi.org/pypi/<pkg>/<ver>/json`, ~130 KB, carries `upload_time`). npm has NO small endpoint with publish dates (the per-version doc lacks `time`, checked 2026-09-23), so npm dates are read by our own code from the full packument, never by agy (§9). Acceptance still parses structure: `ok` never meant "answered" |
| a call that runs far past its wall-clock budget without ever reporting `stall` | the prompt POST STREAMS, so the socket timeout re-arms on every byte and the polling loop that owns `HANG_S` / `HARD_S` is never reached. The timeout guards the poll, not the call. A slow model is therefore unbounded in practice — pin a fast model for experiments rather than trusting the budget |

## 5. Standing cautions

- A model earns a place in the registry by ANSWERING, never by appearing in a
  catalogue. All three catalogues seen here have lied in different directions.
- Single-sample latency is not a ranking signal: the same model measured
  7,928 ms and ~1,000 ms on consecutive probes, and zen-ultra measured 44.8 s
  on four words and 16.6 s on a two-tool task.
- No rate refusal has been observed on the Zen tier (12 sequential calls,
  spacing 6 s and 0.5 s). That supports "not the bottleneck at single-digit
  RPM, serialised" and nothing stronger. Keep the spacing.
- The stall-detect-and-restart path exists in `ratecheck.py` and has never
  fired. Implemented, not proven.

## 6. Spool — the prompt survives the failure

Every request is written to `tools/extdispatch/spool/<id>.json` BEFORE any gate
runs, and updated with its outcome (`ok` / `failed` / `refused:GrantError` /
`refused:CapError` / `refused:AllowlistError`). Retry costs a command line, never
the prompt again:

    extdispatch.py spool                              # list, newest last
    extdispatch.py retry --id <id> --grant <fresh>    # re-dispatch from spool
    extdispatch.py retry --id <id> --grant <fresh> --model <other>   # reroute

Why it exists: the audit record is written on SUCCESS, which is exactly the case
where the prompt is no longer needed. A refusal or a crash used to leave nothing
on disk, so retrying meant re-composing the prompt in the main session and paying
its context a second time — the most expensive artifact of a dispatch was the
only one not persisted. User request 2026-08-16.

One exception: a REDLINE refusal deletes the spool entry. Work that must never
leave the machine does not get a retryable copy sitting in a spool directory.

Grants are single-use, so a retry needs a fresh one. That is the intended
friction: a retry is a new dispatch and is counted as one.

## 7. Layer 5 — adversarial verification

    redteam_verify.py --repo <path> --report <arm.json> \
        --author <model> --verifier <different model> --grant <token>

One verifier per finding, told to REFUTE rather than confirm. The verifier must
differ from the author; the tool refuses otherwise, because a model checking its
own work reproduces its own error.

**Three outcomes, and the third one is load-bearing**: `survived` / `refuted` /
`inconclusive`. Ties break toward refuted only once the verifier has SPOKEN —
model uncertainty is a refutation. Tool failure is not: an unparseable reply or a
dispatch that died is `inconclusive` and must be re-run. The first live run of
this tool got that wrong and reported two independently-proven-true findings as
refuted, one of which the verifier had actually CONFIRMED in prose the parser
could not read. Never read an inconclusive as a refutation.

**Choosing the verifier — measured on claims, 2026-09-23** (26 claims, 13 false
by date / number / attribution / inversion / fabrication, 2 reps per arm; §9
carries the review-when trigger):

| Verifier, format | detect false | accepted a false claim | false alarm | quotes verbatim on the page |
|---|---|---|---|---|
| codex `gpt-6-luna` effort low, anchored | 0.77 / 0.92 | 0 / 0 | 0 / 0.08 | 27 of 40 fetched; misses read as table cells joined across markup |
| codex `gpt-6-luna` effort medium, anchored | 0.38 / 0.77 | 0 / 0 | 0.08 / 0.08 | 25 of 31 fetched; r1 gave up on 16 of 26 claims |
| codex `gpt-6-luna` effort low, plain reason | 0.69 / 0.77 | 0.08 / 0.08 | 0.08 / 0.15 | — |
| Claude Haiku 4.5, anchored | 0.77 / 0.77 | 0.08 / 0.08 | 0 / 0.08 | 4 of 39 fetched; 29 of the 35 misses share under 40 % of their words as one verbatim run (paraphrase) |
| agy `query`, anchored | — | — | — | `context-reset` (§4): the date claims sent it to 31 MB registry pages; untested on a battery without them |

- **Format**: the anchored report — `{"id","verdict","quote","source_url"}`,
  quote verbatim or `SOURCE-NOT-FOUND` — is what kept accepted-false at zero for
  luna; the plain `reason` format let one false date through in both reps. The
  quote only binds a verifier that obeys it: Haiku returned paraphrase in the
  quote field anyway, so a Haiku anchored report is not checkable by string
  match. Check quotes mechanically against the fetched page before trusting a
  `supported`.
- **Strength**: higher reasoning effort did not buy accuracy; it bought
  variance and an early give-up. Default luna effort low.
- **What every verifier got wrong**: pages that show relative time ("published
  11 hours ago" on npm) produced both unverifiable and false-alarm verdicts, and
  a secondary source's CVSS 10.0 was accepted over the advisory's 9.9. Registry
  facts (version, upload date) go to the registry API, not a verifier; security
  facts are checked against the advisory itself (GitHub GHSA / NVD).
- **Transport**: codex runs outside `extdispatch` — no redline refusal, no
  allowlist, no audit row. The §4b redlines are the dispatcher's own duty on
  that path; send only text you would send to any public tier.

## 8. Interop telemetry

`telemetry.jsonl` is ours and free to grow. `telemetry-peer-v0.1.jsonl` is the
peer family's 8-field schema (`ts / observer / key_label / model / status /
latency_s / evidence / note`), written alongside so a shared contract does not
drift every time we add a field. `key_label` names the TIER on the keyless Zen
path (`opencode-zen-keyless`) rather than inventing a key id — a fabricated label
would silently corrupt the cross-key comparison the file exists for.

## 9. Which fast tier for which task shape — measured 2026-09-23

review-when: any of the three tiers changes model id (agy `gemini-3.8-flash`,
codex `gpt-6-luna`, Claude Haiku 4.5), or a later run of the same battery
disagrees. Evidence: the n8n-concept-survey project's `exp-fast-tasks\` folder (a separate local project tree; tasks,
gold, scorer with two-sided controls, `results/summary.json`; claim-verifier
quote check `results/v1_anchors.json`; report
that project's `report-3-fast-task-fit.html`). 104 scored runs, 2 reps per family — a
ranking at this sample size, not a rate to quote to two digits.

| Task shape | Send to | Why |
|---|---|---|
| batch doc/web lookups, non-private, a minute of wait is fine | agy `query` | tied best on dated-fact lookup; free, 3 slots. Concept/trend topics misattribute — spot-check every source |
| one interactive call, small code or extraction against a pinned spec | codex `gpt-6-luna`, effort low | fastest cloud single-call; medium effort helped one family and hurt another |
| claim verification / third-party check | codex `gpt-6-luna` effort low, anchored format (§7 table) | only arm with zero accepted false claims |
| CJK routing, and ANY input read from `~/.claude` | Claude Haiku (in-house) | redline: `~/.claude` never leaves; Haiku led on CJK routing |
| "latest version" / release-date facts | the registry API (PyPI JSON, npm registry) | 12 of 17 wrong model answers had a gold version under 2 days old |
| a hook slot (~1 s budget) | nothing cloud — cloud probe latency measured 6.7–12.0 s | a local resident model is the only fit; local LLMs are parked, see the n8n-concept-survey project's `handoff-local-llm-fast-tasks.md` |

Two things that do NOT work as gates: a model's verbalized confidence (wrong
answers came back at 0.80–1.00), and a tier's `ok` flag (§4 greeting row).
Writing into a working tree is not on this table on purpose — §4a of
`20-dispatch.md`.
