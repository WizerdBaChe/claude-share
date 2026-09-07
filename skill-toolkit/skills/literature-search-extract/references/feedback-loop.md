# Feedback loop — the run record, the identity key, the reflux path, the registry

Companion to SKILL.md P1/P2/P4.5/P5 and Mode 2. This is the loop as the executor
runs it. Design of record (rationale, invariants INV-1..14, decision register):
`~/.claude/references/lse-feedback-loop-design.md`. Tools: `../loop/runs.py`,
`../loop/reflux.py`, `../loop/idkey.py`; registry: `../consumers/registry.json`;
generated bridge: `bridge.md`.

Why it exists: the most expensive product of a run — claim ↔ support span ↔ source
— used to evaporate at delivery, nothing downstream could report an error back, and
"reuse before re-search" was an instruction nobody could check (arch scan C1–C3,
D1–D5). The loop makes four steps impossible to complete without it (F-1..F-4
below); everything else is a consequence.

## The run folder (INV-1, INV-2)

```
<home>/<run_id>/            home = <vault>\literature\EvidenceRuns  (env LSE_RUN_HOME)
  run.json                  contracts, findings verbatim, sources with keys, reuse_check, ledger stats, review_when
  ledger.jsonl              the P4.5 evidence ledger (unchanged citecheck row schema)
  citecheck.json            `verify/citecheck.py ledger.jsonl --json` output, stored, never rewritten
  sources/<name>.txt        retrieved texts — never leave the machine (INV-10)
  record.md                 human-read 【證據查證紀錄】 with the vault card (written by register)
```

The deliverable's CONTENT does not change because of persistence (INV-2): the ledger
stays behind the deliverable, never inside it.

## Per pipeline step (what cannot complete without the loop)

| Step | Do this | Forcing function |
|---|---|---|
| P1 | `python ../loop/runs.py open --question "<question>" --depth <d> --mode <1\|2> [--caller <consumer id> --preset <name> --domain <profile>]` → prints `run_id`, the folder, and the reuse-check line. It performs the reuse check ITSELF and writes `reuse_check` into `run.json`. | **F-1/F-2**: `register` refuses a run without `reuse_check`; `check` V7 fails it. No `open` → no folder → the gate has nowhere to read from |
| P2 | Copy the printed `reuse check: …` line into `search_trail` (it is pre-seeded in `run.json`). On a match, offer the UPDATE run (seed P2 with the prior run's `sources` + `search_trail`; search only unfilled gaps and the period since). | INV-4 |
| P3/P4 | Derive each source's key as you triage: `python ../loop/idkey.py key "<identifier>"` (or `normalize --doi … --arxiv … --title … --author … --year …` when no identifier resolves). Fill `result.sources[]` with `key`, `aliases`, `unresolved`, `unresolved_basis`, `zotero_key` (from `connectors/zotero_local.py`). | INV-3: an unverifiable identifier is NOT minted into a key — the row becomes `unresolved:` and `gaps` says so |
| P4.5 | Write `ledger.jsonl` and `sources/*.txt` INTO the run folder, then `python verify/citecheck.py <run>/ledger.jsonl --json > <run>/citecheck.json`. | **F-3**: the gate reads from the folder; a floating ledger has no home |
| P5 | Put the deliverable text verbatim into `result.findings` (inline deliveries have no file — this IS the durable copy), fill `gaps`/`confidence`/`search_trail`, then `python ../loop/runs.py register <run>` → `record.md`, index, README. End the deliverable with the loop footer (below). | **F-4**: the mandatory Gaps/Confidence trailer carries the footer; `register` refuses an empty `findings` |
| Mode 2 return | Add `run_id` and `sources[].key` (+ `review_when[]`) to the result contract — callers cite without re-resolving. | **F-5** |
| Zotero close-out | The retraction re-sweep (rubric §3b) reports through `reflux.py retraction` — same path as a person. | **F-6** |

Depth does not change any of this; `quick` runs are the招牌 use case and get a run
folder like every other depth (a `quick` run with one numeric claim = one ledger row).

## The loop footer (INV-5) — after Gaps and Confidence, in every deliverable

```
—— 閉路 (loop) ——  run: <run_id> · keys: doi:… , arxiv:… · 推翻條件 (review-when):
T-1 任一引用來源被撤稿／勘誤（Crossref update-to；Zotero 收尾重掃會回報）
T-2 同題重跑找到 ≥10% 新來源，或出現與本表衝突的主張
T-3 任一消費者回報 correction（reflux）
```
Add a `T-4` line naming a source-specific event when one exists (a standard's next
issue, a preprint's journal version). `register` writes the same footer into `record.md`.

## Identity key (INV-3) — one function, fixed precedence

`doi:` (version of record, lowercase, prefix-stripped) > journal DOI from arXiv metadata
> `arxiv:` (versionless; the DataCite `10.48550/arxiv.<id>` DOI is an alias; the version
is stored apart) > `isbn:` (ISBN-13; an edition is its own key) > `patent:` (jurisdiction +
number + kind code) > `pmid:` > `unresolved:<hash8>` with the basis stored beside it
(NFKC title | first-author surname | year | extra). The Zotero item key is a JOIN key
(`zotero_key`), never the identity key; Zotero is never written (INV-9). A hash is an
id, not the identity: joins compare bases, and two bases under one hash print
`COLLISION` and are never merged.

## Reflux (INV-6, INV-11) — the only write path back

```
python ../loop/reflux.py consumed   --actor <consumer id> --run-id <run_id> [--key <key>] --artifact "<where it was used>"
python ../loop/reflux.py correction --actor <id|user>     --run-id <run_id> [--claim-id C2 --key <key>] --evidence "<locator>" --note "…"
python ../loop/reflux.py retraction --actor a3-retraction-sweep|user --key <key> --evidence "<Crossref update-to notice>"
python ../loop/reflux.py handoff    --actor literature-search-extract --run-id <run_id> --key <key> --note "<why the consumer should deep-read it>"
python ../loop/reflux.py rerun      --actor <id|user> --run-id <old run_id> --artifact <new run_id>   # new run declares wasRevisionOf
python ../loop/runs.py affected <key> [--scan-srg] [--scan-papersurvey]                             # who cited it
```
Events are validated fail-closed and appended to `<home>/reflux.jsonl`; a rejected event
prints its reason and appends nothing. A correction or retraction on a key a ledger row
cites moves the run to `invalidated` (`wasInvalidatedBy`, `invalidatedAtTime`) — the
folder stays; a wrong event is answered by a later event, never by editing the file.
Only runs that are indexed (delivered when filed, or adopted) resolve as targets.

## Consumers (INV-7)

Who calls, with which preset, what they consume and write back, where their store's
identity field is: `../consumers/registry.json` (rows) → rendered as `bridge.md`.
Adding a participant = one row + `runs.py bridge`. SKILL.md keeps only the pointer.

## When the home is unavailable (INV-13)

`open` writes the run to `../runs-unfiled/<run_id>/` with `filed: false` and prints the
line `run not filed: home unavailable` — copy it into `search_trail` and `gaps`. The
deliverable still ships. When the vault is back: `python ../loop/runs.py adopt
<unfiled run dir>`. An unfiled run is not indexed, so reflux cannot target it and the
reuse check cannot find it until adopted — both stated in the same line. `runs.py init`
refuses to create the home when the vault itself is missing (never recreate a vault).

## Checks (INV-12)

`python ../loop/runs.py check <run>` — V1 schema · V2 ledger + citecheck present when
claims are numeric · V3 record.md card · V4 keys well-formed (V4b > 30 % unresolved) ·
V5 footer · V6 related wikilinks · V7 reuse_check precedes the gate and is logged. FAIL
where a tool parses (V1/V2/V3/V4/V7), WARN where a human reads (V4b/V5/V6).
V2's numeric detector is a unit LIST (`runs.py NUM_UNIT_RE`), deliberately not a grammar:
it catches the executor who forgot a row; a number in a unit the list lacks is still a
numeric claim that needs its row (P4.5) — extend the list when a real run shows a miss.
The reuse check tokenizes CJK by character bigrams; a same-topic question rephrased in
Chinese still matches, a different topic sharing a few common bigrams may match too —
a false match costs a glance at the named run ids, a miss costs a re-search.
`runs.py --selftest` runs the good and the bad fixture; `reflux.py --selftest` an
accepted and a rejected event; `idkey.py --selftest` must-parse / must-unresolve.

review-when: the vault note contract (`<vault>\AGENTS.md` §2) changes its
required keys; `citecheck.py` renames a ledger field; a second concurrent writer to
`reflux.jsonl` appears (then the log moves to SQLite — design D-L8).
