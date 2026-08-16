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

## 8. Interop telemetry

`telemetry.jsonl` is ours and free to grow. `telemetry-peer-v0.1.jsonl` is the
peer family's 8-field schema (`ts / observer / key_label / model / status /
latency_s / evidence / note`), written alongside so a shared contract does not
drift every time we add a field. `key_label` names the TIER on the keyless Zen
path (`opencode-zen-keyless`) rather than inventing a key id — a fabricated label
would silently corrupt the cross-key comparison the file exists for.
